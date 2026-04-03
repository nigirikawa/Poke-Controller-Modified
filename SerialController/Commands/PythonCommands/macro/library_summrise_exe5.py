import os
import csv
import cv2
import numpy as np
import difflib
from Commands.Keys import Hat
from .base_exe_trade import BaseExeTrade

# ============================================================
# OCR モジュールのインポート準備
# ============================================================
from .lib_ocr.predictor import ExeCharPredictor, TEMPLATE_CODE, TEMPLATE_NUMBER_BLANK
import datetime

# ============================================================
# 座標設定 (process.py より反映)
# ============================================================
Y_RANGES = [
    (171, 230), (235, 294), (299, 358), (363, 422), (427, 486), (491, 550), (555, 614),
]

X_RANGES = [
    (256, 287), (288, 319), (320, 351), (352, 383), (384, 415), (416, 447), (448, 479), (480, 511),# チップ名 (8文字)
    (577, 608), # コード (1文字)
    (673, 704), (705, 736), # 枚数 (2文字)
]
# ============================================================
# カタカナ正規化 (ァ→ア 等)
# ============================================================
KANA_MAP = str.maketrans("ァィゥェォッャュョ", "アイウエオツヤユヨ")

def normalize_kana(text):
    """小書きカタカナを通常のカタカナに変換する"""
    return text.translate(KANA_MAP)

class library_summrise_exe(BaseExeTrade):
    NAME = "エグゼ5_ライブラリ集計"

    def __init__(self, cam):
        super().__init__(cam)
        self.predictor = None
        self.chip_db = {} # {チップ名: [可能コードリスト]}
        self.output_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "recv_library.csv"))
        self.processed_chips = set() # 重複登録防止用 (チップ名+コード)
        self.last_7th_row_img = None

    def load_db(self):
        """チップリストCSVをロードして辞書化する"""
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "exe5_chip_list.csv")
        db_path = os.path.normpath(db_path)
        
        if not os.path.exists(db_path):
            print(f"Error: DB file not found: {db_path}")
            return False
            
        try:
            with open(db_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                for row in reader:
                    if len(row) < 2:
                        continue
                    name = normalize_kana(row[0].strip('"'))
                    codes = [c.strip() for c in row[1].strip('"').split(",")]
                    self.chip_db[name] = codes
            print(f"DBロード完了: {len(self.chip_db)}件")
            return True
        except Exception as e:
            print(f"DBロードエラー: {e}")
            return False

    def _save_chip(self, name, code, count):
        """チップ情報をCSVに保存し、処理済みセットに追加する"""
        chip_key = f"{name}_{code}"
        if chip_key in self.processed_chips:
            return False
            
        with open(self.output_path, "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([name, code, count])
        
        self.processed_chips.add(chip_key)
        return True

    def init_predictor(self):
        """推論エンジンの初期化 (パスを明示的に指定)"""
        try:
            # 自身のディレクトリを基準に、lib_ocr/data 内のパスを解決
            self.predictor = ExeCharPredictor(
                "C:\\develop\\pokecon\\Poke-Controller-Modified-Extension\\SerialController\\Commands\\PythonCommands\\macro\\lib_ocr\\data\\best_model.pth", 
                "C:\\develop\\pokecon\\Poke-Controller-Modified-Extension\\SerialController\\Commands\\PythonCommands\\macro\\lib_ocr\\data\\class_mapping.json"
            )
            return True
        except Exception as e:
            print(f"Error: Failed to initialize Predictor: {e}")
            return False

    def preprocess(self, crop):
        """OCR用の前処理（2値化）"""
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def process_row(self, frame, r_idx):
        """
        指定行のOCR、パイプラインフィルタリング、DB記録を行う。
        """
        y_start, y_end = Y_RANGES[r_idx]
        
        # STEP 1: OCR推論
        name_ocr_results = [] # [[(文字, スコア), ...], ...]
        binaries = []
        raw_name = ""
        
        # チップ名 (8文字対応)
        for i in range(8):
            x_start, x_end = X_RANGES[i]
            crop = frame[y_start:y_end, x_start:x_end]
            binary = self.preprocess(crop)
            binaries.append(binary)
            top_k = self.predictor.predict_top_k(binary, k=3)
            # 正規化した Top-K 結果を格納
            norm_top_k = [(normalize_kana(char), prob) for char, prob in top_k]
            name_ocr_results.append(norm_top_k)
            # 信頼度低により空になった場合は空文字を連結
            raw_name += norm_top_k[0][0] if norm_top_k else ""
        raw_name = raw_name.strip()
        
        # コード (8番目)
        code_pos = 8
        x_sc, x_ec = X_RANGES[code_pos]
        crop_code = frame[y_start:y_end, x_sc:x_ec]
        bin_code = self.preprocess(crop_code)
        binaries.append(bin_code)
        code_ocr_top_k = self.predictor.predict_top_k(bin_code, allowed_chars=TEMPLATE_CODE, k=3)
        raw_code = code_ocr_top_k[0][0].strip()
        
        # 枚数 (9, 10番目)
        raw_count = ""
        for idx in [9, 10]:
            x_sn, x_en = X_RANGES[idx]
            crop_cnt = frame[y_start:y_end, x_sn:x_en]
            bin_cnt = self.preprocess(crop_cnt)
            binaries.append(bin_cnt)
            char, _ = self.predictor.predict(bin_cnt, allowed_chars=TEMPLATE_NUMBER_BLANK)
            raw_count += char
        raw_count = raw_count.strip()

        if not raw_name:
            return # 空行

        # STEP 2: あいまい検索（候補抽出）
        # DB側は読み込み時に正規化されている前提だが、念のためここでも正規化して検索
        raw_name_norm = normalize_kana(raw_name)
        candidates = difflib.get_close_matches(raw_name_norm, self.chip_db.keys(), n=3)

        # STEP 3: 段階的なフィルタリング・パイプライン
        ocr_top_3_codes = [item[0] for item in code_ocr_top_k]

        # 【フェーズ1】 距離1（完全一致）の一致を最優先
        for cand in candidates:
            dist = difflib.SequenceMatcher(None, raw_name_norm, cand).ratio()
            if dist >= 1.0:
                possible_codes = self.chip_db.get(cand, [])
                matched_code = next((c for c in ocr_top_3_codes if c in possible_codes), None)
                
                if matched_code:
                    if self._save_chip(cand, matched_code, raw_count):
                        print(f"特定成功(完全一致): {cand} [{matched_code}] {raw_count}枚")
                    return
                else:
                    # Top-3にないが名前が完全一致する場合：コードの候補を絞り込んで再OCR
                    print(f"  完全一致候補 '{cand}' ですが Top-3 コード不一致。再検証を開始します。候補：{possible_codes} vs OCR：{ocr_top_3_codes}")
                    # allowed_chars に候補を絞り込んで再推論
                    retry_code, _ = self.predictor.predict(bin_code, allowed_chars=possible_codes)
                    if retry_code:
                        if self._save_chip(cand, retry_code, raw_count):
                            print(f"特定成功(完全一致・再検証採用): {cand} [{retry_code}] {raw_count}枚")
                        else:
                            print(f"特定失敗(完全一致・再検証採用): {cand} [{retry_code}] {raw_count}枚")
                        return
                    else:
                        print(f"  再検証でもコードが特定できませんでした ('{cand}')")

        # 類似度距離の出力
        for cand in candidates:
            dist = difflib.SequenceMatcher(None, raw_name_norm, cand).ratio()
            print(f"  [あいまい検索] 候補: {cand:10s}, 距離: {dist:.3f} (キー: {raw_name_norm})")

        # 【フェーズ2】 スコア順にコード検証
        # get_close_matches の結果は既にスコア順にソートされている
        for cand in candidates:
            dist = difflib.SequenceMatcher(None, raw_name_norm, cand).ratio()
            # 距離1のものは既に検証済みだが、ロジック簡略化のため再度流しても問題ない
            possible_codes = self.chip_db.get(cand, [])
            matched_code = next((c for c in ocr_top_3_codes if c in possible_codes), None)
            
            if matched_code:
                if self._save_chip(cand, matched_code, raw_count):
                    print(f"特定成功(コード整合性): {cand} [{matched_code}] {raw_count}枚 (距離: {dist:.3f})")
                return
            else:
                print(f"  除外(コード不一致): '{cand}' (正規:{possible_codes} vs OCR:{ocr_top_3_codes})")

        # 【フェーズ3】 すべての検証に落ちた場合のフォールバック
        self._record_error_and_continue(frame, raw_name, raw_code, raw_count, binaries, name_ocr_results, code_ocr_top_k, candidates)
        return

    def _record_error_and_continue(self, frame, raw_name, raw_code, raw_count, binaries, name_ocr_results, code_ocr_top_k, target_candidates):
        return
        """照合不備時の共通エラー記録フロー"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cap_dir = os.path.join("Captures", "Macro", "rokkuman_exe")
        if not os.path.exists(cap_dir):
            os.makedirs(cap_dir)

        # 画像保存 (ユーザーによりコメントアウト中)
        # filename = os.path.join(cap_dir, f"error_ocr_mismatch_{timestamp}.png")
        # cv2.imwrite(filename, frame)
        # for i, b in enumerate(binaries):
        #     role = "name" if i < 8 else ("code" if i == 8 else "count")
        #     cv2.imwrite(os.path.join(cap_dir, f"error_ocr_mismatch_{timestamp}_char_{i}_{role}.png"), b)

        combined_name = "|".join(target_candidates) if target_candidates else f"【要確認】{raw_name}"
        
        print(f"WARNING: 照合不備のため候補をすべて記録して続行します: {combined_name}")
        print(f"  (読み取りコード: '{raw_code}', 枚数: '{raw_count}')")
        print("--- 各文字の Top-K 推論結果 ---")
        for i, top_k in enumerate(name_ocr_results):
            ranks = ", ".join([f"'{char}'({prob:.2f})" for char, prob in top_k])
            print(f"  位置 {i}: {ranks}")
        print(code_ocr_top_k)
        print("---")
        
        with open(self.output_path, "a", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([combined_name, raw_code, raw_count])
        
        self.processed_chips.add(f"{combined_name}_{raw_code}")

    def do(self):
        if not self.load_db():
            return
        if not self.init_predictor():
            return

        # 出力ファイル初期化 (ヘッダのみ)
        with open(self.output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["チップ名", "コード", "枚数"])

        print("ライブラリ集計を開始します...")

        # --- 1ループ目 (1行目) ---
        frame = self.camera.readFrame()
        if frame is not None:
            self.process_row(frame, 0)
        
        # --- 2〜6ループ目 (2行目〜6行目) ---
        for r_idx in range(1, 6):
            self.press(Hat.BTM, 0.2, 0.4) # アニメーション待ち含む
            frame = self.camera.readFrame()
            if frame is not None:
                self.process_row(frame, r_idx)

        # --- 7ループ目 (7行目とスクロール検知準備) ---
        self.press(Hat.BTM, 0.2, 0.4)
        frame = self.camera.readFrame()
        if frame is not None:
            self.process_row(frame, 6)
            # 画像比較用に保存 (1文字目左端 256 〜 右端 1279)
            y7_s, y7_e = Y_RANGES[6]
            self.last_7th_row_img = frame[y7_s:y7_e, 256:1279].copy()

        # --- 8ループ目以降 (スクロール処理ループ) ---
        while True:
            self.press(Hat.BTM, 0.2, 0.4)
            frame = self.camera.readFrame()
            if frame is None:
                continue

            # 現在の7行目の画像を切り出し (256 〜 1279)
            y7_s, y7_e = Y_RANGES[6]
            current_7th_row_img = frame[y7_s:y7_e, 256:1279]

            # 前回画像と比較
            diff = cv2.absdiff(current_7th_row_img, self.last_7th_row_img)
            if np.mean(diff) < 0.1: # 変化がなければ停止
                print("画面の一番下まで到達しました。集計を終了します。")
                break
            
            # 画像更新して処理
            self.last_7th_row_img = current_7th_row_img.copy()
            self.process_row(frame, 6)

        print(f"全集計が完了しました。出力: {self.output_path}")

if __name__ == "__main__":
    import sys
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    serial_controller_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    sys.path.insert(0, serial_controller_dir)
    __package__ = "Commands.PythonCommands.macro"

    class DummyCamera:
        def readFrame(self): return None
    
    try:
        print("--- コマンドライン実行モード ---")
        app = library_summrise_exe(DummyCamera())
    except Exception:
        import traceback
        traceback.print_exc()