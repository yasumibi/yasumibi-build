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
from common import is_b, plan_s, plan_l, COND_PLAN
from common import site_header, tabbar, footer, og_meta, OUT, DATA, AREA_JA, HOTELS, PRH, ASOF, TODAY, WINDOW_START, WINDOW_END, KY, KM

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
DET = {}; MEAL = {}; ROOMS = {}
for ln in open(f"{DATA}/hotel_detail_20261021.tsv", encoding="utf-8"):
    c = ln.rstrip("\n").split("\t")
    if len(c) >= 10:
        DET[int(c[0])] = c[7] + " " + c[9]
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
    cr = f'<span class="cv-cr">写真：{esc(c["artist"] or "Wikimedia Commons")}（{esc(c["license"])}・Wikimedia Commons）</span>' if c else ""
    return f'<figure class="cv"><img src="../../assets/img/{img}" alt="" width="960" height="540">{cr}</figure>'


def page(slug, area, img, eyebrow, h1, lead, body, note):
    base = "../../"
    v = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css")
    title = f"{h1.rstrip('。')}｜{AREA_JA[area]}の特集｜YASUMIBI"
    desc = f"{lead} ★4.3以上の宿だけを、楽天トラベルの料金で毎日調べています。"
    crumb = (f'<a href="{base}">ホーム</a><span aria-hidden="true">›</span><a href="{base}areas/{area}/">{esc(AREA_JA[area])}</a>'
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
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 otk">
{site_header(base, "features")}
<main class="gin ok rkp sp">
  <nav class="crumb" aria-label="現在地">{crumb}</nav>
  {cover(img)}
  <header class="ok-hd"><p class="sp-eb">特集｜{esc(eyebrow)}</p><h1>{esc(h1)}</h1><p>{lead}</p></header>
  {body}
  <a class="c-apply" href="{base}areas/{area}/">{esc(AREA_JA[area])}のほかのランキングを見る</a>
  <p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。{note}大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。年末年始（12/29〜1/3）は除いています。宿の写真：楽天トラベル</p>
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
write("atami-10man", page("atami-10man", "atami", "atami-fireworks.jpg", "熱海・ご褒美の一泊", "海が見える宿の、神日。",
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
write("yufuin-2haku", page("yufuin-2haku", "yufuin", "yufuin-kinrinko-2.jpg", "由布院・連泊", "由布院、2泊するならこの2日。",
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
write("beppu-1man", page("beppu-1man", "beppu", "beppu-umijigoku.jpg", "別府・1人1万円台", "1人1万円台で泊まれる別府。",
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
write("noboribetsu-size", page("noboribetsu-size", "noboribetsu", "noboribetsu-cover.jpg", "登別・宿の大きさ", "大きな宿ほど、安い？",
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

print("specials built", made)
