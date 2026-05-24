# -*- coding: utf-8 -*-
"""
重点关注报告渲染器 v3.2 · 总览增强 + 模块分区
位置：skills/focus-tracker/scripts/generate_report.py
"""

import json, os, argparse
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, HRFlowable)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# ======================== 字体 ========================
_FD = r"C:\Windows\Fonts"
try:
    pdfmetrics.registerFont(TTFont('CN',  f'{_FD}\\msyh.ttc',  subfontIndex=0))
    pdfmetrics.registerFont(TTFont('CNB', f'{_FD}\\msyhbd.ttc', subfontIndex=0))
    F, FB = 'CN', 'CNB'
except:
    F, FB = 'Helvetica', 'Helvetica-Bold'

# ======================== 配色 ========================
NAVY   = HexColor('#1a1a2e')
RED    = HexColor('#c0392b')
GREEN  = HexColor('#27ae60')
ORANGE = HexColor('#e67e22')
DGREY  = HexColor('#555555')
LGREY  = HexColor('#999999')
XLGREY = HexColor('#bbbbbb')
BORDER = HexColor('#dcdde1')
WHITE  = HexColor('#ffffff')

BG_MAIN  = HexColor('#eef2f7')   # 趋势/驱动/原因 模块
BG_WARN  = HexColor('#fff8f0')   # 操作/风险 模块
BG_CARD  = HexColor('#f7f8fa')   # 指标/简报 模块
BG_ROW   = HexColor('#fafbfc')   # 表格交替行

# ======================== 样式 ========================
_st = getSampleStyleSheet()

def _ps(name, **kw):
    return ParagraphStyle(name, fontName=kw.pop('font', F), fontSize=kw.pop('size', 9),
                          leading=kw.pop('leading', 14), **kw)

S = {
    'title': _ps('t',  font=FB, size=16, leading=22, textColor=NAVY, spaceAfter=2),
    'sub':   _ps('s',  size=8, leading=11, textColor=LGREY, spaceAfter=6),
    'h1':    _ps('h1', font=FB, size=12, leading=16, textColor=NAVY, spaceBefore=10, spaceAfter=4),
    'h2':    _ps('h2', font=FB, size=9, leading=12, textColor=NAVY, spaceBefore=6, spaceAfter=2),
    'body':  _ps('b',  size=8.5, leading=14, spaceAfter=1),
    'small': _ps('sm', size=7.5, leading=11, textColor=LGREY),
    'th':    _ps('th', font=FB, size=7, leading=10, textColor=WHITE, alignment=TA_CENTER),
    'td':    _ps('td', size=7.5, leading=10, alignment=TA_CENTER),
    'tdl':   _ps('tdl',size=7.5, leading=10),
    'up':    _ps('up', size=7.5, leading=10, textColor=RED, alignment=TA_CENTER),
    'down':  _ps('dn', size=7.5, leading=10, textColor=GREEN, alignment=TA_CENTER),
    'up_w':  _ps('upw',size=7.5, leading=10, textColor=RED, alignment=TA_CENTER),
    'down_w': _ps('dnw',size=7.5, leading=10, textColor=GREEN, alignment=TA_CENTER),
    'box':   _ps('bx', size=8, leading=13, textColor=DGREY),
    'warn':  _ps('warn',font=FB, size=8, leading=13, textColor=ORANGE),
    'name':  _ps('nm', font=FB, size=11, leading=15, textColor=NAVY),
    'th_n':  _ps('thn',font=FB, size=7, leading=10, textColor=WHITE),            # 总览表头（海军蓝底+白字）
    'card_h':_ps('ch', font=FB, size=7.5, leading=10, textColor=NAVY),          # 指标卡片小标题（灰底+深字）
    'td_w':  _ps('tdw',size=7.5, leading=10, alignment=TA_CENTER),               # nowrap 居中
}

def _pct_cell(v):
    try:
        fv = float(v)
        if fv > 0: return Paragraph(f'+{fv:.2f}%', S['up'])
        elif fv < 0: return Paragraph(f'{fv:.2f}%', S['down'])
        return Paragraph('0.00%', S['td'])
    except: return Paragraph(str(v) if v else '—', S['td'])

def _fmt(v, unit=''):
    """格式化数字"""
    if v is None: return '—'
    try:
        fv = float(v)
        if abs(fv) >= 1:
            return f'{fv:.2f}{unit}'
        elif abs(fv) >= 0.01:
            return f'{fv*100:.0f}万{unit}' if unit else f'{fv:.2f}'
        return f'{fv:.2f}{unit}'
    except: return str(v)

# ======================== 表格工具 ========================
def _tbl(headers, rows, widths):
    hdr = [Paragraph(h, S['th_n'] if len(h)>3 else S['th']) for h in headers]
    data = [hdr]
    for r in rows:
        data.append(r)
    t = Table(data, colWidths=widths, hAlign='LEFT')
    style = [
        ('BACKGROUND', (0,0), (-1,0), NAVY),
        ('TEXTCOLOR', (0,0), (-1,0), WHITE),
        ('GRID', (0,0), (-1,-1), 0.3, BORDER),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]
    for i in range(2, len(data), 2):
        style.append(('BACKGROUND', (0,i), (-1,i), BG_ROW))
    t.setStyle(TableStyle(style))
    return t

def _box_table(rows, bg_color, widths):
    """带背景色的内容框"""
    data = [[Paragraph(r, S['box'])] for r in rows if r]
    if not data: return None
    t = Table(data, colWidths=widths, hAlign='LEFT')
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), bg_color),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LINEBELOW', (0,0), (-1,-2), 0.3, HexColor('#e8e8e8')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    return t

def _divider():
    return HRFlowable(width="100%", thickness=0.5, color=BORDER, spaceBefore=0, spaceAfter=0)

# ======================== MA/MACD/形态计算 ========================
def _ma_sigs(closes):
    n = len(closes)
    if n < 60: return {'sigs': [], 'align': '—'}
    ma5  = sum(closes[-5:])/5
    ma10 = sum(closes[-10:])/10
    ma20 = sum(closes[-20:])/20
    ma60 = sum(closes[-60:])/60
    cur  = closes[-1]

    sigs = []
    if   ma5>ma10>ma20>ma60: align = '多头排列'
    elif ma5<ma10<ma20<ma60: align = '空头排列'
    else:                     align = '均线纠缠'

    if cur > ma5:  sigs.append('站上MA5')
    else:          sigs.append('跌破MA5')
    if cur > ma20: sigs.append('站上MA20')
    else:          sigs.append('跌破MA20')
    if cur > ma60: sigs.append('站上MA60')
    else:          sigs.append('跌破MA60')

    if n >= 7:
        pm5 = sum(closes[-6:-1])/5
        pm10 = sum(closes[-11:-1])/10
        if pm5 <= pm10 and ma5 > ma10:   sigs.append('MA5上穿MA10')
        elif pm5 >= pm10 and ma5 < ma10: sigs.append('MA5下破MA10')

    return {'sigs': sigs, 'align': align}

def _macd_sig(closes):
    n = len(closes)
    if n < 26: return {'stat': '—', 'desc': '—'}
    e12 = e26 = closes[0]
    for i in range(1, n):
        e12 = closes[i]*2/13 + e12*11/13
        e26 = closes[i]*2/27 + e26*25/27
    dif = e12 - e26
    sigs = ['零轴上方' if dif>0 else '零轴下方']
    if n >= 28:
        o12 = o26 = closes[0]
        for i in range(1, n-2):
            o12 = closes[i]*2/13 + o12*11/13
            o26 = closes[i]*2/27 + o26*25/27
        od = o12 - o26
        if od <= 0 and dif > 0:   sigs.append('金叉')
        elif od >= 0 and dif < 0: sigs.append('死叉')
    return {'stat': '多方' if dif>0 else '空方', 'desc': '|'.join(sigs)}

def _detect_pattern(closes, chg_pct, vol_wan):
    """从日线收盘价序列检测技术形态（仅价格形态，不含量能判断）"""
    n = len(closes)
    if n < 6: return '—'

    prev_chg = (closes[-1]/closes[-2]-1)*100 if n>=2 else 0
    two_ago_chg = (closes[-2]/closes[-3]-1)*100 if n>=3 else 0
    three_ago_chg = (closes[-3]/closes[-4]-1)*100 if n>=4 else 0

    # 一字涨停
    if chg_pct > 9.5:
        return '一字涨停'

    # 反包：今日涨且昨日跌
    if chg_pct > 0 and prev_chg < -1:
        return '反包'

    # 跳空
    if chg_pct > 0 and two_ago_chg < -2:
        return '跳空反弹'

    # 连阳
    if chg_pct > 0 and prev_chg > 0 and two_ago_chg > 0:
        return '连阳'

    # 连阴
    if chg_pct < 0 and prev_chg < 0 and two_ago_chg < 0:
        return '连阴'

    if chg_pct > 5:
        return '强势上涨'
    if chg_pct > 2:
        return '上涨'
    if chg_pct < -5:
        return '大幅下跌'
    if chg_pct < -2:
        return '下跌'
    return '震荡'

# ======================== 个股渲染 ========================
def _stock(stk):
    el = []
    n, c = stk['name'], stk['code']
    q   = stk.get('quote', {})
    sg  = stk.get('signals', {})
    jd  = stk.get('ai_judgment', {})
    cls = stk.get('kline_closes', [])

    ms = _ma_sigs(cls)
    mc = _macd_sig(cls)
    chg = q.get('change_pct', 0)
    chg_c = '#c0392b' if chg>0 else ('#27ae60' if chg<0 else '#555')

    # ── 名称栏 ──
    tags = ' · '.join(stk.get('tags', []))
    el.append(Paragraph(
        f'<font face="{FB}" size="12" color="#1a1a2e">{n}</font>'
        f'<font size="9" color="#999">  {c}</font>'
        f'<font size="7.5" color="#bbb">  {tags}</font>'
        f'<font face="{FB}" size="12" color="{chg_c}">    {q.get("latest","—")}</font>'
        f'<font face="{FB}" size="9" color="{chg_c}">  {chg:+.2f}%</font>',
        S['body']))
    el.append(Spacer(1, 4))

    # ══════════ 模块一：指标卡片 ══════════
    cd = [
        [
            Paragraph('<b>均线</b>', S['card_h']),
            Paragraph(f'{ms["align"]}  |  {"、".join(ms["sigs"][:3])}', S['box']),
            Paragraph('<b>MACD</b>', S['card_h']),
            Paragraph(f'{mc["stat"]}主导  |  {mc["desc"]}', S['box']),
        ],
        [
            Paragraph('<b>量能</b>', S['card_h']),
            Paragraph(f'{sg.get("volume","—")}', S['box']),
            Paragraph('<b>资金</b>', S['card_h']),
            Paragraph(f'{sg.get("fund_signal","—")}  ({sg.get("fund_flow","")})', S['box']),
        ],
        [
            Paragraph('<b>支撑</b>', S['card_h']),
            Paragraph(f'{sg.get("support","—")}', S['box']),
            Paragraph('<b>压力</b>', S['card_h']),
            Paragraph(f'{sg.get("resistance","—")}', S['box']),
        ],
    ]
    ct = Table(cd, colWidths=[36, 216, 36, 216], hAlign='LEFT')
    ct.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BG_CARD),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROUNDEDCORNERS', [3,3,3,3]),
    ]))
    el.append(ct)
    el.append(Spacer(1, 5))

    # ══════════ 模块二：趋势+驱动+原因（蓝灰背景） ══════════
    m1_lines = []
    if jd.get('trend_verdict'):
        m1_lines.append(f'<b>趋势：</b>{jd["trend_verdict"]}')
    if jd.get('key_drivers'):
        m1_lines.append(f'<b>驱动：</b>{jd["key_drivers"]}')
    if jd.get('catalyst_reason'):
        m1_lines.append(f'<b>涨跌原因：</b>{jd["catalyst_reason"]}')
    if m1_lines:
        bt = _box_table(m1_lines, BG_MAIN, [504])
        if bt: el.append(bt)
        el.append(Spacer(1, 4))

    # ══════════ 模块三：操作参考+风险（暖色背景） ══════════
    m2_lines = []
    if jd.get('operation_hint'):
        m2_lines.append(
            f'<font face="{FB}" size="8.5" color="#e67e22">操作参考：</font>'
            f'<font size="8.5">{jd["operation_hint"]}</font>')
    if jd.get('risks'):
        m2_lines.append(
            f'<font color="#c0392b"><b>风险预警：</b>{jd["risks"]}</font>')
    if jd.get('tomorrow_watch'):
        m2_lines.append(
            f'<font size="8" color="#888">明日看点：{jd["tomorrow_watch"]}</font>')
    if m2_lines:
        bt = _box_table(m2_lines, BG_WARN, [504])
        if bt: el.append(bt)
        el.append(Spacer(1, 4))

    # ══════════ 模块四：信息简报（浅灰） ══════════
    parts = []
    ab = stk.get('announcements_brief')
    rb = stk.get('reports_brief')
    nb = stk.get('news_brief')
    parts.append(f'公告：{ab if ab else "无"}')
    parts.append(f'研报：{rb if rb else "无"}')
    if nb: parts.append(f'新闻：{nb}')
    info_line = '  │  '.join(parts)
    ib = _box_table([info_line], BG_CARD, [504])
    if ib: el.append(ib)

    # ── 上次判断 ──
    prv = stk.get('prev_judgment')
    if prv:
        el.append(Spacer(1, 2))
        el.append(Paragraph(
            f'<font size="7" color="#ccc">[上期] {str(prv)[:200]}</font>', S['small']))

    return el

# ======================== 板块/题材 ========================
def _sector_theme(item):
    el = []
    n = item['name']
    tp = item.get('type', 'sector')
    lb = '板块' if tp == 'sector' else '方向'
    jd = item.get('ai_judgment', {})
    prv = item.get('prev_judgment')

    el.append(Paragraph(
        f'<font face="{FB}" size="11" color="#1a1a2e">[{lb}] {n}</font>'
        f'<font size="8" color="#999">  {item.get("code","")}</font>',
        S['h1']))

    lines = []
    if jd.get('trend_verdict'): lines.append(f'<b>走势：</b>{jd["trend_verdict"]}')
    if jd.get('news_summary'):  lines.append(f'<b>动态：</b>{jd["news_summary"]}')
    if jd.get('leaders_brief'): lines.append(f'<b>龙头：</b>{jd["leaders_brief"]}')
    if jd.get('judgment'):
        lines.append(f'<font color="#e67e22"><b>判断：</b>{jd["judgment"]}</font>')

    if lines:
        bt = _box_table(lines, BG_MAIN, [504])
        if bt: el.append(bt)

    if prv:
        el.append(Spacer(1, 2))
        el.append(Paragraph(
            f'<font size="7" color="#ccc">[上期] {prv.get("judgment","")[:200]}</font>', S['small']))
    el.append(Spacer(1, 6))
    return el

# ======================== 主入口 ========================
def generate_report(data_path, output_path=None):
    with open(data_path, 'r', encoding='utf-8') as f:
        d = json.load(f)

    rdate  = d.get('report_date', datetime.now().strftime('%Y-%m-%d'))
    stocks  = d.get('stocks', [])
    sectors = d.get('sectors', [])
    themes  = d.get('themes', [])
    total   = len(stocks) + len(sectors) + len(themes)
    mb      = d.get('market_brief', '')

    if not output_path:
        ws = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        od = os.path.join(ws, 'memory', 'focus-daily')
        os.makedirs(od, exist_ok=True)
        output_path = os.path.join(od, f'{rdate}.pdf')

    doc = SimpleDocTemplate(output_path, pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm, topMargin=16*mm, bottomMargin=14*mm)
    story = []

    # ══════════ 封面 ══════════
    now_str = datetime.now().strftime('%H:%M')
    story.append(Paragraph('重点关注 · 每日跟踪', S['title']))
    story.append(Paragraph(
        f'{rdate}  |  {now_str}  |  个股{len(stocks)} · 板块{len(sectors)} · 方向{len(themes)}',
        S['sub']))
    if mb:
        story.append(Paragraph(f'<font size="8" color="#555">{mb}</font>', S['body']))
    story.append(Spacer(1, 4))
    story.append(_divider())
    story.append(Spacer(1, 6))

    # ══════════ 总览表（满宽） ══════════
    if stocks:
        story.append(Paragraph('总览', S['h2']))

        # 可用宽度 516pt：名称48 | 涨跌34 | 五日36 | 均线48 | MACD42 | 形态48 | 资金88 | 操作参考172
        ov_h = ['名称', '涨跌', '五日', '均线', 'MACD', '技术形态', '资金', '操作参考']
        ov_r = []
        for s in stocks:
            q = s.get('quote', {})
            sg = s.get('signals', {})
            jd = s.get('ai_judgment', {})
            cls = s.get('kline_closes', [])
            ms = _ma_sigs(cls)
            mc = _macd_sig(cls)
            chg = q.get('change_pct', 0)
            vol_wan = q.get('volume_wan', 0)

            # 五日涨幅
            if len(cls) >= 5:
                chg5 = (cls[-1]/cls[-5] - 1)*100
            else:
                chg5 = 0

            # 技术形态
            pattern = _detect_pattern(cls, chg, vol_wan)

            # 资金
            fund_sig = sg.get('fund_signal','—')
            fund_flow = sg.get('fund_flow','')
            fund_display = f'{fund_sig}\n{fund_flow}' if fund_flow else fund_sig

            # 五日涨幅（nowrap 防止百分号换行）
            if chg5 > 0:   chg5_cell = Paragraph(f'+{chg5:.1f}%', S['up_w'])
            elif chg5 < 0: chg5_cell = Paragraph(f'{chg5:.1f}%', S['down_w'])
            else:          chg5_cell = Paragraph('0.00%', S['td_w'])

            ov_r.append([
                Paragraph(s['name'], S['td']),
                _pct_cell(chg),
                chg5_cell,
                Paragraph(ms['align'], S['td']),
                Paragraph(f'{mc["stat"]}\n{mc["desc"]}', S['td']),
                Paragraph(sg.get('pattern') or _detect_pattern(cls, chg, vol_wan), S['td']),
                Paragraph(fund_display, S['td']),
                Paragraph((jd.get('operation_hint','—') or '—')[:24], S['tdl']),
            ])

        ov_tbl = _tbl(ov_h, ov_r,
            [48, 34, 36, 48, 42, 48, 88, 172])
        story.append(ov_tbl)
        story.append(Spacer(1, 6))

    # ══════════ 板块/题材总览 ══════════
    if sectors or themes:
        story.append(Paragraph('板块/方向总览', S['h2']))
        ov_h_sec = ['名称', '涨跌', '五日', '均线', 'MACD', '技术形态']
        ov_r_sec = []
        for item in sectors + themes:
            q = item.get('quote', {})
            cls = item.get('kline_closes', [])
            jd = item.get('ai_judgment', {})
            chg = q.get('change_pct', 0)
            tp = item.get('type', 'sector')

            if len(cls) >= 60:
                ms = _ma_sigs(cls)
                mc = _macd_sig(cls)
                if len(cls) >= 5:
                    chg5 = (cls[-1]/cls[-5] - 1)*100
                else:
                    chg5 = 0
                pattern = _detect_pattern(cls, chg, q.get('volume_wan', 0))
                p5 = f'+{chg5:.1f}%' if chg5>0 else f'{chg5:.1f}%' if chg5<0 else '0.0%'
                ov_r_sec.append([
                    Paragraph(f'[{tp=="sector" and "板块" or "方向"}] {item["name"]}', S['tdl']),
                    _pct_cell(chg),
                    Paragraph(p5, S['td']),
                    Paragraph(ms['align'], S['td']),
                    Paragraph(mc['stat'], S['td']),
                    Paragraph(sg.get('pattern', pattern) if (sg := item.get('signals')) else pattern, S['td']),
                ])
            else:
                # 无K线数据的抽象主题：用2-3句话总结
                brief = jd.get('news_summary', '') or jd.get('trend_verdict', '') or '—'
                ov_r_sec.append([
                    Paragraph(f'[{tp=="sector" and "板块" or "方向"}] {item["name"]}', S['tdl']),
                    _pct_cell(chg),
                    Paragraph('—', S['td']),
                    Paragraph('—', S['td']),
                    Paragraph('—', S['td']),
                    Paragraph('—', S['td']),
                ])
        if ov_r_sec:
            story.append(_tbl(ov_h_sec, ov_r_sec, [154, 42, 44, 56, 52, 102]))
            story.append(Spacer(1, 10))

    # ══════════ 个股详情 ══════════
    for i, s in enumerate(stocks):
        if i > 0:
            story.append(Spacer(1, 4))
            story.append(_divider())
            story.append(Spacer(1, 6))
        story.extend(_stock(s))

    # ══════════ 板块/题材 ══════════
    if sectors or themes:
        story.append(Spacer(1, 6))
        story.append(_divider())
        story.append(Spacer(1, 4))
        story.append(Paragraph('板块 / 方向', S['h1']))
        for sec in sectors: story.extend(_sector_theme(sec))
        for th in themes:   story.extend(_sector_theme(th))

    # ══════════ 尾注 ══════════
    story.append(Spacer(1, 14))
    story.append(_divider())
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        '风险提示：AI生成内容基于公开数据，不构成投资建议。市场有风险，投资需谨慎。'
        f'  |  v3.2  |  {now_str}', S['small']))

    doc.build(story)
    kb = os.path.getsize(output_path)/1024
    print(f'OK {output_path} ({kb:.0f}KB)')
    return output_path

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='重点关注报告渲染器 v3.2')
    p.add_argument('data', help='JSON 数据文件')
    p.add_argument('--output', '-o', help='输出 PDF 路径')
    a = p.parse_args()
    generate_report(a.data, a.output)
