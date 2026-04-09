from .base_exe_trade import BaseExeTrade


class reduce_chip_exe_9(BaseExeTrade):
    NAME = "エグゼ_9枚トレードチップ削減"
    TRADE_TYPE = 10  # チップトレーダーに入れる枚数 (3枚版は別クラスで対応)
    TARGET_CHIP_COUNT = 9  # 受け側のチップ枚数がこの数以上になるようにトレードする
    def do(self):
        self.reduce_chip_loop(csv_filename="exe5_chip_list.csv")
