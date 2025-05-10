# Poke-Controller MODIFIED Extension
機能拡張版Poke-Controller MODIFIEDです。作者がやりたいことを実現するために拡張しています。
主に複数並列起動やProconで操作したい、など。

![カイリューかわいい](https://github.com/futo030/Poke-Controller-Modified-Extension/blob/image/pokecon_modified_extension_image.png)

## MODIFIED版からの変更点

- 機能面(最新の更新はchangelog.txtを参照)
  - [Github - 更新履歴](https://github.com/futo030/Poke-Controller-Modified-Extension/blob/master/changelog.txt)
  - profileの導入
    - 複数並列起動すると、camera IDやSerial deviceの設定をやり直す必要があることから導入。\
      起動時に、Window.py --profile [profile名]とすると、profiles/[profile名]の中の.iniファイルが読み込まれるようになる。\
      メニューバーから新しいprofileを生成可能。
  - シリアルデバイス選択(Windowsのみ)
    - 使用したいシリアルデバイスをコンボボックスで選択した状態にて[Reload Port]をクリックすると、設定したシリアルデバイスを使用できる。\
      [Scan Device]のボタンをクリックすると、シリアルデバイスのリストを更新できる。
  - Proconでの操作
    - PCにProconを接続した状態で、[Use Pro Controller]のチェックボックスにチェックを入れると、proconで操作できるようになる。\
      キャプチャデバイスの処理遅延があるともっさりした挙動になる。\
      このとき、[Record Pro Controller]のチェックボックスにチェックが入っていると、proconの操作ログを[Controller_Log]のディレクトリに保存する。
  - 自動化スクリプトのタグ管理
    - 自動化スクリプトにタグを設定できる。\
      タグまたは自動化スクリプトが保存してあるフォルダ名で自動化スクリプトをフィルタリングできる。
  - 自動化スクリプトショートカット設定
    - ShortCutのタブにあるボタンに自動化スクリプトを割り当てることができる。\
      Python CommandまたはMcu Commandのタブにて、ショートカットに割り当てたい自動化スクリプトを選択、Set Shortcutにて割り当てたいボタンの番号を選択し、[Set]ボタンを押すと割り当てられる。
  - プログラム一時停止
    - [Pause]を押すとプログラムを一時停止できる。(実際は停止しているのではなくsleepしている)\
      このとき、実行中のプログラムの内部変数(self.のつく変数のみ)の値がテキストログ画面に出力される。
      [Restart]を押すと再開できる。
  - Socket通信/MQTT関連関数追加
    - 複数のswitch間で情報をやりとりする際に使用する。詳細はExternalTools.pyを参照。
  - テンプレートマッチングの探索範囲表示
    - [show guide]のチェックボックスにチェックを入れておくと、画像認識時に探索範囲を橙枠で表示する。\
      テンプレートマッチング関数のshow_positionをFalseにすると本機能は無効化され、[show guide]の状態によらず非表示になる。
  - テンプレートマッチングの検出表示機能拡張
    - [show guide]のチェックボックスにチェックを入れておくと、画像認識時に検出結果を青or赤枠で表示する。\
      青は検出成功、赤は検出失敗。\
      テンプレートマッチング関数のshow_positionをFalseにすると本機能は無効化され、[show guide]の状態によらず非表示になる。
  - LINE_Image関数のトリミング対応
    - そのままの意味。
  - 画面キャプチャ機能の拡張
    - キャプチャしている画面部分を'Ctrl+Alt+左クリック'しながらドラッグした範囲をキャプチャすることができる。\
      名前をつけて保存のダイアログボックスが出て、任意の名前をつけることができる。
  - Python 3.10起動対応
    - clrが使用できなくなったことに対する問題に対応。
  - テキストログ2画面表示
    - 常に表示したい情報と処理ログが混在してしまい見づらいという問題を解決するために導入。
  - メニューバーにヘルプを追加(ver.0.0.0.0.2)
    - いろいろと役に立ちそうな項目を追加。
  - 最新版確認機能(ver.0.0.0.0.2)
    - pokeconのアップデートを容易にするため導入。
  - テンプレートマッチング関数の拡充(ver.0.0.4)
    - 事前に準備しておいた画像に対して、カメラから取得したテンプレート画像を用いてテンプレートマッチングを行う関数を追加
    - 画像の2値化に対応

- UI面
  - UI刷新
    - ボタン配置変更。
    - メインウィンドウのテキストログ画面2分割化。
    - 設定関連はnotebookにて一元管理。
    - Tooltipを表示。
    - widgetを追加。
      - テキストログクリアボタン
      - Line通知ボタン
      - 検出結果枠表示
      - Procon操作関連チェックボックス
      - 自動化スクリプトショートカット関連widget
      - プログラム一時停止ボタン
      - テキストログ画面サイズ調整スケールバー
      - 標準出力先変更ラジオボタン
      - 質問フォーム起動ボタン

- その他
  - 画像処理系の関数をImageProcessing.pyに分離。PythonCommandBase.pyからはimportして使用するよう変更。
  - ダイアログ関連の関数をPokeConDialogue.pyに分離。

## Installation

必要なライブラリ(+推奨するライブラリ)がさらに増えています。 構築した環境にインストールしてください。

```python
pygame
paho-mqtt (MQTTを使用する場合のみ)
windows-capture-device-list (Python 3.10以上で使用する場合のみ)
gitpython
plyer
```

## 推奨環境
- OS
  - Windows10
  - (一応Mac/Linuxでも動作するはずだが未確認)
- Python
  - 3.7以上

## 開発環境
Python 3.7.9

以下はMoi-Poke様のMODIFIED版の説明になります。
- - -

本質的な部分はそのままに、機能を一部追加します

![](https://github.com/Moi-Poke/Poke-Controller/blob/photo/photos/poke-con-modded.png)

## 変更点

### 2025/3/29 ver3.1.0公開
主な変更点
- uvを利用したパッケージ管理方式を採用
- 不要なファイルを削除
- カメラからの映像取得を都度readするのではなく、queueにある最新を取得する方式に変更
- loguruを使ったloggingに移行(途中)
- discord連携を追加。通知先の設定はメニューバーから
	- 使い方はサンプルスクリプトを参照してください。
- logエリアへのテキスト出力をqueueを用いた方式に変更。若干高速化
- スクリプト実行中の例外発生時の出力を変更

python 3.10以降であれば動くと思いますが、3.12.7以降推奨。
環境構築手順

Clone後、以下の流れで起動します
```cmd
Poke-Controller-Modified-master\Poke-Controller-Modified-master> pip install uv
Poke-Controller-Modified-master\Poke-Controller-Modified-master> uv sync
Poke-Controller-Modified-master\Poke-Controller-Modified-master> .\.venv\Scripts\activate
Poke-Controller-Modified-master\Poke-Controller-Modified-master> python .\SerialController\Window.py
```

### ~ver3.0の追加・変更点

- ログ機能の追加\
  ボタン入力をメインウィンドウに表示、加えて各関数のログをコンソール画面に表示&ファイル出力を行う\
  ある程度確認しましたがボタン入力表示にはバグがあるかもしれないので注意
- 画像認識時に該当部分を青枠で表示する機能を追加\
  `isContainTemplate`関数に`show_position=False`を引数で渡すと表示しない
- サンプルスクリプトの追加
  - InputSwitchKeyboard.py

    Switchのキーボードの自動入力のサンプルコード
  - InputSerial.py

    シリアルコードの入力自動化サンプルコード
  - LoggingSample.py

    マクロプログラム中でのログのとり方のサンプルコード

-----

### ~ver2.8の追加・変更点

- 開発の都合でpythonの動作確認バージョンを3.7.xとしています(とはいえ3.6でも動くはずです。)
- FPSの設定の追加
- 画面表示サイズの変更オプションの追加
- ログエリアはサイズの変更に応じて横方向に伸縮するように
- スティック周りの機能追加

  **スティックの傾きの強さの設定**
  - スティックの移動可能な範囲を単位円の内部と考えて、\
    傾き度合いを0以上1以下で設定可能にしました。\
    例えば`Direction(Stick.LEFT, θ, r)`\
    というコマンドは、左スティックのx,y座標が
    ```
    x=r*cosθ
    y=r*sinθ
    ```
    となるような入力をします。この場合は半径rの円となります。
  - r=1.0をデフォルト値としているので\
    `Direction(Stick.LEFT, θ)`
    と書いた場合はr=1として認識されます。\
    より詳しくはサンプルコードを同梱していますので\
    そちらとSwitch内設定のスティックの補正画面を合わせて確認してください

  **マウスでスティック操作機能**
  - マウスで直感的な操作ができそうな感じにしています。~~ラグがあるので操作は結構難しいです。~~\
    操作円の半径は変更可能なので、需要があればConfigファイルに載せます。 タッチパネル対応モニタ使用の際などの挙動は不明ですが、そちらのほうが向いているかもしれません。\
    またこの機能の追加に伴い、'Ctrl+左クリック'がクリック点座標表示になっています。
- 画面キャプチャ機能の追加
  - キャプチャしている画面部分を'Ctrl+Shift+左クリック'しながらドラッグした範囲をキャプチャすることができます。
- メニュー機能の追加

  現状は以下の機能のみ
  - LINE連携機能のToken確認\
    Python Commandの関数にLine通知コマンドを追加しています。その設定がちゃんとできているかの確認です\
    **Usage**
    - LINE Notifyより通知用のTokenを取得 Tokenをline_token.iniの`paste_your_token_here`部分に貼り付け テキスト通知をしたいときは
      ```python
      self.LINE_text("通知したい内容")
      ```
      画像認識を用いるプログラム内では\
      画像とテキストを同時に通知することが可能で
      ```python
      self.LINE_image("通知したい内容")
      ```
      と書きます
    - アプリ起動時にLINE Token Check FAILED.と表示される間はtokenが間違っています。
    - Tokenが正しい場合、アプリ起動時にAPI制限までの回数・リセットされる時刻が表示されます。メニューのLINE Token checkから残数を確認できます。 頻繁に通知を行うと制限に達することがあるので気をつけましょう
    - 複数のトークンに対応しています。 tokenファイルに改行して別のトークン名を追記し、関数に引数として渡すことで使い分けてください。 詳しくはサンプルコードを参考にしてください

  - Pokémon Home連携

    そのうち大幅に変わるかもしれません\
    フォルム別の名前があるポケモン(ロトムなど)については現在第7世代までしか対応していません\
    `SerialController/db/poke_form_name.csv`に追記することで対応可能になります
  - キーコンフィグ追加

    主要なキーのコンフィグ機能を追加しています。\
    注意点として、複数キーを同時に割り当てても、同時に入力されることはありません。少々不親切ですがお許しください\
    また、これにともなって設定ファイルの書式が変わっています。手動で書き換え可能になっています。\
    デフォルトに戻す機能はつけていないので、戻したいときは設定ファイルを消すか、Setting.pyを読んでください。
- ~~ボタン入力関数表示機能追加プログラム(作 KCT様)を組み込み~~ ver3.0以降独自の入力表示機能実装に変更
- その他GUIのブラッシュアップ
- Codeのリファクタリング

  私の開発環境の関係で全体的にPEP8準拠寄りにしました
  - タブインデントからスペース4つインデントに変更
  - 不要なimportの削除、並び替えなど最適化

## Installation

必要なライブラリ(+推奨するライブラリ)が増えています。 構築した環境にインストールしてください。

```python
pygubu
requests
pandas
numpy
```

## おまけ

- 好みの表示サイズがある場合は、Window.pyのそれっぽいところに自分好みのサイズを追記してください。fpsも同様です。

- OpenCVで行う処理をNVIDIA GPUで動かすためのコードを同梱しています(TemplateMatchingTimeMeasure.py)。\
  ただし、pip install でインストール可能なライブラリでは使用できません\
  使用してみたい方は、各自で自分のGPUに対応したオプションでpython用のOpenCVをソースコードからビルドして貰う必要があります。\
  それなりに難易度が高くかなり手間な処理になりますが、余裕がある方は試してみてください。\
  `OpenCV + CUDA (+ Windows)`
  などと検索すればビルドの解説ページが出てきます。

以下は本家様の説明になります。
- - -

Pythonで書く！Switchの自動化支援ソフトウェア

<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-4-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->

## セットアップと使い方

- まずはモノの準備
  - [Github - wiki](https://github.com/KawaSwitch/Poke-Controller/wiki)

- 準備ができたら進みましょう
  - [Poke-Controllerの使い方](https://github.com/KawaSwitch/Poke-Controller/wiki/Poke-Controller%E3%81%AE%E4%BD%BF%E3%81%84%E6%96%B9)

  - [デフォルトの実装コマンドの確認](https://github.com/KawaSwitch/Poke-Controller/wiki/%E3%83%87%E3%83%95%E3%82%A9%E3%83%AB%E3%83%88%E3%81%AE%E5%AE%9F%E8%A3%85%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89)

  - [新しいコマンドを作成](https://github.com/KawaSwitch/Poke-Controller/wiki/%E6%96%B0%E3%81%97%E3%81%84Python%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89%E3%81%AE%E4%BD%9C%E3%82%8A%E6%96%B9)

分からないことや改善要望などがあれば遠慮なく[Issue](https://github.com/KawaSwitch/Poke-Controller/issues)まで  
[Q&A](https://github.com/KawaSwitch/Poke-Controller/wiki/Q&A)や[解決済みIssue](https://github.com/KawaSwitch/Poke-Controller/issues?q=is%3Aissue+is%3Aclosed)なども役に立つかもしれません

## クイックビュー

簡単に機能を見てみましょう

### コマンド作成用のライブラリの提供

通常のボタン押下  
`self.press(Button.A) # Aボタンを押して離す`  
`self.press(Button.A, 0.1, 1) # Aボタンを0.1秒間押して離した後, 1秒待機`

左右スティック & HAT(十字)キー  
`self.press(Direction.RIGHT, 5) # 左スティックを右に5秒間倒す`  
`self.press(Hat.LEFT) # 十字キー左を押して離す`

同時押し  
`self.press([Button.A, Button.B]) # AボタンとBボタンを同時に押して離す`

ホールド  
`self.hold([Direction.UP, Direction.R_DOWN], wait=1) # 左スティックを上, 右スティックを下に倒して1秒待つ`  
`self.press(Button.A) # スティックを倒した状態でAボタンを押して離す`

[リファレンス](https://github.com/KawaSwitch/Poke-Controller/wiki/Python%E3%82%B3%E3%83%9E%E3%83%B3%E3%83%89_%E4%BD%9C%E6%88%90How_to)やデフォルトのコマンドなども参考にして中身を覗いてみましょう  
作成したコマンドや便利な機能は[プルリク](https://github.com/KawaSwitch/Poke-Controller/pulls)や[Issue](https://github.com/KawaSwitch/Poke-Controller/issues)で頂けると非常に喜びます

### Pythonファイル管理

作成したコマンドのclassは1つのPythonファイルの中にいくつも記述できます  
またPythonCommandsのフォルダ内であればいくつもフォルダを作成可能です  
自由に配置していきましょう

![](https://github.com/KawaSwitch/Poke-Controller/blob/photo/photos/Wiki/PythonCommandHowTo/command_file_location.PNG)

### 実行時のコマンド切替

配置したコマンド群はマウス操作で簡単に切り替えることができます

### リロード機能

Poke-Controllerを動作しながらファイルの変更を再読込して反映することができます  
こつこつデバグしたい方におすすめ！

### 画像認識

キャプチャボードでSwitchの画面を取り込めば, シリアル通信だけでは叶わない操作もできるかも  
これらもライブラリとして機能を提供しています  
`self.isContainTemplate('status.png') # テンプレートマッチング`

現在の機能([実装内容](https://github.com/KawaSwitch/Poke-Controller/wiki/%E7%94%BB%E5%83%8F%E8%AA%8D%E8%AD%98%E3%81%A8%E3%81%AF))は少ないがアップデート予定  
![リリース前GUI](https://github.com/KawaSwitch/Poke-Controller/blob/photo/photos/pokecon_gui_before_release.PNG)

### キーボード操作

キーボードをスイッチのコントローラとして使用することができます

| Switchコントローラ | キーボード |
| ---- | ---- |
| A, B, X, Y, L, R | 'a', 'b', ...キー |
| ZL | 'k'キー |
| ZR | 'e'キー |
| MINUS | 'm'キー |
| PLUS | 'p'キー |
| LCLICK | 'q'キー |
| RCLICK | 'w'キー |
| HOME | 'h'キー |
| CAPTURE | 'c'キー |
| 左スティック | 矢印キー |

## リリース

- 過去リリース
  - [Github - Releases](https://github.com/KawaSwitch/Poke-Controller/releases)

- 進捗状況の確認
  - [Github - Project](https://github.com/KawaSwitch/Poke-Controller/projects)

- ロードマップ
  - [リリースについて](https://github.com/KawaSwitch/Poke-Controller/wiki/About-Releases)

## 貢献

これらの貢献者に感謝します ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="https://github.com/KawaSwitch"><img src="https://avatars3.githubusercontent.com/u/41296626?v=4" width="100px;" alt=""/><br /><sub><b>KawaSwitch</b></sub></a><br /><a href="https://github.com/KawaSwitch/Poke-Controller/commits?author=KawaSwitch" title="Code">💻</a> <a href="#maintenance-KawaSwitch" title="Maintenance">🚧</a> <a href="https://github.com/KawaSwitch/Poke-Controller/commits?author=KawaSwitch" title="Documentation">📖</a> <a href="#question-KawaSwitch" title="Answering Questions">💬</a></td>
    <td align="center"><a href="https://github.com/Moi-poke"><img src="https://avatars1.githubusercontent.com/u/59233665?v=4" width="100px;" alt=""/><br /><sub><b>Moi-poke</b></sub></a><br /><a href="https://github.com/KawaSwitch/Poke-Controller/commits?author=Moi-poke" title="Code">💻</a> <a href="#question-Moi-poke" title="Answering Questions">💬</a></td>
    <td align="center"><a href="https://github.com/xv13"><img src="https://avatars2.githubusercontent.com/u/47322147?v=4" width="100px;" alt=""/><br /><sub><b>xv13</b></sub></a><br /><a href="https://github.com/KawaSwitch/Poke-Controller/issues?q=author%3Axv13" title="Bug reports">🐛</a></td>
	<td align="center"><a href="https://github.com/vyPeony"><img src="https://avatars0.githubusercontent.com/u/39150264?v=4" width="100px;" alt=""/><br /><sub><b>vyPeony</b></sub></a><br /><a href="https://github.com/KawaSwitch/Poke-Controller/commits?author=vyPeony" title="Code">💻</a></td>
  </tr>
</table>

<!-- markdownlint-enable -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

このプロジェクトは, [all-contributors](https://github.com/all-contributors/all-contributors)仕様に準拠しています. どんな貢献も歓迎します！

## ライセンス

本プロジェクトはMITライセンスです  
詳細は [LISENCE](https://github.com/KawaSwitch/Poke-Controller/blob/master/LICENSE) を参照ください

また, 本プロジェクトではLGPLライセンスのDirectShowLib-2005.dllを同梱し使用しています  
[About DirectShowLib](http://directshownet.sourceforge.net/)  
