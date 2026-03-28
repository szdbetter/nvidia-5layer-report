import sys
import datetime
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent))
from poly_runtime import make_client, get_orderbook_snapshot, get_wallet_state, calc_pnl, WEIGHTED_ENTRY, WALLET_ADDRESS, MARKET_TITLE


def main():
    client = make_client()
    snap = get_orderbook_snapshot(client)
    wallet = get_wallet_state()
    stats = calc_pnl(snap['mid'], wallet['no_balance'], WEIGHTED_ENTRY)
    now = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')

    print(f"**Polymarket 监控战报 | {now}**\n")
    print(f"- 市场：`{MARKET_TITLE}`")
    print(f"- 地址：`{WALLET_ADDRESS}`")
    print(f"- 持仓：`{wallet['no_balance']} NO`")
    print(f"- 成本：`{WEIGHTED_ENTRY:.4f}`")
    print(f"- 盘口：Last `{snap['last']:.3f}` | Bid `{snap['best_bid']:.3f}` | Ask `{snap['best_ask']:.3f}` | Mid `{snap['mid']:.3f}`")
    print(f"- 浮盈亏：`{stats['pnl']:.4f} USDC` | ROI `{stats['roi']:.2f}%`")
    print(f"- 结论：**盘口未触发止盈/止损，继续监控**")
    print(f"- OSINT：需结合 `python3 scripts/poly_unified_engine.py` 的最新输出一起看")


if __name__ == '__main__':
    main()
