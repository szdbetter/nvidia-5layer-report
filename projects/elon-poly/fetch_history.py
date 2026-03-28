#!/usr/bin/env python3
"""
从 xtracker 所有历史 tracking 获取真实周期数据
输出: weekly_history.json — 每个7天周期的实际总推文数 + 每日明细
"""
import requests, json, time, os
from datetime import datetime, timezone

XTRACKER = "https://xtracker.polymarket.com/api"
OUT_FILE = "/root/.openclaw/workspace/projects/elon-poly/weekly_history.json"

def fetch_all_elon_trackings():
    r = requests.get(f"{XTRACKER}/trackings?activeOnly=false", timeout=20)
    data = r.json()["data"]
    elon = []
    for t in data:
        title = t.get("title","").lower()
        if "elon" in title and "tweet" in title:
            start = t.get("startDate","")
            end = t.get("endDate","")
            # 只要7天周期（约±1天容忍）
            if start and end:
                delta = (datetime.fromisoformat(end.replace("Z","+00:00")) - 
                         datetime.fromisoformat(start.replace("Z","+00:00"))).days
                if 6 <= delta <= 8:
                    elon.append(t)
    elon.sort(key=lambda x: x.get("startDate",""))
    return elon

def fetch_tracking_detail(tid):
    r = requests.get(f"{XTRACKER}/trackings/{tid}?includeStats=true", timeout=20)
    return r.json().get("data",{})

def main():
    print("获取所有 Elon 7天周期 tracking...")
    trackings = fetch_all_elon_trackings()
    print(f"  找到 {len(trackings)} 个7天周期")
    
    results = []
    for i, t in enumerate(trackings):
        tid = t["id"]
        title = t["title"]
        start = t.get("startDate","")[:10]
        is_active = t.get("isActive", False)
        
        try:
            detail = fetch_tracking_detail(tid)
            stats = detail.get("stats", {})
            total = stats.get("total", stats.get("cumulative", 0))
            daily = stats.get("daily", [])
            
            # 聚合每日数据（按24小时合并小时数据）
            daily_agg = {}
            for hour in daily:
                date_str = hour.get("date","")[:10]
                cnt = hour.get("count", 0)
                daily_agg[date_str] = daily_agg.get(date_str, 0) + cnt
            
            entry = {
                "id": tid,
                "title": title,
                "start": start,
                "end": t.get("endDate","")[:10],
                "total": total,
                "is_active": is_active,
                "daily": daily_agg,
                "pace": stats.get("pace", 0),
                "days_elapsed": stats.get("daysElapsed", 7),
            }
            results.append(entry)
            status = "🟡" if is_active else "✓"
            print(f"  {status} [{i+1:2d}/{len(trackings)}] {start} total={total} daily_days={len(daily_agg)}")
        except Exception as e:
            print(f"  ✗ [{i+1}] {title[:40]}: {e}")
        
        time.sleep(0.2)  # 限速
    
    with open(OUT_FILE, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ 写入 {len(results)} 条记录 → {OUT_FILE}")
    
    # 打印摘要统计
    completed = [r for r in results if not r["is_active"] and r["total"] > 0]
    if completed:
        totals = [r["total"] for r in completed]
        print(f"\n📊 已完成周期统计 ({len(completed)} 个):")
        print(f"  均值: {sum(totals)/len(totals):.0f}")
        print(f"  最小: {min(totals)}")
        print(f"  最大: {max(totals)}")
        print(f"  范围覆盖的档位: {(min(totals)//20)*20} — {(max(totals)//20)*20}")

if __name__ == "__main__":
    main()
