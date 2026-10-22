"""New search-first top page (Rakuten-Travel-like frame) → yasumibi-site/new/ (noindex until swapped in)."""
import json, os, html, hashlib, datetime, urllib.parse, sys
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # このリポジトリ
OUT = os.environ.get("YB_OUT", os.path.join(os.path.dirname(ROOT), "yasumibi-site"))  # 公開用リポジトリ（隣に置く）
from common import site_header, tabbar, footer, og_meta, load_area, AREAS, AREA_JA, MONTHS, DEFAULT_YM, ASOF, PRH, TODAY
AREA = load_area()
INFO = json.load(open(f"{ROOT}/data/hotel_info_20261021.json"))["hotels"]
AFF = "589faade.b97f81b7.589faadf.010fa421"

# slug/name map shared with build_hotel
from common import SLUG


def logo_html(base, href=None):
    href = base if href is None else href
    return (f'<a class="brand" href="{href}" aria-label="YASUMIBI ホーム">'
            f'<img class="lg-l" src="{base}assets/img/logo.png" alt="YASUMIBI" width="714" height="120">'
            f'<img class="lg-d" src="{base}assets/img/logo-dark.png" alt="" width="714" height="120"></a>')

def esc(s): return html.escape(str(s), quote=True)
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]

import calendar
months = [dict(y=y, m=m, days=calendar.monthrange(y, m)[1]) for (y, m) in MONTHS]
hotels = []
for h in AREA["hotels"]:
    if str(h["no"]) not in INFO: continue
    slug, name, full = SLUG[h["no"]]
    pm = {}
    for mm in months:
        k = f"{mm['y']}-{mm['m']:02d}"
        src = PRH.get(str(h["no"]), {})
        pm[k] = [int(src.get(f"{k}-{d:02d}", 0) or 0) for d in range(1, mm["days"] + 1)]
    hotels.append(dict(no=h["no"], slug=slug, name=name, area=h["area"], tier=h["tier"], loc=h["loc"], avg=h["avg"], cnt=h["cnt"],
                       thumb=INFO[str(h["no"])].get("thumb", ""), p=pm))
CNT = {}
for h in hotels: CNT[h["area"]] = CNT.get(h["area"], 0) + 1
LIVE = [a for a in AREAS if CNT.get(a["key"])]       # 宿が1軒以上あるエリアだけ出す
DATA = dict(months=months, asof=ASOF, aff=AFF, hotels=hotels, areas={a["key"]: a["name"] for a in LIVE})
DEF_MI = next((i for i, mm in enumerate(months) if (mm["y"], mm["m"]) == DEFAULT_YM), 0)
REGIONS = []
for a in LIVE:
    if a["region"] not in REGIONS: REGIONS.append(a["region"])
area_opts = '<option value="all">すべて</option>' + "".join(
    f'<optgroup label="{esc(r)}">' + "".join(f'<option value="{a["key"]}">{esc(a["name"])}</option>' for a in LIVE if a["region"] == r) + "</optgroup>" for r in REGIONS)
area_blocks = "".join(
    f'<div class="reg"><h3>{esc(r)}</h3><ul>' + "".join(f'<li><a href="#search" data-go-area="{a["key"]}">{esc(a["name"])}<small>{CNT[a["key"]]}軒</small></a></li>' for a in LIVE if a["region"] == r) + "</ul></div>" for r in REGIONS)
_dd = datetime.date(*DEFAULT_YM, 16)
date_default = _dd.isoformat()
month_opts = "".join(f'<option value="{i}"{" selected" if i == DEF_MI else ""}>{mm["y"]}年{mm["m"]}月</option>' for i, mm in enumerate(months))
dmin = f"{months[0]['y']}-{months[0]['m']:02d}-01"; dmax = f"{months[-1]['y']}-{months[-1]['m']:02d}-{months[-1]['days']:02d}"

MAXES = list(range(4, 13)) + [15, 20]
max_opts = '<option value="0" selected>こだわらない</option>' + "".join(f'<option value="{m*10000}">〜{m}万円</option>' for m in MAXES)

FEATURES = [("renkyu", "有給1日で、何連休？", "連休のいちばん安い夜を毎日計算", "hakone-torii.jpg"),
            ("ranking", "日をずらすと、いくら浮く？", "全国の宿ランキング・毎日更新", "hakone-fuji-ship.jpg"),
            ("hakone-5man", "箱根の神日。", "2人で5万円前後の人気宿5軒", "hakone-fuji-ship.jpg"),
            ("hakone-10man", "箱根、10万円の夜。", "天悠、富士屋ホテルほか5軒", "hakone-torii.jpg"),
            ("atami-5man", "熱海の神日。", "2人で5万円前後の人気宿5軒", "atami-panorama.jpg"),
            ("atami-10man", "熱海、10万円の夜。", "迎賓館、大観荘ほか5軒", "atami-fireworks.jpg")]

base = ""
v1 = ver("site.css"); v2 = ver("hotel.css", "hotel.js"); v3 = ver("top.css", "top.js")
TILE = {"renkyu": '<span class="tile t-ren">有給1日で<b>何連休？</b></span>', "ranking": '<span class="tile t-rank">ずらすと<b>いくら浮く？</b></span>'}
strip_html = "".join(f'<li><a href="{base}{s if s in TILE else "features/" + s}/">' + (TILE.get(s) or f'<img src="{base}assets/img/{img}" alt="" loading="lazy">') + f'<span class="ft">{esc(t)}</span><span class="fs">{esc(sub)}</span></a></li>' for s, t, sub, img in FEATURES)
feat_html = "".join(f'<li><a href="{base}{s if s in ('renkyu', 'ranking') else 'features/' + s}/"><img src="{base}assets/img/{img}" alt="" loading="lazy"><span class="ft">{esc(t)}</span><span class="fs">{esc(sub)}</span></a></li>' for s, t, sub, img in FEATURES)

page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>神日カレンダー｜箱根・熱海の宿の安い日がわかる｜YASUMIBI</title>
<meta name="description" content="箱根・熱海の人気宿の料金を全日調べ、いちばん安い日（神日）を表示。エリアと予算を選ぶだけで、安い日と料金がすぐわかる。">
<link rel="canonical" href="https://yasumibi.com/">
{og_meta("神日カレンダー｜箱根・熱海の宿の安い日がわかる｜YASUMIBI", "箱根・熱海の人気宿の料金を全日調べ、いちばん安い日（神日）を表示。エリアと予算を選ぶだけで、安い日と料金がすぐわかる。", "")}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">
</head>
<body class="app top2">
{site_header(base)}

<section class="hero" id="search">
  <div class="gin">
    <h1>泊まるなら、いちばん安い日に。</h1>
    <div class="shift" aria-label="YASUMIBIの考え方"><div class="o"><small>これまで</small>休みの日に、安い宿を探す。</div><div class="n"><small>これから</small><b>安い日に、休みを合わせる。</b></div></div>
    <p class="kexp"><span class="star"><i aria-hidden="true">★</i>口コミ4.3以上の宿だけ</span><span class="kd"><b>神日</b>＝その宿がその月でいちばん安い日</span></p>
    <div class="sbox">
      <div class="stabs" role="tablist" aria-label="探し方">
        <button type="button" role="tab" id="t-free" aria-selected="true" aria-controls="p-search">日付はまだ決めていない</button>
        <button type="button" role="tab" id="t-date" aria-selected="false" aria-controls="p-search">日付が決まっている</button>
      </div>
      <form class="sform" id="p-search" role="tabpanel" aria-labelledby="t-free">
        <label class="fld"><span>エリア</span>
          <select id="f-area">{area_opts}</select></label>
        <label class="fld"><span>予算（2名1泊2食）</span>
          <select id="f-max">{max_opts}</select></label>
        <label class="fld" id="w-month"><span>泊まる月</span>
          <select id="f-month">{month_opts}</select></label>
        <label class="fld" id="w-date" hidden><span>泊まる日</span>
          <input type="date" id="f-date" min="{dmin}" max="{dmax}" value="{date_default}"></label>
        <label class="fld" id="w-wd"><span>曜日</span>
          <select id="f-wd"><option value="all">こだわらない</option><option value="sat">土曜泊</option><option value="wk">日〜木泊</option></select></label>
        <button type="submit" class="go" id="f-go">神日を探す</button>
      </form>
    </div>
  </div>
</section>

<main class="gin">
  <section class="fstrip" aria-labelledby="fsh">
    <div class="fs-hd"><h2 id="fsh">特集</h2><a href="#features">すべて見る ›</a></div>
    <ul class="fs-row">{strip_html}</ul>
  </section>

  <section class="res" aria-labelledby="rh" id="results" hidden>
    <div class="rhd"><h2 id="rh">今月の神日</h2><span><span class="prt">PR</span><span id="rc"></span></span></div>
    <p class="rnote" id="rnote"></p>
    <ol class="rlist" id="rlist"></ol>
    <button type="button" class="rmorebtn" id="rmore" hidden>もっと見る</button>
  </section>

  <section class="pick" aria-labelledby="pk1">
    <div class="rhd"><h2 id="pk1"><span id="pk-m"></span>いちばん安い神日</h2><span><span class="prt">PR</span>TOP5</span></div>
    <ol class="rlist" id="p-cheap"></ol>
  </section>
  <section class="pick" aria-labelledby="pk2">
    <div class="rhd"><h2 id="pk2">ずらすと、いちばん浮く宿</h2><span><span class="prt">PR</span>TOP5</span></div>
    <p class="rnote">土曜泊の平均と、その月の神日の差。</p>
    <ol class="rlist" id="p-gap"></ol>
    <a class="pmore" href="{base}ranking/">ランキングをもっと見る ›</a>
  </section>
  <p class="cond">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。{ASOF}時点の楽天トラベルの料金。予約前に最新の料金をご確認ください。宿の写真：楽天トラベル</p>

  <a class="rcb" href="{base}rakuten-card/">
    <span class="pr">PR</span>
    <span class="t">楽天トラベルは、楽天カードで払うとポイント2.5倍</span>
    <span class="s">エントリーして事前決済すると、国内宿泊のポイントが2.5倍。神日と組み合わせて、旅費をもう一段下げる。</span>
    <span class="b">実際の宿で試算を見る →</span>
  </a>

  <section class="areas" id="areas" aria-labelledby="ah">
    <div class="rhd"><h2 id="ah">エリアから探す</h2><span>エリアは順次ふやしていきます</span></div>
    {area_blocks}
  </section>

  <section class="feats" id="features" aria-labelledby="fh">
    <div class="rhd"><h2 id="fh">特集</h2><span>エリアと予算ごとの神日を、読み物で</span></div>
    <ul class="flist">{feat_html}</ul>
  </section>

</main>

{footer(base)}

{tabbar(base, "home")}
<script>window.TOP = {json.dumps(DATA, ensure_ascii=False)};</script>
<script src="{base}assets/top.js?v={v3}"></script>
</body></html>
"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(page)
print("new top built", len(hotels))
