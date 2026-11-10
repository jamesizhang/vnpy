"""
Launch VeighNa Trader with FUTU (simulated trading), CTP, CTA strategy,
backtesting, and data manager.
"""

from vnpy.event import EventEngine

from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp

# ---- Gateways: keep enabled ones installed, commented ones optional ----
from vnpy_ctp import CtpGateway
from vnpy_futu import FutuGateway
# from vnpy_ib import IbGateway                      # pip install vnpy_ib
# from vnpy_longport import LongportGateway          # no official package yet

# ---- Applications ----
from vnpy_ctastrategy import CtaStrategyApp
from vnpy_ctabacktester import CtaBacktesterApp
from vnpy_datamanager import DataManagerApp


def main():
    """Create the main window with CTP, FUTU, CTA strategy, backtester and data manager."""
    qapp = create_qapp()

    event_engine = EventEngine()
    main_engine = MainEngine(event_engine)

    main_engine.add_gateway(CtpGateway)
    main_engine.add_gateway(FutuGateway)
    # main_engine.add_gateway(IbGateway)
    # main_engine.add_gateway(LongportGateway)

    main_engine.add_app(CtaStrategyApp)
    main_engine.add_app(CtaBacktesterApp)
    main_engine.add_app(DataManagerApp)

    main_window = MainWindow(main_engine, event_engine)
    main_window.showMaximized()

    qapp.exec()


if __name__ == "__main__":
    main()
