import cv2
import numpy as np
import os

filepath = 'Captures/Macro/rokkuman_exe/library_summrise_exe/000001.png'
with open(filepath, 'rb') as f:
    file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
_, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

y_start, y_end = 171, 230
x_start, x_end = 257, 511

# 黒文字を抽出するため、対象範囲を切り出してから白黒を反転させる
# otsuにより背景は白(255)、文字は黒(0)になっている想定
roi_bin_org = thresh[y_start:y_end, x_start:x_end]
roi_bin = cv2.bitwise_not(roi_bin_org)

# 念のためのデバッグ画像書き出し
if not os.path.exists("ChipCharTest"):
    os.makedirs("ChipCharTest")
cv2.imwrite('ChipCharTest/debug_roi_bin.png', roi_bin)

# RETR_TREEを使って内部の輪郭(文字)を取得する
contours, hierarchy = cv2.findContours(roi_bin, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
print('Found contours:', len(contours))

bounding_boxes = []
for cnt in contours:
    x, y, w, h = cv2.boundingRect(cnt)
    # 外枠そのもの(wが広すぎるもの)は除外する
    if w > 2 and h > 4 and w < (x_end - x_start - 10): 
        bounding_boxes.append((x, y, w, h))

print('Valid boxes:', len(bounding_boxes))
