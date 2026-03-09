#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Commands.Keys import Button, Direction, Hat
from Commands.PythonCommandBase import ImageProcPythonCommand
from datetime import datetime, timedelta
from .base_exe_trade import BaseExeTrade
from .ExeExceptions import CommunicationError, InitializationError

class send_exe_trade(BaseExeTrade):
    NAME = 'エグゼ交換送り側'

    def __init__(self, cam):
        super().__init__(cam)
        self.cam = cam
        self.party_num = 1  # don't count eggs
        self.hatched_num = 0
        self.hatched_box_num = 0
        self.itr_max = 6

    def do(self):
        while True:
            try:
                self.send_trade()
            # 初期化用例外
            except InitializationError:
                self.reset_to_main_menu(10)
            except Exception as e:
                print("全チップ交換完了", e)
                return


    def send_trade(self):
        # 開始画面・カーソル位置が正しいことを確認。
        self.trade_wait_timeout_check()
        if not self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png", threshold=0.85, crop=[130, 125, 330, 145], use_gray=False):
            return
        print("初期画面を確認しました。")
        # トレードにカーソルを合わせる
        self.press(Hat.BTM, 0.2, 0.3)
        while not self.isContainTemplate("Macro/rokkuman_exe/mainmenu_trade_selected.png", threshold=0.85, crop=[130, 190, 390, 215], use_gray=False):
            self.press(Hat.BTM, 0.2, 0.3)
        print("トレードにカーソルを合わせました。")
        # トレードを選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_type_menu_public_trade_selected.png", [125, 125, 390, 150], "トレード画面")
        print("トレードを選択しました。")
        # ローカルトレードにカーソルを合わせる
        self.press(Hat.TOP, 0.2, 0.3)
        while not self.isContainTemplate("Macro/rokkuman_exe/trade_type_menu_local_trade_selected.png", threshold=0.85, crop=[125, 250, 390, 270], use_gray=False):
            self.press(Hat.TOP, 0.2, 0.3)
        print("ローカルトレードにカーソルを合わせました。")
        # ローカルトレードを選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_tip_trade_selected.png", [140, 190, 410, 215], "トレード設定画面")
        print("ローカルトレードを選択しました。")
        # チップトレード選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_recv_selected.png", [140, 415, 400, 440], "トレード設定画面-チップトレード選択")
        print("チップトレードを選択しました。")

        # 申し込む
        while not self.isContainTemplate("Macro/rokkuman_exe/trade_setting_menu_send_selected.png", threshold=0.85, crop=[140, 475, 400, 495], use_gray=False):
            self.press(Hat.BTM, 0.2, 0.3)
        print("申し込みにカーソルを合わせました。")
        # 申し込む
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_next_selected.png", [140, 570, 285, 590], "トレード設定画面-申し込み選択")
        print("申し込みを選択しました。")

        # nextを選択してチップ選択へ
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_chip_frame.png", [203, 134, 224, 300], "トレード設定画面-Next選択")
        print("nextを選択しました。")

        # ソートルールを変更して枚数順にする
        # 枚数箇所の背景が動いてるので、画像認識はせずに回数で制御。（ちょっと待機長め）
        for _ in range(0, 5):
            self.press(Button.START, 0.2, 0.3)
        print("枚数順に並べ替えをしました。")

        # 枚数が最も少ないものを選ぶ
        self.press(Hat.TOP, 0.2, 0.3)
        self.press(Hat.TOP, 0.2, 0.3)
        count = 0
        while self.isContainTemplate("Macro/rokkuman_exe/no_data_check.png", threshold=0.85, crop=[250, 120, 450, 290], use_gray=False):
            self.press(Hat.TOP, 0.2, 0.3)
            count += 1
            if count > 10:
                print("交換可能なチップがありません。")
                raise InitializationError("交換可能なチップがありません。")
        
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_message_menu_default_selected.png", [590, 195, 900, 225], "トレードメッセージ選択")
        print("送信するチップを選択しました。")
        
        # メッセージ選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_wait_page_any.png", [1020, 142, 1155, 145], "トレード待機画面")
        print("トレードメッセージを選択しました")
        
        trade_wait_start_time = datetime.now()
        # トレード相手が見つかるまで待つ（3分だけ）
        while (datetime.now() - trade_wait_start_time) < timedelta(minutes=3):
            # 相手が見つからない
            # いいえ→メニューに戻るで初期画面
            if self.isContainTemplate("Macro/rokkuman_exe/no_partner_update_no.png", threshold=0.85, crop=[410, 170, 830, 500], use_gray=False):                
                print("相手が見つからない")
                while not self.isContainTemplate("Macro/rokkuman_exe/no_partner_update_yes.png", threshold=0.85, crop=[400, 160, 850, 500], use_gray=False):
                    self.press(Hat.BTM, 0.2, 0.3)
                print("トレードリスト更新にカーソルを合わせました。")
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_list_update.png", [480, 340, 720, 380], "トレードリスト更新")
                print("トレードリスト更新開始")
                continue # 次のループへ
            # 相手が見つかる
            elif self.isContainTemplate("Macro/rokkuman_exe/トレード待機メンバーあり.png", threshold=0.85, crop=[410, 170, 830, 500], use_gray=False):
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/トレード相手選択確認.png", [430, 320, 850, 470], "トレードリスト更新")
                self.wait_for_screen("Macro/rokkuman_exe/successful_trade.png", [550, 300, 740, 480], "トレード完了画面")
                # 交換完了。
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/network_initial_screen.png", [130, 125, 330, 145], "初期画面")
            else:
                self.wait(0.5)
                
        else:
            raise InitializationError("トレード相手が見つからなかったので、初期画面へ戻ります")

            # ここから下は旧実装
            # # 申し込み先待機
            # while True:
            #     print("申込先が見つかるのを待つ")
            #     # リスト更新が必要か判定
            #     # Snipping(770, 300, 250, 20)
            #     if self.isContainTemplate("Macro/rokkuman_exe/choice_of_trading_partner.png", threshold=0.85, crop=[600, 200, 620, 220], use_gray=False):
            #         print("申込先を選択する")
            #         while True:
            #             # Snipping(564, 455, 770, 290)
            #             if not self.isContainTemplate("Macro/rokkuman_exe/trade_application_confirmation.png", threshold=0.85, crop=[420, 325, 880, 500], use_gray=False):
            #                 print("申し込み確定")
            #                 self.press(Button.A,0.2, 0.3)
            #                 break
            #         while True:
            #             # Snipping(564, 455, 770, 290)
            #             if self.isContainTemplate("Macro/rokkuman_exe/trade_application_confirmation.png", threshold=0.85, crop=[420, 325, 880, 500], use_gray=False):
            #                 print("申し込み確定")
            #                 self.press(Button.A,0.2, 0.3)
            #                 self.press(Button.A,0.2, 0.3)
            #                 break
            #         while True:
            #             if self.isContainTemplate("Macro/rokkuman_exe/successful_trade.png", threshold=0.85, crop=[550, 300, 740, 480], use_gray=False):
            #                 # OK　選択
            #                 print("交換成功")
            #                 self.press(Button.A,0.2, 0.3)
            #                 # 画面遷移待ち
            #                 while True:
            #                     # Snipping(190, 180, 410, 40)
            #                     print("交換スクリプト完了")
            #                     if self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png", threshold=0.85, crop=[120, 120, 400, 150], use_gray=False):
            #                         return
            #     # 通信エラーのせいで変な画面に飛んだ場合の対処
            #     elif self.isContainTemplate("Macro/rokkuman_exe/no_communication_partner_update_list.png", threshold=0.85, crop=[410, 170, 830, 500], use_gray=False):
            #             print("リスト更新")
            #             # 更新が必要
            #             # はい　にカーソルを移す
            #             self.press(Hat.TOP, 0.2, 0.3)
            #             # はい　選択
            #             self.press(Button.A, 0.2, 0.3)
            #     # 通信エラーになった場合の対処
            #     elif self.isContainTemplate("Macro/rokkuman_exe/communication_error.png", threshold=0.85, crop=[400, 220, 850, 500], use_gray=False):
            #             print("通信エラー")
            #             self.press(Button.A, 0.2, 0.3)
            #             # 画面遷移待ち
            #             while not self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png", threshold=0.85, crop=[120, 120, 400, 150], use_gray=False):
            #                 # 通信エラーのOKを押せないパターンがあったため
            #                 if self.isContainTemplate("Macro/rokkuman_exe/communication_error.png", threshold=0.85, crop=[400, 220, 850, 500], use_gray=False):
            #                     self.press(Button.A, 0.2, 0.3)
            #             return
            #     else:
            #         print("トレード相手を待つ")
            #         pass
