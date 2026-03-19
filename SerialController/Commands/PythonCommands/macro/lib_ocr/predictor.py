import os
import json
import cv2
import torch
import torch.nn.functional as F
import torchvision.transforms as transforms
import numpy as np
from PIL import Image

# 内部モデルのインポート
from .models import ExeCharCNN

# ============================================================
# 1. 文字種定数
# ============================================================
TEMPLATE_CODE = tuple("ABCDEFGHIJKLMNOPQRSTUVWXYZ＊")
TEMPLATE_NUMBER_BLANK = tuple("0123456789") + ("",)
TEMPLATE_NUMBER_ONLY = tuple("0123456789")

# 標準画像サイズ
IMG_HEIGHT = 59
IMG_WIDTH = 31

# ============================================================
# 2. ExeCharPredictor クラス (リファクタリング版)
# ============================================================
class ExeCharPredictor:
    """エグゼ文字認識用の簡略化されたラッパークラス。
    マクロパッケージ内の data/ フォルダから自動的にモデルとマッピングをロードする。
    """
    @staticmethod
    def resolve_ocr_paths():
        """自身のディレクトリを基準に OCR 用のパスを解決する"""
        base_dir = os.path.dirname(os.path.abspath(__file__))
        model_path = os.path.join(base_dir, "data", "best_model.pth")
        mapping_path = os.path.join(base_dir, "data", "class_mapping.json")
        return model_path, mapping_path

    def __init__(self, model_path=None, mapping_path=None):
        """
        Args:
            model_path (str, optional): .pth ファイルのパス。Noneの場合は自動解決。
            mapping_path (str, optional): class_mapping.json のパス。Noneの場合は自動解決。
        """
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # 引数が None の場合は自動ロード
        if model_path is None or mapping_path is None:
            auto_model, auto_mapping = self.resolve_ocr_paths()
            if model_path is None:
                model_path = auto_model
            if mapping_path is None:
                mapping_path = auto_mapping

        # 1. マッピングのロード
        if not os.path.exists(mapping_path):
            raise FileNotFoundError(f"Mapping file not found: {mapping_path}")
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        
        self.class_names = [None] * len(mapping)
        for name, idx in mapping.items():
            self.class_names[idx] = name
        self.class_to_idx = {name: i for i, name in enumerate(self.class_names)}
        self.num_classes = len(self.class_names)

        # 2. モデルの初期化とロード
        self.model = ExeCharCNN(num_classes=self.num_classes)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
            
        checkpoint = torch.load(model_path, map_location=self.device, weights_only=False)
        if isinstance(checkpoint, dict) and 'model_state_dict' in checkpoint:
            self.model.load_state_dict(checkpoint['model_state_dict'])
        else:
            self.model.load_state_dict(checkpoint)
            
        self.model.to(self.device)
        self.model.eval()

        self.transform = transforms.Compose([
            transforms.ToTensor(),
        ])

    def _load_image(self, image_data):
        if isinstance(image_data, np.ndarray):
            if len(image_data.shape) == 3:
                return cv2.cvtColor(image_data, cv2.COLOR_BGR2GRAY)
            return image_data
        elif isinstance(image_data, Image.Image):
            return np.array(image_data.convert('L'))
        elif isinstance(image_data, str):
            with open(image_data, 'rb') as f:
                file_bytes = np.frombuffer(f.read(), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_GRAYSCALE)
            return img
        return image_data

    def predict(self, image_data, allowed_chars=None):
        """互換性のための単一予測メソッド"""
        results = self.predict_top_k(image_data, allowed_chars=allowed_chars, k=1)
        return results[0]

    def predict_top_k(self, image_data, allowed_chars=None, k=3):
        """
        上位K件の推論結果を取得する。
        Args:
            image_data: 画像データ
            allowed_chars: 許可文字リスト
            k: 取得件数
        Returns:
            list: [(文字1, 確率1), (文字2, 確率2), ...]
        """
        img_gray = self._load_image(image_data)
        
        # --- 自動サイズ正規化ロジック (パディング / クロップ) ---
        h, w = img_gray.shape
        target_h, target_w = IMG_HEIGHT, IMG_WIDTH

        # ★背景色の自動判定（画像内で最も出現回数が多いピクセル値を取得）
        bg_color = int(np.bincount(img_gray.flatten()).argmax())

        if h != target_h or w != target_w:
            # 1. はみ出ている場合は中央でクロップ
            if h > target_h:
                start_y = (h - target_h) // 2
                img_gray = img_gray[start_y : start_y + target_h, :]
                h = target_h
            if w > target_w:
                start_x = (w - target_w) // 2
                img_gray = img_gray[:, start_x : start_x + target_w]
                w = target_w

            # 2. 足りない場合は「自動判定した背景色」で中央になるようにパディング
            pad_top = (target_h - h) // 2
            pad_bottom = target_h - h - pad_top
            pad_left = (target_w - w) // 2
            pad_right = target_w - w - pad_left

            if pad_top > 0 or pad_bottom > 0 or pad_left > 0 or pad_right > 0:
                img_gray = cv2.copyMakeBorder(
                    img_gray, pad_top, pad_bottom, pad_left, pad_right,
                    cv2.BORDER_CONSTANT, value=bg_color
                )
        # ----------------------------------------------------

        img_tensor = self.transform(img_gray).unsqueeze(0).to(self.device)

        with torch.no_grad():
            logits = self.model(img_tensor)

            if allowed_chars is not None:
                allowed_indices = []
                for char in allowed_chars:
                    if char in self.class_to_idx:
                        allowed_indices.append(self.class_to_idx[char])
                
                if allowed_indices:
                    masked_logits = torch.full_like(logits, float('-inf'))
                    for idx in allowed_indices:
                        masked_logits[0, idx] = logits[0, idx]
                    logits = masked_logits

            probs = F.softmax(logits, dim=1)
            
            # 実装上の安全のため、要求された k とクラス数の小さい方を採用
            k = min(k, self.num_classes)
            top_probs, top_indices = torch.topk(probs, k, dim=1)
            
            results = []
            for i in range(k):
                conf = top_probs[0, i].item()
                if conf <= 0.1: # 信頼度0.1以下は除外
                    continue
                idx = top_indices[0, i].item()
                res_char = self.class_names[idx]
                results.append((res_char, conf))
            
            return results
