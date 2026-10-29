"""特集（/features/<slug>/）。エリアごとに切り口を変えた7本。料金データから毎日自動で作り直す。

 hakone-5man     同じ5万円で、いちばん良い宿。（予算固定 → ★の高い順）
 hakone-10man    10万円の宿が、手の届く日。（高級宿の値下がり幅）
 atami-5man      金曜の夜に、熱海へ。（金曜泊だけ）
 atami-10man     海が見える宿の、神日。（宿の紹介文・設備に海の眺めがある宿）
 kusatsu-winter  冬の草津、いちばん安い週。（12〜3月を週ごとに）
 yufuin-2haku    由布院、2泊するならこの2日。（連泊の合計がいちばん安い2日）
 beppu-1man      1人1万円台で泊まれる別府。（1人あたり2万円未満）
"""
import os, sys, json, html, hashlib, datetime as dt, statistics, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import img_v
from common import is_b, plan_s, plan_l, COND_PLAN, usual_price, is_hc, HC_MIN
from common import site_header, tabbar, footer, og_meta, OUT, DATA, AREA_JA, HOTELS, PRH, ASOF, TODAY, WINDOW_START, WINDOW_END, KY, KM

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
DET = {}; MEAL = {}; ROOMS = {}; FAC = {}
# 新しく足した宿は、候補調査の表（食事の評価・客室数）から補う
for _fn in sorted(os.listdir(f"{DATA}/candidates")) if os.path.isdir(f"{DATA}/candidates") else []:
    if not _fn.endswith(".tsv"): continue
    for _ln in open(f"{DATA}/candidates/{_fn}", encoding="utf-8"):
        _c = _ln.rstrip("\n").split("\t")
        if len(_c) >= 8 and _c[1].isdigit():
            try:
                if float(_c[5]): MEAL[int(_c[1])] = float(_c[5])
                if int(_c[7] or 0): ROOMS[int(_c[1])] = int(_c[7])
            except Exception: pass
for ln in open(f"{DATA}/hotel_detail_20261021.tsv", encoding="utf-8"):
    c = ln.rstrip("\n").split("\t")
    if len(c) >= 10:
        DET[int(c[0])] = c[7] + " " + c[9]; FAC[int(c[0])] = c[9]
        try: MEAL[int(c[0])] = float(c[3].split(",")[5])
        except Exception: pass
        try: ROOMS[int(c[0])] = int(c[6] or 0)
        except Exception: pass
try: CREDITS = json.load(open(f"{OUT}/assets/img/credits.json"))
except Exception: CREDITS = {}
WD = "月火水木金土日"
H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}
built = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(int(v))
def lab(d): return f"{d.month}/{d.day}({WD[d.weekday()]})"
def nyr(d): return (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def nights(no):
    """これから先の、料金のある夜 [(date, price)]。年末年始は除く。"""
    src = PRH.get(str(no), {}); out = []
    d = max(TODAY + dt.timedelta(days=1), WINDOW_START)
    while d <= WINDOW_END:
        v = src.get(d.isoformat())
        if v and not nyr(d): out.append((d, int(v)))
        d += dt.timedelta(days=1)
    return out


def rk_link(no, d, n=1):
    e = d + dt.timedelta(days=n)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={d.year}&f_tuki1={d.month}&f_hi1={d.day}"
         f"&f_nen2={e.year}&f_tuki2={e.month}&f_hi2={e.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


def item(i, no, big, small, sub, d, n=1):
    h = H[no]; info = INFO[str(no)]
    hp = f"../../hotels/{h['slug']}/" if h["slug"] in built else None
    name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
    return f"""<li class="ri">
  <span class="rk">{i}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{esc(h.get('loc',''))}｜★{h.get('avg',0):.2f}（{h.get('cnt',0):,}件）</span>
    <div class="rv"><b>{big}</b><span>{small}</span></div>
    <div class="rk2">{sub}</div>
  </div>
  <a class="rgo" href="{esc(rk_link(no, d, n))}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a>
</li>"""


def ol(items, n=5):
    if not items: return '<p class="rlead">条件に合う宿が、いまの料金データでは見つかりませんでした。毎日更新しています。</p>'
    more = ""
    if len(items) > n:
        more = f'<details class="rmore"><summary>{n + 1}位から見る</summary><ol class="rl">{"".join(items[n:n + 10])}</ol></details>'
    return f'<ol class="rl">{"".join(items[:n])}</ol>{more}'


def bars(rows, fmt=yen):
    """rows: [(label, value, note)]"""
    if len(rows) < 2: return ""
    lo, hi = min(r[1] for r in rows), max(r[1] for r in rows)
    out = ""
    for lb, v, note in rows:
        w = 30 + 70 * (v - lo) / (hi - lo) if hi > lo else 60
        cls = " lo" if v == lo else (" hi" if v == hi else "")
        out += f'<li class="w{cls}"><span class="wm">{esc(lb)}</span><span class="wb"><i style="width:{w:.0f}%"></i></span><b>{fmt(v)}</b></li>'
    return f'<ul class="wl">{out}</ul>'


def cover(img):
    if not img or not os.path.exists(f"{OUT}/assets/img/{img}"): return ""
    c = CREDITS.get(img)
    cr = f'<span class="cv-cr">写真：{esc(c["artist"] or "Wikimedia Commons")}（{esc(c["license"])}・Wikimedia Commons{"・" + esc(c["edit"]) if c.get("edit") else ""}）</span>' if c else ""
    return f'<figure class="cv"><img src="../../assets/img/{img}?v={img_v(img)}" alt="" width="960" height="540">{cr}</figure>'


def page(slug, area, img, eyebrow, h1, lead, body, note, place=None, place_href=None):
    base = "../../"
    v = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css")
    place = place or AREA_JA[area]; place_href = place_href or f"areas/{area}/"
    title = f"{h1.rstrip('。')}｜{place}の特集｜YASUMIBI"
    desc = f"{lead} ★4.3以上の宿だけを、楽天トラベルの料金で毎日調べています。"
    crumb = (f'<a href="{base}">ホーム</a><span aria-hidden="true">›</span><a href="{base}{place_href}">{esc(place)}</a>'
             f'<span aria-hidden="true">›</span><span>特集</span>')
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{og_meta(esc(title), esc(desc), f"features/{slug}/")}<link rel="canonical" href="https://yasumibi.com/features/{slug}/">
<link rel="stylesheet" href="{base}assets/site.css?v={v[0]}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v[1]}">
<link rel="stylesheet" href="{base}assets/top.css?v={v[2]}">
<link rel="stylesheet" href="{base}assets/otoku.css?v={v[2]}">
<link rel="stylesheet" href="{base}assets/rank.css?v={v[2]}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 otk">
{site_header(base, "features")}
<main class="gin ok rkp sp">
  <nav class="crumb" aria-label="現在地">{crumb}</nav>
  {cover(img)}
  <header class="ok-hd"><p class="sp-eb">特集｜{esc(eyebrow)}</p><h1>{esc(h1)}</h1><p>{lead}</p></header>
  {body}
  <a class="c-apply" href="{base}{place_href}">{esc(place)}のほかのランキングを見る</a>
  <p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上。ハイクラスの宿は20件以上・★4.6以上）の宿。{note}大人2名・1室・{plan_l(area)}の最安プラン（2名合計・税込）。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。年末年始（12/29〜1/3）は除いています。宿の写真：楽天トラベル</p>
</main>
""" + footer(base) + tabbar(base, "") + "</body></html>\n"


def sec(title, lead, inner, quip=""):
    q = f'<p class="quip">{quip}</p>' if quip else ""
    cls = "rsec when" if 'class="wl"' in inner else "rsec"
    return f'<section class="{cls}"><h2>{title}</h2><p class="rlead">{lead}</p>{q}{inner}</section>'


def area_nos(a): return [no for no, h in H.items() if h["area"] == a]


def write(slug, s):
    os.makedirs(f"{OUT}/features/{slug}", exist_ok=True)
    open(f"{OUT}/features/{slug}/index.html", "w", encoding="utf-8").write(s)


made = []

# 1. 箱根・同じ5万円で、いちばん良い宿
rows = []
for no in area_nos("hakone"):
    ns = [x for x in nights(no) if 40000 <= x[1] <= 55000]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0]))
        rows.append((H[no]["avg"], H[no]["cnt"], no, d, v, len(ns)))
rows.sort(key=lambda r: (-r[0], -r[1]))
its = [item(i + 1, no, f"★{a:.2f}", f"5万円台で泊まれる日 {k}日", f"いちばん安い日 {lab(d)} <b>{yen(v)}</b>", d) for i, (a, c, no, d, v, k) in enumerate(rows)]
q = f"1位の{esc(H[rows[0][2]]['name'])}は★{rows[0][0]:.2f}。5万円でこの★、ちょっと反則。" if rows else ""
write("hakone-5man", page("hakone-5man", "hakone", "hakone-fuji-ship.jpg", "箱根・2人で5万円",
      "同じ5万円で、いちばん良い宿。", "予算は2人で4〜5.5万円に固定。その中で、口コミの★がいちばん高い宿から並べました。",
      sec("★の高い順", "この先の半年で、2人4〜5.5万円の日がある宿だけ。", ol(its), q), "期間はこの先の半年。"))
made.append("hakone-5man")

# 2. 箱根・10万円の宿が、手の届く日
rows = []
for no in area_nos("hakone"):
    ns = nights(no)
    if len(ns) < 10: continue
    hi = max(ns, key=lambda x: x[1]); lo = min(ns, key=lambda x: (x[1], x[0]))
    if hi[1] >= 90000 and hi[1] > lo[1]:
        rows.append((1 - lo[1] / hi[1], no, hi, lo))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, f"−{p * 100:.0f}%", f"{lab(hi[0])} {yen(hi[1])} → 神日", f"神日 {lab(lo[0])} <b>{yen(lo[1])}</b>（{hi[1] - lo[1]:,}円安い）", lo[0])
       for i, (p, no, hi, lo) in enumerate(rows)]
q = (f"1位の{esc(H[rows[0][1]]['name'])}は、同じ宿なのに{rows[0][2][1] - rows[0][3][1]:,}円の差。差額で、もう1泊できるかもしれない。" if rows else "")
write("hakone-10man", page("hakone-10man", "hakone", "hakone-torii.jpg", "箱根・2人で10万円の宿",
      "10万円の宿が、手の届く日。", "いちばん高い日が2人で9万円を超える宿だけ。その宿がいちばん下がる日と、下がり幅を並べました。",
      sec("値下がり幅の大きい順", "この先の半年で、いちばん高い日と神日の差。", ol(its), q), "期間はこの先の半年。"))
made.append("hakone-10man")

# 3. 熱海・金曜の夜に、熱海へ。
fri = {}
rows = []
for no in area_nos("atami"):
    ns = [x for x in nights(no) if x[0].weekday() == 4]
    for d, v in ns: fri.setdefault(d, []).append(v)
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0]))
        sat = [x[1] for x in nights(no) if x[0].weekday() == 5]
        rows.append((v, no, d, round(statistics.mean(sat)) if sat else 0))
rows.sort(key=lambda r: r[0])
fr = [(lab(d), statistics.median(v), "") for d, v in sorted(fri.items()) if len(v) >= 5][:12]
its = [item(i + 1, no, yen(v), f"いちばん安い金曜 {lab(d)}", (f"土曜泊の平均より <b>−{sa - v:,}円</b>" if sa > v else "土曜とほぼ同じ"), d)
       for i, (v, no, d, sa) in enumerate(rows)]
best = min(fr, key=lambda r: r[1]) if fr else None
body = ""
if fr: body += sec("安い金曜は、いつ？", f"熱海の宿の金曜泊・料金の中央値。いちばん安いのは<b>{best[0]}</b>。", bars(fr))
body += sec("金曜泊が安い宿", "仕事終わりに出発して、土曜はゆっくり。金曜泊がいちばん安い日を宿ごとに。", ol(its),
            f"1位は{esc(H[rows[0][1]]['name'])}。金曜の夜に、{yen(rows[0][0])}で温泉。" if rows else "")
write("atami-5man", page("atami-5man", "atami", "atami-panorama.jpg", "熱海・金曜泊", "金曜の夜に、熱海へ。",
      "東京から新幹線で約40分。仕事のあとに行ける熱海で、金曜泊がいちばん安い日を探しました。", body, "金曜泊のみ。"))
made.append("atami-5man")

# 4. 熱海・海が見える宿の、神日。
SEA = ("オーシャンビュー", "海一望", "海を一望", "海が見え", "海を望", "相模湾", "海を見渡", "全室オーシャン", "海側", "海の見える", "初島")
rows = []
for no in area_nos("atami"):
    t = DET.get(no, "")
    if not any(k in t for k in SEA): continue
    ns = [x for x in nights(no) if x[0].year == KY and x[0].month == KM] or nights(no)
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0]))
        rows.append((H[no]["avg"], no, d, v))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, yen(v), f"{KM}月の神日 {lab(d)}", f"★{a:.2f}・宿の紹介文に海の眺め", d) for i, (a, no, d, v) in enumerate(rows)]
write("atami-10man", page("atami-10man", "atami", "atami-panorama.jpg", "熱海・ご褒美の一泊", "海が見える宿の、神日。",
      f"宿の紹介文や設備に「オーシャンビュー」「相模湾一望」などの言葉がある宿だけ。★の高い順に、{KM}月の神日を並べました。",
      sec("★の高い順", "特別な一泊こそ、安い日に。", ol(its, 6), f"{len(rows)}軒、どれも海の見える宿。神日なら、ご褒美の値段が少しやさしくなる。" if rows else ""),
      "「海が見える」は楽天トラベルの宿の紹介文・設備情報をもとにしています。部屋によって眺めは異なります。"))
made.append("atami-10man")

# 5. 草津・冬の草津、いちばん安い週。
weeks = {}
per = {}
for no in area_nos("kusatsu"):
    for d, v in nights(no):
        if d.month in (12, 1, 2, 3):
            wk = d - dt.timedelta(days=d.weekday())
            weeks.setdefault(wk, {}).setdefault(no, []).append(v)
wr = []
for wk in sorted(weeks):
    mins = [min(v) for v in weeks[wk].values()]
    if len(mins) >= 5: wr.append((wk, statistics.median(mins)))
body = ""
if wr:
    bw = min(wr, key=lambda r: r[1])[0]
    body += sec("週ごとの料金", f"12〜3月、週ごとに各宿のいちばん安い夜の中央値。いちばん安いのは<b>{bw.month}/{bw.day}からの週</b>。",
                bars([(f"{w.month}/{w.day}〜", v, "") for w, v in wr]))
    rows = []
    for no, vs in weeks[bw].items():
        ds = [(d, v) for d, v in nights(no) if bw <= d < bw + dt.timedelta(days=7)]
        if ds:
            d, v = min(ds, key=lambda x: (x[1], x[0])); rows.append((v, no, d))
    rows.sort()
    its = [item(i + 1, no, yen(v), f"{bw.month}/{bw.day}からの週の神日 {lab(d)}", f"★{H[no]['avg']:.2f}", d) for i, (v, no, d) in enumerate(rows)]
    body += sec("その週に泊まるなら", "いちばん安い週の、宿ごとの神日。", ol(its), "雪見の湯畑は、安い週でも同じ景色。")
write("kusatsu-winter", page("kusatsu-winter", "kusatsu", "kusatsu-yubatake.jpg", "草津・冬", "冬の草津、いちばん安い週。",
      "雪の湯畑を見に行くなら、どの週がいちばん安い？ 12〜3月を週ごとに比べました。", body, "12〜3月のうち、料金データのある期間。"))
made.append("kusatsu-winter")

# 6. 由布院・2泊するならこの2日。
rows = []
for no in area_nos("yufuin"):
    ns = dict(nights(no)); best = None; frisat = None
    for d, v in ns.items():
        n2 = ns.get(d + dt.timedelta(days=1))
        if not n2: continue
        tot = v + n2
        if best is None or tot < best[0]: best = (tot, d)
        if d.weekday() == 4 and (frisat is None or tot < frisat): frisat = tot
    if best: rows.append((best[0], no, best[1], frisat))
rows.sort()
its = [item(i + 1, no, yen(t), f"{lab(d)}〜2泊（2名合計）", (f"金・土の2泊より <b>−{fs - t:,}円</b>" if fs and fs > t else f"★{H[no]['avg']:.2f}"), d, 2)
       for i, (t, no, d, fs) in enumerate(rows)]
q = ""
if rows and rows[0][3] and rows[0][3] > rows[0][0]:
    q = f"1位の{esc(H[rows[0][1]]['name'])}は、金土の2泊と比べて{rows[0][3] - rows[0][0]:,}円安い。浮いたお金で、湯の坪街道を食べ歩き。"
write("yufuin-2haku", page("yufuin-2haku", "yufuin", "yufuin-kinrinko-sunny.jpg", "由布院・連泊", "由布院、2泊するならこの2日。",
      "せっかくの由布院は、ゆっくり2泊。2泊の合計がいちばん安くなる2日を、宿ごとに探しました。",
      sec("2泊の合計が安い順", "続けて2泊できる日だけで計算しています。", ol(its), q), "2泊とも同じ最安プランで計算した目安です（実際は連泊プランで変わることがあります）。"))
made.append("yufuin-2haku")

# 7. 別府・1人1万円台で泊まれる別府。
rows = []
for no in area_nos("beppu"):
    ns = [x for x in nights(no) if x[1] < 40000]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d, len(ns)))
rows.sort()
its = [item(i + 1, no, f"1人 {yen(v // 2)}", f"2名合計 {yen(v)}・{lab(d)}", f"1人2万円未満の日 {k}日・★{H[no]['avg']:.2f}", d) for i, (v, no, d, k) in enumerate(rows)]
write("beppu-1man", page("beppu-1man", "beppu", "beppu-chinoike.jpg", "別府・1人1万円台", "1人1万円台で泊まれる別府。",
      "★4.3以上で、2食付き。それでも1人2万円を切る日がある宿を、安い順に並べました。",
      sec("1人あたりが安い順", f"{len(rows)}軒が、1人1万円台の日あり。", ol(its, 8), "温泉の湧出量は日本一。宿代は、日本一じゃなくていい。"), "1人あたり＝2名合計÷2。"))
made.append("beppu-1man")

# 8. 鬼怒川・平日1泊、いちばん安い鬼怒川。
import jp_holidays
def rest(d): return d.weekday() >= 5 or bool(jp_holidays.name(d)) or nyr(d)
wd = {}
rows = []
for no in area_nos("kinugawa"):
    ns = [x for x in nights(no) if x[0].weekday() in (6, 0, 1, 2, 3)]
    for d, v in ns: wd.setdefault(WD[d.weekday()], []).append(v)
    sat = [x[1] for x in nights(no) if x[0].weekday() == 5]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0]))
        rows.append((v, no, d, round(statistics.mean(sat)) if sat else 0))
rows.sort()
body = ""
wr = [(f"{k}曜泊", statistics.median(wd[k]), "") for k in "日月火水木" if len(wd.get(k, [])) >= 5]
if wr:
    bk = min(wr, key=lambda r: r[1])
    body += sec("何曜日に泊まると安い？", f"鬼怒川の宿の、日〜木泊の料金の中央値。いちばん安いのは<b>{bk[0]}</b>。", bars(wr))
its = [item(i + 1, no, yen(v), f"平日の神日 {lab(d)}", (f"土曜泊の平均より <b>−{sa - v:,}円</b>" if sa > v else f"★{H[no]['avg']:.2f}"), d) for i, (v, no, d, sa) in enumerate(rows)]
body += sec("平日に泊まるなら、この宿・この日", "日〜木泊だけで、宿ごとにいちばん安い日。", ol(its),
            f"1位の{esc(H[rows[0][1]]['name'])}は、平日なら{yen(rows[0][0])}。東京から特急で約2時間、休みを1日取る価値はある。" if rows else "")
write("kinugawa-heijitsu", page("kinugawa-heijitsu", "kinugawa", "kinugawa-cover.jpg", "鬼怒川・平日", "平日1泊、いちばん安い鬼怒川。",
      "週末は混む鬼怒川も、平日はぐっと安くなる。日曜〜木曜の夜だけで、いちばん安い日を探しました。", body, "日〜木泊のみ。"))
made.append("kinugawa-heijitsu")

# 9. 下呂・ごはんの★が高い宿の、神日。
rows = []
for no in area_nos("gero"):
    ns = nights(no)
    if ns and MEAL.get(no):
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((MEAL[no], no, d, v))
rows.sort(key=lambda r: (-r[0], r[3]))
its = [item(i + 1, no, f"食事 ★{m:.2f}", f"神日 {lab(d)}", f"<b>{yen(v)}</b>・総合★{H[no]['avg']:.2f}", d) for i, (m, no, d, v) in enumerate(rows)]
write("gero-gohan", page("gero-gohan", "gero", "gero-cover.jpg", "下呂・ごはん", "ごはんの★が高い宿の、神日。",
      "飛騨牛の宿が多い下呂。楽天トラベルの口コミで「食事」の評価が高い順に、それぞれの神日を並べました。",
      sec("食事の評価が高い順", "口コミの「食事」の点数（5点満点）。", ol(its, 6),
          f"1位の{esc(H[rows[0][1]]['name'])}は、食事★{rows[0][0]:.2f}。神日なら{yen(rows[0][3])}で、このごはん。" if rows else ""),
      "食事の評価は楽天トラベルの口コミの「食事」の平均点です。"))
made.append("gero-gohan")

# 10. 登別・大きな宿ほど、安い？
rows = []
for no in area_nos("noboribetsu"):
    ns = nights(no)
    if ns and ROOMS.get(no):
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((ROOMS[no], no, d, v))
rows.sort(key=lambda r: -r[0])
body = ""
if len(rows) >= 4:
    big = [r[3] for r in rows if r[0] >= 100]; small = [r[3] for r in rows if r[0] < 100]
    if big and small:
        mb, ms = statistics.median(big), statistics.median(small)
        gap = abs(mb - ms) / max(mb, ms)
        ans = ("ほとんど変わらない" if gap < 0.05 else ("大きな宿のほうが安い" if mb < ms else "小さな宿のほうが安い"))
        body += sec("答え：" + ans, f"客室100室以上の宿{len(big)}軒と、100室未満の宿{len(small)}軒の、神日の料金の中央値。差は{abs(mb - ms):,.0f}円。",
                    bars([("100室以上", mb, ""), ("100室未満", ms, "")]))
its = [item(i + 1, no, f"{r}室", f"神日 {lab(d)}", f"<b>{yen(v)}</b>・★{H[no]['avg']:.2f}", d) for i, (r, no, d, v) in enumerate(rows)]
body += sec("客室数の多い順", "宿の大きさと、それぞれの神日。", ol(its, 9), "大きな宿は大浴場が広く、小さな宿は静か。値段だけで決めなくていい。")
write("noboribetsu-size", page("noboribetsu-size", "noboribetsu", "noboribetsu-jigokudani-day.jpg", "登別・宿の大きさ", "大きな宿ほど、安い？",
      "地獄谷の湯けむりの町、登別。客室の数と神日の料金に関係があるのか、★4.3以上の宿で比べました。宿の数が少ないので、傾向の目安です。", body, "客室数は楽天トラベルの施設情報です。"))
made.append("noboribetsu-size")

# 11. 有馬・連休でも安い日。
def in_long(d):
    """d泊が、3日以上続く休み（土日・祝日）の中の夜か。"""
    if not (rest(d) and rest(d + dt.timedelta(days=1))): return None
    a = b = d
    while rest(a - dt.timedelta(days=1)): a -= dt.timedelta(days=1)
    while rest(b + dt.timedelta(days=1)): b += dt.timedelta(days=1)
    return (a, b) if (b - a).days >= 2 else None
blocks = {}
rows = []
for no in area_nos("arima"):
    best = None
    for d, v in nights(no):
        bl = in_long(d)
        if not bl: continue
        blocks.setdefault(bl, []).append(v)
        if best is None or v < best[1]: best = (d, v, bl)
    if best: rows.append((best[1], no, best[0], best[2]))
rows.sort()
body = ""
br = [(f"{a.month}/{a.day}〜{b.month}/{b.day}", statistics.median(v), "") for (a, b), v in sorted(blocks.items()) if len(v) >= 5]
if br:
    bb = min(br, key=lambda r: r[1])
    body += sec("いちばん安い連休は？", f"この先の連休ごとに、有馬の宿の料金の中央値。いちばん安いのは<b>{bb[0]}</b>の連休。", bars(br))
its = [item(i + 1, no, yen(v), f"連休中の神日 {lab(d)}", f"{a.month}/{a.day}〜{b.month}/{b.day}の連休・★{H[no]['avg']:.2f}", d) for i, (v, no, d, (a, b)) in enumerate(rows)]
body += sec("連休でも安い宿", "3日以上続く休みの中の夜だけで、宿ごとにいちばん安い日。", ol(its),
            f"1位の{esc(H[rows[0][1]]['name'])}は、連休中でも{yen(rows[0][0])}。金泉・銀泉は、連休でも逃げない。" if rows else "")
write("arima-renkyu", page("arima-renkyu", "arima", "arima-view.jpg", "有馬・連休", "有馬、連休でも安い日。",
      "連休はどこも高い。それでも、有馬には連休中に安くなる夜がある。3連休以上の夜だけで、いちばん安い日を探しました。", body,
      "連休＝土日・祝日が3日以上続く休み。年末年始は除きます。"))
made.append("arima-renkyu")

# ---- 京都・沖縄・札幌（1泊朝食付きで比べるエリア）
def month_min(no, y, m):
    v = [p for d, p in nights(no) if d.year == y and d.month == m]
    return (min(v), [d for d, p in nights(no) if d.year == y and d.month == m and p == min(v)][0]) if v else (0, None)


def med_by_month(nos):
    out = []
    for y, m in sorted({(d.year, d.month) for no in nos for d, _ in nights(no)}):
        # 料金を取れている日が少ない月（先の月は数日おきにしか取らない）は、宿ごとの最安が高めに出るので数えない
        mins = [month_min(no, y, m)[0] for no in nos if sum(1 for d, _ in nights(no) if d.year == y and d.month == m) >= 8]
        mins = [x for x in mins if x]
        if len(mins) >= 5: out.append((y, m, statistics.median(mins)))
    return out


# 12. 京都・紅葉の11月と、1月。
KYO = area_nos("kyoto")
mm = med_by_month(KYO)
body = ""
if mm:
    lo = min(mm, key=lambda r: r[2]); hi = max(mm, key=lambda r: r[2])
    body += sec("月ごとの料金", f"京都の宿の、月ごとの神日の中央値。いちばん安いのは<b>{lo[1]}月</b>、いちばん高いのは<b>{hi[1]}月</b>。",
                bars([(f"{m}月", v, "") for y, m, v in mm]))
rows = []
ny = TODAY.year if TODAY.month <= 11 else TODAY.year + 1
for no in KYO:
    a, da = month_min(no, ny, 11); b, db = month_min(no, ny + 1, 1)
    if a and b and a > b: rows.append((a - b, no, a, b, db))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, f"−{g:,}円", f"11月の神日 {yen(a)} → 1月", f"1月の神日 {lab(db)} <b>{yen(b)}</b>", db) for i, (g, no, a, b, db) in enumerate(rows)]
body += sec("11月と1月で、差が大きい宿", "同じ宿の、11月の神日と1月の神日の差。", ol(its),
            f"1位の{esc(H[rows[0][1]]['name'])}は、1月にずらすだけで{rows[0][0]:,}円。紅葉はないけれど、差額で京料理がもう一軒。" if rows else "")
write("kyoto-koyo", page("kyoto-koyo", "kyoto", "kyoto-kiyomizu-autumn.jpg", "京都・紅葉と冬", "紅葉の11月と、1月。同じ宿でいくら違う？",
      "京都がいちばん高いのは紅葉の11月。同じ宿に1月に泊まると、いくら安くなるのかを比べました。", body,
      "11月は残りの日、1月は料金を取れている日で比べた目安です。"))
made.append("kyoto-koyo")

# 13. 京都・朝ごはんの★が高い宿。
rows = []
for no in KYO:
    ns = nights(no)
    if ns and MEAL.get(no):
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((MEAL[no], no, d, v))
rows.sort(key=lambda r: (-r[0], r[3]))
its = [item(i + 1, no, f"食事 ★{m:.2f}", f"神日 {lab(d)}", f"<b>{yen(v)}</b>（2名1泊朝食）・総合★{H[no]['avg']:.2f}", d) for i, (m, no, d, v) in enumerate(rows)]
write("kyoto-asagohan", page("kyoto-asagohan", "kyoto", "kyoto-inari.jpg", "京都・朝ごはん", "朝ごはんで選ぶ、京都の宿。",
      "京都の宿は朝食付きで比べています。だから朝ごはんの評価は大事。楽天トラベルの口コミで「食事」の評価が高い順に、それぞれの神日を並べました。",
      sec("食事の評価が高い順", "口コミの「食事」の点数（5点満点）。", ol(its, 8),
          f"1位の{esc(H[rows[0][1]]['name'])}は、食事★{rows[0][0]:.2f}。神日なら2人で{yen(rows[0][3])}。" if rows else ""),
      "食事の評価は楽天トラベルの口コミの「食事」の平均点です（朝食・夕食を含む宿全体の評価）。"))
made.append("kyoto-asagohan")

# 14. 京都・★4.6以上で、1人1万円台。
rows = []
for no in KYO:
    if H[no]["avg"] < 4.6: continue
    ns = [x for x in nights(no) if x[1] < 40000]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d, len(ns)))
rows.sort()
its = [item(i + 1, no, f"1人 {yen(v // 2)}", f"2名合計 {yen(v)}・{lab(d)}", f"★{H[no]['avg']:.2f}・1人2万円未満の日 {k}日", d) for i, (v, no, d, k) in enumerate(rows)]
write("kyoto-46", page("kyoto-46", "kyoto", "kyoto-inari.jpg", "京都・★4.6以上", "★4.6以上の京都の宿に、1人1万円台で。",
      "口コミ★4.6以上は、京都でもひと握り。その中で、1人2万円を切る日がある宿を安い順に並べました。",
      sec("1人あたりが安い順", f"{len(rows)}軒に、1人1万円台の日があります。", ol(its, 8), f"★4.6以上は、京都の★4.3以上の宿{len(KYO)}軒のうち{sum(1 for no in KYO if H[no]['avg'] >= 4.6)}軒だけ。" if rows else ""),
      "1人あたり＝2名合計÷2。"))
made.append("kyoto-46")

# 15. 沖縄・いちばん安い月は？
OKI = ["naha", "onna", "chatan", "miyako", "ishigaki"]
ONOS = [no for a in OKI for no in area_nos(a)]
mm = med_by_month(ONOS)
body = ""
if mm:
    lo = min(mm, key=lambda r: r[2]); hi = max(mm, key=lambda r: r[2])
    body += sec("月ごとの料金", f"沖縄の宿（那覇・恩納・北谷・宮古島・石垣）の、月ごとの神日の中央値。いちばん安いのは<b>{lo[1]}月</b>。",
                bars([(f"{m}月", v, "") for y, m, v in mm]))
    rows = []
    for no in ONOS:
        a, da = month_min(no, hi[0], hi[1]); b, db = month_min(no, lo[0], lo[1])
        if a and b and a > b: rows.append((a - b, no, a, b, db))
    rows.sort(key=lambda r: -r[0])
    its = [item(i + 1, no, f"−{g:,}円", f"{hi[1]}月の神日 {yen(a)} → {lo[1]}月", f"{AREA_JA[H[no]['area']]}・{lo[1]}月の神日 {lab(db)} <b>{yen(b)}</b>", db) for i, (g, no, a, b, db) in enumerate(rows)]
    body += sec(f"{lo[1]}月にずらすと、いくら安い？", f"同じ宿の、{hi[1]}月と{lo[1]}月の神日の差。", ol(its),
                f"1位の{esc(H[rows[0][1]]['name'])}は、{lo[1]}月にずらすだけで{rows[0][0]:,}円。" if rows else "")
write("okinawa-month", page("okinawa-month", "naha", "ishigaki-bay.jpg", "沖縄・時期", "沖縄、いちばん安い月は？",
      "海に入るなら夏。でも、宿がいちばん安いのはいつ？ この先半年の料金で、月ごとに比べました。", body,
      "この先半年の料金で比べています（夏の料金は含みません）。", place="沖縄", place_href="areas/naha/"))
made.append("okinawa-month")

# 16. 沖縄・離島と本島、神日で比べると。
body = ""
ar = []
for a in OKI:
    ks = [min(nights(no), key=lambda x: x[1])[1] for no in area_nos(a) if nights(no)]
    if len(ks) >= 5: ar.append((AREA_JA[a], statistics.median(ks), ""))
if ar: body += sec("エリアごとの神日", "エリアごとの、宿の神日（この先半年でいちばん安い日）の中央値。", bars(ar))
rows = []
for a in ("miyako", "ishigaki"):
    for no in area_nos(a):
        ns = nights(no)
        if ns:
            d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d))
rows.sort()
its = [item(i + 1, no, yen(v), f"{AREA_JA[H[no]['area']]}・神日 {lab(d)}", f"★{H[no]['avg']:.2f}", d) for i, (v, no, d) in enumerate(rows)]
q = ""
if ar:
    isl = [r for r in ar if r[0] in (AREA_JA["miyako"], AREA_JA["ishigaki"])]; main = [r for r in ar if r not in isl]
    if isl and main:
        ai = statistics.mean(r[1] for r in isl); am = statistics.mean(r[1] for r in main)
        q = (f"離島の神日は、本島より平均{ai - am:,.0f}円高い。飛行機代とあわせて考えたい。" if ai > am else f"離島の神日は、本島より平均{am - ai:,.0f}円安い。意外。")
body += sec("離島（宮古島・石垣）の神日が安い宿", "★4.3以上の離島の宿を、神日の安い順に。", ol(its, 8), q)
write("okinawa-ritou", page("okinawa-ritou", "ishigaki", "ishigaki-kabira.jpg", "沖縄・離島と本島", "離島と本島、神日で比べると。",
      "宮古島・石垣の離島と、那覇・恩納・北谷の本島。宿がいちばん安い日の料金で比べました。", body,
      "航空券は含みません。", place="沖縄", place_href="areas/ishigaki/"))
made.append("okinawa-ritou")

# 17. 札幌・雪まつりの週と、前後の週。（2027年2月4日〜11日・公式発表）
YK = (dt.date(2027, 2, 4), dt.date(2027, 2, 10))
SP = area_nos("sapporo")
wk = [("前の週", dt.date(2027, 1, 28), dt.date(2027, 2, 3)), ("雪まつり", YK[0], YK[1]),
      ("あとの週", dt.date(2027, 2, 12), dt.date(2027, 2, 18))]
body = ""
br = []
for lb, a, b in wk:
    vs = [min([p for d, p in nights(no) if a <= d <= b] or [0]) for no in SP]; vs = [x for x in vs if x]
    if len(vs) >= 5: br.append((lb, statistics.median(vs), ""))
if len(br) == 3:
    body += sec("週ごとの料金", "札幌の宿の、その週でいちばん安い夜の中央値。前の週＝1/28〜2/3泊、雪まつり＝2/4〜2/10泊、あとの週＝2/12〜2/18泊。", bars(br),
                f"雪まつりの週は、前の週より{br[1][1] - br[0][1]:,.0f}円{'高い' if br[1][1] > br[0][1] else '安い'}。")
rows = []
for no in SP:
    ns = nights(no)
    aft = [x for x in ns if wk[2][1] <= x[0] <= wk[2][2]] + [x for x in ns if wk[0][1] <= x[0] <= wk[0][2]]
    dur = [x for x in ns if YK[0] <= x[0] <= YK[1]]
    if aft and dur:
        d, v = min(aft, key=lambda x: (x[1], x[0])); dv = min(x[1] for x in dur)
        rows.append((dv - v, no, d, v, dv))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, (f"−{g:,}円" if g > 0 else "ほぼ同じ"), f"雪まつり中 {yen(dv)} → 前後の週", f"前後の週の神日 {lab(d)} <b>{yen(v)}</b>", d) for i, (g, no, d, v, dv) in enumerate(rows)]
body += sec("前後の週にずらすと、安くなる宿", "同じ宿の、雪まつり期間中のいちばん安い夜と、前後の週のいちばん安い夜の差。", ol(its),
            "")
write("sapporo-yukimatsuri", page("sapporo-yukimatsuri", "sapporo", "sapporo-snow.jpg", "札幌・雪まつり", "雪まつりの週と、前後の週。",
      "2027さっぽろ雪まつりは2月4日（木）〜11日（木・祝）。その週と前後の週で、宿の料金を比べました。", body,
      "会期はさっぽろ雪まつり実行委員会の発表（2027年2月4日〜11日）。先の日付は料金を取る間隔が空くため、取れている日で比べた目安です。"))
made.append("sapporo-yukimatsuri")

# 18. 札幌・1人1万円以下で泊まれる、★4.3以上の宿。
rows = []
for no in SP:
    ns = [x for x in nights(no) if x[1] <= 14000]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d, len(ns)))
rows.sort()
its = [item(i + 1, no, f"1人 {yen(v // 2)}", f"2名合計 {yen(v)}・{lab(d)}", f"★{H[no]['avg']:.2f}・1人7千円以下の日 {k}日", d) for i, (v, no, d, k) in enumerate(rows)]
write("sapporo-1man", page("sapporo-1man", "sapporo", "sapporo-odori-blue.jpg", "札幌・1人7千円以下", "1人7千円以下で泊まれる、札幌の宿。",
      f"★4.3以上・朝食付きで、1人7千円（2人で1万4千円）以下になる日がある宿を、安い順に並べました。札幌の★4.3以上の宿{len(SP)}軒のうち{len(rows)}軒です。",
      sec("1人あたりが安い順", f"{len(rows)}軒に、1人7千円以下の日があります。", ol(its, 8), "浮いたぶんで、スープカレーとジンギスカン。" if rows else ""),
      "1人あたり＝2名合計÷2。"))
made.append("sapporo-1man")

# ---- 既存エリアの2本目以降
import re as _re
def wk_sat(no):
    """(土曜泊の平均, 日〜木泊の平均)。どちらかが2日未満なら None。"""
    ns = nights(no)
    sa = [v for d, v in ns if d.weekday() == 5]; wk = [v for d, v in ns if d.weekday() in (6, 0, 1, 2, 3)]
    return (statistics.mean(sa), statistics.mean(wk)) if len(sa) >= 2 and len(wk) >= 2 else None


def kami(no):
    ns = nights(no)
    return min(ns, key=lambda x: (x[1], x[0])) if ns else None


# 19. 箱根・露天風呂付き客室、土曜と平日でいくら違う？
ROTEN = r"露天風呂付|露天付|客室露天|部屋付.{0,3}露天|専用露天"
rows = []
for no in area_nos("hakone"):
    if not _re.search(ROTEN, DET.get(no, "")): continue
    ws = wk_sat(no); k = kami(no)
    if ws and k: rows.append((ws[0] - ws[1], no, ws, k))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, f"−{g:,.0f}円", f"土曜 {yen(ws[0])} → 日〜木 {yen(ws[1])}（平均）", f"神日 {lab(k[0])} <b>{yen(k[1])}</b>", k[0]) for i, (g, no, ws, k) in enumerate(rows) if g > 0]
body = ""
if rows:
    gs = [r[0] for r in rows]
    body += sec("土曜をやめると、いくら浮く？", f"露天風呂付き客室のある箱根の宿{len(rows)}軒の、土曜泊と日〜木泊の平均の差。中央値は<b>{statistics.median(gs):,.0f}円</b>。", "", "")
body += sec("平日に泊まると差が大きい宿", "土曜泊の平均と、日〜木泊の平均の差が大きい順。", ol(its),
            f"1位の{esc(H[rows[0][1]]['name'])}は、平日にするだけで平均{rows[0][0]:,.0f}円。部屋の露天風呂は、平日でも同じお湯。" if its else "")
write("hakone-rotenburo", page("hakone-rotenburo", "hakone", "hakone-torii.jpg", "箱根・露天風呂付き客室", "部屋に露天風呂。土曜と平日で、いくら違う？",
      "露天風呂付き客室は、箱根でも人気が高い。土曜泊と日〜木泊で、同じ宿の料金がどれだけ違うかを比べました。", body,
      "「露天風呂付き客室」は楽天トラベルの宿の紹介文・設備情報をもとにしています。表示の料金は露天風呂付きの部屋とは限りません。"))
made.append("hakone-rotenburo")

# 20. 熱海・何曜日に泊まると安い？
WDJ = "月火水木金土日"
byw = {}
for no in area_nos("atami"):
    for d, v in nights(no): byw.setdefault(d.weekday(), []).append(v)
wr = [(f"{WDJ[w]}曜泊", statistics.median(byw[w]), "") for w in (6, 0, 1, 2, 3, 4, 5) if len(byw.get(w, [])) >= 10]
body = ""
if wr:
    lo = min(wr, key=lambda r: r[1]); hi = max(wr, key=lambda r: r[1])
    body += sec("曜日ごとの料金", f"熱海の宿の、泊まる曜日ごとの料金の中央値。いちばん安いのは<b>{lo[0]}</b>、いちばん高い{hi[0]}とは{hi[1] - lo[1]:,.0f}円の差。", bars(wr))
    lw = [k for k, w in enumerate(WDJ) if f"{w}曜泊" == lo[0]][0]
    rows = []
    for no in area_nos("atami"):
        ns = [x for x in nights(no) if x[0].weekday() == lw]
        if ns:
            d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d))
    rows.sort()
    its = [item(i + 1, no, yen(v), f"いちばん安い{lo[0]} {lab(d)}", f"★{H[no]['avg']:.2f}", d) for i, (v, no, d) in enumerate(rows)]
    body += sec(f"{lo[0]}が安い宿", f"{lo[0]}だけで、宿ごとにいちばん安い日。", ol(its), f"{lo[0]}は、土曜泊より中央値で{hi[1] - lo[1]:,.0f}円安い。")
write("atami-youbi", page("atami-youbi", "atami", "atami-panorama.jpg", "熱海・曜日", "熱海、何曜日に泊まると安い？",
      "同じ熱海の宿でも、泊まる曜日で料金は変わる。この先半年の料金を、曜日ごとに比べました。", body, "期間はこの先の半年。"))
made.append("atami-youbi")

# 21. 由布院・いちばん安い月は？
YNOS = area_nos("yufuin")
mm = med_by_month(YNOS)
body = ""
if mm:
    lo = min(mm, key=lambda r: r[2]); hi = max(mm, key=lambda r: r[2])
    body += sec("月ごとの料金", f"由布院の宿の、月ごとの神日の中央値。いちばん安いのは<b>{lo[1]}月</b>、いちばん高いのは<b>{hi[1]}月</b>。", bars([(f"{m}月", v, "") for y, m, v in mm]))
    rows = []
    for no in YNOS:
        a, da = month_min(no, hi[0], hi[1]); b, db = month_min(no, lo[0], lo[1])
        if a and b and a > b: rows.append((a - b, no, a, b, db))
    rows.sort(key=lambda r: -r[0])
    its = [item(i + 1, no, f"−{g:,}円", f"{hi[1]}月の神日 {yen(a)} → {lo[1]}月", f"{lo[1]}月の神日 {lab(db)} <b>{yen(b)}</b>", db) for i, (g, no, a, b, db) in enumerate(rows)]
    body += sec(f"{lo[1]}月にずらすと、いくら安い？", f"同じ宿の、{hi[1]}月と{lo[1]}月の神日の差。", ol(its),
                f"1位の{esc(H[rows[0][1]]['name'])}は、{lo[1]}月にずらすだけで{rows[0][0]:,}円。" if rows else "")
write("yufuin-month", page("yufuin-month", "yufuin", "yufuin-kinrinko.jpg", "由布院・時期", "由布院、いちばん安い月は？",
      "朝霧の金鱗湖は、秋から冬が見ごろ。宿がいちばん安いのはいつなのか、この先半年の料金を月ごとに比べました。", body, "この先半年の料金で比べています。"))
made.append("yufuin-month")

# 22. 別府・土曜でも、ほぼ平日。
rows = []
for no in area_nos("beppu"):
    ws = wk_sat(no); k = kami(no)
    if ws and k: rows.append((ws[0] - ws[1], no, ws, k))
rows.sort(key=lambda r: (r[0], r[3][1]))
its = [item(i + 1, no, (f"+{g:,.0f}円" if g > 0 else "土曜の方が安い"), f"土曜 {yen(ws[0])}／日〜木 {yen(ws[1])}（平均）", f"神日 {lab(k[0])} <b>{yen(k[1])}</b>", k[0]) for i, (g, no, ws, k) in enumerate(rows)]
q = ""
if rows:
    q = (f"1位の{esc(H[rows[0][1]]['name'])}は、土曜と平日の差が{max(0, rows[0][0]):,.0f}円。"
         f"別府の{len(rows)}軒全体では、土曜は平日より平均{statistics.median(r[0] for r in rows):,.0f}円高い（中央値）。")
write("beppu-doyou", page("beppu-doyou", "beppu", "beppu-chinoike.jpg", "別府・土曜泊", "土曜の値上がりが小さい、別府の宿。",
      "温泉地は土曜が高いのがふつう。土日しか休めない人のために、別府の宿を土曜泊と日〜木泊の差が小さい順に並べました。",
      sec("土曜の値上がりが小さい順", "土曜泊の平均と、日〜木泊の平均の差。", ol(its, 8), q), "期間はこの先の半年。"))
made.append("beppu-doyou")

# 23. 伊豆高原・ペットと泊まれる宿の神日。
pet = []; other = []
for no in area_nos("izukogen"):
    k = kami(no)
    if not k: continue
    (pet if "ペット同宿可" in FAC.get(no, "") else other).append((k[1], no, k[0]))
pet.sort(); body = ""
if pet and other:
    mp, mo = statistics.median(v for v, _, _ in pet), statistics.median(v for v, _, _ in other)
    body += sec("ペットと泊まれる宿は、高い？", f"伊豆高原の★4.3以上の宿で、ペットと泊まれる宿{len(pet)}軒と、そうでない宿{len(other)}軒の神日の中央値。",
                bars([("ペット可", mp, ""), ("それ以外", mo, "")]),
                ("ほとんど変わらない。" if abs(mp - mo) / max(mp, mo) < 0.05 else (f"ペット可の宿のほうが{mp - mo:,.0f}円高い。" if mp > mo else f"ペット可の宿のほうが{mo - mp:,.0f}円安い。")))
its = [item(i + 1, no, yen(v), f"神日 {lab(d)}", f"★{H[no]['avg']:.2f}・ペット同宿可", d) for i, (v, no, d) in enumerate(pet)]
body += sec("ペットと泊まれる宿・神日の安い順", "楽天トラベルの設備に「ペット同宿可」がある宿。", ol(its, 8))
write("izukogen-pet", page("izukogen-pet", "izukogen", "izukogen-jogasaki.jpg", "伊豆高原・ペット", "ペットと泊まれる、伊豆高原の神日。",
      "ペットと行く旅先として人気の伊豆高原。★4.3以上で、ペットと泊まれる宿の神日を並べました。", body,
      "「ペット同宿可」は楽天トラベルの設備情報です。泊まれる動物の種類・大きさ、ペット可の部屋の数・料金は宿ごとに違います。予約の前に宿のページで確かめてください。"))
made.append("izukogen-pet")

# 24. 軽井沢・高級ホテルが下がる日。
rows = []
for no in area_nos("karuizawa"):
    ns = nights(no)
    if len(ns) < 10: continue
    med = statistics.median(v for _, v in ns)
    if med < 60000: continue
    d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((1 - v / med, no, med, d, v))
rows.sort(key=lambda r: -r[0])
its = [item(i + 1, no, f"−{p * 100:.0f}%", f"いつもは {yen(med)}（中央値）", f"神日 {lab(d)} <b>{yen(v)}</b>", d) for i, (p, no, med, d, v) in enumerate(rows)]
write("karuizawa-luxury", page("karuizawa-luxury", "karuizawa", "karuizawa-kumoba-pond.jpg", "軽井沢・高級ホテル", "軽井沢の高級ホテルが、下がる日。",
      "ふだんは2人で6万円を超える軽井沢のホテル・旅館。その宿がいちばん下がる日と、いつもとの差を並べました。",
      sec("いつもより下がる順", f"この先半年の料金の中央値が6万円以上の宿{len(rows)}軒。", ol(its),
          f"1位の{esc(H[rows[0][1]]['name'])}は、神日にいつもより{rows[0][0] * 100:.0f}%安い。" if rows else ""), "「いつも」＝この先半年の料金の中央値。"))
made.append("karuizawa-luxury")

# 25. 城崎・かにの季節は、いくら高い？
KNOS = area_nos("kinosaki")
mm = med_by_month(KNOS)
body = ""
if mm:
    lo = min(mm, key=lambda r: r[2]); hi = max(mm, key=lambda r: r[2])
    body += sec("月ごとの料金", f"城崎の宿の、月ごとの神日の中央値。いちばん高いのは<b>{hi[1]}月</b>、いちばん安いのは<b>{lo[1]}月</b>。", bars([(f"{m}月", v, "") for y, m, v in mm]))
rows = []
for no in KNOS:
    k = [(d, v) for d, v in nights(no) if d.month in (11, 12, 1, 2, 3)]
    if k:
        d, v = min(k, key=lambda x: (x[1], x[0])); rows.append((v, no, d))
rows.sort()
its = [item(i + 1, no, yen(v), f"かにの季節の神日 {lab(d)}", f"★{H[no]['avg']:.2f}・食事★{MEAL.get(no, 0):.2f}", d) for i, (v, no, d) in enumerate(rows)]
body += sec("かにの季節に、いちばん安く泊まれる宿", "11〜3月だけで、宿ごとにいちばん安い日。", ol(its, 8))
write("kinosaki-kani", page("kinosaki-kani", "kinosaki", "kinosaki-willow-day.jpg", "城崎・かにの季節", "かにの季節の城崎、いちばん安い日。",
      "松葉がにの季節（11月〜3月）は、城崎がいちばんにぎわう時期。その中でいちばん安く泊まれる日を探しました。", body,
      "表示の料金は2食付きの最安プランで、かに料理のプランとは限りません。"))
made.append("kinosaki-kani")

# 26. 伊東・1人1万円台で泊まれる伊東。
rows = []
for no in area_nos("ito"):
    ns = [x for x in nights(no) if x[1] < 40000]
    if ns:
        d, v = min(ns, key=lambda x: (x[1], x[0])); rows.append((v, no, d, len(ns)))
rows.sort()
its = [item(i + 1, no, f"1人 {yen(v // 2)}", f"2名合計 {yen(v)}・{lab(d)}", f"1人2万円未満の日 {k}日・★{H[no]['avg']:.2f}", d) for i, (v, no, d, k) in enumerate(rows)]
write("ito-1man", page("ito-1man", "ito", "ito-okawa-river-day.jpg", "伊東・1人1万円台", "1人1万円台で泊まれる伊東。",
      "★4.3以上で、2食付き。それでも1人2万円を切る日がある伊東の宿を、安い順に並べました。",
      sec("1人あたりが安い順", f"伊東の★4.3以上の宿{len(area_nos('ito'))}軒のうち{len(rows)}軒に、1人1万円台の日があります。", ol(its, 8),
          "東京から特急踊り子で約1時間45分。近くて、安くて、温泉。" if rows else ""), "1人あたり＝2名合計÷2。"))
made.append("ito-1man")

# ---- ハイクラスの宿が、下がる日（エリア別・憧れの宿）
def hc_rows(keys):
    rows = []
    for a in keys:
        for no in area_nos(a):
            if not is_hc(no, a): continue
            k = kami(no); u = usual_price(no)
            if k and u > k[1]: rows.append((1 - k[1] / u, no, u, k))
    rows.sort(key=lambda r: -r[0])
    return rows


def hc_page(slug, keys, place, img, h1, lead, quip_tail, place_href=None):
    rows = hc_rows(keys)
    b = is_b(keys[0])
    its = [item(i + 1, no, f"−{p * 100:.0f}%", f"いつもは {yen(u)}", f"神日 {lab(k[0])} <b>{yen(k[1])}</b>（{u - k[1]:,}円安い）", k[0]) for i, (p, no, u, k) in enumerate(rows)]
    th = HC_MIN[1 if b else 2] // 10000
    q = (f"1位の{esc(H[rows[0][1]]['name'])}は、神日ならいつもより{rows[0][0] * 100:.0f}%安い。{quip_tail}" if rows else "")
    body = sec("いつもより下がる順", f"ふだんの料金（この先半年の中央値）が2名{th}万円以上の宿{len(rows)}軒。神日にどれだけ下がるか。", ol(its, 8), q)
    write(slug, page(slug, keys[0], img, place + "・ハイクラス", h1, lead, body,
                     f"ハイクラス＝この先半年の料金の中央値が2名{th}万円以上の宿（{'1泊朝食付き' if b else '1泊2食付き'}）。「いつも」＝その中央値。",
                     place=place, place_href=place_href))
    made.append(slug)


hc_page("hc-hakone", ["hakone"], "箱根", "hakone-torii.jpg", "箱根のハイクラス宿が、下がる日。",
        "ふだんは2名9万円を超える箱根の宿。その宿がいちばん下がる日と、いつもとの差を並べました。", "憧れの宿は、日を選べば手が届く。")
hc_page("hc-kyoto", ["kyoto"], "京都", "kyoto-kiyomizu-autumn.jpg", "京都のハイクラスホテルが、下がる日。",
        "ふだんは2名6万円を超える京都のホテル・旅館（朝食付き）。いちばん下がる日と、いつもとの差を並べました。", "紅葉の季節を外すと、差はさらに大きい。")
hc_page("hc-karuizawa", ["karuizawa"], "軽井沢", "karuizawa-kumoba-pond.jpg", "軽井沢のハイクラス宿が、下がる日。",
        "ふだんは2名9万円を超える軽井沢の宿。いちばん下がる日と、いつもとの差を並べました。", "森の中の一泊が、ぐっと近くなる。")
hc_page("hc-okinawa", ["onna", "naha", "chatan", "miyako", "ishigaki", "nanbu"], "沖縄", "onna-beach-sunny.jpg", "沖縄のハイクラスリゾートが、下がる日。",
        "ふだんは2名6万円を超える沖縄のリゾート・ホテル（朝食付き）。いちばん下がる日と、いつもとの差を並べました。", "海の見える部屋は、日を選んで。", place_href="areas/onna/")
# 憧れの宿：全国の食事付きのハイクラス宿
hc_page("akogare", [a for a in sorted({h["area"] for h in H.values()}) if not is_b(a)], "全国", "hakone-fuji-ship.jpg", "憧れの宿が、手の届く日。",
        "全国の★4.3以上で、ふだんは2名9万円を超える食事付きの宿。神日にいつもよりどれだけ下がるかの大きい順に並べました。", "日を選ぶだけで、いつもの憧れが現実になる。", place_href="ranking/")

# ---- 空きが出にくい人気宿、いま空いている日（空きの少なさは毎日の料金データから。空きが増えたら自動で外れる）
from common import open_days
RARE_MAX = 40          # この先の空きがこの日数未満
def rare_rows(lane_b):
    rows = []
    for no, h in H.items():
        if is_b(h["area"]) != lane_b: continue
        if not ((h.get("cnt") or 0) >= 100 or is_hc(no, h["area"])): continue
        od = open_days(no); ns = nights(no)
        if not ns or od >= RARE_MAX: continue
        rows.append((od, no, ns))
    rows.sort(key=lambda r: (r[0], -(H[r[1]].get("cnt") or 0)))
    return rows

def rare_items(rows):
    out = []
    for i, (od, no, ns) in enumerate(rows):
        h = H[no]; info = INFO[str(no)]
        near = ns[0]; low = min(ns, key=lambda x: x[1])
        hp = f"../../hotels/{h['slug']}/" if h["slug"] in built else None
        name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
        chips = "".join(f"<i>{lab(d)}</i>" for d, _ in ns[:4])
        more = f"<em>ほか{len(ns) - 4}日</em>" if len(ns) > 4 else ""
        out.append(f"""<li class="ri rare">
  <span class="rk">{i + 1}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{esc(h.get('loc',''))}｜★{h.get('avg',0):.2f}（{h.get('cnt',0):,}件）</span>
    <div class="rv"><span class="ak">空き</span><b>{od}</b><span class="ak">日</span><span class="ak2">この先半年</span></div>
    <dl class="rare-d"><div><dt>いちばん近い空き</dt><dd><span>{lab(near[0])}</span><b>{yen(near[1])}</b></dd></div><div><dt>いちばん安い日</dt><dd><span>{lab(low[0])}</span><b>{yen(low[1])}</b></dd></div></dl>
    <div class="rare-days"><span>空いている日</span>{chips}{more}</div>
  </div>
  <a class="rgo" href="{esc(rk_link(no, near[0]))}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a>
</li>""")
    return out

r2, rb = rare_rows(False), rare_rows(True)
body = sec("食事付きの宿（夕食・朝食つき）", f"口コミ100件以上の人気宿・ハイクラスの宿のうち、この先半年で空きが{RARE_MAX}日未満の{len(r2)}軒。空きの少ない順。", ol(rare_items(r2), 10),
           (f"1位の{esc(H[r2[0][1]]['name'])}は、半年で空きが{r2[0][0]}日だけ。" if r2 else ""))
if rb:
    body += sec("朝食付きの宿（街・リゾート）", f"京都・沖縄・北海道の街などの宿。同じ基準で{len(rb)}軒。", ol(rare_items(rb), 10))
write("aki-rare", page("aki-rare", "kusatsu", "kusatsu-yubatake-night.jpg", "空きが出にくい人気宿", "空きが出にくい人気宿、いま空いている日。",
      "いつ見ても埋まっている人気宿にも、ぽつんと空く日があります。毎日の料金データから、空きの少ない宿と、いま空いている日を並べました。空きはすぐ埋まるので、気になる日は早めに。",
      body, f"空き＝大人2名・1室で予約できるプランがある日（この先半年・毎日取り直し）。空きが{RARE_MAX}日以上に増えた宿は、自動でこのページから外れます。食事付きの宿は1泊2食付き、朝食付きの宿は1泊朝食付きの料金です。",
      place="全国", place_href="ranking/"))
made.append("aki-rare")

print("specials built", made)
