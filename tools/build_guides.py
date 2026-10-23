"""検索から入ってくる人向けの3ページを作る（毎日自動で作り直す）。

- /renkyu/2027/  2027年の連休カレンダー（祝日・有給を足した連休・その連休のいちばん安い夜）
- /otoku-days/   楽天トラベルで、さらに安くなる日（5と0のつく日・スーパーSALE・楽天カード）
- /weekend/      今週末・来週末に泊まれる神日（直前）
"""
import os, sys, json, html, hashlib, statistics, datetime as dt, urllib.parse, calendar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (site_header, tabbar, footer, og_meta, OUT, DATA, AREA_JA, HOTELS, PRH, ASOF,
                    WINDOW_START, WINDOW_END, TODAY, CARD_AFF)
import jp_holidays

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
WD = "月火水木金土日"
H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}
built = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(int(v))
def lab(d): return f"{d.month}/{d.day}({WD[d.weekday()]})"
def day(n): return dt.timedelta(days=n)
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def aff(u):
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


def rk_link(no, d):
    e = d + day(1)
    return aff(f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={d.year}&f_tuki1={d.month}&f_hi1={d.day}"
               f"&f_nen2={e.year}&f_tuki2={e.month}&f_hi2={e.day}&f_heya_su=1&f_otona_su=2")


def price(no, d):
    return int(PRH.get(str(no), {}).get(d.isoformat(), 0) or 0)


def sat_median(no):
    v = [int(p) for k, p in PRH.get(str(no), {}).items() if p and WINDOW_START.isoformat() <= k <= WINDOW_END.isoformat()
         and dt.date.fromisoformat(k).weekday() == 5]
    return statistics.median(v) if len(v) >= 4 else 0


def all_median(no):
    v = [int(p) for k, p in PRH.get(str(no), {}).items() if p and WINDOW_START.isoformat() <= k <= WINDOW_END.isoformat()]
    return statistics.median(v) if len(v) >= 10 else 0


def item(i, no, d, p, base, sub):
    h = H[no]; info = INFO[str(no)]
    hp = f"{base}hotels/{h['slug']}/" if h["slug"] in built else None
    name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
    return f"""<li class="ri">
  <span class="rk">{i}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{esc(AREA_JA.get(h['area'], ''))}・{esc(h.get('loc',''))}｜★{h.get('avg',0):.2f}</span>
    <div class="rv"><b>{yen(p)}</b><span>{lab(d)}泊・2名1泊2食</span></div>
    {sub}
  </div>
  <a class="rgo" href="{esc(rk_link(no, d))}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a>
</li>"""


def page(path, title, desc, crumb, body, base, extra_js=""):
    v = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css")
    return f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{og_meta(esc(title), esc(desc), path)}<link rel="canonical" href="https://yasumibi.com/{path}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
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
<main class="gin ok rkp gd">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>{esc(crumb)}</span></nav>
  {body}
</main>
""" + footer(base) + tabbar(base, "") + extra_js + "</body></html>\n"


def write(path, s):
    os.makedirs(f"{OUT}/{path}", exist_ok=True)
    open(f"{OUT}/{path}index.html", "w", encoding="utf-8").write(s)


# =====================================================================
# ① 2027年の連休カレンダー
# =====================================================================
Y = 2027


def nyr(d): return (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)
def hol(d): return jp_holidays.name(d) or ("年末年始" if nyr(d) else "")
def rest(d): return d.weekday() >= 5 or bool(hol(d))


def run_of(d):
    a = b = d
    while rest(a - day(1)): a -= day(1)
    while rest(b + day(1)): b += day(1)
    return a, b


def extend(a, b, k):
    """[a,b] を含み、平日を k 日まで休んで作れるいちばん長い連休 (始め, 終わり, 休む日)。"""
    best = (a, b, [])
    for s in range(0, 12):
        for e in range(0, 12):
            x, y = a - day(s), b + day(e)
            work = [x + day(i) for i in range((y - x).days + 1) if not rest(x + day(i))]
            if len(work) > k: continue
            ln, bl = (y - x).days + 1, (best[1] - best[0]).days + 1
            if ln > bl or (ln == bl and len(work) < len(best[2])): best = (x, y, work)
    return best


def nick(a, b):
    ds = [a + day(i) for i in range((b - a).days + 1)]
    if any(d.month == 5 and d.day in (3, 4, 5) for d in ds): return "ゴールデンウィーク"
    if any(nyr(d) for d in ds): return "年末年始"
    if any(d.month == 9 and hol(d) for d in ds) and (b - a).days >= 4: return "シルバーウィーク"
    names = sorted({hol(d) for d in ds if hol(d) and hol(d) != "振替休日"}, key=lambda n: min(d for d in ds if hol(d) == n))
    return "・".join(names)


def events():
    """祝日・年末年始を含む休みのかたまりごとに、有給0〜3日での最長連休。"""
    out = []; seen = set()
    d = dt.date(Y - 1, 12, 26)
    while d <= dt.date(Y, 12, 31):
        if hol(d) and d not in seen:
            a, b = run_of(d)
            for i in range((b - a).days + 1): seen.add(a + day(i))
            opts = [extend(a, b, k) for k in (1, 2, 3)]
            out.append(dict(a=a, b=b, n=(b - a).days + 1, opts=opts))
        d += day(1)
    # 同じ連休に行き着く、となりのかたまりはまとめる
    merged = []
    for e in out:
        if merged and any(o[0] <= merged[-1]["b"] + day(1) and o[1] >= merged[-1]["a"] for o in e["opts"][1:]) \
                and e["opts"][-1][:2] == merged[-1]["opts"][-1][:2]:
            m = merged[-1]
            if e["n"] > m["n"]: m.update(a=e["a"], b=e["b"], n=e["n"])
            m["opts"] = [max(x, y, key=lambda o: ((o[1] - o[0]).days, -len(o[2]))) for x, y in zip(m["opts"], e["opts"])]
            continue
        merged.append(e)
    return [e for e in merged if e["b"].year >= Y or e["b"] >= dt.date(Y, 1, 1)]


def good(o, n):
    """有給1日あたり、休みが2日以上のびる足し方だけをおすすめにする。"""
    return o[2] and (o[1] - o[0]).days + 1 - n >= 2 * len(o[2])


def strip(a, b, leaves):
    cells = ""; d = a
    while d <= b:
        k = "pl" if d in leaves else ("hd" if hol(d) else ("we" if d.weekday() >= 5 else ""))
        t = "有給" if d in leaves else (hol(d) or "休み")
        cells += f'<li class="{k}"><span class="rs-d">{d.month}/{d.day}</span><span class="rs-w">{WD[d.weekday()]}</span><span class="rs-t">{esc(t)}</span></li>'
        d += day(1)
    return f'<ol class="rstrip" aria-label="連休の日程">{cells}</ol>'


def cheapest_nights(a, b, n=3):
    nights = [a + day(i) for i in range((b - a).days) if WINDOW_START <= a + day(i) <= WINDOW_END and a + day(i) > TODAY]
    rows = []
    for no in H:
        pv = [(d, price(no, d)) for d in nights if price(no, d)]
        if pv:
            d, p = min(pv, key=lambda x: (x[1], x[0])); rows.append((p, d, no))
    rows.sort()
    return rows[:n], bool(nights)


def shows_from(d):
    """その日付の料金を出し始める月（掲載は今月から6か月分）。"""
    m = d.year * 12 + d.month - 1 - 5
    return f"{m // 12}年{m % 12 + 1}月" if m // 12 != TODAY.year else f"{m % 12 + 1}月"


def ev_section(e, base, i):
    o1, o2, o3 = e["opts"]
    gains = [o for o in (o1, o2, o3) if good(o, e["n"])]
    best = max(gains, key=lambda o: ((o[1] - o[0]).days, -len(o[2]))) if gains else (e["a"], e["b"], [])
    bx, by, bl = best
    bn = (by - bx).days + 1
    nm = nick(min([e["a"]] + [o[0] for o in e["opts"]]), max([e["b"]] + [o[1] for o in e["opts"]]))
    if e["a"].month == 8: nm += "（お盆休みと重なる会社も）"
    note = '<p class="rnote2">※年末年始（12/29〜1/3）がお休みの会社の場合。</p>' if any(nyr(e["a"] + day(k)) for k in range(e["n"])) else ""
    opts = ""
    for k, o in enumerate((o1, o2, o3), 1):
        ln = (o[1] - o[0]).days + 1
        if not good(o, e["n"]) or (k > 1 and ln == ((e["opts"][k - 2][1] - e["opts"][k - 2][0]).days + 1) and good(e["opts"][k - 2], e["n"])): continue
        opts += f'<li><span class="k">有給{len(o[2])}日</span><b>{ln}連休</b><span class="d">{lab(o[0])}〜{lab(o[1])}（休む日：{"・".join(lab(x) for x in o[2])}）</span></li>'
    opts = f'<ul class="lv">{opts}</ul>' if opts else ""
    rows, inwin = cheapest_nights(bx, by)
    if rows:
        hot = '<h3 class="gd-h3">この連休で、いちばん安い夜</h3><ol class="rl">' + "".join(
            item(j + 1, no, d, p, base, "") for j, (p, d, no) in enumerate(rows)) + "</ol>"
    elif by < TODAY:
        hot = ""
    elif not inwin or bx > WINDOW_END:
        hot = f'<p class="gd-soon">宿の料金は<b>{shows_from(bx)}ごろ</b>から、ここに出ます。</p>'
    else:
        hot = ""
    base_s = f"{e['n']}連休" if e["n"] >= 2 else "祝日"
    return f"""<section class="rsec rky gd-ev" id="e{e['a']:%m%d}">
  <h2><span class="rky-l">{esc(nm)}</span><span class="rky-n">{'最大' if bl else ''}{bn}連休</span></h2>
  <p class="rlead">{lab(e['a'])}〜{lab(e['b'])}｜そのままで<b>{base_s}</b>{f'。有給{len(bl)}日で<b>{bn}連休</b>' if bl else ''}</p>
  {strip(bx, by, set(bl))}{note}
  {opts}
  {hot}
</section>"""


def mini_cal(m, leaves):
    first = dt.date(Y, m, 1); n = calendar.monthrange(Y, m)[1]
    cells = '<li class="e"></li>' * ((first.weekday() + 1) % 7)   # 日曜はじまり
    for i in range(n):
        d = first + day(i)
        k = "pl" if d in leaves else ("hd" if hol(d) and not nyr(d) else ("su" if d.weekday() == 6 else ("sa" if d.weekday() == 5 else "")))
        t = f' title="{esc(hol(d))}"' if hol(d) and not nyr(d) else (' title="有給をおすすめ"' if d in leaves else "")
        cells += f'<li class="{k}"{t}>{d.day}</li>'
    return f'<div class="mc"><h3>{m}月</h3><ol class="mc-h"><li class="su">日</li><li>月</li><li>火</li><li>水</li><li>木</li><li>金</li><li class="sa">土</li></ol><ol class="mc-g">{cells}</ol></div>'


def build_2027():
    evs = events()
    leaves = set()
    for e in evs:
        g = [o for o in e["opts"] if good(o, e["n"])]
        if g: leaves.update(max(g, key=lambda o: ((o[1] - o[0]).days, -len(o[2])))[2])
    hs = sorted((d, n) for d, n in jp_holidays.holidays(Y).items())
    three = [e for e in evs if e["n"] >= 3 and e["a"].year == Y]
    plus1 = [e for e in evs if good(e["opts"][0], e["n"]) and (e["opts"][0][1] - e["opts"][0][0]).days + 1 >= 4 and e["a"].year == Y]
    longest = max(evs, key=lambda e: ((e["opts"][0][1] - e["opts"][0][0]).days, -e["a"].toordinal()))
    ln1 = (longest["opts"][0][1] - longest["opts"][0][0]).days + 1
    base = "../../"
    cal = "".join(mini_cal(m, leaves) for m in range(1, 13))
    tbl = "".join(f'<tr><td>{d.month}月{d.day}日（{WD[d.weekday()]}）</td><td>{esc(n)}</td></tr>' for d, n in hs)
    secs = "".join(ev_section(e, base, i) for i, e in enumerate(evs))
    body = f"""<header class="ok-hd"><h1>2027年の連休カレンダー</h1>
  <p>2027年の祝日は<b>{len(hs)}日</b>。そのままで3連休以上になるのは<b>{len(three)}回</b>。有給を1日足すと4連休以上になるチャンスが<b>{len(plus1)}回</b>あり、有給1日でいちばん長くなるのは{esc(nick(longest['opts'][0][0], longest['opts'][0][1]))}の<b>{ln1}連休</b>。連休ごとに、いちばん安く泊まれる夜も出しています。</p></header>
<section class="rsec"><h2>2027年のカレンダー</h2>
  <p class="mc-lg"><span class="hd">祝日</span><span class="pl">有給をおすすめする日</span></p>
  <div class="mcs">{cal}</div>
</section>
<section class="rsec"><h2>連休と、有給の足し方</h2><p class="rlead">休む日（黄色）を足すと、連休がここまで伸びます。料金が出ている連休は、★4.3以上の宿でいちばん安い夜も並べました。</p></section>
{secs}
<section class="rsec"><h2>2027年の祝日一覧（{len(hs)}日）</h2><table class="gd-t"><tbody>{tbl}</tbody></table>
  <p class="rnote2">内閣府「国民の祝日について」の令和9年の一覧と同じ日付です。お盆休み・年末年始は会社によって違うため、年末年始は12/29〜1/3を休みとして計算しています。</p></section>
<p class="gd-next"><a href="{base}renkyu/">この先半年の「有給1日で何連休？」を見る →</a></p>
<p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。宿の料金は、今月から6か月先の分まで出しています。宿の写真：楽天トラベル</p>"""
    t = "2027年の連休カレンダー｜祝日一覧と、有給で何連休になるか｜YASUMIBI"
    dsc = f"2027年の祝日{len(hs)}日と3連休・GW・シルバーウィーク・年末年始を一覧に。有給を何日足すと何連休になるかと、その連休でいちばん安く泊まれる夜（口コミ★4.3以上の宿）がわかります。"
    write("renkyu/2027/", page("renkyu/2027/", t, dsc, "2027年の連休カレンダー", body, base))
    print("2027 built", len(evs), "events,", len(three), "3連休+,", len(plus1), "plus1, longest", ln1)


# =====================================================================
# ② 楽天トラベルで、さらに安くなる日
# =====================================================================
FIVE0 = "https://travel.rakuten.co.jp/camp/50luxday/"
MATSURI = "https://travel.rakuten.co.jp/coupon/special/matsuri/"
# スーパーSALE（楽天トラベル）。実績は公表された日程、先の回は例年の時期からの予想。
SALES = [(dt.date(2026, 3, 4), dt.date(2026, 3, 20), "実績"), (dt.date(2026, 6, 4), dt.date(2026, 6, 20), "実績"),
         (dt.date(2026, 9, 4), dt.date(2026, 10, 1), "実績"), (dt.date(2026, 12, 4), dt.date(2026, 12, 20), "予想"),
         (dt.date(2027, 3, 4), dt.date(2027, 3, 20), "予想"), (dt.date(2027, 6, 4), dt.date(2027, 6, 20), "予想")]
CHECKED = "2026年10月"


def sale_on(d):
    for a, b, k in SALES:
        if a <= d <= b: return k
    return ""


def big_cal(y, m):
    first = dt.date(y, m, 1); n = calendar.monthrange(y, m)[1]
    cells = '<li class="e"></li>' * ((first.weekday() + 1) % 7)
    for i in range(n):
        d = first + day(i)
        cls = []
        if d.day % 5 == 0: cls.append("f0")
        s = sale_on(d)
        if s: cls.append("ss" + (" yo" if s == "予想" else ""))
        if d < TODAY: cls.append("past")
        if d == TODAY: cls.append("td")
        if d.weekday() == 6 or hol(d): cls.append("su")
        elif d.weekday() == 5: cls.append("sa")
        tag = '<i>5と0</i>' if d.day % 5 == 0 else ""
        cells += f'<li class="{" ".join(cls)}" data-d="{d.isoformat()}"><b>{d.day}</b>{tag}</li>'
    return f'<div class="bc"><h3>{y}年{m}月</h3><ol class="mc-h"><li class="su">日</li><li>月</li><li>火</li><li>水</li><li>木</li><li>金</li><li class="sa">土</li></ol><ol class="bc-g">{cells}</ol></div>'


def build_otoku_days():
    base = "../"
    y2, m2 = (TODAY.year + (TODAY.month == 12), TODAY.month % 12 + 1)
    cals = big_cal(TODAY.year, TODAY.month) + big_cal(y2, m2)
    nxt = next(TODAY + day(i) for i in range(0, 7) if (TODAY + day(i)).day % 5 == 0 and (TODAY + day(i)).day <= 30)
    up = next(((a, b, k) for a, b, k in SALES if b >= TODAY), None)
    sale_rows = "".join(f'<tr><td>{a.year}年{a.month}月</td><td>{a.month}/{a.day}〜{b.month}/{b.day}</td><td>{"<span class=yo>予想</span>" if k == "予想" else "開催済み"}</td></tr>'
                        for a, b, k in SALES)
    up_s = (f'次は<b>{up[0].month}月{up[0].day}日（{WD[up[0].weekday()]}）</b>から' + ("の予想" if up[2] == "予想" else "")) if up else ""
    body = f"""<header class="ok-hd"><h1>楽天トラベルで、さらに安くなる日</h1>
  <p><b>泊まる日</b>は神日で決める。<b>予約する日</b>は「5と0のつく日」かスーパーSALE。<b>払う</b>のは楽天カード。この3つを重ねるのが、いちばん安い泊まり方です。</p></header>
<div class="od-now"><div><small>次の5と0のつく日</small><b id="od-next">{nxt.month}月{nxt.day}日（{WD[nxt.weekday()]}）</b><span id="od-left"></span></div>
  <div><small>楽天トラベル スーパーSALE</small><b>{up_s}</b></div></div>
<section class="rsec"><h2>予約するなら、この日</h2>
  <p class="od-lg"><span class="f0">5と0のつく日</span><span class="ss">スーパーSALE</span><span class="ss yo">SALE（例年の時期からの予想）</span></p>
  <div class="bcs">{cals}</div>
  <p class="rnote2">※カレンダーは「予約する日」です。泊まる日とは別に考えます。</p>
</section>
<section class="rsec od-steps"><h2>3つの重ね方</h2>
  <ol class="od-s">
    <li><span class="n">01</span><div><h3>泊まる日は、神日で決める</h3><p>同じ宿でも、日によって2名1泊で数万円ちがいます。まずはYASUMIBIで、その宿がいちばん安い日（神日）を見つけます。</p><a class="od-a" href="{base}">神日を探す →</a></div></li>
    <li><span class="n">02</span><div><h3>予約は、5と0のつく日に</h3><p>毎月5・10・15・20・25・30日は、楽天トラベルで使える割引クーポンが出る日です。クーポンを取ってから予約します。クーポンの内容や対象の宿泊日は、回ごとに変わります。</p><a class="od-a" href="{esc(aff(FIVE0))}" target="_blank" rel="noopener sponsored">5と0のつく日のクーポンを見る →</a></div></li>
    <li><span class="n">03</span><div><h3>払うのは、楽天カードで事前決済</h3><p>楽天カードで事前にオンライン決済すると、ポイントは通常2倍。キャンペーンにエントリーすると2.5倍になります（国内宿泊・カード払いの分）。</p><a class="od-a" href="{base}cards/">旅行に使うカードを比べる →</a></div></li>
  </ol>
</section>
<section class="rsec"><h2>スーパーSALE（年4回）</h2>
  <p class="rlead">楽天トラベルのスーパーSALEは、例年<b>3月・6月・9月・12月</b>の4日の夜から始まります。半額以下のセールプランが出て、クーポンとも組み合わせられます。</p>
  <table class="gd-t od-t"><thead><tr><th>回</th><th>期間</th><th></th></tr></thead><tbody>{sale_rows}</tbody></table>
  <p class="rnote2">※「予想」は例年の時期から出したもので、正式な日程ではありません。発表されたら、ここを直します。</p>
</section>
<section class="rsec"><h2>毎月の、ほかのクーポン</h2>
  <p class="rlead">楽天トラベルでは毎月「クーポン祭」も開かれます。クーポンの種類や条件は毎月変わるので、予約の前に見ておくと安心です。</p>
  <p><a class="od-a" href="{esc(aff(MATSURI))}" target="_blank" rel="noopener sponsored">今月のクーポン祭を見る →</a></p>
</section>
<aside class="od-card"><p class="prtop"><span>PR</span></p>
  <h2>楽天トラベルで払うなら、楽天カード</h2>
  <p>年会費は永年無料。楽天トラベルの予約をカードで事前決済すると、ポイントが上乗せされます。</p>
  <a class="bcta" href="{esc(CARD_AFF)}" target="_blank" rel="noopener sponsored">楽天カードを見る</a>
</aside>
<p class="fine">※{CHECKED}時点で確認した内容です。キャンペーンの条件・期間・クーポンの内容は変わることがあります。予約の前に、楽天トラベルの公式ページで確認してください。</p>"""
    js = """<script>
(function(){var el=document.getElementById('od-next'),lf=document.getElementById('od-left');if(!el)return;
var n=new Date(Date.now()+9*3600e3),t=new Date(Date.UTC(n.getUTCFullYear(),n.getUTCMonth(),n.getUTCDate()));
for(var i=0;i<8;i++){var d=new Date(t.getTime()+i*864e5),x=d.getUTCDate();if(x%5===0&&x<=30){var w='日月火水木金土'[d.getUTCDay()];
el.textContent=(d.getUTCMonth()+1)+'月'+x+'日（'+w+'）';lf.textContent=i===0?'今日です':'あと'+i+'日';break;}}
document.querySelectorAll('.bc-g li[data-d]').forEach(function(li){var d=li.getAttribute('data-d'),s=t.toISOString().slice(0,10);
li.classList.toggle('past',d<s);li.classList.toggle('td',d===s);});})();
</script>
"""
    t = "楽天トラベルで、さらに安くなる日｜5と0のつく日・スーパーSALEのカレンダー｜YASUMIBI"
    dsc = "楽天トラベルで予約するなら、いつが安い？毎月の5と0のつく日、年4回のスーパーSALE、楽天カードのポイントを、泊まる日（神日）と重ねて使う方法をカレンダーで。"
    write("otoku-days/", page("otoku-days/", t, dsc, "さらに安くなる日", body, base, js))
    print("otoku-days built")


# =====================================================================
# ③ 今週末・来週末に泊まれる神日
# =====================================================================
def weekend_list(d, n=8):
    rows = []
    for no in H:
        p = price(no, d)
        if not p: continue
        med = sat_median(no) if d.weekday() == 5 else all_median(no)
        if not med or p >= med: continue
        rows.append((-(med - p) / med, p, no, int(med)))
    rows.sort()
    return rows[:n]


def area_best(d):
    best = {}
    for no in H:
        p = price(no, d)
        if p and (H[no]["area"] not in best or p < best[H[no]["area"]][0]): best[H[no]["area"]] = (p, no)
    return best


def build_weekend():
    base = "../"
    sat0 = TODAY + day((5 - TODAY.weekday()) % 7)
    secs = ""
    for k, s in enumerate((sat0, sat0 + day(7))):
        lab_w = "今週末" if k == 0 else "来週末"
        nights = [x for x in (s - day(1), s, s + day(1)) if x >= TODAY and (x.weekday() in (4, 5) or hol(x + day(1)))]
        for d in nights:
            if d.weekday() == 6 and not hol(d + day(1)): continue
            if not any(price(no, d) for no in H): continue      # その日の料金をまだ取っていない
            rows = weekend_list(d)
            kind = "土曜" if d.weekday() == 5 else ("金曜" if d.weekday() == 4 else "連休中")
            ab = area_best(d)
            chips = "".join(f'<li><span>{esc(AREA_JA.get(a, a))}</span><b>{yen(p)}〜</b></li>'
                            for a, (p, no) in sorted(ab.items(), key=lambda x: x[1][0]))
            if rows:
                lst = '<ol class="rl">' + "".join(item(i + 1, no, d, p, base,
                    f'<div class="rk2">いつもの{kind}泊より <b>{yen(med - p)}</b> 安い（{int(-r * 100)}%）</div>')
                    for i, (r, p, no, med) in enumerate(rows)) + "</ol>"
            else:
                lst = '<p class="gd-soon">いつもより安い宿は、いまは見つかりませんでした。</p>'
            hd = f"・{esc(hol(d + day(1)))}の前" if hol(d + day(1)) else ""
            secs += f"""<section class="rsec wk" id="w{d:%m%d}">
  <h2><span class="rky-l">{lab_w}</span><span class="rky-n">{lab(d)}泊</span><span class="wk-k">{kind}{hd}</span></h2>
  <p class="rlead">いつもの{kind}泊より安くなっている宿（★4.3以上・空室のあるプランのみ）。</p>
  {lst}
  <details class="rmore"><summary>エリアごとの最安を見る</summary><ul class="wk-a">{chips}</ul></details>
</section>"""
    # 平日に休めるなら：この先14日
    wk = []
    for i in range(1, 15):
        d = TODAY + day(i)
        if rest(d + day(1)) or d.weekday() >= 5: continue
        for no in H:
            p = price(no, d); med = all_median(no)
            if p and med and p < med: wk.append(((p - med) / med, p, no, d, int(med)))
    wk.sort()
    used = set(); top = []
    for r in wk:
        if r[2] in used: continue
        used.add(r[2]); top.append(r)
        if len(top) == 6: break
    wday = '<ol class="rl">' + "".join(item(i + 1, no, d, p, base,
        f'<div class="rk2">この宿のふだんより <b>{yen(med - p)}</b> 安い（{int(-r * 100)}%）</div>')
        for i, (r, p, no, d, med) in enumerate(top)) + "</ol>" if top else ""
    if not secs: secs = '<section class="rsec"><p class="gd-soon">この2週間の週末の料金を取得しています。明日の更新から、ここに並びます。</p></section>'
    body = f"""<header class="ok-hd"><h1>今週末・来週末に泊まれる神日</h1>
  <p>直前でも、安くなっている宿はあります。この先2週間の週末で、<b>いつもの週末より安い</b>★4.3以上の宿を、毎日更新で並べました。</p></header>
{secs}
<section class="rsec"><h2>平日に休めるなら（この先2週間）</h2>
  <p class="rlead">ふだんの料金と比べて、いちばん下がっている平日の夜です。</p>{wday}</section>
<p class="gd-next"><a href="{base}renkyu/">有給1日で、何連休？を見る →</a>　<a href="{base}otoku-days/">さらに安くなる日を見る →</a></p>
<p class="fine">※「いつもの土曜泊」＝その宿の、この先半年の土曜泊の料金の中央値。金曜・平日も同じように、その宿のふだんの料金と比べています。直前は空室が早く埋まります。予約の前に楽天トラベルで空室と料金を確認してください。★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。料金は楽天トラベルの{esc(ASOF)}時点のものです。宿の写真：楽天トラベル</p>"""
    t = "今週末・来週末に泊まれる神日｜直前でも安い温泉宿｜YASUMIBI"
    dsc = "今週末・来週末に空室があって、いつもの週末より安くなっている口コミ★4.3以上の温泉宿を毎日更新。箱根・熱海・草津・由布院など、2名1泊2食付きの料金で比べられます。"
    write("weekend/", page("weekend/", t, dsc, "今週末・来週末の神日", body, base))
    print("weekend built", sat0)


build_2027()
build_otoku_days()
build_weekend()
