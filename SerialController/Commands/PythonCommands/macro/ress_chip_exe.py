import os
import csv
import cv2
import numpy as np
import difflib
from Commands.Keys import Button, Hat
from .base_exe_trade import BaseExeTrade

from .lib_ocr.predictor import ExeCharPredictor, TEMPLATE_CODE, TEMPLATE_NUMBER_BLANK

# ============================================================
# 座標設定 (library_summrise_exe.py と共通)
# ============================================================
Y_RANGES = [
    (171, 230), (235, 294), (299, 358), (363, 422), (427, 486), (491, 550), (555, 614),
]

X_RANGES = [
    (256, 287), (288, 319), (320, 351), (352, 383), (384, 415), (416, 447), (448, 479), (480, 511),  # チップ名 (8文字)
    (577, 608),  # コード (1文字)
    (673, 704), (705, 736),  # 枚数 (2文字)
]

# ============================================================
# カタカナ正規化
# ============================================================
KANA_MAP = str.maketrans("ァィゥェォッャュョ", "アイウエオツヤユヨ")


def normalize_kana(text):
    return text.translate(KANA_MAP)


class ress_chip_exe(BaseExeTrade):
    NAME = "エグゼ_トレードチップ削減"
    TRADE_TYPE = 10  # チップトレーダーに入れる枚数 (3枚版は別クラスで対応)

    def __init__(self, cam):
        super().__init__(cam)
        self.predictor = None
        self.chip_db = {}       # {チップ名: [可能コードリスト]}
        self.chip_map = {}      # {(チップ名, コード): 受け側保持枚数}
        self.last_row_img = None

    # ============================================================
    # DB / Predictor ロード (library_summrise_exe.py から流用)
    # ============================================================
    def load_db(self):
        db_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "exe4_chip_list.csv")
        )
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

    def load_chip_map(self):
        csv_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", "recv_library.csv")
        )
        if not os.path.exists(csv_path):
            print(f"Error: recv_library.csv not found: {csv_path}")
            return False
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.reader(f)
                next(reader, None)  # ヘッダスキップ
                for row in reader:
                    if len(row) < 3:
                        continue
                    name = normalize_kana(row[0].strip())
                    code = row[1].strip()
                    try:
                        count = int(row[2].strip())
                    except ValueError:
                        continue
                    self.chip_map[(name, code)] = count
            print(f"chip_mapロード完了: {len(self.chip_map)}件")
            return True
        except Exception as e:
            print(f"chip_mapロードエラー: {e}")
            return False

    def init_predictor(self):
        try:
            self.predictor = ExeCharPredictor()
            return True
        except Exception as e:
            print(f"Error: Failed to initialize Predictor: {e}")
            return False

    # ============================================================
    # 前処理 / OCR
    # ============================================================
    def preprocess(self, crop):
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        return binary

    def ocr_row(self, frame, r_idx):
        """
        指定行のOCRを行い、(チップ名, コード, 枚数) を返す。
        認識失敗時は None を返す。
        """
        y_start, y_end = Y_RANGES[r_idx]

        # --- チップ名 (8文字) ---
        name_ocr_results = []
        raw_name = ""
        for i in range(8):
            x_start, x_end = X_RANGES[i]
            crop = frame[y_start:y_end, x_start:x_end]
            binary = self.preprocess(crop)
            top_k = self.predictor.predict_top_k(binary, k=3)
            norm_top_k = [(normalize_kana(char), prob) for char, prob in top_k]
            name_ocr_results.append(norm_top_k)
            raw_name += norm_top_k[0][0] if norm_top_k else ""
        raw_name = raw_name.strip()

        if not raw_name:
            return None

        # --- コード (1文字) ---
        x_sc, x_ec = X_RANGES[8]
        crop_code = frame[y_start:y_end, x_sc:x_ec]
        bin_code = self.preprocess(crop_code)
        code_ocr_top_k = self.predictor.predict_top_k(bin_code, allowed_chars=TEMPLATE_CODE, k=3)
        # --- 枚数 (2文字) ---
        raw_count = ""
        for idx in [9, 10]:
            x_sn, x_en = X_RANGES[idx]
            crop_cnt = frame[y_start:y_end, x_sn:x_en]
            bin_cnt = self.preprocess(crop_cnt)
            char, _ = self.predictor.predict(bin_cnt, allowed_chars=TEMPLATE_NUMBER_BLANK)
            raw_count += char
        raw_count = raw_count.strip()

        # --- あいまい検索でチップ名を解決 ---
        raw_name_norm = normalize_kana(raw_name)
        candidates = difflib.get_close_matches(raw_name_norm, self.chip_db.keys(), n=3)
        ocr_top_3_codes = [item[0] for item in code_ocr_top_k]

        resolved_name = None
        resolved_code = None

        # フェーズ1: 完全一致
        for cand in candidates:
            dist = difflib.SequenceMatcher(None, raw_name_norm, cand).ratio()
            if dist >= 1.0:
                possible_codes = self.chip_db.get(cand, [])
                matched_code = next((c for c in ocr_top_3_codes if c in possible_codes), None)
                if matched_code:
                    resolved_name = cand
                    resolved_code = matched_code
                    break
                else:
                    retry_code, _ = self.predictor.predict(bin_code, allowed_chars=possible_codes)
                    if retry_code:
                        resolved_name = cand
                        resolved_code = retry_code
                        break

        # フェーズ2: スコア順コード検証
        if resolved_name is None:
            for cand in candidates:
                possible_codes = self.chip_db.get(cand, [])
                matched_code = next((c for c in ocr_top_3_codes if c in possible_codes), None)
                if matched_code:
                    resolved_name = cand
                    resolved_code = matched_code
                    break

        if resolved_name is None:
            print(f"  OCR解決失敗: '{raw_name}' (候補: {candidates})")
            return None

        # 枚数をintに変換
        try:
            count_int = int(raw_count) if raw_count else 0
        except ValueError:
            count_int = 0

        print(f"  OCR認識: {resolved_name} [{resolved_code}] {count_int}枚")
        return (resolved_name, resolved_code, count_int)

    # ============================================================
    # スクロール末尾検知
    # ============================================================
    def is_end_of_list(self, frame, r_idx):
        y_s, y_e = Y_RANGES[min(r_idx, 6)]
        current_img = frame[y_s:y_e, 256:1279]

        if self.last_row_img is not None:
            diff = cv2.absdiff(current_img, self.last_row_img)
            if np.mean(diff) < 0.1:
                return True

        self.last_row_img = current_img.copy()
        return False

    # ============================================================
    # メインエントリポイント
    # ============================================================
    def do(self):
        if not self.load_db():
            return
        if not self.load_chip_map():
            return
        if not self.init_predictor():
            return

        print("=== チップ削減マクロを開始します ===")
        print(f"  トレードタイプ: {self.TRADE_TYPE}枚")
        print(f"  chip_map: {len(self.chip_map)}件ロード済み")

        # --- チップトレーダー起動 ---
        self.hold(Button.B)                    # Bホールド（会話スキップ用）
        # NPCに話しかける
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_01_begin.png", [500,579,808,637], "トレード開始確認")
        # 「はい」を選択 # チップ選択画面の表示待ち
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_02_select.png", [599,123,603,152], "チップ選択画面")

        # --- メインループ ---
        batch_count = 0
        while True:
            btm_count = 0
            self.last_row_img = None
            skip_count = 0
            end_of_list = False

            batch_count += 1
            print(f"\n--- バッチ {batch_count} 開始 ---")

            for i in range(self.TRADE_TYPE):
                if end_of_list:
                    break

                while True:
                    # skip最適化: 同じチップが続くのでA押すだけ
                    if skip_count > 0:
                        self.press(Button.A, 0.2, 0.3)
                        skip_count -= 1
                        print(f"  [{i+1}/{self.TRADE_TYPE}] skip選択 (残skip: {skip_count})")
                        break

                    # OCR対象の行を決定
                    row_idx = min(6, btm_count)
                    frame = self.camera.readFrame()
                    if frame is None:
                        continue

                    result = self.ocr_row(frame, row_idx)

                    if result is None:
                        # OCR失敗 → スキップして次のチップへ
                        self.press(Hat.BTM, 0.2, 0.4)
                        frame_after = self.camera.readFrame()
                        if frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        continue

                    name, code, held_count = result
                    chip_key = (name, code)

                    if chip_key not in self.chip_map:
                        # 未登録チップ → スキップ
                        print(f"  [{i+1}/{self.TRADE_TYPE}] スキップ(未登録): {name} [{code}]")
                        self.press(Hat.BTM, 0.2, 0.4)
                        frame_after = self.camera.readFrame()
                        if frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        continue

                    receiver_held = self.chip_map[chip_key]
                    needed = 99 - receiver_held
                    diff = held_count - needed

                    if diff >= 0:
                        # 余剰あり → トレーダーに入れる
                        self.press(Button.A, 0.2, 0.3)
                        remaining_slots = self.TRADE_TYPE - i - 1
                        skip_count = min(diff, remaining_slots)
                        print(f"  [{i+1}/{self.TRADE_TYPE}] 選択: {name} [{code}] "
                              f"(保持:{held_count}, 受側:{receiver_held}, 余剰:{diff}, skip設定:{skip_count})")
                        break
                    else:
                        # 余剰なし → スキップ
                        print(f"  [{i+1}/{self.TRADE_TYPE}] スキップ(余剰なし): {name} [{code}] "
                              f"(保持:{held_count}, 受側:{receiver_held}, 必要:{needed})")
                        self.press(Hat.BTM, 0.2, 0.4)
                        frame_after = self.camera.readFrame()
                        if frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        continue

            if end_of_list:
                self.holdEnd(Button.B)
                for _ in range(20):
                    self.press(Button.B, 0.2, 0.3)
                print(f"\n=== 全チップ確認完了。{batch_count - 1}バッチ実行しました。 ===")
                return

            # 10枚選択完了 → トレード実行
            # Bホールド中なので結果表示後、自動で「はい・いいえ」に戻る
            print(f"  バッチ {batch_count} トレード実行中...")
            # self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_03_confirm.png", [586,334,887,388], "トレード確認")  # トレード確認画面待ち
            # トレード演出の待機（要調整）
            self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_04_agein.png", [500,472,835,587], "再度使用")  # トレード確認画面待ち
             # 「はい」選択
            self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_02_select.png", [599,123,603,152], "チップ選択画面")  # チップ選択画面の表示待ち
            
