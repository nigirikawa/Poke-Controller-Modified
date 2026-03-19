import torch.nn as nn

class ExeCharCNN(nn.Module):
    """エグゼ文字認識用CNN (位置ズレ・色反転 耐性強化版)"""

    def __init__(self, num_classes, img_height=59, img_width=31):
        super().__init__()

        # 畳み込みブロック1 (ピクセルレベルの特徴抽出)
        self.conv_block1 = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # 59x31 → 29x15
        )

        # 畳み込みブロック2 (パーツレベルの特徴抽出)
        self.conv_block2 = nn.Sequential(
            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # 29x15 → 14x7
        )

        # 畳み込みブロック3 (図形全体の特徴抽出：ズレへの耐性強化)
        self.conv_block3 = nn.Sequential(
            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),  # 14x7 → 7x3
        )

        # Flatten後のサイズ計算: 128チャネル * 縦7 * 横3
        self._flat_size = 128 * 7 * 3  # = 2688

        # 全結合層
        self.classifier = nn.Sequential(
            nn.Flatten(),
            nn.Linear(self._flat_size, 256),
            nn.ReLU(),
            nn.Dropout(0.4),
            nn.Linear(256, num_classes),
        )

    def forward(self, x):
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        x = self.conv_block3(x)
        x = self.classifier(x)
        return x
