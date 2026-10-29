"""お気に入り（/favorites/）：この端末に保存した宿を並べて、神日カレンダーを比べる。中身は favs.js が作る。"""
import os, sys, html, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, plan_s, plan_l, COND_PLAN
from common import site_header, tabbar, footer, og_meta, OUT


def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


base = "../"
v = ver("site.css"), ver("hotel.css"), ver("top.css", "rank.css"), ver("favs.js")
t = "お気に入り｜宿の神日を並べて比べる｜YASUMIBI"
d = "お気に入りに入れた宿の神日カレンダーを、2〜3軒並べて比べられます。どの日に、どの宿がいちばん安いかが一目でわかります。"
page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,follow">
<title>{html.escape(t)}</title>
<meta name="description" content="{html.escape(d)}">
{og_meta(html.escape(t), html.escape(d), "favorites/")}<link rel="canonical" href="https://yasumibi.com/favorites/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={v[0]}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v[1]}">
<link rel="stylesheet" href="{base}assets/top.css?v={v[2]}">
<link rel="stylesheet" href="{base}assets/rank.css?v={v[2]}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 otk">
{site_header(base, "fav")}
<main class="gin ok rkp fvp">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>お気に入り</span></nav>
  <header class="ok-hd"><h1>お気に入り</h1><p>宿のページの「♡お気に入り」で保存した宿です。<b>3軒まで選んで</b>、神日カレンダーを並べて比べられます。</p></header>
  <div id="fv-empty" class="fv-empty" hidden>
    <p>まだお気に入りの宿がありません。</p>
    <p class="s">気になる宿のページで「♡お気に入り」を押すと、ここに並びます。保存はこの端末のブラウザだけで、ログインはいりません。</p>
    <a class="fall" href="{base}">神日を探す ›</a>
  </div>
  <section class="rsec" id="fv-list-sec" hidden>
    <h2>保存した宿 <small id="fv-n"></small></h2>
    <ul class="fv-list" id="fv-list"></ul>
  </section>
  <section class="rsec fv-cmp" id="fv-cmp" hidden>
    <h2>並べて比べる</h2>
    <div class="mtabs" id="fv-months" role="tablist" aria-label="月"></div>
    <div class="pills" role="group" aria-label="泊まる曜日">
      <button type="button" data-fwd="all" aria-pressed="true">すべて</button>
      <button type="button" data-fwd="sat" aria-pressed="false">土曜泊</button>
      <button type="button" data-fwd="wk" aria-pressed="false">日〜木泊</button>
    </div>
    <div class="fv-sum" id="fv-sum"></div>
    <div class="fv-tw"><table class="fv-t" id="fv-t"></table></div>
    <p class="fv-lg"><span class="lo">その宿の神日</span><span class="best">その日いちばん安い宿</span>数字は2名1泊の料金（万円）。朝食付きで比べている宿には「朝食付き」と表示</p>
  </section>
  <p class="fine">※お気に入りは、この端末のブラウザに保存しています（ほかの端末とは共有されません）。{COND_PLAN}（2名合計・税込）。料金は楽天トラベルの料金で、毎日更新しています。</p>
</main>
""" + footer(base) + tabbar(base, "fav") + f"""<script src="{base}assets/favs.js?v={v[3]}"></script>
</body></html>
"""
os.makedirs(f"{OUT}/favorites", exist_ok=True)
open(f"{OUT}/favorites/index.html", "w", encoding="utf-8").write(page)
print("favorites built")
