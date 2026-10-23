"""エリアのページと検索結果のページ（/search/）で使う、宿の一覧のデータと、エリアのタイル。

一覧の絞り込み・並び替えは assets/list.js が行う。ここでは、そのためのデータ（宿・料金・タグ）を作る。
最初に見える状態（最初に開く月・安い順・10軒）は、Pythonでも同じものをHTMLに書いておく（あとからJSで入れると、下の段がずれる＝CLS）。
"""
import os, sys, json, html, datetime, calendar, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (AREAS, MONTHS, DEFAULT_YM, PRH, SLUG, TODAY, CARD_CAMP, is_b, load_area, OUT)
from tagdefs import tags_of, INFO, TAGS

AFF = "589faade.b97f81b7.589faadf.010fa421"
WD = "日月火水木金土"
FIRST = 10          # はじめに見せる軒数（残りは「もっと見る」）

# 掲載するエリアの写真（Wikimedia Commons・credits.json にクレジット）。明るい昼の写真にそろえる。
AREA_IMG = {"hakone": "hakone-fuji-ship.jpg", "atami": "atami-panorama.jpg", "kusatsu": "kusatsu-yubatake.jpg",
            "yufuin": "yufuin-kinrinko-sunny.jpg", "beppu": "beppu-chinoike.jpg",
            "arima": "arima-view.jpg", "kinugawa": "kinugawa-cover.jpg", "gero": "gero-cover.jpg", "noboribetsu": "noboribetsu-jigokudani-day.jpg",
            "ito": "ito-okawa-river-day.jpg", "izukogen": "izukogen-jogasaki.jpg", "shuzenji": "shuzenji-river-day.jpg",
            "karuizawa": "karuizawa-kumoba-pond.jpg", "kawaguchiko": "kawaguchiko-fuji.jpg", "kinosaki": "kinosaki-willow-day.jpg",
            "kyoto": "kyoto-kiyomizu-autumn.jpg", "sapporo": "sapporo-odori-blue.jpg", "jozankei": "jozankei-bridge.jpg", "otaru": "otaru-canal-sunny.jpg",
            "hakodate": "hakodate-hachimanzaka-day.jpg", "toya": "toya-lake.jpg", "akan": "akan-lake.jpg", "naha": "naha-shureimon.jpg",
            "onna": "onna-beach-sunny.jpg", "chatan": "chatan-village.jpg", "ishigaki": "ishigaki-kabira.jpg",
            "ikaho": "ikaho-steps.jpg", "nikko": "nikko-toshogu.jpg", "shima": "shima-river.jpg", "yugawara": "yugawara-fujiki-sunny.jpg",
            "miyako": "miyako-maehama-beach.jpg", "nasu": "nasu-mountain-autumn.jpg", "isawa": "isawa-peach-blossom.jpg",
            "shirahama": "shirahama-beach.jpg", "okuhida": "okuhida-shinhotaka.jpg"}
AREA_IMG = {k: v for k, v in AREA_IMG.items() if os.path.exists(f"{OUT}/assets/img/{v}")}


def esc(s): return html.escape(str(s), quote=True)


MONTHS_L = [dict(y=y, m=m, days=calendar.monthrange(y, m)[1]) for (y, m) in MONTHS]
DEF_KEY = f"{DEFAULT_YM[0]}-{DEFAULT_YM[1]:02d}"
_AREA = load_area()
HOTELS_L = []
for h in _AREA["hotels"]:
    if str(h["no"]) not in INFO: continue
    slug, name, full = SLUG[h["no"]]
    src = PRH.get(str(h["no"]), {})
    pm = {}
    for mm in MONTHS_L:
        k = f"{mm['y']}-{mm['m']:02d}"
        pm[k] = [int(src.get(f"{k}-{d:02d}", 0) or 0) for d in range(1, mm["days"] + 1)]
    r = dict(no=h["no"], slug=slug, name=name, area=h["area"], loc=h["loc"], avg=round(h["avg"], 2),
             thumb=INFO[str(h["no"])].get("thumb", ""), t=tags_of(h["no"]), p=pm)
    if is_b(h["area"]): r["b"] = 1
    HOTELS_L.append(r)
CNT = {}
for h in HOTELS_L: CNT[h["area"]] = CNT.get(h["area"], 0) + 1
LIVE = [a for a in AREAS if CNT.get(a["key"])]            # 宿が1軒以上あるエリアだけ
_RO = ["北海道", "東北", "北関東", "関東・伊豆", "甲信", "北陸", "東海", "関西", "中国", "四国", "九州", "沖縄"]   # 北から南へ
REGIONS = sorted(dict.fromkeys(a["region"] for a in LIVE), key=lambda r: _RO.index(r) if r in _RO else 99)
OPEN_REGION = "関東・伊豆" if "関東・伊豆" in REGIONS else REGIONS[0]   # トップで最初に開く地方（宿がいちばん多い）
TAG_JA = {t["slug"]: t["name"] for t in TAGS}


def area_min(key):
    """そのエリアの宿の、今日から先（掲載期間内）でいちばん安い料金。"""
    best = 0
    for h in HOTELS_L:
        if h["area"] != key: continue
        for k, arr in h["p"].items():
            y, m = int(k[:4]), int(k[5:])
            for d, v in enumerate(arr, 1):
                if v and datetime.date(y, m, d) >= TODAY and (not best or v < best): best = v
    return best


AREA_MIN = {a["key"]: area_min(a["key"]) for a in LIVE}


try: CREDITS = json.load(open(f"{OUT}/assets/img/credits.json"))
except Exception: CREDITS = {}


def credits_html(keys):
    """タイルに使った写真のクレジット（Wikimedia Commons のライセンスの表示）。小さくたたんでおく。"""
    AJ = {a["key"]: a["name"] for a in LIVE}
    it = []
    for k in keys:
        c = CREDITS.get(AREA_IMG.get(k, ""))
        if c: it.append(f'{esc(AJ[k])}：<a href="{esc(c["source"])}" target="_blank" rel="noopener">{esc(c["artist"] or "Wikimedia Commons")}</a>（{esc(c["license"])}）')
    return f'<details class="at-cr"><summary>写真のクレジット</summary><p>{"・".join(it)}　出典：Wikimedia Commons</p></details>' if it else ""


def meal_ja(key): return "朝食付き" if is_b(key) else "2食付き"


def data(area=None):
    """list.js に渡すデータ。area を渡すとそのエリアの宿だけ。"""
    hs = [h for h in HOTELS_L if area is None or h["area"] == area]
    return dict(months=MONTHS_L, def_ym=DEF_KEY, aff=AFF,
                camp=dict(bookEnd=CARD_CAMP["book_end"], outLast=CARD_CAMP["out_last"]),
                areas={a["key"]: a["name"] for a in LIVE}, regions={a["key"]: a["region"] for a in LIVE},
                b=[a["key"] for a in LIVE if is_b(a["key"])], tags=TAG_JA, hotels=hs)


# ---- エリアのタイル（写真＋地名＋いちばん安い料金）。トップは地方のタブで切り替え、エリア・検索のページは横スクロールの1列。
def tile(a, base):
    k = a["key"]; img = AREA_IMG.get(k)
    vis = (f'<img src="{base}assets/img/{img}" alt="" loading="lazy" width="480" height="300">' if img
           else f'<span class="at-nt">{esc(a["name"])}</span>')
    pr = f'<em>¥{AREA_MIN[k]:,}〜</em>' if AREA_MIN.get(k) else ""
    return (f'<li><a class="at" href="{base}areas/{k}/">{vis}<i class="at-ml">{meal_ja(k)}</i>'
            f'<span class="at-cap"><b>{esc(a["name"])}</b>{pr}</span></a></li>')


def tiles_by_region(base, open_region=None):
    open_region = open_region or OPEN_REGION
    tabs = "".join(f'<button type="button" role="tab" aria-selected="{"true" if r == open_region else "false"}" data-reg="{i}">{esc(r)}</button>'
                   for i, r in enumerate(REGIONS))
    grids = "".join(f'<ul class="at-grid" data-reg="{i}"{"" if r == open_region else " hidden"}>'
                    + "".join(tile(a, base) for a in LIVE if a["region"] == r) + "</ul>" for i, r in enumerate(REGIONS))
    return f'<div class="at-tabs" role="tablist" aria-label="地方">{tabs}</div>{grids}{credits_html([a["key"] for a in LIVE])}'


def tiles_row(base, first=None, skip=None):
    """横スクロールの1列。first（同じ地方）を先に、そのあと残りのエリア。"""
    order = [a for a in LIVE if a["key"] != skip and a["region"] == first] + [a for a in LIVE if a["key"] != skip and a["region"] != first]
    return f'<ul class="at-row">{"".join(tile(a, base) for a in order)}</ul>{credits_html([a["key"] for a in order])}'


# ---- はじめに見える一覧（list.js の row() と同じ中身）
def lab(y, m, d): return f"{m}/{d}({WD[(datetime.date(y, m, d).weekday() + 1) % 7]})"


def link(no, y, m, d, n=1):
    a = datetime.date(y, m, d); b = a + datetime.timedelta(days=n)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={a.year}&f_tuki1={a.month}&f_hi1={a.day}"
         f"&f_nen2={b.year}&f_tuki2={b.month}&f_hi2={b.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="-_.!~*'()")   # JSの encodeURIComponent と同じ
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


def first_rows(area, base):
    """最初に開く月・こだわらない・安い順。過ぎた日は除く。"""
    mm = next(x for x in MONTHS_L if f"{x['y']}-{x['m']:02d}" == DEF_KEY)
    y, m = mm["y"], mm["m"]
    past = mm["days"] if (y, m) < (TODAY.year, TODAY.month) else (TODAY.day - 1 if (y, m) == (TODAY.year, TODAY.month) else 0)
    rows = []
    for h in HOTELS_L:
        if area and h["area"] != area: continue
        p = [0 if i < past else v for i, v in enumerate(h["p"][DEF_KEY])]
        vs = [v for v in p if v]
        if not vs: continue
        v = min(vs); days = [i + 1 for i, x in enumerate(p) if x == v]
        rows.append((h, v, days))
    rows.sort(key=lambda r: r[1])                    # Pythonのsortも安定ソート＝JSと同じ順
    out = []
    for i, (h, v, days) in enumerate(rows[:FIRST]):
        dl = "・".join(lab(y, m, d) for d in days[:2]) + (f" ほか{len(days) - 2}日" if len(days) > 2 else "")
        meta = f'{esc(h["loc"])}｜★{h["avg"]:.2f}' if area else f'{esc(dict((a["key"], a["name"]) for a in LIVE)[h["area"]])}・{esc(h["loc"])}｜★{h["avg"]:.2f}<i class="mb">{meal_ja(h["area"])}</i>'
        out.append(f'<li class="ri"><span class="rk">{i + 1}</span><a href="{base}hotels/{h["slug"]}/"><img class="rt" src="{h["thumb"]}" alt="" loading="lazy" width="96" height="64"></a>'
                   f'<div class="rb"><a class="rn" href="{base}hotels/{h["slug"]}/">{esc(h["name"])}</a><span class="rm">{meta}</span>'
                   f'<div class="rk2"><i class="kd">神日</i>{dl} <b>¥{v:,}</b></div></div>'
                   f'<a class="rgo" href="{link(h["no"], y, m, days[0])}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a></li>')
    return "".join(out), len(rows)


def list_section(area, base, src=None):
    """一覧（絞り込みのチップ＋宿の一覧）。area があればそのエリアのデータをページに埋める。なければ src（JSON）を読む＝検索のページ。"""
    AJ = {a["key"]: a["name"] for a in LIVE}
    if area:
        rows, n = first_rows(area, base)
        more = f'<button type="button" class="more2" id="lmore"{"" if n > FIRST else " hidden"}>もっと見る（あと{n - FIRST}軒）</button>'
        title = f'{esc(AJ[area])}の宿'
        meal = f'<span class="meal" id="lmeal">{meal_ja(area)}</span>'
        cnt = f"{n}軒"
        dat = f'<script type="application/json" id="list-data">{json.dumps(data(area), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")}</script>'
        attrs = f'data-area="{area}"'
    else:
        rows = '<li class="rempty">読み込んでいます…</li>'
        more = '<button type="button" class="more2" id="lmore" hidden>もっと見る</button>'
        title = "全エリアの宿"; meal = '<span class="meal" id="lmeal" hidden></span>'; cnt = ""; dat = ""
        attrs = f'data-src="{src}"'
    return f"""<section class="alist" id="alist" data-base="{base}" {attrs} aria-labelledby="ltitle">
  <div class="lh"><h2 id="ltitle">{title}</h2>{meal}</div>
  <div class="fbar" id="fbar"></div>
  <button type="button" class="fsum" id="fsum" hidden><span class="fsum-l">条件</span><span id="fsum-t"></span><span class="fsum-c">変える</span></button>
  <div class="sortrow"><b id="lc">{cnt}</b><div class="seg" id="lsort" role="group" aria-label="並び替え"></div></div>
  <p class="lnote" id="lnote"></p>
  <ol class="rl" id="lrows">{rows}</ol>
  {more}
  {dat}
</section>"""
