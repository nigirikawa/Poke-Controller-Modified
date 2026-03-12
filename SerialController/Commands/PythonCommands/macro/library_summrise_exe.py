#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
import traceback
from Commands.Keys import Button, Hat
from .base_exe_trade import BaseExeTrade
from . import ExeExceptions



# ロックマンエグゼのライブラリを集計する。
# チップ・コード・枚数をファイルで出力する。
# 出力先は pokecon\Poke-Controller-Modified-Extension\SerialController\db
class library_summrise_exe(BaseExeTrade):
    NAME = "エグゼ_ライブラリ集計"

    def __init__(self, cam):
        super().__init__(cam)

    '''
    実装プラン
    1. スクショを取得するコードをdo関数に作成し、pokecon\Poke-Controller-Modified-Extension\SerialController\Template\Macro\rokkuman_exe\library__summrise_exeに保存する。
        * 全画面スクショ -> 下ボタン -> 全画面スクショ -> 下ボタンをループ
        * 終了条件は難しいが、画面の右半分が前の画面の右半分と完全一致するようになったら終了。
        * 画像の名称は通番で管理。6桁の0埋め右寄せ。
        * この画像をもとにして判定ロジックの作成を実施する。
    2. 判定ロジック作成。
        * ここの検証で1のスクショを活用して行う。
        * 実行はpythonコマンドでできるようにキック関数を別途用意しなきゃいけない。（pokeconが稼働中と思われるため。）
        * ocrは2パターン必要。
            * 精度よりも変化しないことを優先。（ある程度ズレててもいいけど、同じものは色が違っても絶対に同じ値であってほしい。）
            * 精度優先。（ここは数値なので、比較的楽だと信じたい。）
        * 2値化を行い、制度の高いOCRを行いたい。（過去にやった際は失敗している）
        * 想定される困難
            * OCRの精度問題ロックマンエグゼは独自フォント、表示が角ばっている、カタカナ・英字・数字・符号が含まれる。
            * 2値化の閾値も難しい。バージョンによって背景の色や文字の濃淡が逆だったり、色が違ったりするので、その変動するか
            * 枠問題。下ボタンで進んでいくので、いまカーソルがいる行というのを気にしてOCRしたり比較したりする必要がある。
                * 1 ~ 6行目は変動するので、ズレが出ないようにしなきゃいけないのか？この辺画像処理よくわからん。
                * 7行目以降は常に位置固定。なので楽。
                * データなしパターンも考える必要がありそう。（7行もないケース）
    3. 集計ロジックのスクリプト化
        * 2がうまく行ったら、ゲームの操作実装も加えて、実際に検証して集計の状況を確認する。
    
    '''

    def do(self):
        # self.test01()
        print("hello")

    # test2はmainで実行できるようにしてね
    # 画像を拡大して、ピクセルの座標を図ってみた。
    # まずは縦の座標だけ。
    '''
    y座標
    1:171 ~ 230
    2:235 ~ 294
    3:299 ~ 358
    4:363 ~ 422
    5:427 ~ 486
    6:491 ~ 550
    7:555 ~ 614
    '''

    '''
    x座標
    チップ名 + コード：257 ~ 609
    枚数10の桁：676 ~ 703
    枚数1の桁：708 ~ 735
    '''
    def test02(self):
        import cv2
        import os
        print("画像のY座標確認用テスト(test02)を開始します。")

        import numpy as np

        # 対象画像ファイルのパス
        input_filepath = "Captures/Macro/rokkuman_exe/library_summrise_exe/000000 - コピー.png"
        output_filepath = "Captures/Macro/rokkuman_exe/library_summrise_exe/000000_lines.png"

        # numpyを使って日本語パスでも読み込めるようにする
        with open(input_filepath, 'rb') as f:
            file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
        img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            print(f"エラー: 画像が見つからないか読み込めません -> {input_filepath}")
            return

        # 描画設定（紫: BGR=(255, 0, 255)、太さ=1）
        line_color = (255, 0, 255)
        thickness = 1

        # コメントにあるY座標のペア (y_start, y_end)
        y_ranges = [
            (171, 230),
            (235, 294),
            (299, 358),
            (363, 422),
            (427, 486),
            (491, 550),
            (555, 614)
        ]

        # コメントにあるX座標のペア (x_start, x_end)
        x_ranges = [
            (257, 609), # チップ名 + コード
            (676, 703), # 枚数10の桁
            (708, 735)  # 枚数1の桁
        ]

        # 各行(Y)・各列(X)の交差部分に四角形を描画する
        for y_start, y_end in y_ranges:
            for x_start, x_end in x_ranges:
                cv2.rectangle(img, (x_start, y_start), (x_end, y_end), line_color, thickness)

        # numpyを使って日本語パスでも保存できるようにする
        result, encoded_img = cv2.imencode('.png', img)
        if result:
            with open(output_filepath, 'wb') as f:
                f.write(encoded_img)
        print(f"Y座標の確認用画像を出力しました -> {output_filepath}")
    def test01(self):
        print("ライブラリ集計用のスクリーンショット取得を開始します。")

        # スクリーンショットの保存先ディレクトリ（Capturesフォルダ以下）
        save_dir_prefix = "Macro/rokkuman_exe/library_summrise_exe/"

        # Poke-Controllerの仕様上、isContainTemplate は `Template/` フォルダ内を基準に探します。
        # そのため、比較用の一時テンプレート画像は、自動で `Captures/` に保存される self.camera.saveCapture ではなく、
        # `Template/` フォルダ内に保存して参照できるようにします。
        
        # isContainTemplate に渡す用のパス（Template/以下の相対パス）
        temp_template_relative_path = "Macro/rokkuman_exe/library_summrise_exe/temp_right_half.png"
        
        # 実際に画像を保存する際の絶対（または実行時からの相対）パス
        # SerialController/Template/Macro/rokkuman_exe/library_summrise_exe/temp_right_half.png
        import os
        template_dir_path = os.path.join("Template", "Macro", "rokkuman_exe", "library_summrise_exe")
        os.makedirs(template_dir_path, exist_ok=True)
        temp_template_absolute_path = os.path.join(template_dir_path, "temp_right_half.png")

        right_half_crop = [640, 0, 1280, 720]
        image_count = 0

        while True:
            # 1. 本番用の全画面スクリーンショットを保存する（連番6桁ゼロ埋め、Capturesへ）
            filename = f"{image_count:06d}"
            self.camera.saveCapture(filename=save_dir_prefix + filename)
            print(f"スクリーンショットを保存しました: {save_dir_prefix}{filename}.png")

            # 3. 現在の右半分の画面を、「次回の比較用テンプレート」として `Template/` フォルダ内に保存する
            # camera.readFrame() で現在のフレーム(NumPy配列)を取得
            current_frame = self.camera.readFrame()
            if current_frame is not None:
                # crop_ax = [640, 0, 1280, 720] -> [y1:y2, x1:x2]
                cropped_frame = current_frame[right_half_crop[1]:right_half_crop[3], right_half_crop[0]:right_half_crop[2]]
                import cv2
                cv2.imwrite(temp_template_absolute_path, cropped_frame)
                print(f"比較用テンプレートを更新しました: {temp_template_absolute_path}")
            else:
                print("カメラからのフレーム取得に失敗しました。")

            # 3. 下ボタンを押して次の行へ
            self.press(Hat.BTM, 0.2, 0.4)

            # 画面のスクロールエフェクト（アニメーション）が完了するまで待機
            # ページ送りか1行送りか等のゲームの仕様に合わせて秒数を調整してください
            #self.sleep(0.1)

            image_count += 1

        print(f"スクリーンショット取得が完了しました。総枚数: {image_count}枚")
        return

if __name__ == "__main__":
    import sys
    import os

    # Poke-Controller-Modified-Extension/SerialController をsys.pathの先頭に追加して
    # `from Commands.Keys` 等の相対・絶対インポートが通るようにする
    current_dir = os.path.dirname(os.path.abspath(__file__))
    serial_controller_dir = os.path.abspath(os.path.join(current_dir, "..", "..", ".."))
    sys.path.insert(0, serial_controller_dir)

    # 直接実行したときに `from .base_exe_trade` のような相対インポートを通すためにパッケージ名を手動設定
    __package__ = "Commands.PythonCommands.macro"

    # BaseExeTrade の初期化で必要な cam オブジェクトのダミーを用意
    class DummyCamera:
        pass

    import traceback
    try:
        print("--- コマンドライン実行モード: test02 を実行します ---")
        app = library_summrise_exe(DummyCamera())
        app.test02()
    except Exception as e:
        print("エラーが発生しました:")
        traceback.print_exc()