"""New search-first top page (Rakuten-Travel-like frame) → yasumibi-site/new/ (noindex until swapped in)."""
import json, os, html, hashlib, datetime, urllib.parse, sys
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # このリポジトリ
OUT = os.environ.get("YB_OUT", os.path.join(os.path.dirname(ROOT), "yasumibi-site"))  # 公開用リポジトリ（隣に置く）
from common import img_v, tile_img, place_of, bk_attr, is_hc, usual_price
from common import is_b, plan_s, plan_l, COND_PLAN
from common import site_header, tabbar, footer, og_meta, load_area, AREAS, AREA_JA, MONTHS, DEFAULT_YM, ASOF, PRH, TODAY
AREA = load_area()
INFO = json.load(open(f"{ROOT}/data/hotel_info_20261021.json"))["hotels"]
AFF = "589faade.b97f81b7.589faadf.010fa421"

# slug/name map shared with build_hotel
from common import SLUG
from common import CARD_CAMP, card_extra
import listdata as L


def logo_html(base, href=None):
    href = base if href is None else href
    return (f'<a class="brand" href="{href}" aria-label="YASUMIBI ホーム">'
            f'<img class="lg-l" src="{base}assets/img/logo.png" alt="YASUMIBI" width="714" height="120">'
            f'</a>')   # 暗い色のロゴは使っていない（ダークモードなし）。読み込まないよう外した

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
    if is_b(h["area"]): hotels[-1]["b"] = 1           # 1泊朝食付きで比べる宿（TOP5には入れない）
CNT = {}
for h in hotels: CNT[h["area"]] = CNT.get(h["area"], 0) + 1
LIVE = [a for a in AREAS if CNT.get(a["key"])]       # 宿が1軒以上あるエリアだけ出す
_big = [a["name"] for a in sorted(LIVE, key=lambda a: -CNT[a["key"]])][:5]
TOP_T = "YASUMIBI｜★4.3以上の宿が、いちばん安い日（神日）がわかる｜神日カレンダー"
TOP_D = (f"{'・'.join(_big)}など{len(LIVE)}エリア、口コミ★4.3以上の宿{sum(CNT[a['key']] for a in LIVE)}軒（温泉宿は2食付き、街の宿は朝食付き）の料金を毎日全日調べて、"
         "いちばん安く泊まれる日（神日）を表示。安い日に、休みを合わせる。")
DATA = dict(months=months, asof=ASOF, aff=AFF, hotels=hotels, areas={a["key"]: a["name"] for a in LIVE},
            camp=dict(bookEnd=CARD_CAMP["book_end"], outLast=CARD_CAMP["out_last"]))
DEF_MI = next((i for i, mm in enumerate(months) if (mm["y"], mm["m"]) == DEFAULT_YM), 0)
REGIONS = []
for a in LIVE:
    if a["region"] not in REGIONS: REGIONS.append(a["region"])
area_opts = '<option value="all">すべて</option>' + "".join(
    f'<optgroup label="{esc(r)}">' + "".join(f'<option value="{a["key"]}"{' data-b="1"' if is_b(a["key"]) else ''}>{esc(a["name"])}</option>' for a in LIVE if a["region"] == r) + "</optgroup>" for r in REGIONS)
N2 = sum(CNT[a["key"]] for a in LIVE if not is_b(a["key"])); NB = sum(CNT[a["key"]] for a in LIVE if is_b(a["key"]))
lane_html = (f'<div class="ln" role="tablist" aria-label="比べる宿">'
             f'<button type="button" role="tab" id="ln-2" aria-selected="true">食事付きの宿<small>夕食・朝食つき {N2}軒</small></button>'
             f'<button type="button" role="tab" id="ln-b" aria-selected="false">朝食付きの宿<small>街・リゾート {NB}軒</small></button></div>') if NB else ""
area_blocks = '<div class="regs">' + "".join(
    f'<div class="reg"><h3>{esc(r)}</h3><ul>' + "".join(f'<li><a href="#search" data-go-area="{a["key"]}">{esc(a["name"])}<small>{CNT[a["key"]]}軒</small></a></li>' for a in LIVE if a["region"] == r) + "</ul></div>" for r in REGIONS) + "</div>"
_dd = datetime.date(*DEFAULT_YM, 16)
date_default = _dd.isoformat()
month_opts = "".join(f'<option value="{i}"{" selected" if i == DEF_MI else ""}>{mm["y"]}年{mm["m"]}月</option>' for i, mm in enumerate(months))
dmin = f"{months[0]['y']}-{months[0]['m']:02d}-01"; dmax = f"{months[-1]['y']}-{months[-1]['m']:02d}-{months[-1]['days']:02d}"

MAXES = list(range(4, 13)) + [15, 20]
max_opts = '<option value="0" selected>こだわらない</option>' + "".join(f'<option value="{m*10000}">〜{m}万円</option>' for m in MAXES)

FEATURES = [("weekend/", "今週末に泊まれる神日。", "直前でも、いつもより安い宿", None),
            ("renkyu/2027/", "2027年の連休カレンダー。", "祝日と、有給で何連休になるか", None),
            ("otoku-days/", "楽天で、さらに安くなる日。", "5と0のつく日・スーパーSALE", None),
            ("renkyu/", "有給1日でつくれる連休", "連休のいちばん安い夜を毎日計算", None),
            ("ranking/", "日をずらすと安くなる宿", "全国の宿ランキング・毎日更新", None)]
# 写真つきの特集：手で作ったもの＋自動でつくる特集（条件を満たしているものだけ）
from autofeat import FEATURE_CARDS, live as af_live, card_sub as af_sub, IMG as AF_IMG
FEATURES += FEATURE_CARDS + [(f"features/{sl}/", hd, af_sub(a, t), AF_IMG[a]) for a, t, sl, hd in af_live()]
FEATURES = [f for f in FEATURES if f[3] is None or os.path.isdir(f"{OUT}/{f[0]}")]
TILE = {"weekend/": '<span class="tile">直前でも<b>今週末</b></span>', "renkyu/2027/": '<span class="tile">2027年の<b>連休</b></span>', "otoku-days/": '<span class="tile">予約は<b>5と0の日</b></span>', "renkyu/": '<span class="tile t-ren">有給1日で<b>つくれる連休</b></span>', "ranking/": '<span class="tile t-rank">ずらすと<b>安い宿</b></span>'}
base = ""
def fcard(s, t, sub, img):
    vis = TILE.get(s) or tile_img(base, img, "236px")
    return f'<li><a href="{base}{s}">{vis}<span class="ft">{esc(t)}</span><span class="fs">{esc(sub)}</span></a></li>'
strip_html = "".join(fcard(*f) for f in FEATURES)
_tg = json.load(open(f"{OUT}/tags/tags.json")) if os.path.exists(f"{OUT}/tags/tags.json") else []
tag_html = ('<nav class="tgc tgc-top" aria-label="こだわりで探す"><span class="tgc-l">こだわり<small>いくつでも</small></span><ul>'
            + "".join(f'<li><a href="tags/{t["slug"]}/" data-tag="{t["slug"]}" role="button" aria-pressed="false">{esc(t["name"])}</a></li>' for t in _tg) + "</ul></nav>") if _tg else ""   # 押すと選ぶ／外す（いくつでも）。「神日を探す」で、選んだこだわりをすべて満たす宿を出す
TOP_N = 8   # トップの下に出す特集の数（残りは /features/ へ）
_tx = [f for f in FEATURES if f[3] is None]; _ph = [f for f in FEATURES if f[3]]
FEATURES = [x for pair in zip(_tx, _ph) for x in pair] + _tx[len(_ph):] + _ph[len(_tx):]   # 文字と写真を交互に
feat_html = "".join(fcard(*f) for f in FEATURES[:TOP_N])
v1 = ver("site.css"); v2 = ver("hotel.css", "hotel.js"); v3 = ver("top.css", "top.js")

# ---- TOP5の2つを、はじめからHTMLに書いておく（あとからJSで入れると、下の段がずれる＝CLS）
#      assets/top.js の card()・picks() と同じ中身。JSは読み込み後に同じものを描き直すだけ。
_WD = "日月火水木金土"
def _lab(m, d): return f'{m["m"]}/{d}({_WD[(datetime.date(m["y"], m["m"], d).weekday() + 1) % 7]})'
def _plink(no, m, d):
    a = datetime.date(m["y"], m["m"], d); b = a + datetime.timedelta(days=1)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={a.year}&f_tuki1={a.month}&f_hi1={a.day}"
         f"&f_nen2={b.year}&f_tuki2={b.month}&f_hi2={b.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="-_.!~*'()")   # JSの encodeURIComponent と同じ
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"
def _pcard(h, i, m, v, days, gap):
    dl = "・".join(_lab(m, d) for d in days[:3]) + (f"など{len(days)}日" if len(days) > 3 else "")
    body = (f'<div class="pr"><span class="tg">神日</span><span class="d">{dl}</span><span class="v">¥{v:,}</span></div>'
            + (f'<div class="gap">土曜泊の平均より <b>{gap:,}円安い</b></div>' if gap
               else f'<div class="pt">楽天カードなら +{card_extra(v, datetime.date(m["y"], m["m"], days[0])):,}円分</div>'))
    return (f'<li class="rc"><a class="ph" href="../hotels/{h["slug"]}/"><img src="{h["thumb"]}" alt="" loading="lazy" width="300" height="200"></a>'
            f'<div class="inf"><span class="rk">{i + 1}</span><a class="nm" href="../hotels/{h["slug"]}/">{h["name"]}</a>'
            f'<span class="meta">{esc(place_of(h))}｜★{h["avg"]:.2f}<i class="mb">{"朝食付き" if is_b(h["area"]) else "2食付き"}</i></span>{body}</div>'
            f'<div class="acts"><a class="cal" href="../hotels/{h["slug"]}/">神日カレンダー<span aria-hidden="true">›</span></a>'
            f'<a class="bk" href="{_plink(h["no"], m, days[0])}"{bk_attr(h["no"], datetime.date(m["y"], m["m"], days[0]))} target="_blank" rel="noopener sponsored">楽天トラベルで見る</a></div></li>')
def _picks(mi, lane="2", reg=None):
    m = months[mi]; k = f"{m['y']}-{m['m']:02d}"
    past = m["days"] if (m["y"], m["m"]) < (TODAY.year, TODAY.month) else (TODAY.day - 1 if (m["y"], m["m"]) == (TODAY.year, TODAY.month) else 0)
    nyr = lambda d: (m["m"] == 12 and d >= 29) or (m["m"] == 1 and d <= 3)
    rows = []
    for h in hotels:
        if bool(h.get("b")) != (lane == "b"): continue   # 2食付きと朝食付きは同じランキングに入れない
        if reg and REG_OF.get(h["area"]) != reg: continue   # 地方で絞る（2026/11/10）
        p = [0 if d < past else x for d, x in enumerate(h["p"].get(k, []))]
        vs = [p[d - 1] for d in range(1, m["days"] + 1) if p[d - 1] and not nyr(d)]
        if not vs: continue
        sat = [p[d - 1] for d in range(1, m["days"] + 1) if p[d - 1] and not nyr(d) and datetime.date(m["y"], m["m"], d).weekday() == 5]
        v = min(vs); days = [d for d in range(1, m["days"] + 1) if p[d - 1] == v and not nyr(d)]
        sa = sum(sat) / len(sat) if len(sat) >= 2 else 0
        gap = int(round((sa - v) / 10)) * 10 if sa else 0   # JSの Math.round とほぼ同じ（.5ちょうどはまず出ない）
        rows.append((h, v, days, gap))
    cheap = sorted(rows, key=lambda r: r[1])[:5]          # Pythonのsortも安定ソート＝JSと同じ順
    gapr = sorted([r for r in rows if r[3] > 0], key=lambda r: -r[3])[:5]
    return (f'{m["m"]}月泊で', "".join(_pcard(h, i, m, v, d, 0) for i, (h, v, d, g) in enumerate(cheap)),
            "".join(_pcard(h, i, m, v, d, g) for i, (h, v, d, g) in enumerate(gapr)))
# ---- TOP5は地方で絞る（全国だと各地のビジネスホテルが並びがち。2026/11/10）
#      はじめは「関東・伊豆」。ほかの地方は top-picks/r<番号>.json に分けて置き、タブを押したときだけ読む（トップを重くしない）
REG_OF = {a["key"]: a["region"] for a in LIVE}
REGIONS = list(L.REGIONS)   # 地方の並びは「エリアから探す」のタブと同じ（北から南へ）
DEF_REG = "関東・伊豆" if "関東・伊豆" in REGIONS else REGIONS[0]
pk_m, pk_cheap, pk_gap = _picks(DEF_MI, "2", DEF_REG)
# トップで使うのは「月×食事条件ごとのTOP5」だけ。全宿の料金（3.4MB）を送ってスマホで計算するのをやめ、
# ページを作るときに全部の組み合わせを作って埋める（数十KB）。表示の速さ（LCP）と、押したときの反応（INP）のため。2026/11/9
def _reg_picks(reg): return {f"{i}-{ln}": list(_picks(i, ln, reg)) for i in range(len(months)) for ln in ("2", "b")}
# トップに埋めるのは、はじめに見える「関東・伊豆 × いまの月」の分だけ（2026/11/12。ほかの月・地方は top-picks/ から読む）
_top_picks = {k: v for k, v in _reg_picks(DEF_REG).items() if k.startswith(f"{DEF_MI}-")}
os.makedirs(f"{OUT}/top-picks", exist_ok=True)
for _ri, _r in enumerate(["all"] + REGIONS):
    with open(f"{OUT}/top-picks/r{_ri}.json", "w", encoding="utf-8") as _f:
        json.dump(_reg_picks(None if _r == "all" else _r), _f, ensure_ascii=False, separators=(",", ":"))
pk_tabs = ('<div class="at-tabs pk-tabs" role="tablist" aria-label="地方で絞る">'
           + "".join(f'<button type="button" role="tab" aria-selected="{str(r == DEF_REG).lower()}" data-preg="{i}">{"全国" if r == "all" else esc(r)}</button>'
                     for i, r in enumerate(["all"] + REGIONS)) + "</div>")

# ---- いちばん上の写真（1枚・草津温泉 湯畑のライトアップ。2026/11/11）と、「今月の神日」の写真カード（★4.6以上の宿）
#      写真には文字を重ねない。スマホは900px、PCは1440px の WebP。いちばん大きく見える要素なので先に読み込む（LCP）
_CR = json.load(open(f"{OUT}/assets/img/credits.json", encoding="utf-8"))
_HF = "kusatsu-night-hero"
hero_html = (f'<figure class="hph"><img src="{base}assets/img/{_HF}-900.webp?v={img_v(_HF + "-900.webp")}" '
             f'srcset="{base}assets/img/{_HF}-900.webp?v={img_v(_HF + "-900.webp")} 900w, {base}assets/img/{_HF}-1440.webp?v={img_v(_HF + "-1440.webp")} 1440w" '
             f'sizes="100vw" width="1440" height="810" alt="ライトアップされた夜の草津温泉・湯畑" fetchpriority="high">'
             '<figcaption>草津温泉・湯畑のライトアップ</figcaption></figure>')
_c = _CR.get(_HF + "-1440.webp") or _CR.get("kusatsu-night-hero.jpg") or {}
hero_credit = f'上の写真：草津温泉・湯畑（{esc(_c.get("artist", ""))}・{esc(_c.get("license", ""))}）。出典：Wikimedia Commons（明るさ・色味を調整）'

def _kami(lane):
    """ハイクラスの宿（タグ「ハイクラス」と同じ基準）の、その月の神日。ふだんの料金（この先半年の中央値）との差も出す。1エリア1軒・8軒"""
    m = months[DEF_MI]; k = f"{m['y']}-{m['m']:02d}"; rows = []
    nyr = lambda d: (m["m"] == 12 and d >= 29) or (m["m"] == 1 and d <= 3)
    for h in hotels:
        if bool(h.get("b")) != (lane == "b") or h["avg"] < 4.6 or not is_hc(h["no"], h["area"]): continue
        p = h["p"].get(k, []); vs = [(x, d + 1) for d, x in enumerate(p) if x and not nyr(d + 1)]
        if not vs: continue
        v, d = min(vs); u = usual_price(h["no"])
        rows.append((h, v, d, (1 - v / u) if u else 0))
    rows.sort(key=lambda r: (-r[3], -r[0]["avg"]))
    seen = set(); out = []
    for r in rows:
        if r[0]["area"] in seen: continue
        seen.add(r[0]["area"]); out.append(r)
        if len(out) == 8: break
    li = "".join(
        f'<li><a href="{base}hotels/{h["slug"]}/"><img src="{esc(INFO[str(h["no"])].get("img") or h["thumb"])}" alt="" loading="lazy" decoding="async" width="400" height="500">'
        f'<span class="st">★{h["avg"]:.2f}</span>' + (f'<span class="off">ふだんより{round(g * 100)}%安い</span>' if g >= 0.05 else "") +
        f'<span class="c"><span class="ar">{esc(place_of(h))}</span><b class="nm">{esc(h["name"])}</b>'
        f'<span class="pr"><span class="tg">神日</span>{_lab(m, d)}<span class="v">¥{v:,}</span></span></span></a></li>' for h, v, d, g in out)
    return f'<ul class="km-row" data-lane="{lane}"{" hidden" if lane == "b" else ""}>{li}</ul>' if out else ""
_km = months[DEF_MI]
kami_html = (f'<section class="kmc" aria-labelledby="kmh"><h2 id="kmh"><small class="keb">★4.6以上の高級宿・旅館</small>ハイクラスの宿が、<span class="kw">安く泊まれる日</span></h2>'
             f'<p class="sub">憧れの宿も、{_km["m"]}月の神日（その月いちばん安い日）なら、ふだんよりこれだけ安く泊まれます。2名1泊・税込</p>'
             + _kami("2") + _kami("b") + f'<a class="kmore" href="{base}tags/hc/">ハイクラスの宿をもっと見る ›</a></section>')
TOP_JS = json.dumps(dict(months=months, areas=DATA["areas"], picks=_top_picks, preg=(["all"] + REGIONS).index(DEF_REG), regs=["全国"] + REGIONS), ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
if os.path.exists(f"{OUT}/top-data.json"): os.remove(f"{OUT}/top-data.json")   # 前の大きいファイルは消す

page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{TOP_T}</title>
<meta name="description" content="{TOP_D}">
<link rel="canonical" href="https://yasumibi.com/">
{og_meta(TOP_T, TOP_D, "")}
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..900&display=swap" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..900&display=swap"></noscript>
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2">
{site_header(base)}

<section class="hero hero-ph" id="search">
  {hero_html}
  <div class="gin">
    <div class="hcopy">
    <div class="shift"><div class="o"><small>これまで</small>休みの日に、安い宿を探す。</div><h1 class="n"><small>これから</small><b>安い日に、休みを合わせる。</b></h1></div>
    <p class="lead">口コミ★4.3以上の宿だけを、毎日の料金で比べて、月ごとにいちばん安い日（神日）を出しています。</p>
    <p class="kexp"><span class="star"><i aria-hidden="true">★</i>口コミ4.3以上の宿だけ</span><span class="kd"><b>神日</b>＝その月いちばん安い日</span></p>
    </div>
    <div class="sbox">
      {lane_html}
      <div class="stabs" role="tablist" aria-label="探し方">
        <button type="button" role="tab" id="t-free" aria-selected="true" aria-controls="p-search">日付はまだ決めていない</button>
        <button type="button" role="tab" id="t-date" aria-selected="false" aria-controls="p-search">日付が決まっている</button>
      </div>
      <form class="sform" id="p-search" role="tabpanel" aria-labelledby="t-free">
        <label class="fld"><span>エリア</span>
          <select id="f-area">{area_opts}</select></label>
        <label class="fld"><span>予算（2名1泊）</span>
          <select id="f-max">{max_opts}</select></label>
        <label class="fld" id="w-month"><span>泊まる月</span>
          <select id="f-month">{month_opts}</select></label>
        <label class="fld" id="w-date" hidden><span>泊まる日</span>
          <input type="date" id="f-date" min="{dmin}" max="{dmax}" value="{date_default}"></label>
        <label class="fld" id="w-range" hidden><span>前後の日も見る</span>
          <select id="f-range"><option value="0">この日だけ</option><option value="1">前後1日も見る</option><option value="3">前後3日も見る（記念日など）</option></select></label>
        <label class="fld" id="w-wd"><span>曜日・泊数</span>
          <select id="f-wd"><option value="all">こだわらない</option><option value="sat">土曜泊</option><option value="wk">日〜木泊</option><option value="n2">2泊する（合計が安い2日）</option></select></label>
        <label class="fld" id="w-ppl"><span>泊まる人数</span>
          <select id="f-ppl"><option value="1-0">大人1人</option><option value="2-0" selected>大人2人</option><option value="3-0">大人3人</option><option value="4-0">大人4人</option><option value="5-0">大人5人</option><option value="2-1">大人2＋子ども1</option><option value="2-2">大人2＋子ども2</option><option value="2-3">大人2＋子ども3</option><option value="1-1">大人1＋子ども1</option></select></label>
        <button type="submit" class="go" id="f-go">神日を探す</button>
        <p class="ppl-note" hidden></p>
        <div class="cands" id="w-cands" hidden><span class="cl">ほかに休めそうな日</span><div class="cl2" id="f-cands"></div><button type="button" class="cadd" id="f-add">＋日付を追加</button></div>
      </form>
      <form class="kw" id="kw" role="search" data-base="{base}" autocomplete="off">
        <label class="kw-f"><svg viewBox="0 0 24 24" fill="none" stroke-width="2" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-4-4"/></svg>
          <input type="search" id="kw-in" placeholder="宿の名前・地名・こだわりで探す" aria-label="宿の名前・地名・こだわりで探す" aria-controls="kw-dd" enterkeyhint="search"><button type="submit">探す</button></label>
        <div class="kw-dd" id="kw-dd" role="listbox" hidden></div>
      </form>
      {tag_html}
    </div>
    {kami_html}
  </div>
</section>

<main class="gin">


  <section class="areas" id="areas" aria-labelledby="ah">
    <div class="rhd"><h2 id="ah">エリアから探す</h2></div>
    {L.tiles_by_region(base)}
  </section>

  <section class="pick" aria-labelledby="pk1">
    <div class="rhd"><h2 id="pk1"><span class="pkl" id="pk-lane">食事付きの宿</span><span id="pk-m" class="pkm">{pk_m}</span>いちばん安い<span class="kw">神日</span></h2><span class="pkr"><span class="prt">PR</span><b class="top5">TOP5</b></span></div>
    {pk_tabs}
    <ol class="rlist" id="p-cheap">{pk_cheap}</ol>
  </section>
  <section class="fstrip" aria-labelledby="fsh">
    <div class="fs-hd rhd"><h2 id="fsh"><span class="fs-eb">特集</span>テーマから探す</h2><a href="{base}features/">すべて見る ›</a></div>
    <p class="fs-lead">連休・週末・予算など、テーマごとに神日をまとめました。</p>
    <div class="fs-wrap"><button type="button" class="fs-ar prev" aria-label="前へ" hidden>‹</button><ul class="fs-row" id="fs-row">{strip_html}</ul><button type="button" class="fs-ar next" aria-label="次へ">›</button></div>
  </section>

  <section class="pick" aria-labelledby="pk2">
    <div class="rhd"><h2 id="pk2">ずらすと、超お得に泊まれる宿</h2><span class="pkr"><span class="prt">PR</span><b class="top5">TOP5</b></span></div>
    <p class="rnote">土曜泊の平均と、その月の神日の差（<span id="pk-reg2">{esc(DEF_REG)}</span>）。</p>
    <ol class="rlist" id="p-gap">{pk_gap}</ol>
    <a class="pmore" id="pk-rank" href="{base}ranking/">ランキングをもっと見る ›</a>
  </section>
  <p class="cond">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上。ハイクラスの宿は20件以上・★4.6以上）の宿。{COND_PLAN}（2名合計・税込）。{ASOF}時点の楽天トラベルの料金。予約前に最新の料金をご確認ください。宿の写真：楽天トラベル。{hero_credit}</p>


</main>

{footer(base)}

{tabbar(base, "home")}
<script>window.TOP = {TOP_JS};</script>
<script src="{base}assets/top.js?v={v3}"></script>
<script src="{base}assets/kw.js?v={ver("kw.js")}" defer></script>
</body></html>
"""
open(f"{OUT}/index.html", "w", encoding="utf-8").write(page)
print("new top built", len(hotels))

# ---- 特集の一覧ページ（/features/）
base = "../"
fl = "".join(fcard(*f) for f in FEATURES)
_t = "特集一覧｜YASUMIBI"; _d = "神日（いちばん安い日）を、エリア・予算・連休・週末ごとにまとめた特集の一覧。口コミ★4.3以上の宿だけで、毎日更新しています。"
fpage = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{esc(_t)}</title>
<meta name="description" content="{esc(_d)}">
{og_meta(esc(_t), esc(_d), "features/")}<link rel="canonical" href="https://yasumibi.com/features/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..900&display=swap" media="print" onload="this.media='all'"><noscript><link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,400..900&display=swap"></noscript>
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2">
{site_header(base, "features")}
<main class="gin">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>特集一覧</span></nav>
  <section class="feats fpage" aria-labelledby="fh">
    <div class="rhd"><h1 id="fh">特集</h1><span>全{len(FEATURES)}本・毎日更新</span></div>
    <ul class="flist">{fl}</ul>
  </section>
</main>
{footer(base)}
{tabbar(base, "")}
</body></html>
"""
open(f"{OUT}/features/index.html", "w", encoding="utf-8").write(fpage)
print("features index", len(FEATURES))
