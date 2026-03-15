import os
import csv
import cv2
import numpy as np
import difflib
from Commands.Keys import Hat
from .base_exe_trade import BaseExeTrade
import time

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
        (256, 287),
        (288, 319),
        (320, 351),
        (352, 383),
        (384, 415),
        (416, 447),
        (448, 479),
        (480, 511),# ココまでチップ名
        (577, 608), # コード (1文字)
        (673, 704), (705, 736), # 枚数 (2文字)
]

class library_summrise_exe(BaseExeTrade):
    NAME = "エグゼ_OCRデータ作成"

    def __init__(self, cam):
        super().__init__(cam)
        self.predictor = None
        self.chip_db = {} # {チップ名: [可能コードリスト]}
        self.output_path = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "recv_library.csv"))
        self.processed_chips = set() # 重複登録防止用 (チップ名+コード)
        self.last_7th_row_img = None

    def load_db(self):
        """チップリストCSVをロードして辞書化する"""
        db_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "exe4_chip_list.csv")
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
                    name = row[0].strip('"')
                    codes = [c.strip() for c in row[1].strip('"').split(",")]
                    self.chip_db[name] = codes
            print(f"DBロード完了: {len(self.chip_db)}件")
            return True
        except Exception as e:
            print(f"DBロードエラー: {e}")
            return False

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
            name_ocr_results.append(top_k)
            raw_name += top_k[0][0]
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
        candidates = difflib.get_close_matches(raw_name, self.chip_db.keys(), n=3, cutoff=0.0)

        # STEP 3: 段階的なフィルタリング・パイプライン
        
        # 検証用の事前準備
        valid_ocr_top_k = []
        for res in name_ocr_results:
            if res[0][0] == "": break # Top-1が空文字＝終端
            valid_ocr_top_k.append(res)
        valid_count = len(valid_ocr_top_k)
        ocr_top_3_codes = [item[0] for item in code_ocr_top_k]

        # 【フェーズ1】 コード整合性による絞り込み
        step1_candidates = []
        for cand in candidates:
            possible_codes = self.chip_db.get(cand, [])
            if any(code in possible_codes for code in ocr_top_3_codes):
                step1_candidates.append(cand)
            else:
                print(f"  除外(コード不一致): '{cand}' (正規:{possible_codes} vs OCR:{ocr_top_3_codes})")

        # 【フェーズ2】 フェーズ1通過後の要素数による分岐（アーリーリターン）
        length = len(step1_candidates)
        
        if length == 1:
            # ケースA: 1つに特定できた場合 (成功)
            best_name = step1_candidates[0]
            possible_codes = self.chip_db.get(best_name, [])
            best_code = next(code for code in ocr_top_3_codes if code in possible_codes)
            
            # 記録処理
            chip_key = f"{best_name}_{best_code}"
            if chip_key in self.processed_chips: return
            with open(self.output_path, "a", encoding="utf-8", newline="") as f:
                csv.writer(f).writerow([best_name, best_code, raw_count])
            self.processed_chips.add(chip_key)
            print(f"記録済: {best_name} [{best_code}] {raw_count}枚")
            return

        elif length == 0:
            # ケースB: 全滅した場合 (エラー記録)
            self._record_error_and_continue(frame, raw_name, raw_code, raw_count, binaries, name_ocr_results, code_ocr_top_k, candidates)
            return

        # ケースC: 要素数 >= 2 の場合は【フェーズ3】へ進む
        print(f"複数候補が残っています: {step1_candidates}。名前の精密検証を開始します。")

        # 【フェーズ3】 文字列ランキング（Top-3）検証による最終絞り込み
        for cand in step1_candidates:
            # 1. 文字数チェック
            if len(cand) != valid_count:
                print(f"  検証失敗(文字数): '{cand}'")
                continue
            
            # 2. 名前の Top-3 照合
            name_match = True
            for i in range(valid_count):
                target_char = cand[i]
                if target_char not in [item[0] for item in valid_ocr_top_k[i]]:
                    name_match = False
                    break
            
            if name_match:
                # 合格した瞬間に確定 (早期終了)
                best_name = cand
                possible_codes = self.chip_db.get(best_name, [])
                best_code = next(code for code in ocr_top_3_codes if code in possible_codes)
                
                chip_key = f"{best_name}_{best_code}"
                if chip_key in self.processed_chips: return
                with open(self.output_path, "a", encoding="utf-8", newline="") as f:
                    csv.writer(f).writerow([best_name, best_code, raw_count])
                self.processed_chips.add(chip_key)
                print(f"特定成功(精密検証): {best_name} [{best_code}] {raw_count}枚")
                return

        # 【フェーズ4】 すべての検証に落ちた場合のフォールバック
        print("警告: フェーズ3の精密検証を通過した候補がありません。")
        self._record_error_and_continue(frame, raw_name, raw_code, raw_count, binaries, name_ocr_results, code_ocr_top_k, step1_candidates)
        return

    def _record_error_and_continue(self, frame, raw_name, raw_code, raw_count, binaries, name_ocr_results, code_ocr_top_k, target_candidates):
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
        number = 0
        cap_dir = os.path.join("C:\\develop\\pokecon\\Poke-Controller-Modified-Extension\\SerialController\\Captures\\lern2")
        if not os.path.exists(cap_dir):
            os.makedirs(cap_dir)

        while True:
            
            # 画像保存 (ユーザーによりコメントアウト中)
            filename = os.path.join(cap_dir, f"{number:03}.png")
            # 下に移動。0.85秒待機
            self.camera.saveCapture(
                filename=filename
            )
            self.press(Hat.BTM, 0.15, 0.85)
            
            number += 1
        
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