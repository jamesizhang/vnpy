"""
Launch VeighNa Trader with FUTU (simulated trading), CTP, CTA strategy,
backtesting, and data manager.
"""

import os
from pathlib import Path

from vnpy.event import EventEngine

from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

from vnpy_ctp import CtpGateway
from vnpy_futu import FutuGateway

from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_datamanager import DataManagerApp

from vnpy_ctastrategy.engine import CtaEngine

REPO_ROOT = Path(__file__).resolve().parents[2]

# 铁桶方案：无论谁在中间改了进程 cwd，加载策略的瞬间都强制切回仓库根
_orig_load = CtaEngine.load_strategy_class

def load_with_fixed_cwd(self):
    old = Path.cwd()
    try:
        os.chdir(REPO_ROOT)
        _orig_load(self)
    finally:
        os.chdir(old)

CtaEngine.load_strategy_class = load_with_fixed_cwd


def main():
    """Create the main window with CTP, FUTU, CTA strategy, backtester and data manager."""
    qapp = create_qapp()

    os.chdir(REPO_ROOT)
    print("PYTHON CWD:", Path.cwd())

    event_engine = EventEngine()

    print("cwd before MainEngine:", Path.cwd())
    main_engine = MainEngine(event_engine)
    print("cwd after MainEngine:", Path.cwd())

    main_engine.add_gateway(CtpGateway)
    print("cwd after CtpGateway:", Path.cwd())
    main_engine.add_gateway(FutuGateway)
    print("cwd after FutuGateway:", Path.cwd())

    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(DataManagerApp)
    print("cwd after apps:", Path.cwd())

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
