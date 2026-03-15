import cv2
import numpy as np
import os
import math

INPUT_DIR = "ChipCharTest"
OUTPUT_DIR = "ChipCharGridTest"

# フィンガープリントのサイズ
FP_SIZE = 16
# 同じ文字とみなすピクセル誤差の許容値 (0.0 ~ 1.0)
# この値を少し緩めにしつつ、縦横比やサイズでの足切りを導入する
MSE_THRESHOLD = 0.001

# 縦横比の許容誤差 (20%)
ASPECT_RATIO_TOLERANCE = 0.00
# 実際の幅・高さの許容ピクセル誤差
SIZE_TOLERANCE = 0

# グリッド画像のセルサイズ (5割増し)
CELL_SIZE = 50
# 1行あたりの列数
GRID_COLS = 20


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

def extract_fingerprint(img):
    """
    画像から16x16の特徴量（白黒のバイナリ配列）を抽出する
    """
    # グレースケール化
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 大津の二値化でテキスト(黒)を白(255)、背景を黒(0)にする
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)
    
    # アスペクト比を維持して正方形にパディングする
    h, w = thresh.shape
    size = max(h, w)
    
    # 中心に配置するための余白を計算
    pad_h = (size - h) // 2
    pad_w = (size - w) // 2
    
    padded = cv2.copyMakeBorder(
        thresh, 
        pad_h, size - h - pad_h, 
        pad_w, size - w - pad_w, 
        cv2.BORDER_CONSTANT, 
        value=0
    )
    
    # 16x16 にリサイズ
    resized = cv2.resize(padded, (FP_SIZE, FP_SIZE), interpolation=cv2.INTER_AREA)
    
    # 再度2値化して 0 か 1 の値にする
    _, final_bin = cv2.threshold(resized, 127, 1, cv2.THRESH_BINARY)
    
    aspect_ratio = w / float(h) if h > 0 else 0
    
    return {
        "pixels": final_bin.astype(np.float32),
        "w": w,
        "h": h,
        "aspect_ratio": aspect_ratio
    }

def calculate_mse(fp1, fp2, max_shift=1):
    """
    2つのフィンガープリント間の平均二乗誤差(Mean Squared Error)を計算する
    最大 max_shift ピクセル分のズレ(上下左右)を許容し、最も誤差が小さくなるパターンの値を返す
    """
    min_err = float('inf')
    
    pixels1 = fp1["pixels"]
    pixels2 = fp2["pixels"]
    
    h, w = pixels1.shape
    
    for dy in range(-max_shift, max_shift + 1):
        for dx in range(-max_shift, max_shift + 1):
            # アフィン変換で画像をシフト (はみ出た部分は0埋め)
            M = np.float32([[1, 0, dx], [0, 1, dy]])
            shifted_fp1 = cv2.warpAffine(
                pixels1, M, (w, h), 
                flags=cv2.INTER_NEAREST, 
                borderMode=cv2.BORDER_CONSTANT, 
                borderValue=0
            )
            err = np.sum((shifted_fp1 - pixels2) ** 2) / float(h * w)
            if err < min_err:
                min_err = err
                
    return min_err

def create_grid_image(images, cell_size=CELL_SIZE, cols=GRID_COLS):
    """
    複数の画像を1枚のグリッド画像にまとめる
    """
    n = len(images)
    rows = math.ceil(n / cols)
    
    # グリッドのベース画像を作成（背景は薄いグレー）
    grid_img = np.ones((rows * cell_size, cols * cell_size, 3), dtype=np.uint8) * 200
    
    for idx, img in enumerate(images):
        row = idx // cols
        col = idx % cols
        
        y_offset = row * cell_size
        x_offset = col * cell_size
        
        h, w = img.shape[:2]
        
        # セルサイズを超える場合はリサイズ
        if h > cell_size or w > cell_size:
            scale = min(cell_size / w, cell_size / h)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            h, w = img.shape[:2]
            
        # セルの中央に配置
        start_y = y_offset + (cell_size - h) // 2
        start_x = x_offset + (cell_size - w) // 2
        
        grid_img[start_y:start_y+h, start_x:start_x+w] = img
        
        # セルの枠線を描画
        cv2.rectangle(
            grid_img, 
            (x_offset, y_offset), 
            (x_offset + cell_size, y_offset + cell_size), 
            (150, 150, 150), 
            1
        )
        
    return grid_img

def main():
    if not os.path.exists(INPUT_DIR):
        print(f"入力ディレクトリが見つかりません: {INPUT_DIR}")
        return
        
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        
    files = sorted([f for f in os.listdir(INPUT_DIR) if f.endswith(".png")])
    if not files:
        print(f"画像が見つかりません")
        return
        
    print(f"合計 {len(files)} 枚の画像を読み込み中...")
    
    # 画像データとフィンガープリントの準備
    items = []
    for f in files:
        path = os.path.join(INPUT_DIR, f)
        img = imread_japanese(path)
        if img is not None:
            fp = extract_fingerprint(img)
            items.append({
                "filename": f,
                "image": img,
                "fingerprint": fp
            })
            
    print("クラスタリング（グループ化）を実行中...")
    clusters = [] # [ {"representative_fp": fp, "items": [item1, item2, ...]} ]
    
    for item in items:
        fp = item["fingerprint"]
        
        # 既存のクラスタと比較
        best_match_idx = -1
        min_error = float('inf')
        
        for i, cluster in enumerate(clusters):
            rep_fp = cluster["representative_fp"]
            
            # まずサイズとアスペクト比で足切りを行う
            # 1. 縦横比が一定以上違うものは別文字
            ratio_diff = abs(fp["aspect_ratio"] - rep_fp["aspect_ratio"])
            if ratio_diff > ASPECT_RATIO_TOLERANCE:
                continue
                
            # 2. 高さや幅が大きく違うものは別文字
            if abs(fp["w"] - rep_fp["w"]) > SIZE_TOLERANCE or \
               abs(fp["h"] - rep_fp["h"]) > SIZE_TOLERANCE:
                continue
            
            # クラスタの代表特徴量とMSEを比較
            err = calculate_mse(fp, rep_fp)
            if err < min_error:
                min_error = err
                best_match_idx = i
                
        # 閾値以内ならクラスタに追加
        if min_error < MSE_THRESHOLD and best_match_idx != -1:
            clusters[best_match_idx]["items"].append(item)
            # 代表を平均化するかどうか（今回はシンプルに最初の要素を代表のままにする）
        else:
            # 新しいクラスタを作成
            clusters.append({
                "representative_fp": fp,
                "items": [item]
            })
            
    # グループ数が多い順にソートして出力する
    clusters.sort(key=lambda c: len(c["items"]), reverse=True)
            
    print(f"結果: {len(clusters)} 個のグループに分類されました。")
    print("グリッド画像を生成中...")
    
    for i, cluster in enumerate(clusters):
        cluster_items = cluster["items"]
        rep_fp = cluster["representative_fp"]
        
        # 代表特徴量（最初に登録された文字）との類似度(MSE)でソートする
        for item in cluster_items:
            item["distance"] = calculate_mse(item["fingerprint"], rep_fp)
        cluster_items.sort(key=lambda x: x["distance"])
        
        images = [item["image"] for item in cluster_items]
        
        grid_img = create_grid_image(images)
        
        count = len(cluster_items)
        # ファイル名: cluster_001_5items.png のような形式
        filename = f"cluster_{i:03d}_{count}items.png"
        save_path = os.path.join(OUTPUT_DIR, filename)
        
        imwrite_japanese(save_path, grid_img)
        
    print(f"完了しました！ {OUTPUT_DIR} にグリッド画像を保存しました。")

if __name__ == "__main__":
    main()
