#!/usr/bin/env bash
cd "$(dirname "$0")"
source .venv/bin/activate
echo "===== 启动目录: $(pwd) ====="
ls -la strategies/
LANG=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8 python examples/veighna_trader/run_futu.py
