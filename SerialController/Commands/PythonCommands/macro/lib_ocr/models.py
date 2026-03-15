import torch.nn as nn

class ExeCharCNN(nn.Module):
    """
    エグゼ文字認識用のシンプルなCNNモデル。
    """
    def __init__(self, num_classes, img_height=59, img_width=28):
        super().__init__()

        # 畳み込みブロック1
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),  # (1, 59, 28) → (32, 59, 28)
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                           # → (32, 29, 14)
        )

        # 畳み込みブロック2
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),  # (32, 29, 14) → (64, 29, 14)
            nn.ReLU(),
            nn.MaxPool2d(2, 2),                            # → (64, 14, 7)
        )

        # Flatten後のサイズを計算
        self._flat_size = 64 * 14 * 7  # = 6272

        # 全結合層
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self._flat_size, 128),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(128, num_classes)
        )

    def forward(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.classifier(x)
        return x
