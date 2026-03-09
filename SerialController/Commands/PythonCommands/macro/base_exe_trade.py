#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Commands.Keys import Button, Direction, Hat
from Commands.PythonCommandBase import ImageProcPythonCommand
from datetime import datetime, timedelta
from .ExeExceptions import CommunicationError, InitializationError


class BaseExeTrade(ImageProcPythonCommand):
    def __init__(self, cam):
        super().__init__(cam)

    def reset_to_main_menu(self, count=10):
        # bボタン連打（仮関数）
        for _ in range(count):
            self.press(Button.B, 0.1, 0.25)
        # + → ↑ → ↑ → A の順に押す
        self.press(Button.START, 0.4, 0.4)
        self.press(Hat.TOP, 0.1, 0.4)
        self.press(Hat.TOP, 0.1, 0.4)
        self.press(Button.A, 0.4, 0.4)
        print("初期画面へ戻りました（推測）")
        # 初期画面へ戻して終了
        return

    # 通信エラーのチェック
    def communication_error_check(self):
        if self.isContainTemplate("Macro/rokkuman_exe/communication_error.png", threshold=0.95, crop=[400, 220, 850, 500], use_gray=False):
            raise CommunicationError()
        else:
            pass

    def trade_wait_timeout_check(self):
        if self.isContainTemplate("Macro/rokkuman_exe/trade_wait_timeout.png", threshold=0.95, crop=[370, 140, 850, 570], use_gray=False):
            print("トレード待機タイムアウトのため、初期画面へ戻ります。")
            self.menu_selection("Macro/rokkuman_exe/network_initial_screen.png", [130, 125, 330, 145], "初期画面へ戻る", wait_seconds=10)
            print("初期画面へ戻りました。", datetime.now())
        else:
            pass

    def menu_selection(self, path, crop, page_name, wait_seconds=3):
        # トレードを選択（最大2回試行）
        for _ in range(2):
            # 通信エラーのチェック
            try:
                self.communication_error_check()
            except CommunicationError:
                self.press(Button.A, 0.4, 0.4)
                raise InitializationError("メインメニューに戻ります。")

            start_time = datetime.now()
            while (datetime.now() - start_time) < timedelta(seconds=wait_seconds):
                if self.isContainTemplate(path, threshold=0.95, crop=crop, use_gray=False):
                    break
            else:
                print(page_name + "に遷移できませんでした。再試行します。")
                continue  # 反応なければもう一度ループ

            break  # 成功したのでループを抜けて次へ

        # 失敗した場合のリカバリー
        else:
            print(str(wait_seconds * 2)+"秒待機しましたが、" + page_name + "に遷移できませんでした。メインメニューに戻ります。")
            raise InitializationError("メインメニューに戻ります。")

    def reset_to_main_menu(self, count=10):
        # 念の為、メインメニューに戻るための選択を一周して、メインメニューに戻るボタンがあることを確認する。（bで戻れないため。）
        for _ in range(4):
            self.press(Hat.BTM, 0.4, 0.4)
            if self.isContainTemplate("Macro/rokkuman_exe/return_to_main_menu_button.png", threshold=0.8, crop=[470, 520, 800, 550], use_gray=False):
                print("メインメニューに戻るボタンを確認しました。")
                self.menu_selection("Macro/rokkuman_exe/network_initial_screen.png", [130, 125, 330, 145], "初期画面")
                return
        # bボタン連打（仮関数）
        for _ in range(count):
            self.press(Button.B, 0.17, 0.17)
        # + → ↑ → ↑ → A の順に押す
        self.press(Button.START, 0.4, 0.4)
        self.press(Hat.TOP, 0.4, 0.4)
        self.press(Hat.TOP, 0.4, 0.4)
        self.press(Button.A, 0.4, 0.4)
        # 初期画面へ戻して終了
        return
