#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import traceback
from Commands.Keys import Button, Hat

from .base_exe_trade import BaseExeTrade
from . import ExeExceptions


class recv_exe_trade(BaseExeTrade):
    NAME = "エグゼ交換受け側"

    def __init__(self, cam):
        super().__init__(cam)
        self.hatched_num = 0
        self.count = 5
        self.place = "wild_area"

    def do(self):
        while True:
            try:
                self.recv_trade()
            # 初期化用例外
            except ExeExceptions.InitializationError:
                if self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png", threshold=0.9, crop=[130, 125, 330, 145], use_gray=False):
                    continue
                else:
                    self.reset_to_main_menu(10)
                    continue
            except Exception as e:
                print("全チップ交換完了", e)
                error_trace_string = traceback.format_exc()
                # 取得した文字列を print() で出力
                print("=== エラー詳細レポート ===")
                print(error_trace_string)
                print("==========================")
                return

    def recv_trade(self):
        # 開始画面・カーソル位置が正しいことを確認。
        if not self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png",threshold=0.9,crop=[120, 120, 400, 150],use_gray=False,):
            return
        print("初期画面を確認しました。")
        # トレードにカーソルを合わせる
        self.press(Hat.BTM, 0.17, 0.17)
        while not self.isContainTemplate("Macro/rokkuman_exe/mainmenu_trade_selected.png",threshold=0.9,crop=[130, 190, 390, 215],use_gray=False,):
            self.press(Hat.BTM, 0.17, 0.17)
        print("トレードにカーソルを合わせました。")
        # トレードを選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_type_menu_public_trade_selected.png",[125, 125, 390, 150],"トレード画面",)
        print("トレードを選択しました。")
        # ローカルトレードにカーソルを合わせる
        self.press(Hat.TOP, 0.17, 0.17)
        while not self.isContainTemplate("Macro/rokkuman_exe/trade_type_menu_local_trade_selected.png",threshold=0.9,crop=[125, 250, 390, 270],use_gray=False,):
            self.press(Hat.TOP, 0.17, 0.17)
        print("ローカルトレードにカーソルを合わせました。")
        # ローカルトレードを選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_tip_trade_selected.png",[140, 190, 410, 215],"トレード設定画面",)
        print("ローカルトレードを選択しました。")
        # チップトレード選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_recv_selected.png",[140, 415, 400, 440],"トレード設定画面-チップトレード選択",)
        print("チップトレードを選択しました。")
        # 待ち受ける
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_setting_menu_next_selected.png",[140, 570, 285, 590],"トレード設定画面-受取選択",)
        print("受取を選択しました。")
        # nextを選択してチップ選択へ
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_chip_frame.png",[203, 134, 224, 300],"トレード設定画面-Next選択",)
        print("nextを選択しました。")

        # 並べ替えをして、カーソル位置リセット
        self.press(Button.START, 0.17, 0.17)
        print("並べ替えをしました。")

        # NoDataにカーソルを合わせる
        self.press(Hat.TOP, 0.2, 0.2)
        while not self.isContainTemplate("Macro/rokkuman_exe/no_data_check.png",threshold=0.9,crop=[250, 120, 450, 290],use_gray=False,):
            self.press(Button.START, 0.17, 0.17)
            self.press(Hat.TOP, 0.17, 0.17)
        print("NoDataにカーソルを合わせました。")

        # NoDataを選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_message_menu_default_selected.png",[590, 195, 900, 225],"トレードメッセージ選択",)
        print("NoDataを選択しました。")

        # メッセージ選択
        self.press_a_and_wait_for_screen("Macro/rokkuman_exe/trade_wait_page_any.png",[1020, 142, 1155, 145],"トレード待機画面",)
        print("トレードメッセージを選択しました")
        trade_wait_start_time = datetime.now()
        print("トレード待機を開始します。開始時刻:",trade_wait_start_time,"待機終了時刻:",trade_wait_start_time + timedelta(minutes=3),)
        while True:
            if self.isContainTemplate("Macro/rokkuman_exe/trade_acceptance_selection.png",threshold=0.9,crop=[780, 200, 800, 220],use_gray=False,):
                # トレード相手が見つかるパターン
                print("トレード相手を見つけました")
                while True:
                    # トレード相手を待つケースはnot判定なので、例外処理パターンを先に記載してます。
                    if self.isContainTemplate("Macro/rokkuman_exe/network_battle_list.png",threshold=0.9,crop=[1040, 144, 1162, 175],use_gray=False,):
                        # 通信エラーが発生した場合、ネットワーク対戦の待機リストに行ってしまう。
                        # それを防ぐための処理です。
                        # b -> confirm a -> top check
                        # 確認画面を出す。（エラーの復帰ケースなので、気持ちの余裕を持って待つ）
                        self.press(Button.B, 0.17, 2.0)
                        # 確認画面表示待ち
                        while not self.isContainTemplate("Macro/rokkuman_exe/return_top_confirm.png",threshold=0.9,crop=[430, 250, 840, 480],use_gray=False,):
                            pass
                        # はいを選択（エラーの復帰ケースなので、気持ちの余裕を持って待つ）
                        self.press(Button.A, 0.17, 2.0)
                        while not self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png",threshold=0.9,crop=[120, 120, 400, 150],use_gray=False,):
                            pass
                        # 状況がリセットされるので、次のループに入る
                        return
                    elif not self.isContainTemplate("Macro/rokkuman_exe/trade_application_confirmation.png",threshold=0.9,crop=[420, 325, 880, 500],use_gray=False,):
                        # トレード相手選択
                        print("トレード相手を選択します")
                        self.press(Button.A, 0.17, 0.25)
                        break
                        # FIXME ここバグがある。交換が終わってるのに、breakがないために永遠とAボタン押し続ける。
                        # 最後バトルメニュールートに入って、例外で抜ける。
                    else:
                        # elifの条件がnotだから、わかりにくいが、トレード相手選択確認画面に遷移できた場合は、breakでループを抜ける。
                        break
                while not self.isContainTemplate("Macro/rokkuman_exe/trade_application_confirmation.png",threshold=0.9,crop=[420, 325, 880, 500],use_gray=False,):
                    pass
                # トレード申し込み確認
                print("トレード相手を確定します")
                # 交換完了まで待機
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/successful_trade.png",[550, 300, 740, 480],"交換完了",)
                # OK　選択
                print("交換成功")
                self.press_a_and_wait_for_screen("Macro/rokkuman_exe/network_initial_screen.png",[120, 120, 400, 150],"初期画面",)
                print("初期画面へ戻りました。")
                # 交換完了のため、次の交換へ
                return

            # 通信エラー # 終了させる
            elif self.isContainTemplate("Macro/rokkuman_exe/communication_error.png",threshold=0.9,crop=[400, 220, 850, 500],use_gray=False,):
                print("通信エラーが発生しました")
                self.press(Button.A, 0.17, 0.25)
                # 画面遷移待ち
                while not self.isContainTemplate("Macro/rokkuman_exe/network_initial_screen.png",threshold=0.9,crop=[120, 120, 400, 150],use_gray=False,):
                    # 通信エラーのOKを押せないパターンがあったため
                    if self.isContainTemplate("Macro/rokkuman_exe/communication_error.png",threshold=0.9,crop=[400, 220, 850, 500],use_gray=False,):
                        self.press(Button.A, 0.17, 0.25)
                return
            elif (datetime.now() - trade_wait_start_time) > timedelta(minutes=3):
                print("トレード待機時間が3分を超えました。メインメニューに戻ります。")
                #self.reset_to_main_menu(20)
                raise ExeExceptions.InitializationError("メインメニューに戻ります。")
            else:
                # トレード相手を待つ
                pass
