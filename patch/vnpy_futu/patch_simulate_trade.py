"""
Patch vnpy_futu gateway to synthesize trade records from order status.

Futu OpenAPI does not support deal_list_query in the SIMULATE environment,
so the CTA engine never receives trade events and strategy pos stays 0.
This patch makes the gateway fall back to polling order status and
emitting synthesized TradeData from filled orders, restoring the native
trade event flow without touching any strategy code.

Real environment impact: ZERO. The fallback is double-guarded: it only
activates when deal_list_query returns an error AND self.env is
TrdEnv.SIMULATE, and the periodic polling self-registers only after the
first such failure, so in a real account the code path, query frequency
and logs stay identical to the original gateway.

Usage (inside the vnpy venv on the target machine):
    python patch_simulate_trade.py

The script locates the installed vnpy_futu/futu_gateway.py, backs it up
as futu_gateway.py.bak, applies three text replacements, and prints the
result. It is idempotent: running it again reports "already patched".
If vnpy_futu is reinstalled, run this script again.
"""

import importlib.util
from pathlib import Path


def find_gateway_file() -> Path:
    """Locate the installed vnpy_futu/futu_gateway.py."""
    spec = importlib.util.find_spec("vnpy_futu")
    if spec is None or not spec.submodule_search_locations:
        raise SystemExit("vnpy_futu is not installed in the current environment")

    root: Path = Path(spec.submodule_search_locations[0])
    path: Path = root.joinpath("futu_gateway.py")
    if not path.exists():
        raise SystemExit(f"gateway file not found: {path}")
    return path


# Edit 1: track emitted fills and the first-run baseline flag.
EDIT1_OLD = "        self.trades: Set = set()"
EDIT1_NEW = """        self.trades: Set = set()
        self.traded_volume: dict = {}
        self.synced_orders: bool = False"""

# Edit 2: fall back to order status when deal query fails (simulate env).
EDIT2_OLD = '''    def query_trade(self) -> None:
        """查询成交"""
        code, data = self.trade_ctx.deal_list_query("", trd_env=self.env)

        if code:
            self.write_log(f"查询成交失败：{data}")
            return

        self.process_deal(data)
        self.write_log("成交查询成功")
'''
EDIT2_NEW = '''    def query_trade(self) -> None:
        """查询成交"""
        code, data = self.trade_ctx.deal_list_query("", trd_env=self.env)

        if code:
            # 仅模拟盘启用合成成交回报；实盘即使偶发查询失败也保持原生逻辑
            if self.env != TrdEnv.SIMULATE:
                self.write_log(f"查询成交失败：{data}")
                return

            # 模拟盘不支持成交明细，转用委托状态合成，并加入周期轮询
            if self.query_trade not in self.query_funcs:
                self.query_funcs.append(self.query_trade)
            self.query_simulate_trade()
            return

        self.process_deal(data)
        self.write_log("成交查询成功")

    def query_simulate_trade(self) -> None:
        """模拟盘无成交明细，用委托状态合成成交回报"""
        code, data = self.trade_ctx.order_list_query("", trd_env=self.env)

        if code:
            self.write_log(f"查询成交失败：{data}")
            return

        for ix, row in data.iterrows():
            orderid: str = str(row["order_id"])
            dealt_qty: float = float(row["dealt_qty"])
            if not dealt_qty > 0:
                continue

            # 首次运行只记基准，避免重启后把历史成交重复计入
            if not self.synced_orders:
                self.traded_volume[orderid] = dealt_qty
                continue

            volume: float = dealt_qty - self.traded_volume.get(orderid, 0)
            if volume <= 0:
                continue
            self.traded_volume[orderid] = dealt_qty

            direction, offset = DIRECTION_FUTU2VT[row["trd_side"]]
            symbol, exchange = convert_symbol_futu2vt(row["code"])

            trade: TradeData = TradeData(
                symbol=symbol,
                exchange=exchange,
                direction=direction,
                offset=offset,
                tradeid=f"{orderid}-{dealt_qty}",
                orderid=orderid,
                price=float(row["dealt_avg_price"]),
                volume=volume,
                datetime=generate_datetime(row["updated_time"]),
                gateway_name=self.gateway_name,
            )
            self.on_trade(trade)

        self.synced_orders = True
'''

# Edit 3 has been removed: the periodic polling now self-registers
# inside query_trade (see EDIT2_NEW) and only after the first
# deal_list_query failure, so a real account is left untouched.

EDITS: list = [(EDIT1_OLD, EDIT1_NEW), (EDIT2_OLD, EDIT2_NEW)]


def main() -> None:
    """Apply the patch."""
    path: Path = find_gateway_file()
    print(f"Patching: {path}")

    content: str = path.read_text(encoding="utf-8")

    if "query_simulate_trade" in content:
        print("Already patched, nothing to do.")
        return

    backup: Path = path.with_suffix(".py.bak")
    backup.write_text(content, encoding="utf-8")
    print(f"Backup saved: {backup}")

    for index, (old, new) in enumerate(EDITS, start=1):
        count: int = content.count(old)
        if count != 1:
            print(f"Edit {index} failed: pattern found {count} time(s), aborting.")
            return
        content = content.replace(old, new)
        print(f"Edit {index} applied.")

    path.write_text(content, encoding="utf-8")
    print("Patch complete. Restart vnpy to take effect.")


if __name__ == "__main__":
    main()
