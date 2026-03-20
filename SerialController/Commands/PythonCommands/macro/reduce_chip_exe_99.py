from .base_exe_trade import BaseExeTrade


class reduce_chip_exe_99(BaseExeTrade):
    NAME = "エグゼ_99枚トレードチップ削減"
    TRADE_TYPE = 10  # チップトレーダーに入れる枚数 (3枚版は別クラスで対応)
    TARGET_CHIP_COUNT = 99  # 受け側のチップ枚数がこの数以上になるようにトレードする
    def do(self):
        self.reduce_chip_loop()
