# 浩泉-每日智能复盘

A股市场多维度深度分析系统。按时间维度自动生成4类报告，并自动推送到 QQ Bot 和 GitHub Pages 网站。

## 报告类型

| 报告 | 时间 | 适用日 |
|------|------|--------|
| 早盘扫描 | 8:00 | 开盘日 |
| 午盘扫描 | 11:40 | 开盘日 |
| 深度复盘 | 23:00 | 开盘日 |
| 周度盘前 | 23:00 | 开盘前夜(周日/节前) |

## 目录结构

```
浩泉-每日智能复盘/
├── SKILL.md          # 技能定义（完整报告模板+数据获取清单+规则）
├── README.md         # 本文件
├── scripts/          # 辅助脚本
│   └── parse_onechart.py    # onechart.top 加权评分数据解析
├── data/             # 数据文件（预留）
├── output/           # 输出文件
│   └── reports-viewer.html  # GitHub Pages 报告查看器源码
└── templates/        # 报告模板（预留）
```

## 依赖

- **浩泉-报告排版引擎** — Markdown → HTML 转换（md2html.py + report.css）
- **tdx-board-radar** — 板块资金雷达数据
- **通达信数据工具** — tdx_quotes / tdx_kline / tdx_screener / tdx_api_data
- **问达资讯工具** — wenda_news_query / wenda_notice_query / wenda_report_query
- **板块资金雷达/sync_reports.py** — 报告同步到 GitHub Pages

## 输出位置

- **本地**: `分析报告汇总/YYYY-MM-DD/`
- **网站**: https://bluemangogogogo.github.io/TOP/reports.html
- **QQ Bot**: 每次生成后自动推送摘要

## 部署说明

1. 确保通达信 TdxQuant 已登录且数据就绪
2. 确保 `D:\库\Desktop\TdxClaw金融龙虾\` 目录结构完整
3. 配置 3 个 Cron 定时任务（参见 SKILL.md 末尾）
4. 确保 GitHub Pages 仓库已配置（BlueMangogogogo/TOP）

## 免责声明

本系统由 TdxClaw AI 自动生成，仅供参考研究，不构成任何投资建议。
