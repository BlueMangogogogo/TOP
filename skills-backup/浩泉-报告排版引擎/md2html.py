#!/usr/bin/env python3
"""
md2html.py — Markdown → 排版 HTML
用法: python md2html.py input.md
输出: 分析报告汇总/YYYY-MM-DD/文章标题.html
      文件名从 Markdown 的 # 标题自动提取并做安全处理。
"""
import sys, os, re
from datetime import datetime
from markdown import markdown
from markdown.extensions import tables, fenced_code, codehilite, sane_lists

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(SCRIPT_DIR, "report.css")

def load_css():
    if os.path.exists(CSS_PATH):
        with open(CSS_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return ""

def sanitize_filename(name):
    """把标题变成安全的文件名（保留中文）"""
    # 移除或替换 Windows 文件名非法字符
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    name = re.sub(r'\s+', ' ', name).strip()
    # 限制长度
    if len(name) > 80:
        name = name[:80]
    return name

def get_output_dir():
    """返回输出目录: 分析报告汇总/YYYY-MM-DD/"""
    today = datetime.now().strftime("%Y-%m-%d")
    # Primary: D 盘桌面路径
    base_dirs = [
        r"D:\库\Desktop\TdxClaw金融龙虾",
        os.path.join(os.environ.get("USERPROFILE", ""), "Desktop", "TdxClaw金融龙虾"),
    ]
    for base in base_dirs:
        out_dir = os.path.join(base, "分析报告汇总", today)
        parent = os.path.dirname(out_dir)
        if os.path.isdir(parent) or os.path.isdir(base):
            return out_dir
    # fallback
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR))), "分析报告汇总", today)

def extract_title_and_meta(md_text):
    """从 markdown 提取 h1 作为标题，📅 行作为自定义 meta。"""
    lines = md_text.split("\n")
    title = ""
    date_str = ""
    custom_meta = ""
    content_start = 0

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("# ") and not title:
            title = stripped[2:].strip()
            content_start = i + 1
        elif stripped.startswith("📅") and not custom_meta:
            custom_meta = stripped
            content_start = i + 1
        elif stripped.lower().startswith("date:") or stripped.lower().startswith("日期:"):
            date_str = stripped.split(":", 1)[1].strip()
            if content_start <= i:
                content_start = i + 1
        elif stripped == "" and content_start <= i + 1:
            continue
        elif not title:
            continue
        else:
            break

    if not title:
        for line in lines:
            s = line.strip()
            if s and not s.startswith("date:") and not s.startswith("日期:") and not s.startswith("📅"):
                title = s.lstrip("#").strip()
                break

    if not date_str and not custom_meta:
        date_str = datetime.now().strftime("%Y年%m月%d日 %H:%M")

    body = "\n".join(lines[content_start:]).strip()
    return title, date_str, body, custom_meta

def wrap_html(title, date_str, body_html, css, custom_meta=""):
    if custom_meta:
        meta_html = custom_meta
    else:
        meta_html = f"📅 {date_str}"
    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<style>
{css}
</style>
</head>
<body>

<header>
  <h1>{title}</h1>
  <div class="meta">
    {meta_html}
  </div>
</header>

{body_html}

<footer>
  <p><strong>免责声明</strong>：本报告由 TdxClaw AI 自动生成，仅供参考研究，不构成任何投资建议。投资有风险，决策须谨慎。</p>
  <p>数据来源：通达信 TdxQuant &nbsp;|&nbsp; 生成时间：{date_str}</p>
</footer>

</body>
</html>"""

def convert_md_to_html(md_text, css):
    title, date_str, body_md, custom_meta = extract_title_and_meta(md_text)
    body_html = markdown(
        body_md,
        extensions=["tables", "fenced_code", "codehilite", "sane_lists"],
        output_format="html5"
    )
    body_html = re.sub(r'(<table>)', r'<div class="table-wrapper">\1', body_html)
    body_html = re.sub(r'(</table>)', r'\1</div>', body_html)
    # 替换 blockquote → div（同时替换开闭标签，修复缩进累积 bug）
    body_html = body_html.replace('<blockquote>\n<p>⚠', '<div class="warning">\n<p>⚠')
    body_html = body_html.replace('<blockquote>\n<p>💡', '<div class="highlight">\n<p>💡')
    body_html = body_html.replace('<blockquote>\n<p>📊', '<div class="highlight">\n<p>📊')
    body_html = body_html.replace('</blockquote>', '</div>')
    return title, date_str, wrap_html(title, date_str, body_html, css, custom_meta)

def main():
    if len(sys.argv) < 2:
        print("用法: python md2html.py input.md")
        print("输出自动写入: 分析报告汇总/YYYY-MM-DD/文章标题.html")
        sys.exit(1)

    input_path = sys.argv[1]
    with open(input_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    css = load_css()
    title, date_str, html = convert_md_to_html(md_text, css)

    out_dir = get_output_dir()
    filename = sanitize_filename(title) + ".html"
    output_path = os.path.join(out_dir, filename)

    os.makedirs(out_dir, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"✅ {output_path}")
    print(f"   ({len(html)} chars, {title})")

if __name__ == "__main__":
    main()
