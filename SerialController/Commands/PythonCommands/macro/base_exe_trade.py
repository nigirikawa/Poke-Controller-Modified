#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import csv
import time
from datetime import datetime, timedelta

import cv2
import numpy as np
import difflib

from Commands.Keys import Button, Hat
from Commands.PythonCommandBase import ImageProcPythonCommand

from . import ExeExceptions
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


class BaseExeTrade(ImageProcPythonCommand):
    SLEEP_TIME = 0.3
    PUSH_TIME = 0.2

    def __init__(self, cam):
        super().__init__(cam)
        self.predictor = None
        self.chip_db = {}       # {チップ名: [可能コードリスト]}
        self.chip_map = {}      # {(チップ名, コード): 受け側保持枚数}
        self.last_row_img = None

    def sleep(self, value: float):
        time.sleep(value)

    def reset_to_main_menu(self, count=10):
        # 呼び出し元をプリント・
        import traceback
        print("====== reset_to_main_menu caller ======")
        traceback.print_stack()
        scrennshot_filename = "return_to_main_menu" + datetime.now().strftime("%Y%m%d%H%M%S%f_") + ".png"
        self.camera.saveCapture(filename=scrennshot_filename,)
        print("念の為、スクリーンショットを保存しました。{}".format(scrennshot_filename))
        print("=======================================")

        print("メインメニューに戻ります。")
        # 交換待機のタイムアウト前に関数タイムアウトで入ってきたとき用。
        if self.isContainTemplate("Macro/rokkuman_exe/trade_wait_page_before_return_top.png", threshold=0.95, crop=[117, 135, 147, 156], use_gray=True,):
            self.press(Button.B, self.PUSH_TIME, self.SLEEP_TIME)
            self.camera.saveCapture(filename="before_return_top_confirm" + datetime.now().strftime("%Y%m%d%H%M%S%f_") + ".png",)
            self.wait_for_screen("Macro/rokkuman_exe/return_top_confirm.png", [418, 247, 876, 496], "トップに戻る確認", wait_seconds=5)
            self.camera.saveCapture(filename="after_return_top_confirm" + datetime.now().strftime("%Y%m%d%H%M%S%f_") + ".png",)
            self.press_a_and_wait_for_screen("Macro/rokkuman_exe/network_initial_screen.png",[130, 125, 330, 145],"初期画面",)
            print("初期画面に戻りました。", datetime.now())
            return

        # 念の為、メインメニューに戻るための選択を一周して、メインメニューに戻るボタンがあることを確認する。（bで戻れないため。）
        for _ in range(4):
            self.press(Hat.BTM, self.PUSH_TIME, self.SLEEP_TIME)
            # self.camera.saveCapture(filename="return_to_main_menu_button" + datetime.now().strftime("%Y%m%d%H%M%S%f_") + ".png",crop=1,crop_ax=[470, 520, 800, 550],)
            if self.isContainTemplate("Macro/rokkuman_exe/return_to_main_menu_button.png",threshold=0.9,crop=[470, 520, 800, 550],use_gray=False,):
                print("メインメニューに戻るボタンを確認しました。")
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/network_initial_screen.png",[130, 125, 330, 145],"初期画面",)
                print("初期画面に戻りました。", datetime.now())
                return
        # bボタン連打での初期画面戻し（仮関数）
        for _ in range(4):
            for _ in range(count):
                self.press(Button.B, self.PUSH_TIME, self.SLEEP_TIME)
            # + → ↑ → ↑ → A の順に押す
            self.press(Button.START, self.PUSH_TIME, self.SLEEP_TIME)
            self.press(Hat.TOP, self.PUSH_TIME, self.SLEEP_TIME)
            self.press(Hat.TOP, self.PUSH_TIME, self.SLEEP_TIME)
            self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)
            # 交換画面が表示されるための待機。
            time.sleep(1)
            # 初期画面へ戻して終了
            if self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png", threshold=0.95, crop=[130, 125, 330, 145], use_gray=False):
                print("初期画面に戻りました。", datetime.now())
                return

    # 通信エラーのチェック
    def communication_error_check(self):
        if self.isContainTemplate("Macro/rokkuman_exe/communication_error.png",threshold=0.95,crop=[400, 220, 850, 500],use_gray=False,):
            raise ExeExceptions.CommunicationError()
        else:
            pass

    def trade_wait_timeout_check(self):
        if self.isContainTemplate("Macro/rokkuman_exe/trade_wait_timeout.png",threshold=0.95,crop=[370, 140, 850, 570],use_gray=False,):
            print("トレード待機タイムアウトのため、初期画面へ戻ります。")
            self.press_a_and_wait_for_screen("Macro/rokkuman_exe/network_initial_screen.png",[130, 125, 330, 145],"初期画面へ戻る",wait_seconds=10,)
            print("初期画面へ戻りました。", datetime.now())
        else:
            pass

    # 画面の状態になるまで待機する。
    def wait_for_screen(self, path, crop, page_name, wait_seconds=60):
        start_time = datetime.now()
        while (datetime.now() - start_time) < timedelta(seconds=wait_seconds):
            if self.isContainTemplate(path, threshold=0.95, crop=crop, use_gray=False):
                return
            else:
                # 次の確認まで0.5秒待機
                self.sleep(self.SLEEP_TIME)
        else:
            print(str(wait_seconds)+ "秒待機しましたが、"+ page_name+ "に遷移しませんでした。")
            raise ExeExceptions.InitializationError("メインメニューに戻ります。")

    def press_a_and_wait_for_screen(self, path, crop, page_name, use_gray=False, threshold=0.95, wait_seconds=20):
        for _ in range(2):
            # ボタンを押す
            self.press(Button.A, self.PUSH_TIME)

            # 画面の状態が変わるのを待つ
            start_time = datetime.now()
            while (datetime.now() - start_time) < timedelta(seconds=wait_seconds):
                # 指定した変化先の画像と一致することを確認できたら待機を完了
                if self.isContainTemplate(path, threshold=threshold, crop=crop, use_gray=use_gray):
                    break
                elif self.isContainTemplate("Macro/rokkuman_exe/communication_error.png",threshold=0.95,crop=[400, 220, 850, 500],use_gray=False,):
                    # 通信エラーのチェック
                    print("通信エラーのため、メインメニューに戻ります。")
                    self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)
                    raise ExeExceptions.InitializationError("メインメニューに戻ります。")
                else:
                    # デバッグ用。画面判定がズレた場合に指定場所とその場所のssを作成
                    print(page_name + "への遷移を待機します")
                    self.sleep(self.SLEEP_TIME)
            else:
                self.camera.saveCapture(filename=path + datetime.now().strftime("%Y%m%d%H%M%S%f_")+ page_name,crop=1,crop_ax=crop,)
                print(page_name + "に遷移できませんでした。再試行します。")
                print("crop: ", crop)
                continue  # 反応なければもう一度ループ

            break  # 成功したのでループを抜けて次へ

        # 失敗した場合のリカバリー
        else:
            print(str(wait_seconds * 2) + "秒待機しましたが、"+ page_name+ "に遷移できませんでした。メインメニューに戻ります。")
            raise ExeExceptions.InitializationError("メインメニューに戻ります。")

    # ============================================================
    # DB / Predictor ロード (library_summrise_exe.py から流用)
    # ============================================================
    def load_db(self, csv_filename="exe4_chip_list.csv"):
        db_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..", "db", csv_filename)
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

    def press_a_and_wait_for_screen_char(self, expected_char: str, crop_rect: tuple):
        """Aを押し、指定領域のOCRが expected_char になるまで待機する"""
        self.press(Button.A, self.PUSH_TIME)
        print(f"画面への遷移を待機します（OCR: 「{expected_char}」検出待ち）")
        x1, y1, x2, y2 = crop_rect
        while True:
            frame = self.camera.readFrame()
            if frame is not None:
                crop = frame[y1:y2, x1:x2]
                binary = self.preprocess(crop)
                char, _ = self.predictor.predict(binary)
                if char == expected_char:
                    break
            self.sleep(0.1)

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
    # チップ削減メインエントリポイント
    # ============================================================
    def reduce_chip_loop(self, csv_filename="exe4_chip_list.csv"):
        if not self.load_db(csv_filename):
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
        # self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_01_begin.png", [500,579,808,637], "トレード開始確認", use_gray=True,threshold=0.5, wait_seconds=3)
        # # 「はい」を選択 # チップ選択画面の表示待ち
        # self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_02_select.png", [599,123,603,152], "チップ選択画面", use_gray=True, threshold=0.5, wait_seconds=3)
        self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)  # トレード確認画面待ち
        self.sleep(0.2)
        self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)  # チップ選択画面の表示待ち
        self.sleep(0.2)

        # --- メインループ ---
        batch_count = 0
        r_press_count = 0  # バッチ開始時にRボタンを押す回数（ページスキップ用）
        while True:
            btm_count = 0
            self.last_row_img = None
            skip_count = 0
            end_of_list = False

            batch_count += 1
            print(f"\n--- バッチ {batch_count} 開始 ---")

            # 処理済みページをRボタンでスキップ
            if r_press_count > 0:
                for _ in range(r_press_count):
                    self.press(Button.R, 0.2, 0.4)
                print(f"  Rボタン {r_press_count}回押下 (ページスキップ)")

            for i in range(self.TRADE_TYPE):
                if end_of_list:
                    break

                while True:
                    # skip最適化: 同じチップが続くのでA押すだけ
                    if skip_count > 0:
                        self.press(Button.A, 0.05, 0.05)
                        skip_count -= 1
                        print(f"  [{i+1}/{self.TRADE_TYPE}] skip選択 (残skip: {skip_count})")
                        # skip終了時に誤操作防止のため、少し待機を入れる
                        if skip_count == 0:
                            self.sleep(0.3)
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
                        # Rスキップ後は7回目の下ボタンまで終了判定をスキップ
                        can_check_end = (r_press_count == 0) or (btm_count + 1 >= 7)
                        if can_check_end and frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        if btm_count % 7 == 0:
                            r_press_count += 1
                        continue

                    name, code, held_count = result
                    chip_key = (name, code)

                    if chip_key not in self.chip_map:
                        # 未登録チップ → スキップ
                        print(f"  [{i+1}/{self.TRADE_TYPE}] スキップ(未登録): {name} [{code}]")
                        self.press(Hat.BTM, 0.2, 0.4)
                        frame_after = self.camera.readFrame()
                        # Rスキップ後は7回目の下ボタンまで終了判定をスキップ
                        can_check_end = (r_press_count == 0) or (btm_count + 1 >= 7)
                        if can_check_end and frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        if btm_count % 7 == 0:
                            r_press_count += 1
                        continue

                    receiver_held = self.chip_map[chip_key]
                    needed = max(self.TARGET_CHIP_COUNT - receiver_held, 0)
                    diff = held_count - needed

                    if diff >= 0:
                        # 余剰あり → トレーダーに入れる
                        print("diff: ", diff)
                        self.press(Button.A, 0.2, 0.4)
                        remaining_slots = self.TRADE_TYPE - i - 1
                        skip_count = min(diff - 1, remaining_slots) # すでに1つ選択してあるため、残りスロット-1が最大
                        print(f"  [{i+1}/{self.TRADE_TYPE}] 選択: {name} [{code}] "
                              f"(保持:{held_count}, 受側:{receiver_held}, 余剰:{diff}, skip設定:{skip_count})")
                        break
                    else:
                        # 余剰なし → スキップ
                        print(f"  [{i+1}/{self.TRADE_TYPE}] スキップ(余剰なし): {name} [{code}] "
                              f"(保持:{held_count}, 受側:{receiver_held}, 必要:{needed})")
                        self.press(Hat.BTM, 0.2, 0.4)
                        frame_after = self.camera.readFrame()
                        # Rスキップ後は7回目の下ボタンまで終了判定をスキップ
                        can_check_end = (r_press_count == 0) or (btm_count + 1 >= 7)
                        if can_check_end and frame_after is not None and self.is_end_of_list(frame_after, min(6, btm_count + 1)):
                            end_of_list = True
                            break
                        btm_count += 1
                        if btm_count % 7 == 0:
                            r_press_count += 1
                        continue

            if end_of_list:
                self.holdEnd(Button.B)
                for _ in range(20):
                    self.press(Button.B, 0.2, 0.4)
                print(f"\n=== 全チップ確認完了。{batch_count - 1}バッチ実行しました。 ===")
                return
            
            # 10枚選択完了 → トレード実行
            # Bホールド中なので結果表示後、自動で「はい・いいえ」に戻る
            self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)  # トレード確認画面待ち
            self.sleep(0.2)
            # self.wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_03_confirm.png", [586,334,887,388], "トレード確認画面", wait_seconds=10)  # トレード確認画面待ち

            print(f"  バッチ {batch_count} トレード実行中...")
            # トレード演出の待機（要調整）
            time.sleep(0.2)
            # self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_04_agein.png", [500,472,835,587], "再度使用", use_gray=True,threshold=0.5, wait_seconds=3)  
            #  # 「はい」選択
            # self.press_a_and_wait_for_screen("Macro/rokkuman_exe/ress_chip_exe/trader_02_select.png", [599,123,603,152], "チップ選択画面", use_gray=True,threshold=0.5, wait_seconds=3)  # チップ選択画面の表示待ち
            self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)  # トレード確認画面待ち
            self.sleep(1.5)
            self.press(Button.A, self.PUSH_TIME, self.SLEEP_TIME)  # チップ選択画面の表示待ち
            self.sleep(0.2)
