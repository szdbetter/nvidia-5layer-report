import sys
import datetime
from pathlib import Path
import requests
sys.path.append(str(Path(__file__).resolve().parent))
from poly_runtime import make_client, get_orderbook_snapshot, get_wallet_state, calc_pnl, WEIGHTED_ENTRY, WALLET_ADDRESS, MARKET_TITLE, load_secret


def search_news(query):
    brave_key = load_secret("BRAVE_API_KEY")
    if not brave_key:
        return []

    url = "https://api.search.brave.com/res/v1/news/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": brave_key}
    r = requests.get(url, headers=headers, params={"q": query, "count": 2, "freshness": "pw"})
    if r.status_code == 200:
        return r.json().get('results', [])
    return []


def run_engine():
    print("==================================================")
    print(f"📡 靖安科技逻辑：美伊冲突统一监控引擎 (Price + OSINT)")
    print(f"🕒 时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("==================================================\n")

    print("[1] OSINT 信号计算 (靖安模型)")
    news1 = search_news("KC-135 OR B-2A OR RC-135 Middle East deployment")
    news2 = search_news("CVN-72 OR USS Abraham Lincoln OR Carrier Strike Group Middle East")
    news3 = search_news("Iran air defense OR Patriot OR THAAD Middle East")

    score = 25
    if news1:
        score += 10
    if news2:
        score += 5
    if news3:
        score += 5
    print(f"  - 空袭/冲突爆发综合概率: {score}%\n")

    print("[2] Polymarket 盘口监控")
    current_price = 0
    try:
        client = make_client()
        snap = get_orderbook_snapshot(client)
        wallet = get_wallet_state()
        pnl = calc_pnl(snap['mid'], wallet['no_balance'], WEIGHTED_ENTRY)
        current_price = snap['mid']
        print(f"  - 市场: {MARKET_TITLE}")
        print(f"  - Polygon 地址: {WALLET_ADDRESS}")
        print(f"  - NO Last: ${snap['last']:.3f} | Bid: ${snap['best_bid']:.3f} | Ask: ${snap['best_ask']:.3f} | Mid: ${snap['mid']:.3f}")
        print(f"  - 持仓: {wallet['no_balance']} NO | 加权成本: ${WEIGHTED_ENTRY:.4f} | 未实现盈亏: ${pnl['pnl']:.4f} ({pnl['roi']:.2f}%)")
        print("  - OSINT 来源: Brave News 检索 + 靖安六维简化评分（战略空运/航母动态/防空信号）")
    except Exception as e:
        print(f"  - 获取价格失败: {type(e).__name__}: {e}")
        raise

    print("\n[3] 统一风控决策 (Unified Decision)")
    if current_price >= 0.85:
        print("  🚨 动作触发: 达到止盈线 ($0.85)! 建议立刻卖出 50% 仓位!")
    elif current_price <= 0.40:
        print("  🚨 动作触发: 跌破止损线 ($0.40)! 建议清仓!")
    elif score >= 60 and current_price < 0.85:
        print(f"  🚨 动作触发: OSINT 概率飙升至 {score}%，但盘面尚未反应。建议加仓!")
    else:
        print("  🟢 综合评判: 盘口与基本面静默，系统持续蛰伏中。")
        print("TEST_PULSE_OK")


if __name__ == "__main__":
    run_engine()
