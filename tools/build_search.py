"""検索結果のページ（/search/）。トップの検索で「すべて」のエリア、または「日付が決まっている」で探したときに移る先。

条件はURL（?ym=2027-01&wd=sat&max=50000&d=2027-01-16&r=1&c=...&area=hakone）で受け取り、assets/list.js が一覧を作る。
宿と料金のデータは search/data.json（全エリア）。検索結果なので、検索エンジンには載せない（noindex）。
"""
import os, sys, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import site_header, tabbar, footer, OUT, COND_PLAN, ASOF
import listdata as L


def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


os.makedirs(f"{OUT}/search", exist_ok=True)
json.dump(L.data(None), open(f"{OUT}/search/data.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
dv = hashlib.md5(open(f"{OUT}/search/data.json", "rb").read()).hexdigest()[:8]

# ---- トップのキーワード検索で使う、軽い一覧（宿の名前・地名・エリア・こだわり）。料金は入れない
_AJ = {x["key"]: x["name"] for x in L.LIVE}
_lc = {}
for h in L.HOTELS_L:
    if h["loc"] and h["loc"] != _AJ[h["area"]]: _lc[(h["area"], h["loc"])] = _lc.get((h["area"], h["loc"]), 0) + 1
from area_yomi import YOMI
KW = dict(a=[[x["key"], x["name"], x["region"], L.CNT[x["key"]], YOMI.get(x["key"], "") + " " + x["key"]] for x in L.LIVE],
          l=[[a, lo, n] for (a, lo), n in sorted(_lc.items(), key=lambda kv: -kv[1])],
          h=[[h["name"], h["slug"], h["area"], h["loc"]] for h in L.HOTELS_L],
          t=[[k, v] for k, v in L.TAG_JA.items()])
json.dump(KW, open(f"{OUT}/search/kw.json", "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
base = "../"
v1, v2, v3, vl = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css"), ver("list.js")
page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,follow">
<title>宿をさがす｜YASUMIBI</title>
<meta name="description" content="口コミ★4.3以上の宿を、泊まる月・曜日・予算・こだわりで絞り込んで、いちばん安い日（神日）と料金を表示します。">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="stylesheet" href="{base}assets/otoku.css?v={v3}">
<link rel="stylesheet" href="{base}assets/rank.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">
<link rel="manifest" href="{base}manifest.webmanifest">
<meta name="theme-color" content="#ffffff">
<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 otk">
{site_header(base)}
<main class="gin ok rkp">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>宿をさがす</span></nav>
  {L.list_section(None, base, src=f"data.json?v={dv}")}
  <p class="srch-back"><a href="{base}#search">トップで条件を変える</a></p>
  <section class="rsec ar-more" aria-labelledby="arm-h"><h2 id="arm-h">エリアから探す</h2>{L.tiles_row(base)}</section>
  <p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上。ハイクラスの宿は20件以上・★4.6以上）の宿。{COND_PLAN}（2名合計・税込）。料金は楽天トラベルの{ASOF}時点のもので、毎日更新しています。宿の写真：楽天トラベル</p>
</main>
{footer(base)}
{tabbar(base, "")}
<script src="{base}assets/list.js?v={vl}" defer></script>
</body></html>
"""
open(f"{OUT}/search/index.html", "w", encoding="utf-8").write(page)
print("search built", len(L.HOTELS_L), "hotels")
