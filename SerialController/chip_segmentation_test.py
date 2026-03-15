import cv2
import numpy as np
import os

# --- 定数・座標定義 ---
CAPTURE_DIR = "Captures/Macro/rokkuman_exe/library_summrise_exe"
OUTPUT_DIR = "ChipCharTest"

# 対象とするファイル名のプレフィックス (000001 ～ 000010)
TARGET_FILES = [f"{i:06d}.png" for i in range(1, 11)]

# 行のY座標 (start, end)
Y_RANGES = [
    (171, 230), (235, 294), (299, 358),
    (363, 422), (427, 486), (491, 550), (555, 614)
]

# チップ名のX座標 (start, end)
CHIP_NAME_X_RANGE = (257, 511)

# --- ユーティリティ ---
def imread_japanese(filename, flags=cv2.IMREAD_COLOR):
    """日本語パス対応のimread"""
    if not os.path.exists(filename):
        return None
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

# --- メイン処理 ---
def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    total_saved = 0

    for filename in TARGET_FILES:
        filepath = os.path.join(CAPTURE_DIR, filename)
        img = imread_japanese(filepath)
        
        if img is None:
            print(f"画像が見つかりません: {filepath}")
            continue

        print(f"処理中: {filename}")
        basename = os.path.splitext(filename)[0]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # まず全体の二値化(白黒反転なし)を行ってから、切り出した部分だけ反転する
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

        for row_idx, (y_start, y_end) in enumerate(Y_RANGES, start=1):
            x_start, x_end = CHIP_NAME_X_RANGE
            
            # 黒文字を白浮きさせるために反転
            roi_bin = cv2.bitwise_not(thresh[y_start:y_end, x_start:x_end])
            
            # カラーでの切り出し用
            roi_color = img[y_start:y_end, x_start:x_end]
            
            # 内部の輪郭(個別の文字)も取得するため RETR_TREE に変更
            contours, _ = cv2.findContours(roi_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
            
            bounding_boxes = []
            for cnt in contours:
                x, y, w, h = cv2.boundingRect(cnt)
                # ゴーミのノイズ除去: 面積が極端に小さいものは無視 (幅2px以下、高さ4px以下など)
                # また、外枠全体(wが広すぎるもの)を除外する
                if w > 2 and h > 4 and w < (x_end - x_start - 10): 
                    bounding_boxes.append((x, y, w, h))
            
            # X座標（左から右）へソートして、文字の順番通りにする
            bounding_boxes.sort(key=lambda b: b[0])

            char_count = 1
            for x, y, w, h in bounding_boxes:
                # 少しパディングを取って切り抜く（範囲外に出ないようmax/minでクリップ）
                pad = 1
                crop_y1 = max(0, y - pad)
                crop_y2 = min(roi_color.shape[0], y + h + pad)
                crop_x1 = max(0, x - pad)
                crop_x2 = min(roi_color.shape[1], x + w + pad)
                # やはりカラーのまま切り出す（2値化するとフォントがガビガビになるため）
                char_img = roi_color[crop_y1:crop_y2, crop_x1:crop_x2]
                
                # 元ファイル名_行番(1-7)_何文字目かの通番.png
                save_name = f"{basename}_row{row_idx}_char{char_count}.png"
                save_path = os.path.join(OUTPUT_DIR, save_name)
                
                if imwrite_japanese(save_path, char_img):
                    total_saved += 1
                    char_count += 1
                    
    print(f"完了しました！ {total_saved} 枚の文字画像を {OUTPUT_DIR} に保存しました。")

if __name__ == "__main__":
    main()
