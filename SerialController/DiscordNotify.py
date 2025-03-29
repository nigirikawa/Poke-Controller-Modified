import os
from tkinter import messagebox, simpledialog
import cv2
import io

from deprecated import deprecated
import requests
from PIL import Image
from loguru import logger
import yaml
import tkinter as tk
from Camera import Camera


class Discord_Notify:
    """
    Discordに通知するクラス
    """

    def __init__(self, config_file: str = "discord.yml", camera: Camera = None):
        if camera is None:
            self.use_camera = False
        else:
            self.camera = camera
            self.use_camera = True
        self.config_file = config_file
        self.webhooks = self.load_config()

    # camera読み込みをbyte形式に変換する関数
    def camera_to_byte(self) -> bytes:
        """
        カメラの画像をbyte形式に変換する関数
        """
        image_bgr = self.camera.readFrame()
        image_rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(image_rgb)
        png = io.BytesIO()
        image.save(
            png, format="png"
        )  # 空のio.BytesIOオブジェクトにpngファイルとして書き込み
        b_frame = png.getvalue()  # io.BytesIOオブジェクトをbytes形式で読みとり
        return b_frame

    # YAML設定ファイルからWebhook URLリストを読み込む関数
    def load_config(self) -> list:
        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
            return list(config.get("webhooks", []))  # Webhooksのリストを返す
        except FileNotFoundError:
            return []  # 設定ファイルが見つからない場合、空のリストを返す

    # YAML設定ファイルにWebhookリストを保存する関数
    def save_config(self) -> None:
        config = {"webhooks": self.webhooks}
        with open(self.config_file, "w", encoding="utf-8") as f:
            yaml.dump(config, f)

    # Webhookリストから選択されたURLを取得
    def get_webhook_url(self, index: int) -> str | None:
        if 0 <= index < len(self.webhooks):
            return str(self.webhooks[index]["url"])
        return None

    # 新しいWebhookを追加する関数
    def add_webhook(self, name: str, url: str) -> None:
        self.webhooks.append({"name": name, "url": url})
        self.save_config()

    # Webhookを更新する関数
    def update_webhook(self, index: int, name: str, url: str) -> None:
        if 0 <= index < len(self.webhooks):
            self.webhooks[index] = {"name": name, "url": url}
            self.save_config()

    # Webhookを削除する関数
    def delete_webhook(self, index: int) -> None:
        if 0 <= index < len(self.webhooks):
            del self.webhooks[index]
            self.save_config()

    # Discordにメッセージを送信する関数
    def send_message(self, index: int, content: str) -> None:
        url = self.get_webhook_url(index)
        if url:
            files = (
                {"file": ("image.png", self.camera_to_byte(), "image/png")}
                if self.use_camera
                else {}
            )
            data = {"content": content}
            response = requests.post(url, data=data, files=files)
            if response.status_code == 204:
                print(f"{self.webhooks[index]['name']}にメッセージを送信しました。")
            else:
                print(f"エラーが発生しました: {response.status_code}")
        else:
            print("Webhook URLが選択されていません。")

    @deprecated(reason="Use send_message instead")
    def send_text(self, notification_message: str, token: str = "token") -> None:
        try:
            self.send_message(0, notification_message)
        except KeyError:
            print("token名が間違っています")
            logger.error("Using the wrong token")

    @deprecated(reason="Use send_message instead")
    def send_text_n_image(
        self, notification_message: str, token: str = "token"
    ) -> None:
        try:
            self.send_message(0, notification_message)
        except KeyError:
            print("token名が間違っています")
            logger.error("Using the wrong token")


# GUIの設定と操作
class WebhookGUI:
    def __init__(self, parent: tk.Tk, webhook: Discord_Notify):
        self.root = parent
        self.webhook = webhook

        self.window: tk.Toplevel = tk.Toplevel(self.root)

        self.window.geometry("200x300")
        self.window.resizable(False, False)  # リサイズ不可に設定
        # 親ウィンドウの最小化、最大化ボタンを無効化
        # self.window.overrideredirect(True)  # 装飾（タイトルバー）を完全に消す

        self.window.title("Discord設定")

        # Webhook選択のラベルとドロップダウンメニュー
        self.label_url = tk.Label(self.window, text="Webhook選択:")
        self.label_url.pack(pady=10)

        self.webhook_options = (
            [webhook["name"] for webhook in self.webhook.webhooks]
            if self.webhook.webhooks
            else [""]
        )
        self.selected_webhook = tk.StringVar(self.window)
        self.selected_webhook.set(
            self.webhook_options[0] if self.webhook_options else ""
        )  # 初期値の設定

        self.dropdown = tk.OptionMenu(
            self.window, self.selected_webhook, *self.webhook_options
        )
        self.dropdown.pack(pady=10)

        # メッセージ送信ボタン
        self.send_button = tk.Button(
            self.window, text="テスト送信", command=self.send_webhook
        )
        self.send_button.pack(pady=10)

        # Webhook追加、更新、削除ボタン
        self.add_button = tk.Button(
            self.window, text="Webhook追加", command=self.add_webhook
        )
        self.add_button.pack(pady=10)

        self.update_button = tk.Button(
            self.window, text="Webhook更新", command=self.update_webhook
        )
        self.update_button.pack(pady=10)

        self.delete_button = tk.Button(
            self.window, text="Webhook削除", command=self.delete_webhook
        )
        self.delete_button.pack(pady=10)

    # Webhookを選択してメッセージ送信
    def send_webhook(self) -> None:
        selected_index = self.webhook_options.index(self.selected_webhook.get())
        content = "こんにちは、Discord！"
        self.webhook.send_message(selected_index, content)
        messagebox.showinfo("成功", "メッセージが送信されました！")

    # 新しいWebhookを追加
    def add_webhook(self) -> None:
        name = simpledialog.askstring(
            "Webhookの名前", "Webhookの名前を入力してください:"
        )
        url = simpledialog.askstring("WebhookのURL", "WebhookのURLを入力してください:")
        if name and url:
            self.webhook.add_webhook(name, url)
            self.refresh_dropdown()

    # Webhookを更新
    def update_webhook(self) -> None:
        selected_index = self.webhook_options.index(self.selected_webhook.get())
        name = simpledialog.askstring("Webhookの名前", "新しい名前を入力してください:")
        url = simpledialog.askstring("WebhookのURL", "新しいURLを入力してください:")
        if name and url:
            self.webhook.update_webhook(selected_index, name, url)
            self.refresh_dropdown()

    # Webhookを削除
    def delete_webhook(self) -> None:
        selected_index = self.webhook_options.index(self.selected_webhook.get())

        # 削除確認ダイアログを表示
        result = messagebox.askyesno("確認", "本当に削除しますか?")

        if result:  # ユーザーが「はい」を選んだ場合
            self.webhook.delete_webhook(selected_index)
            self.refresh_dropdown()
            messagebox.showinfo("削除完了", "Webhookが削除されました。")
        else:
            messagebox.showinfo("キャンセル", "削除がキャンセルされました。")

    # ドロップダウンメニューを更新
    def refresh_dropdown(self) -> None:
        self.webhook_options = (
            [webhook["name"] for webhook in self.webhook.webhooks]
            if self.webhook.webhooks
            else []
        )
        self.selected_webhook.set(
            self.webhook_options[0] if self.webhook_options else ""
        )
        self.dropdown["menu"].delete(0, "end")
        for option in self.webhook_options:
            self.dropdown["menu"].add_command(
                label=option, command=tk._setit(self.selected_webhook, option)
            )


if __name__ == "__main__":
    os.chdir("./SerialController")
    Webhook = Discord_Notify()

    root = tk.Tk()
    gui = WebhookGUI(root, Webhook)

    root.mainloop()
