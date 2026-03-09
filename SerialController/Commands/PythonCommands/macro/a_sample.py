#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from Commands.Keys import Button, Direction
from Commands.PythonCommandBase import ImageProcPythonCommand
from PIL import Image


# Egg hatching at count times
# すべての孵化(キャプボあり)
# 現在は手持ちのみ
class a_sample(ImageProcPythonCommand):
    NAME = '作業用マクロ'

    def __init__(self, cam):
        super().__init__(cam)
        self.hatched_num = 0
        self.count = 5
        self.place = 'wild_area'

    def do(self):
        path_pre="./Template/Macro/rokkuman_exe/"
        # crop_and_save_png(path_pre+"2025-05-25_23-33-11.png", path_pre+"trade_type_menu_public_trade_selected.png", 125, 125, 390, 150)
        # crop_and_save_png(path_pre+"2025-05-25_23-33-17.png", path_pre+"trade_type_menu_local_trade_selected.png", 125, 250, 390, 270)
        # crop_and_save_png(path_pre+"2025-05-25_23-33-22.png", path_pre+"trade_setting_menu_tip_trade_selected.png", 140, 190, 410, 215)
        # crop_and_save_png(path_pre+"2025-05-25_23-33-25.png", path_pre+"trade_setting_menu_recv_selected.png", 140, 415, 400, 440)
        # crop_and_save_png(path_pre+"2025-05-25_23-33-38.png", path_pre+"trade_setting_menu_send_selected.png", 140, 475, 400, 495)
        # crop_and_save_png(path_pre+"2025-05-25_23-33-42.png", path_pre+"trade_setting_menu_next_selected.png", 140, 570, 285, 590)
        # crop_and_save_png(path_pre+"2025-05-26_00-00-07.png", path_pre+"trade_message_menu_default_selected.png", 590, 195, 900, 225)
        # crop_and_save_png(path_pre+"2025-05-26_00-07-28.png", path_pre+"trade_wait_page_any.png", 1020, 142, 1155, 145)
        # crop_and_save_png(path_pre+"2025-05-27_00-41-18.png", path_pre+"network_initial_screen.png", 130, 125, 330, 145)
        # crop_and_save_png(path_pre+"2025-05-27_10-16-26.png", path_pre+"trade_wait_timeout.png", 370, 140, 850, 570)
        # crop_and_save_png(path_pre+"2025-05-28_00-11-31.png", path_pre+"no_partner_update_yes.png", 400, 160, 850, 500)
        crop_and_save_png(path_pre+"2025-05-28_00-21-05.png", path_pre+"trade_list_update.png", 480, 340, 720, 380)
        
        
        
        
        
   

def crop_and_save_png(input_path, output_path, x1, y1, x2, y2):
    """
    指定したPNG画像を(x1, y1, x2, y2)で切り取り、新しい画像として保存する。

    Args:
        input_path (str): 入力PNG画像のファイルパス
        output_path (str): 出力PNG画像のファイルパス
        x1, y1, x2, y2 (int): 切り取る矩形の座標（左上 (x1, y1) ～ 右下 (x2, y2)）
    """
    try:
        # 画像を開く
        img = Image.open(input_path)

        # 指定範囲を切り取る
        cropped_img = img.crop((x1, y1, x2, y2))
 
        # 新しいPNG画像として保存
        cropped_img.save(output_path, format="PNG")
        print(f"画像を切り取って保存しました: {output_path}")
    
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# 使用例
# crop_and_save_png("input.png", "output.png", 100, 50, 400, 300)