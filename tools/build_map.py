"""地図から探す（/map/）：★4.3以上の宿を地図に並べ、月ごとの神日の料金をピンで見せる。中身は map.js が作る。
地図：Leaflet 1.9.4 ＋ Leaflet.markercluster 1.5.3（cdnjs・版を固定）／背景：国土地理院（地理院タイル・淡色地図）。
食事付き（2食）と朝食付きの宿は混ぜない（上の切り替えでどちらかだけを出す）。
"""
import os, sys, json, html, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, plan_s, COND_PLAN, HOTELS, MONTHS, DEFAULT_YM, AREA_JA, AREAS, DATA, month_prices
from common import site_header, tabbar, footer, og_meta, OUT

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
built = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()


def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


# ---- データ（宿ごと：月ごとの最安と、その日）
hs = []
for h in HOTELS:
    i = INFO.get(str(h["no"]), {})
    if not i.get("lat") or h["slug"] not in built: continue
    mp = []
    for y, m in MONTHS:
        p = month_prices(h["no"], y, m)
        v = [x for x in p if x]
        mp.append([min(v), p.index(min(v)) + 1] if v else [0, 0])
    if not any(x[0] for x in mp): continue
    hs.append(dict(n=h["name"], s=h["slug"], no=h["no"], a=AREA_JA.get(h["area"], ""), k=h["area"], la=round(i["lat"], 5), lo=round(i["lng"], 5),
                   r=round(h.get("avg", 0), 2), t=i.get("thumb", "").replace("https://img.travel.rakuten.co.jp/", "~"), b=1 if is_b(h["area"]) else 0, p=mp))
data = dict(months=[dict(y=y, m=m) for y, m in MONTHS], dm=MONTHS.index(DEFAULT_YM) if DEFAULT_YM in MONTHS else 0, aff=AFF, hotels=hs)
os.makedirs(f"{OUT}/map", exist_ok=True)
json.dump(data, open(f"{OUT}/map/data.json", "w"), ensure_ascii=False, separators=(",", ":"))

base = "../"
v = ver("site.css"), ver("top.css"), ver("map.css", "map.js"), ver("hotel.css")
t = "地図から探す｜★4.3以上の宿の神日を地図で｜YASUMIBI"
d = "★4.3以上の宿を地図で。行きたい場所の宿が、その月いちばん安い日（神日）と料金を地図の上で見比べられます。毎日更新。"
n2 = sum(1 for x in hs if not x["b"]); nb = len(hs) - n2
month_opts = "".join(f'<option value="{i}"{" selected" if i == data["dm"] else ""}>{m}月</option>' for i, (y, m) in enumerate(MONTHS))
area_opts = '<option value="">エリアへ移動</option>' + "".join(
    f'<option value="{a["key"]}" data-b="{1 if is_b(a["key"]) else 0}">{html.escape(a["name"])}</option>' for a in AREAS if any(x["k"] == a["key"] for x in hs))
page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{html.escape(t)}</title>
<meta name="description" content="{html.escape(d)}">
{og_meta(html.escape(t), html.escape(d), "map/")}<link rel="canonical" href="https://yasumibi.com/map/">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/MarkerCluster.min.css">
<link rel="stylesheet" href="{base}assets/site.css?v={v[0]}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v[3]}">
<link rel="stylesheet" href="{base}assets/top.css?v={v[1]}">
<link rel="stylesheet" href="{base}assets/map.css?v={v[2]}">
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 mapp">
{site_header(base, "map")}
<main class="mp">
  <div class="mp-bar">
    <div class="ln" role="tablist" aria-label="比べる宿">
      <button type="button" role="tab" id="ln-2" aria-selected="true">食事付きの宿<small>夕食・朝食つき {n2}軒</small></button>
      <button type="button" role="tab" id="ln-b" aria-selected="false">朝食付きの宿<small>街・リゾート {nb}軒</small></button>
    </div>
    <div class="mp-sel">
      <label><span class="vh">泊まる月</span><select id="mp-month">{month_opts}</select></label>
      <label><span class="vh">エリア</span><select id="mp-area">{area_opts}</select></label>
    </div>
  </div>
  <div class="mp-body">
    <aside class="mp-side" aria-label="この範囲の宿">
      <h1 class="mp-h">地図から探す</h1>
      <p class="mp-lead"><b id="mp-cnt">0</b>軒・<span id="mp-mo"></span>の神日の安い順<small>地図を動かすと、見えている範囲の宿に変わります</small></p>
      <ol class="mp-list" id="mp-list"></ol>
    </aside>
    <div class="mp-map" id="mp-map" role="region" aria-label="地図"></div>
    <div class="mp-card" id="mp-card" hidden></div>
  </div>
  <p class="mp-note">※★4.3以上（口コミ50件以上）の宿。料金は大人2名・1室の最安プラン（食事付きは1泊2食、朝食付きは1泊朝食・2名合計・税込）で、その月いちばん安い日（神日）の料金です。地図：国土地理院（地理院タイル）</p>
</main>
""" + tabbar(base, "map") + f"""<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet.markercluster/1.5.3/leaflet.markercluster.min.js"></script>
<script src="{base}assets/map.js?v={v[2]}"></script>
</body></html>
"""
open(f"{OUT}/map/index.html", "w", encoding="utf-8").write(page)
print("map built", len(hs), "hotels", n2, nb)
