#!/usr/bin/env python3
"""Download and parse onechart.top radar_data_latest.js"""
import urllib.request, json, re, os, sys

sys.stdout.reconfigure(encoding='utf-8')

url = 'https://onechart.top/radar_data_latest.js'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
raw = urllib.request.urlopen(req, timeout=30).read().decode('utf-8')

# Find where the main flow data starts (after CONSTITUENT_MAP)
# The data is in JS format: variable = JSON;
# Let's find the data array assignment

# Extract LATEST_DATE
latest = re.findall(r"LATEST_DATE\s*=\s*'([^']+)'", raw)
print(f"数据日期: {latest[0] if latest else 'N/A'}")

# Find flow data arrays - they're assigned to global variables
# Look for HTML_TABLE_DATA or similar
patterns = [
    (r'const\s+FLOW_DATA\s*=\s*(\[[\s\S]*?\]);', 'FLOW_DATA'),
    (r'const\s+SECTOR_DATA\s*=\s*(\[[\s\S]*?\]);', 'SECTOR_DATA'),
    (r'const\s+RADAR_DATA\s*=\s*(\[[\s\S]*?\]);', 'RADAR_DATA'),
    (r'const\s+TABLE_DATA\s*=\s*(\[[\s\S]*?\]);', 'TABLE_DATA'),
]

found_data = None
for pattern, name in patterns:
    m = re.search(pattern, raw)
    if m:
        try:
            data = json.loads(m.group(1))
            print(f"找到 {name}: {len(data)} 条记录")
            found_data = data
            break
        except:
            print(f"{name} 解析失败")

if not found_data:
    # Try to find any JSON array that contains the field names we need
    print("\n尝试定位资金流数据数组...")
    # Look for arrays containing index_name field
    idx = raw.find('"index_name"')
    if idx > 0:
        # Find the enclosing array
        start = raw.rfind('[', 0, idx)
        bracket_count = 0
        for i in range(start, len(raw)):
            if raw[i] == '[':
                bracket_count += 1
            elif raw[i] == ']':
                bracket_count -= 1
                if bracket_count == 0:
                    end = i + 1
                    break
        try:
            found_data = json.loads(raw[start:end])
            print(f"定位到数据数组: {len(found_data)} 条记录")
        except Exception as e:
            print(f"解析失败: {e}")
            # Try to extract one item to see the structure
            print("数据样本(前500字符):", raw[start:start+500])

if found_data:
    # Extract relevant fields for our analysis
    print(f"\n=== 资金进攻榜 TOP 10 (按加权评分) ===")
    sorted_data = sorted(found_data, key=lambda x: x.get('Swing_Score', 0) or x.get('Ratio_Score', 0) or 0, reverse=True)
    
    for i, item in enumerate(sorted_data[:15]):
        name = item.get('index_name', 'N/A')
        if isinstance(name, str):
            name = name.replace('板块', '')
        pct = (item.get('pct_change', 0) or 0)
        swing_val = (item.get('Swing_Ratio_Val', 0) or 0) * 100
        ratio_val = (item.get('Ratio_Raw_Pct', 0) or 0) * 100
        amount_bn = (item.get('Amount_Raw_BN', 0) or 0)
        score = item.get('Swing_Score', 0) or item.get('Ratio_Score', 0) or 0
        swing_rank = item.get('Swing_RankPos', '-')
        ratio_rank = item.get('Ratio_RankPos', '-')
        amount_rank = item.get('Amount_RankPos', '-')
        top30d = item.get('Swing_Top30d', 0)
        
        print(f"{i+1}. {name} | 涨跌幅:{pct:+.2f}% | 波段流入率:{swing_val:.2f}% | 单日流入率:{ratio_val:.2f}% | 单日净额:{amount_bn:.1f}亿 | 评分:{score:.1f} | 30日在榜:{top30d}天")

    # Also find bottom 10 (资金重灾区)
    print(f"\n=== 资金重灾区 BOTTOM 10 ===")
    sorted_bottom = sorted(found_data, key=lambda x: x.get('Swing_Score', 0) or 0)
    for i, item in enumerate(sorted_bottom[:10]):
        name = item.get('index_name', 'N/A')
        if isinstance(name, str):
            name = name.replace('板块', '')
        pct = (item.get('pct_change', 0) or 0)
        amount_bn = (item.get('Amount_Raw_BN', 0) or 0)
        score = item.get('Swing_Score', 0) or 0
        print(f"{i+1}. {name} | 涨跌幅:{pct:+.2f}% | 净额:{amount_bn:.1f}亿 | 评分:{score:.1f}")

else:
    print("\n未能定位到资金流数据，显示文件结构:")
    # Show all const/variable declarations
    decls = re.findall(r'(?:const|let|var)\s+(\w+)\s*=', raw[:50000])
    print("变量声明:", decls[:20])
    # Search for last array in the file
    print(f"\n文件总大小: {len(raw)} 字符")
    # Show last 1000 chars for clues
    print("文件末尾:", raw[-1000:])