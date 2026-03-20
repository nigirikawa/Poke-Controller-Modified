#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta

from Commands.Keys import Button, Hat
from Commands.PythonCommandBase import ImageProcPythonCommand

from . import ExeExceptions


class BaseExeTrade(ImageProcPythonCommand):
    SLEEP_TIME = 0.3
    PUSH_TIME = 0.2

    def __init__(self, cam):
        super().__init__(cam)

    def sleep(self, value: float):
        time.sleep(value)

    def reset_to_main_menu(self, count=10):
        # 呼び出し元をプリント・
        import traceback
        print("====== reset_to_main_menu caller ======")
        traceback.print_stack()
        print("=======================================")

        print("メインメニューに戻ります。")
        # 念の為、メインメニューに戻るための選択を一周して、メインメニューに戻るボタンがあることを確認する。（bで戻れないため。）
        for _ in range(4):
            self.press(Hat.BTM, self.PUSH_TIME, self.SLEEP_TIME)
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

    def press_a_and_wait_for_screen(self, path, crop, page_name, use_gray=False, threshold=0.95, wait_seconds=60):
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
                    # self.camera.saveCapture(filename=path + datetime.now().strftime("%Y%m%d%H%M%S%f_")+ page_name,crop=1,crop_ax=crop,)
                    print(page_name + "への遷移を待機します")
                    self.sleep(self.SLEEP_TIME)
            else:
                print(page_name + "に遷移できませんでした。再試行します。")
                print("crop: ", crop)
                continue  # 反応なければもう一度ループ

            break  # 成功したのでループを抜けて次へ

        # 失敗した場合のリカバリー
        else:
            print(str(wait_seconds * 2) + "秒待機しましたが、"+ page_name+ "に遷移できませんでした。メインメニューに戻ります。")
            raise ExeExceptions.InitializationError("メインメニューに戻ります。")
