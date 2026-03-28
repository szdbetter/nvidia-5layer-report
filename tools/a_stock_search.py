#!/usr/bin/env python3
"""
A股实时行情查询工具
数据源：新浪财经（VPS境外可达）
用法：python3 a_stock_search.py <股票代码或名称> [股票代码2 ...]
示例：python3 a_stock_search.py 600519 贵州茅台 sh000001
"""

import sys, re, json, urllib.request

def query_sina(codes: list) -> list:
    """查询新浪财经实时行情"""
    normalized = []
    for c in codes:
        c = c.strip()
        if re.match(r'^\d{6}$', c):
            prefix = 'sh' if c.startswith('6') else 'sz'
            normalized.append(prefix + c)
        elif c.startswith(('sh', 'sz', 'SH', 'SZ')):
            normalized.append(c.lower())
        else:
            normalized.append(c)
    
    url = f"http://hq.sinajs.cn/list={','.join(normalized)}"
    req = urllib.request.Request(url, headers={
        'Referer': 'http://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0'
    })
    with urllib.request.urlopen(req, timeout=10) as r:
        raw = r.read().decode('gbk')
    
    results = []
    for line in raw.strip().split('\n'):
        m = re.match(r'var hq_str_(\w+)="(.*)"', line)
        if not m:
            continue
        code, data = m.group(1), m.group(2)
        if not data:
            continue
        fields = data.split(',')
        if len(fields) < 10:
            continue
        
        name = fields[0]
        if not name:
            continue
            
        # 指数字段与股票字段不同
        if 'idx' in code or len(fields) < 32:
            results.append({
                'code': code,
                'name': name,
                'price': fields[3],
                'change_pct': f"{(float(fields[3])-float(fields[2]))/float(fields[2])*100:.2f}%" if float(fields[2]) > 0 else 'N/A',
                'type': '指数'
            })
        else:
            open_p, close_p, curr_p = float(fields[1]), float(fields[2]), float(fields[3])
            high_p, low_p = float(fields[4]), float(fields[5])
            volume = int(fields[8]) if fields[8] else 0
            amount = float(fields[9]) if fields[9] else 0
            change_pct = (curr_p - close_p) / close_p * 100 if close_p > 0 else 0
            results.append({
                'code': code,
                'name': name,
                'price': curr_p,
                'change_pct': f"{change_pct:+.2f}%",
                'high': high_p,
                'low': low_p,
                'volume_万手': round(volume / 10000 / 100, 2),
                'amount_亿': round(amount / 100000000, 2),
                'date': fields[30] if len(fields) > 30 else '',
                'time': fields[31] if len(fields) > 31 else '',
                'type': '股票'
            })
    return results


def search_by_name(name: str) -> str:
    """通过名称搜索股票代码（使用新浪搜索）"""
    url = f"http://suggest3.sinajs.cn/suggest/type=11,12&key={urllib.parse.quote(name)}&name=suggestdata"
    req = urllib.request.Request(url, headers={'Referer': 'http://finance.sina.com.cn', 'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode('gbk')
        # 解析返回格式
        m = re.search(r'"([^"]+)"', raw)
        if m:
            items = m.group(1).split(';')
            for item in items[:3]:
                parts = item.split(',')
                if len(parts) >= 4:
                    return parts[3]  # 返回代码
    except:
        pass
    return name


import urllib.parse

def main():
    if len(sys.argv) < 2:
        print("用法: python3 a_stock_search.py <股票代码/名称> [...]")
        sys.exit(1)
    
    queries = sys.argv[1:]
    codes = []
    for q in queries:
        if re.match(r'^\d{6}$', q) or re.match(r'^(sh|sz|SH|SZ)\d{6}$', q):
            codes.append(q)
        elif q.startswith('sh') or q.startswith('sz'):
            codes.append(q)
        else:
            # 名称搜索
            found = search_by_name(q)
            codes.append(found)
    
    results = query_sina(codes)
    
    if not results:
        print("未找到相关股票数据")
        sys.exit(1)
    
    for r in results:
        print(f"\n{'='*40}")
        print(f"【{r['name']}】{r['code']}")
        print(f"最新价: {r['price']}  涨跌幅: {r['change_pct']}")
        if r['type'] == '股票':
            print(f"最高: {r['high']}  最低: {r['low']}")
            print(f"成交量: {r['volume_万手']}万手  成交额: {r['amount_亿']}亿")
            print(f"时间: {r.get('date','')} {r.get('time','')}")


if __name__ == '__main__':
    main()
