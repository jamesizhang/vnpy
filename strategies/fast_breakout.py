"""
Fast Donchian channel breakout strategy.

Trades on 1-minute bars: buys when close breaks above the highest high
of the previous entry_window bars, exits when close breaks below the
lowest low of the previous exit_window bars. Short windows produce
frequent trades, so use smaller windows for higher frequency.

Deploy: copy to ~/.vntrader/strategies/ and restart vnpy.
"""

from vnpy_ctastrategy import (
    CtaTemplate,
    BarData,
    TickData,
    BarGenerator,
    ArrayManager,
)


class FastBreakoutStrategy(CtaTemplate):
    """Fast Donchian channel breakout strategy."""

    author = "lucifer"

    entry_window = 10      # 入场：突破前N根K线最高价
    exit_window = 5        # 出场：跌破前M根K线最低价
    trading_size = 100

    pos = 0
    highest_price = 0.0
    lowest_price = 0.0

    parameters = ["entry_window", "exit_window", "trading_size"]
    variables = ["pos", "highest_price", "lowest_price"]

    def __init__(self, cta_engine, strategy_name, vt_symbol, setting):
        """Init strategy."""
        super().__init__(cta_engine, strategy_name, vt_symbol, setting)

        self.bg = BarGenerator(self.on_bar)
        self.am = ArrayManager(100)

    def on_init(self):
        """Callback when strategy is inited."""
        self.write_log("策略初始化")
        self.load_bar(10)

    def on_start(self):
        """Callback when strategy is started."""
        self.write_log("策略启动")

    def on_stop(self):
        """Callback when strategy is stopped."""
        self.write_log("策略停止")

    def on_tick(self, tick: TickData):
        """Callback of new tick data update."""
        self.bg.update_tick(tick)

    def on_bar(self, bar: BarData):
        """Callback of new bar data update."""
        self.cancel_all()

        am = self.am
        am.update_bar(bar)
        if not am.inited:
            return

        # 窗口取"之前"的K线（不含当前根），避免把当前bar自己算进突破
        self.highest_price = am.high[-self.entry_window - 1:-1].max()
        self.lowest_price = am.low[-self.exit_window - 1:-1].max()

        if self.pos == 0:
            if bar.close_price > self.highest_price:
                self.buy(bar.close_price, self.trading_size)
        else:
            if bar.close_price < self.lowest_price:
                self.sell(bar.close_price, self.trading_size)

        self.put_event()