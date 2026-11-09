"""全ページに予約前シート（assets/bsheet.js）を入れる。キャンペーンの条件は common.py の CARD_CAMP から渡す。
add_analytics.py と同じく、ページを作り終えたあとに動かす（何度動かしても同じ結果）。"""
import os, re, hashlib, html
from common import OUT, CARD_AFF, CARD_CAMP, CARD_BONUS
import urllib.parse
AFF = "589faade.b97f81b7.589faadf.010fa421"   # 楽天トラベルのアフィリエイトID（build_* と同じ）
_c = urllib.parse.quote("https://travel.rakuten.co.jp/card/campaign/", safe="")
ENTRY = f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={_c}&m={_c}"   # 楽天カード2.5倍のエントリーページ
SECOND = ""   # 2枚目のカード（承認されたら JSON：{"name":..,"url":..,"text":..}）

js = f"{OUT}/assets/bsheet.js"
v = hashlib.md5(open(js, "rb").read()).hexdigest()[:8]
_a = lambda s: html.escape(str(s), quote=True)
tag = (f'<script defer src="/assets/bsheet.js?v={v}" data-card="{_a(CARD_AFF)}" data-end="{CARD_CAMP["book_end"]}" data-out="{CARD_CAMP["out_last"]}"'
       f' data-end-ja="{_a(CARD_CAMP["book_end_ja"])}" data-out-ja="{_a(CARD_CAMP["out_last_ja"])}" data-bonus="{CARD_BONUS}" data-checked="{_a(CARD_CAMP["checked"])}" data-entry="{_a(ENTRY)}"{f' data-second="{_a(SECOND)}"' if SECOND else ""}></script>')
pat = re.compile(r'<script defer src="/assets/bsheet\.js[^>]*></script>')
n = 0
for d, _, fs in os.walk(OUT):
    if "/.git" in d: continue
    for f in fs:
        if not f.endswith(".html"): continue
        p = os.path.join(d, f); s = open(p, encoding="utf-8").read()
        if "</head>" not in s: continue
        t = pat.sub("", s).replace("</head>", tag + "</head>", 1)
        if t != s: open(p, "w", encoding="utf-8").write(t); n += 1
print("予約前シート", n)
