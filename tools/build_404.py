"""404 page."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import site_header, footer, OUT
page = f"""<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex"><title>ページが見つかりません｜YASUMIBI</title>
<link rel="stylesheet" href="/assets/site.css"><link rel="icon" href="/assets/img/favicon-48.png" type="image/png"></head>
<body class="nf">
{site_header("/")}
<main class="gin" style="padding:48px 16px 64px;max-width:640px">
  <h1 style="font-size:22px;margin:0">ページが見つかりません</h1>
  <p style="font-size:14px;line-height:1.8;color:var(--muted)">URLが変わったか、ページが削除された可能性があります。トップページから、宿と神日を探してください。</p>
  <p><a href="/" style="font-weight:700">トップページへ →</a></p>
</main>
{footer("/")}
</body></html>
"""
open(f"{OUT}/404.html", "w", encoding="utf-8").write(page)
print("404 built")
