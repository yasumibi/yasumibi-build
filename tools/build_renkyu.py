"""特集「有給1日で、何連休？」（/renkyu/）。祝日と料金データから毎日自動で作り直す。

- 休み：土日・祝日・年末年始（12/29〜1/3）。
- 平日を1日だけ休むと4連休以上になる日を「有給チャンス」として並べる。
- 連休中の各夜（最終日はチェックアウト）の料金を宿ごとに見て、
  土曜泊（土曜がなければ連休中でいちばん高い夜）と、いちばん安い夜の差が大きい宿を出す。
"""
import os, sys, json, html, hashlib, datetime as dt, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (site_header, tabbar, footer, og_meta, OUT, DATA, AREA_JA, HOTELS, PRH, ASOF,
                    WINDOW_START, WINDOW_END, TODAY)
import jp_holidays

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
WD = "月火水木金土日"
MORE = 4


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(int(v))
def lab(d): return f"{d.month}/{d.day}({WD[d.weekday()]})"
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def nyr(d): return (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)
def rest(d): return d.weekday() >= 5 or bool(jp_holidays.name(d)) or nyr(d)


def block(d, leave):
    """leave（有給の日）を休みにしたとき、d を含む連休の (始め, 終わり)。"""
    off = lambda x: x == leave or rest(x)
    a = b = d
    while off(a - dt.timedelta(days=1)): a -= dt.timedelta(days=1)
    while off(b + dt.timedelta(days=1)): b += dt.timedelta(days=1)
    return a, b


def run_len(d):
    if not rest(d): return 0
    a, b = block(d, None)
    return (b - a).days + 1


def chances():
    out = []
    d = max(TODAY + dt.timedelta(days=1), WINDOW_START)
    while d <= WINDOW_END:
        if not rest(d):
            a, b = block(d, d)
            n = (b - a).days + 1
            base = max(run_len(d - dt.timedelta(days=1)), run_len(d + dt.timedelta(days=1)))
            if n >= 4 and n > base: out.append(dict(leave=d, a=a, b=b, n=n, base=base))
        d += dt.timedelta(days=1)
    return out


def rk_link(no, d):
    e = d + dt.timedelta(days=1)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={d.year}&f_tuki1={d.month}&f_hi1={d.day}"
         f"&f_nen2={e.year}&f_tuki2={e.month}&f_hi2={e.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}
built = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()


def best_nights(c):
    nights = [c["a"] + dt.timedelta(days=i) for i in range(c["n"] - 1)]
    rows = []
    for no in H:
        src = PRH.get(str(no), {})
        pv = [(d, int(src[d.isoformat()])) for d in nights if src.get(d.isoformat())]
        if len(pv) < 2: continue
        lo = min(pv, key=lambda x: (x[1], x[0]))
        sat = [x for x in pv if x[0].weekday() == 5]
        ref = max(sat, key=lambda x: x[1]) if sat else max(pv, key=lambda x: x[1])
        if ref[1] - lo[1] <= 0: continue
        rows.append(dict(no=no, lo=lo, ref=ref, save=ref[1] - lo[1], sat=bool(sat)))
    rows.sort(key=lambda r: (-r["save"], r["lo"][1]))
    return rows


def item(i, r, base):
    h = H[r["no"]]; info = INFO[str(r["no"])]
    hp = f"{base}hotels/{h['slug']}/" if h["slug"] in built else None
    name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
    return f"""<li class="ri">
  <span class="rk">{i}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{esc(AREA_JA.get(h['area'], ''))}・{esc(h.get('loc',''))}｜★{h.get('avg',0):.2f}</span>
    <div class="rv"><b>−{r['save']:,}円</b><span>{lab(r['ref'][0])}泊 {yen(r['ref'][1])} → {lab(r['lo'][0])}泊</span></div>
    <div class="rk2">いちばん安い夜 {lab(r['lo'][0])} <b>{yen(r['lo'][1])}</b></div>
  </div>
  <a class="rgo" href="{esc(rk_link(r['no'], r['lo'][0]))}" target="_blank" rel="noopener sponsored">楽天で見る</a>
</li>"""


def strip(c):
    cells = ""
    d = c["a"]
    while d <= c["b"]:
        k = "pl" if d == c["leave"] else ("hd" if (jp_holidays.name(d) or nyr(d)) else ("we" if d.weekday() >= 5 else ""))
        t = "有給" if d == c["leave"] else (jp_holidays.name(d) or ("年末年始" if nyr(d) else "休み"))
        cells += f'<li class="{k}"><span class="rs-d">{d.month}/{d.day}</span><span class="rs-w">{WD[d.weekday()]}</span><span class="rs-t">{esc(t)}</span></li>'
        d += dt.timedelta(days=1)
    return f'<ol class="rstrip" aria-label="連休の日程">{cells}</ol>'


def quip(c, r, k):
    nm = esc(H[r["no"]]["name"]); day = lab(r["lo"][0])
    if c["n"] >= 7: return f"有給1日で{c['n']}連休。しかも{nm}は{day}泊にすると{r['save']:,}円安い。使わない理由が見つからない。"
    lines = [f"{nm}は{day}泊にするだけで{r['save']:,}円。有給1日ぶんの日給、宿が払ってくれたようなもの。",
             f"{nm}、{day}泊なら{r['save']:,}円浮く。浮いたお金で、帰りにもう一軒寄れる。",
             f"同じ連休、同じ宿。{day}に泊まるだけで{nm}は{r['save']:,}円の差。"]
    return lines[k % len(lines)]


def section(k, c, base):
    rows = best_nights(c)
    if not rows: return ""
    note = '<p class="rnote2">※年末年始（12/29〜1/3）がお休みの会社の場合。</p>' if any(nyr(c["a"] + dt.timedelta(days=i)) for i in range(c["n"])) else ""
    gain = c["n"] - c["base"]
    sub = f"休みが{c['base']}日 → {c['n']}日に" if c["base"] else f"{c['n']}連休に"
    more = ""
    if len(rows) > 1:
        more = (f'<details class="rmore"><summary>ほかの宿も見る</summary><ol class="rl">'
                + "".join(item(i + 2, r, base) for i, r in enumerate(rows[1:1 + MORE])) + "</ol></details>")
    return f"""<section class="rsec rky" id="r{c['leave']:%m%d}" aria-labelledby="r{c['leave']:%m%d}-h">
  <h2 id="r{c['leave']:%m%d}-h"><span class="rky-l">{lab(c['leave'])}を休むと</span><span class="rky-n">{c['n']}連休</span></h2>
  <p class="rlead">{lab(c['a'])}〜{lab(c['b'])}｜{sub}（+{gain}日）</p>
  {strip(c)}{note}
  <p class="quip">{quip(c, rows[0], k)}</p>
  <ol class="rl">{item(1, rows[0], base)}</ol>{more}
</section>"""


def page(body, cs, base):
    v = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css")
    path = "renkyu/"
    longest = max((c["n"] for c in cs), default=0)
    title = "有給1日で、何連休？｜連休のいちばん安い夜がわかる｜YASUMIBI"
    desc = "平日を1日休むだけで4連休以上になる日と、その連休でいちばん安く泊まれる夜を、口コミ★4.3以上の宿の料金から毎日計算。"
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
<main class="gin ok rkp">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>有給1日で、何連休？</span></nav>
  <header class="ok-hd"><h1>有給1日で、何連休？</h1><p>この先の半年、平日を1日休むだけで4連休以上になる日は<b>{len(cs)}回</b>。最長は<b>{longest}連休</b>。連休の中で、いちばん安く泊まれる夜も出しました。</p></header>
  {body}
  <p class="gd-next"><a href="{base}renkyu/2027/">2027年の連休カレンダーを見る →</a></p>
  <p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。連休の最終日はチェックアウトの日として、泊まる夜に含めていません。宿の写真：楽天トラベル</p>
</main>
""" + footer(base) + tabbar(base, "") + "</body></html>\n"


cs = chances()
base = "../"
body = "".join(section(k, c, base) for k, c in enumerate(cs))
os.makedirs(f"{OUT}/renkyu", exist_ok=True)
open(f"{OUT}/renkyu/index.html", "w", encoding="utf-8").write(page(body, cs, base))
print("renkyu built", [(str(c["leave"]), c["n"]) for c in cs])
