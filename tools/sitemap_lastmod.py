"""サイトマップの lastmod を「そのページの中身が実際に変わった日」にする（2026/11/17）。

build_site.py は全ページを今日の日付で書く。公開の最後にこれを動かして、
前回公開したページ（サイトのリポジトリの HEAD）と中身を比べ、変わっていないページは前回の lastmod に戻す。
「11/17時点」のような日付だけの違いは、変わったことにしない。
Google は lastmod が正確なサイトでだけこの値を使う（Search Central「サイトマップの作成と送信」）。
"""
import html
import os
import re
import subprocess
import datetime

from common import OUT, TODAY as _TD

TODAY = _TD.isoformat()   # 日本時間の今日（Actions は UTC なので date.today() だと前の日になる）
_DROP = [re.compile(p, re.S) for p in (
    r"<script.*?</script>", r"<style.*?</style>", r"<head>.*?</head>",
    r"\d{4}年\d{1,2}月\d{1,2}日", r"\d{1,2}/\d{1,2}\s?\d{1,2}:\d{2}", r"\d{1,2}/\d{1,2}(時点|取得|現在)",
    r"取得\s*\d{1,2}/\d{1,2}(〜\d{1,2}/\d{1,2})?", r'\?v=[0-9a-f]+', r'data-[a-z]+="[^"]*"',
)]
_TAG = re.compile(r"<[^>]+>")


def norm(s):
    """見た目の中身だけを残す（タグ・スクリプト・日付・版の印を外す）。"""
    for p in _DROP: s = p.sub(" ", s)
    s = html.unescape(_TAG.sub(" ", s))
    return " ".join(s.split())


def git(*a, inp=None):
    return subprocess.run(["git", "-C", OUT, *a], input=inp, capture_output=True, check=False).stdout


def head_files(paths):
    """HEAD にあるファイルの中身をまとめて読む（git cat-file --batch）。無いファイルは None。"""
    if not paths: return {}
    out = git("cat-file", "--batch", inp="".join(f"HEAD:{p}\n" for p in paths).encode())
    res, i = {}, 0
    for p in paths:
        j = out.index(b"\n", i); head = out[i:j].decode()
        if head.endswith("missing"): res[p] = None; i = j + 1; continue
        n = int(head.split()[2]); res[p] = out[j + 1:j + 1 + n].decode("utf-8", "replace"); i = j + 1 + n + 1
    return res


LOC = re.compile(r"<url><loc>https://yasumibi\.com/([^<]*)</loc><lastmod>([^<]*)</lastmod></url>")
kinds = sorted(f for f in os.listdir(OUT) if re.fullmatch(r"sitemap-[a-z]+\.xml", f))
prev_lm = {}
for f in kinds:
    for u, lm in LOC.findall(head_files([f]).get(f) or ""): prev_lm[u] = lm

changed = kept = 0
idx = []
for f in kinds:
    cur = open(f"{OUT}/{f}", encoding="utf-8").read()
    urls = [u for u, _ in LOC.findall(cur)]
    paths = [f"{u}index.html" for u in urls]
    old = head_files(paths)
    lms = []
    for u, p in zip(urls, paths):
        lm = TODAY
        if u in prev_lm and old.get(p) is not None:
            try:
                if norm(open(f"{OUT}/{p}", encoding="utf-8").read()) == norm(old[p]): lm = prev_lm[u]
            except OSError: pass
        if lm == TODAY: changed += 1
        else: kept += 1
        lms.append((u, lm))
    open(f"{OUT}/{f}", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "".join(f"  <url><loc>https://yasumibi.com/{u}</loc><lastmod>{lm}</lastmod></url>\n" for u, lm in lms) + "</urlset>\n")
    idx.append((f, max((lm for _, lm in lms), default=TODAY)))
open(f"{OUT}/sitemap.xml", "w", encoding="utf-8").write(
    '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    + "".join(f"  <sitemap><loc>https://yasumibi.com/{f}</loc><lastmod>{lm}</lastmod></sitemap>\n" for f, lm in idx) + "</sitemapindex>\n")
print("sitemap lastmod: changed", changed, "kept", kept)
