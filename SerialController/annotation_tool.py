import cv2
import numpy as np
import os
import re
import json
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk

# --- 定数・座標定義 ---
# キャプチャ画像フォルダのパス (Poke-Controller実行ディレクトリからの相対パス想定)
CAPTURE_DIR = "Captures/Macro/rokkuman_exe/library_summrise_exe"
# 切り出した1文字ごとの画像を保存するベースディレクトリ
OUTPUT_DIR = "CharImages"
# 正解ラベルを保存するファイル
LABELS_FILE = "labels.json"

# 行のY座標 (start, end)
Y_RANGES = [
    (171, 230), (235, 294), (299, 358),
    (363, 422), (427, 486), (491, 550), (555, 614)
]

# パーツごとのX座標 (start, end, part_name)
X_RANGES = [
    (257, 511, "chip"),
    (577, 609, "code"),
    (676, 703, "amount_tens"),
    (708, 735, "amount_ones")
]

# --- 画像処理・分割処理 ---
def get_target_files(directory):
    """ディレクトリ内の対象ファイル(\d{6}.png)をリストアップする"""
    target_files = []
    if not os.path.exists(directory):
        print(f"ディレクトリが見つかりません: {directory}")
        return []
    
    pattern = re.compile(r'^\d{6}( - コピー)?\.png$') # コピーファイルもテスト用に一時許容
    for filename in os.listdir(directory):
        if pattern.match(filename):
            target_files.append(os.path.join(directory, filename))
    return sorted(target_files)

def imread_japanese(filename, flags=cv2.IMREAD_COLOR):
    """日本語パス対応のimread"""
    with open(filename, 'rb') as f:
        file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
    return cv2.imdecode(file_bytes, flags)

def imwrite_japanese(filename, img, params=None):
    """日本語パス対応のimwrite"""
    ext = os.path.splitext(filename)[1]
    result, n = cv2.imencode(ext, img, params)
    if result:
        with open(filename, mode='w+b') as f:
            n.tofile(f)
        return True
    return False

def segment_characters():
    """画像群を読み込み、1文字ずつ切り出して保存する"""
    files = get_target_files(CAPTURE_DIR)
    if not files:
        print("処理対象の画像が見つかりませんでした。")
        return []

    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    generated_images = []

    for filepath in files:
        basename = os.path.splitext(os.path.basename(filepath))[0]
        # " - コピー" などのサフィックスがあれば除去してベース名にする
        basename = basename.replace(" - コピー", "")

        img = imread_japanese(filepath)
        if img is None:
            continue

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        # 輪郭抽出用の二値化 (黒背景に白文字とするため反転)
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        for row_idx, (y_start, y_end) in enumerate(Y_RANGES, start=1):
            for x_start, x_end, part_name in X_RANGES:
                roi_bin = thresh[y_start:y_end, x_start:x_end]
                roi_color = img[y_start:y_end, x_start:x_end]

                # 輪郭を抽出
                contours, _ = cv2.findContours(roi_bin, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                bounding_boxes = []
                for cnt in contours:
                    x, y, w, h = cv2.boundingRect(cnt)
                    # ノイズ除去: 面積が小さすぎるものは無視
                    if w > 2 and h > 5: 
                        bounding_boxes.append((x, y, w, h))
                
                # X座標（左から右）へソート
                bounding_boxes.sort(key=lambda b: b[0])

                for char_idx, (cx, cy, cw, ch) in enumerate(bounding_boxes, start=1):
                    # 少しだけマージンを取って切り抜く（範囲外に出ないようクリップ）
                    pad = 1
                    crop_y1 = max(0, cy - pad)
                    crop_y2 = min(roi_color.shape[0], cy + ch + pad)
                    crop_x1 = max(0, cx - pad)
                    crop_x2 = min(roi_color.shape[1], cx + cw + pad)
                    
                    char_img = roi_color[crop_y1:crop_y2, crop_x1:crop_x2]
                    
                    save_name = f"{basename}_{row_idx}_{part_name}_{char_idx}.png"
                    save_path = os.path.join(OUTPUT_DIR, save_name)
                    
                    if imwrite_japanese(save_path, char_img):
                        generated_images.append(save_path)
    
    print(f"文字画像の切り出しが完了しました。合計: {len(generated_images)}枚")
    return generated_images

# --- 推論・GUI連携 ---
def predict_label(filename):
    """
    ファイル名や画像パスから初期ラベルを推測するダミー関数。
    将来的には外部JSONなどと連携する。
    """
    # スタブとして現在は空文字を返す
    return ""

def load_labels():
    if os.path.exists(LABELS_FILE):
        with open(LABELS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_labels(labels):
    with open(LABELS_FILE, 'w', encoding='utf-8') as f:
        json.dump(labels, f, ensure_ascii=False, indent=4)

# --- GUIアプリケーション ---
class AnnotationApp:
    def __init__(self, root, image_paths):
        self.root = root
        self.root.title("文字アノテーションツール")
        self.root.geometry("400x400")
        
        self.image_paths = sorted(image_paths)
        self.current_idx = 0
        self.labels = load_labels()
        
        self.setup_ui()
        self.load_image()

    def setup_ui(self):
        # 画像表示エリア
        self.img_label = tk.Label(self.root)
        self.img_label.pack(pady=20)

        # ファイル名表示
        self.filename_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.filename_var, font=("Arial", 10)).pack()

        # 推測ラベル表示
        self.pred_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.pred_var, fg="blue", font=("Arial", 12)).pack(pady=5)

        # 入力ボックス
        tk.Label(self.root, text="正解を入力（空欄で推測を利用）:").pack()
        self.entry_var = tk.StringVar()
        self.entry = tk.Entry(self.root, textvariable=self.entry_var, font=("Arial", 14), justify="center")
        self.entry.pack(pady=10)
        self.entry.bind('<Return>', lambda event: self.next_image())

        # ボタンエリア
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=20)
        
        tk.Button(btn_frame, text="戻る (Prev)", command=self.prev_image, width=10).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame, text="次へ (Next)", command=self.next_image, width=10, bg="lightblue").pack(side=tk.LEFT, padx=10)

        # 完了メッセージ
        self.status_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.status_var, fg="green").pack(side=tk.BOTTOM, pady=10)

    def load_image(self):
        if not self.image_paths:
            self.status_var.set("画像がありません。")
            return

        if self.current_idx >= len(self.image_paths):
            self.status_var.set("すべての画像を処理しました！")
            self.img_label.config(image='')
            return
            
        if self.current_idx < 0:
            self.current_idx = 0

        filepath = self.image_paths[self.current_idx]
        filename = os.path.basename(filepath)
        self.filename_var.set(f"ファイル: {filename} ({self.current_idx + 1}/{len(self.image_paths)})")
        
        # Pillowで画像を読み込みリサイズ（拡大表示）
        try:
            pil_img = Image.open(filepath)
            # 見やすいように拡大 (Nearest Neighborでドット感を残す)
            width, height = pil_img.size
            scale = 4
            pil_img = pil_img.resize((width * scale, height * scale), Image.NEAREST)
            self.tk_img = ImageTk.PhotoImage(pil_img)
            self.img_label.config(image=self.tk_img)
        except Exception as e:
            print(f"画像ロードエラー: {e}")

        # 予測
        pred = predict_label(filename)
        self.pred_var.set(f"推測値: [{pred}]" if pred else "推測値: (なし)")
        
        # 既存のラベルがあれば復元、なければクリア
        existing_label = self.labels.get(filename, "")
        self.entry_var.set(existing_label)
        
        self.entry.focus_set()

    def next_image(self):
        if self.current_idx >= len(self.image_paths):
            return

        filepath = self.image_paths[self.current_idx]
        filename = os.path.basename(filepath)
        
        user_input = self.entry_var.get().strip()
        
        # 入力が空なら推測値を採用する
        if not user_input:
            pred = predict_label(filename)
            final_label = pred
        else:
            final_label = user_input
            
        # 登録
        self.labels[filename] = final_label
        save_labels(self.labels)
        
        # 次へ
        self.current_idx += 1
        self.load_image()

    def prev_image(self):
        self.current_idx -= 1
        self.load_image()

if __name__ == "__main__":
    print("--- 1. 文字画像の切り出し処理を開始します ---")
    char_images = segment_characters()
    
    if not char_images:
        print("表示する文字画像がありません。終了します。")
    else:
        print("--- 2. アノテーションGUIを起動します ---")
        root = tk.Tk()
        app = AnnotationApp(root, char_images)
        root.mainloop()
