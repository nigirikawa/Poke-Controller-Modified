#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Commands.Keys import Button, Direction, Hat
from Commands.PythonCommandBase import ImageProcPythonCommand


# auto egg hatching using image recognition
# 自動卵孵化(キャプボあり)
class send_exe_trade(ImageProcPythonCommand):
    NAME = 'エグゼ交換送り側'

    def __init__(self, cam):
        super().__init__(cam)
        self.cam = cam
        self.party_num = 1  # don't count eggs
        self.hatched_num = 0
        self.hatched_box_num = 0
        self.itr_max = 6

    def do(self):
        # 通信エラー
        # Snipping(560, 294, 800, 450)
        # return
        #Loop()
        #{
        
        # トレード
        self.press(Hat.BTM, 0.15, 0.15)
        self.press(Button.A, 0.15, 0.15)

        # ローカルトレード
        self.press(Hat.TOP, 0.15, 0.15)
        self.press(Button.A, 0.15, 0.15)

        # チップトレード
        self.press(Button.A, 0.15, 0.15)

        # 申し込む
        self.press(Hat.BTM, 0.15, 0.15)
        self.press(Button.A, 0.15, 0.15)

        # next
        self.press(Button.A, 0.15, 0.15)

        # 画面判定
        count=0
        
        while True:
            self._logger.info('画面遷移判定開始')
            # トレード画面マッチング用画像取得
            # Snipping(306, 200, 30, 240)
            # トレード画面への遷移をチェック
            self._logger.info("文字化け確認：Macro/rokkuman_exe/trade_chip_frame.png")
            if not self.isContainTemplate("Macro/rokkuman_exe/trade_chip_frame.png", crop=[ 306,200, 306 + 30, 200 + 240]):
                # 画面遷移失敗
                self._logger.info("トレード画面遷移失敗")
                count+=1
                if count>5:
                    return
            else:
                # 画面遷移成功
                self._logger.info("トレード画面への遷移成功")
                # チップの有無チェック
                # Snipping(380, 185, 290, 240)
                # len(image): 720 y 
                # len(image[0]): 1280 x
                if self.isContainTemplate("Macro/rokkuman_exe/no_data判定.png", crop=[ 380,185, 380+290, 185+240]):
                    self._logger.info("交換不可")
                    # 交換不可
                    return
                else:
                    self._logger.info("交換可能")
                    # 交換可能
                    # 枚数まで画面切り替え
                    for _ in range(0, 5):
                        self.press(Button.START, 0.15, 0.15)
                    
                    # 枚数が最も少ないものを選ぶ
                    self.press(Hat.TOP, 0.15, 0.15)
                    self.press(Hat.TOP, 0.15, 0.15)
                    # チップ選択
                    self.press(Button.A, 0.15, 0.15)
                    # メッセージ選択
                    self.press(Button.A, 0.15, 0.15)
                    
                    # 申し込み先待機
                    while True:
                    
                        self._logger.info("申込先が見つかるのを待つ")
                        # リスト更新が必要か判定
                        # Snipping(770, 300, 250, 20)
                        if self.isContainTemplate("Macro/rokkuman_exe/トレード相手選択可能.png", crop=[ 770,300, 770+250, 300+20]):
                            
                            
                            while True:
                                # Snipping(564, 455, 770, 290)
                                if self.isContainTemplate("Macro/rokkuman_exe/トレード申込確認.png", crop=[ 564,455, 564+770, 455+290]):
                                    # 選択
                                    self.press(Button.A, 0.15, 0.15)
                                    break
                            
                            while True: 
                                # Snipping(564, 455, 770, 290)
                                if self.isContainTemplate("Macro/rokkuman_exe/トレード申込確認.png", crop=[ 564,455, 564+770, 455+290]):
                                    # 申し込み決定
                                    self.press(Button.A, 0.15, 0.15)
                                    break
                            while True:
                                if self.isContainTemplate("Macro/rokkuman_exe/トレード成功2.png", crop=[ 800,420, 800+300, 420+280]):
                                    # OK　選択
                                    self.press(Button.A, 0.15, 0.15)
                                    # 画面遷移待ち
                                    while True:
                                        # Snipping(190, 180, 410, 40)
                                        if self.isContainTemplate("Macro/rokkuman_exe/ネットワーク初期画面.png", crop=[ 190,180, 190+410, 180+40]):
                                            return
                        else:
                            # Snipping(586, 227, 685, 487)
                            if self.isContainTemplate("Macro/rokkuman_exe/通信相手なし_リスト更新.png", crop=[ 586,227, 586+685, 227+487]):
                                # 更新が必要
                                # はい　にカーソルを移す
                                self.press(Hat.TOP, 0.15, 0.15)
                                # はい　選択
                                self.press(Button.A, 0.15, 0.15)
        
