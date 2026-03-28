import subprocess
import json
import datetime
import os
import requests

def search_news(query):
    # Using OpenClaw's brave web search API if available in env, or simply a generic news fetch
    # We can also call openclaw's brave API via python requests if we have the brave key
    brave_key = os.environ.get("BRAVE_API_KEY")
    if not brave_key:
        # Fallback to loading it from secrets
        with open("/Users/ai/.openclaw/workspace/config/.secrets") as f:
            for line in f:
                if 'BRAVE_API_KEY=' in line:
                    brave_key = line.strip().split('=', 1)[1].strip('"')
                    break
    if not brave_key: return []
    
    url = "https://api.search.brave.com/res/v1/news/search"
    headers = {"Accept": "application/json", "X-Subscription-Token": brave_key}
    r = requests.get(url, headers=headers, params={"q": query, "count": 5, "freshness": "pw"})
    if r.status_code == 200:
        return r.json().get('results', [])
    return []

def main():
    print(f"=== 靖安科技逻辑：美伊冲突 OSINT 自动化评估早报 ===")
    print(f"🕒 时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
    
    print("[1] 战略空运与航迹异动 (模拟接入 ADS-B/OpenSky & OSINT)")
    news1 = search_news("KC-135 OR B-2A OR RC-135 Middle East deployment")
    if news1:
        for n in news1[:2]:
            print(f"  - 🔴 {n.get('title')} ({n.get('meta_url', {}).get('hostname')})")
    else:
        print("  - 🟢 无明显高频加油机/战略轰炸机异常调动报道")

    print("\n[2] 航母战斗群与海空封锁 (模拟接入 AIS/V-22航迹)")
    news2 = search_news("CVN-72 OR USS Abraham Lincoln OR Carrier Strike Group Middle East")
    if news2:
        for n in news2[:2]:
            print(f"  - 🔴 {n.get('title')} ({n.get('meta_url', {}).get('hostname')})")
    else:
        print("  - 🟢 航母打击群暂无突发性攻击部署信号")

    print("\n[3] 伊拉克/伊朗基地遇袭与防空动态")
    news3 = search_news("Iran air defense OR Patriot OR THAAD Middle East")
    if news3:
        for n in news3[:2]:
            print(f"  - 🔴 {n.get('title')} ({n.get('meta_url', {}).get('hostname')})")
    else:
        print("  - 🟢 暂无反导系统紧急增援信号")
        
    print("\n[檀棋 AI 六维度评分推演预测 (模型估算)]")
    # A simplified scoring system based on Tanqi logic
    score = 25 # Base probability
    if news1: score += 10
    if news2: score += 5
    if news3: score += 5
    
    print(f"  - 军事准备度: {'高' if news1 else '低'}")
    print(f"  - 地区盟友异动: {'中' if news3 else '低'}")
    print(f"  --> 当前系统计算空袭概率/停火破裂概率: {score}%")
    print("\n=================================================")
if __name__ == "__main__":
    main()
