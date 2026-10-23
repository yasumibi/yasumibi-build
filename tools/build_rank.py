"""エリア別の特集（/areas/<key>/）と全国ランキング（/ranking/）。料金データから毎日自動で作り直す。

指標（最初に開く月 KY/KM の料金で計算。年末年始は除く）
 - ずらし甲斐   ：土曜泊の平均 − 神日（その月の最安）。大きいほど、日をずらすと得。
 - 土曜ペナルティ：土曜泊の平均 ÷ 日〜木泊の平均。1.00に近いほど、土曜でも高くならない。
 - 神日の多さ   ：神日から+5%以内で泊まれる日数。多いほど日程を合わせやすい。
 - いつ行く？   ：エリアの宿の「月の最安」の中央値を、月ごとに並べる。
"""
import os, sys, json, html, hashlib, datetime, calendar, statistics, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import B_AREA_NAMES, B_AREA_LABEL, is_b, plan_s, plan_l, COND_PLAN
from common import (site_header, tabbar, footer, og_meta, OUT, DATA, AREAS, AREA_JA, HOTELS, MONTHS, KY, KM,
                    month_prices, ASOF_BY_AREA, ASOF, TODAY)

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
WD = "日月火水木金土"
TOPN = 3


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(int(v))
def lab(y, m, d): return f"{m}/{d}({WD[(datetime.date(y, m, d).weekday() + 1) % 7]})"
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def nyr(m, d): return (m == 1 and d <= 3) or (m == 12 and d >= 29)


def stats(no, y, m):
    p = month_prices(no, y, m)
    days = [(i + 1, v) for i, v in enumerate(p) if v and not nyr(m, i + 1) and datetime.date(y, m, i + 1) >= TODAY]
    if len(days) < 8: return None
    mn = min(v for _, v in days)
    kd = [d for d, v in days if v == mn]
    sat = [v for d, v in days if datetime.date(y, m, d).weekday() == 5]
    wk = [v for d, v in days if datetime.date(y, m, d).weekday() in (6, 0, 1, 2, 3)]
    near = sum(1 for _, v in days if v <= mn * 1.05)
    s = dict(no=no, mn=mn, kd=kd, near=near, ndays=len(days))
    if len(sat) >= 2 and wk:
        sa = statistics.mean(sat); wa = statistics.mean(wk)
        s.update(sa=round(sa), wa=round(wa), gap=round(sa - mn), pen=sa / wa)
    return s


def rk_link(no, y, m, d):
    a = datetime.date(y, m, d); b = a + datetime.timedelta(days=1)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={a.year}&f_tuki1={a.month}&f_hi1={a.day}"
         f"&f_nen2={b.year}&f_tuki2={b.month}&f_hi2={b.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}
built_hotels = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()


def item(i, s, big, small, base, show_area=False):
    h = H[s["no"]]; info = INFO[str(s["no"])]
    hp = f"{base}hotels/{h['slug']}/" if h["slug"] in built_hotels else None
    kd = "・".join(lab(KY, KM, d) for d in s["kd"][:2]) + (f" ほか{len(s['kd'])-2}日" if len(s["kd"]) > 2 else "")
    name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
    area = f'{esc(AREA_JA.get(h["area"], ""))}・' if show_area else ""
    return f"""<li class="ri">
  <span class="rk">{i}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{area}{esc(h.get('loc',''))}｜口コミ {h.get('avg',0):.2f}{'<i class="mb">朝食付き</i>' if is_b(h['area']) else ''}</span>
    <div class="rv"><b>{big}</b><span>{small}</span></div>
    <div class="rk2">神日 {kd} <b>{yen(s['mn'])}</b></div>
  </div>
  <a class="rgo" href="{esc(rk_link(s['no'], KY, KM, s['kd'][0]))}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a>
</li>"""


def ranking_block(rid, title, lead, rows, fmt, base, show_area=False, n=TOPN, quip=None):
    if not rows: return ""
    q = f'<p class="quip">{quip(rows[0])}</p>' if quip else ""
    lis = "".join(item(i + 1, s, *fmt(s), base, show_area) for i, s in enumerate(rows[:n]))
    more = ""
    if len(rows) > n:
        lis2 = "".join(item(i + 1, s, *fmt(s), base, show_area) for i, s in enumerate(rows[n:n + 10], start=n))
        more = f'<details class="rmore"><summary>{n + 1}位から見る</summary><ol class="rl">{lis2}</ol></details>'
    return f"""<section class="rsec" id="{rid}" aria-labelledby="{rid}-h">
  <h2 id="{rid}-h">{title}</h2><p class="rlead">{lead}</p>{q}
  <ol class="rl">{lis}</ol>{more}
</section>"""


F_GAP = lambda s: (f"−{s['gap']:,}円", f"土曜 {yen(s['sa'])} → 神日")
F_PEN = lambda s: (f"+{max(0, s['sa'] - s['wa']):,}円", "土曜の追加料金（日〜木と比べて）")
F_NEAR = lambda s: (f"{s['near']}日", f"{s['ndays']}日のうち、ほぼ神日の日")


def _name(s): return esc(H[s["no"]]["name"])
Q_GAP = lambda s: f"1位の{_name(s)}は、ずらすだけで{s['gap']:,}円。ラーメンなら{s['gap'] // 1000}杯ぶん。"
Q_PEN = lambda s: (f"1位の{_name(s)}は、土曜でもほぼ平日料金。差は缶ビール{max(1, (s['sa'] - s['wa']) // 250)}本ぶん。"
                   if s["sa"] > s["wa"] else f"1位の{_name(s)}は、土曜の方がむしろ安い。どういうこと。")
Q_NEAR = lambda s: f"1位の{_name(s)}は、{s['ndays']}日のうち{s['near']}日がほぼ神日。もはや毎日が神日。"


F_COSPA = lambda s: (yen(s["mn"]), f"★{H[s['no']]['avg']:.2f}・{KM}月の神日の料金")
Q_COSPA = lambda s: f"1位の{_name(s)}は、★{H[s['no']]['avg']:.2f}で{yen(s['mn'])}。2人で割ると、1人{yen(s['mn'] // 2)}。"


def cospa(nos):
    """コスパ：口コミ★4.5以上の宿を、神日の料金が安い順に。"""
    ss = [s for s in (stats(no, KY, KM) for no in nos) if s and H[s["no"]].get("avg", 0) >= 4.5]
    return sorted(ss, key=lambda s: (s["mn"], -H[s["no"]]["avg"]))


def rank_sets(nos):
    ss = [s for s in (stats(no, KY, KM) for no in nos) if s]
    gap = sorted([s for s in ss if s.get("gap", 0) > 0], key=lambda s: -s["gap"])
    pen = sorted([s for s in ss if "pen" in s], key=lambda s: (s["sa"] - s["wa"], s["mn"]))
    near = sorted(ss, key=lambda s: (-s["near"], s["mn"]))
    return gap, pen, near


def when_block(nos):
    rows = []
    for (y, m) in MONTHS:
        mins = []
        for no in nos:
            p = [v for i, v in enumerate(month_prices(no, y, m)) if v and datetime.date(y, m, i + 1) >= TODAY]
            if p: mins.append(min(p))
        if len(mins) >= 3: rows.append((y, m, statistics.median(mins), len(mins)))
    if len(rows) < 2: return ""
    lo, hi = min(r[2] for r in rows), max(r[2] for r in rows)
    bars = ""
    for y, m, v, n in rows:
        w = 30 + 70 * (v - lo) / (hi - lo) if hi > lo else 60
        cls = " lo" if v == lo else (" hi" if v == hi else "")
        bars += f'<li class="w{cls}"><span class="wm">{m}月</span><span class="wb"><i style="width:{w:.0f}%"></i></span><b>{yen(v)}</b></li>'
    best = min(rows, key=lambda r: r[2]); worst = max(rows, key=lambda r: r[2])
    return f"""<section class="rsec when" aria-labelledby="when-h">
  <h2 id="when-h">いつ行く？</h2>
  <p class="rlead">いちばん安いのは<b>{best[1]}月</b>。{('いちばん高い' + str(worst[1]) + '月とは、1泊' + format(round(worst[2] - best[2]), ',') + '円の差。') if worst[2] > best[2] else ''}</p>
  <ul class="wl">{bars}</ul>
</section>"""


AREA_IMG = {"hakone": "hakone-fuji-ship.jpg", "atami": "atami-panorama.jpg", "kusatsu": "kusatsu-yubatake.jpg",
            "yufuin": "yufuin-kinrinko.jpg", "beppu": "beppu-chinoike.jpg",
            "arima": "arima-view.jpg", "kinugawa": "kinugawa-cover.jpg", "gero": "gero-cover.jpg", "noboribetsu": "noboribetsu-cover.jpg",
            "ito": "ito-matsukawa.jpg", "izukogen": "izukogen-jogasaki.jpg", "shuzenji": "shuzenji-temple.jpg",
            "karuizawa": "karuizawa-forest.jpg", "kawaguchiko": "kawaguchiko-fuji.jpg", "kinosaki": "kinosaki-night.jpg",
            "kyoto": "kyoto-yasaka.jpg", "sapporo": "sapporo-odori.jpg", "jozankei": "jozankei-bridge.jpg", "otaru": "otaru-canal.jpg",
            "hakodate": "hakodate-night.jpg", "toya": "toya-lake.jpg", "akan": "akan-lake.jpg", "naha": "naha-shureimon.jpg",
            "onna": "onna-cape.jpg", "chatan": "chatan-village.jpg", "ishigaki": "ishigaki-kabira.jpg"}
try: CREDITS = json.load(open(f"{OUT}/assets/img/credits.json"))
except Exception: CREDITS = {}


def cover(key, base):
    img = AREA_IMG.get(key)
    if not img: return ""
    c = CREDITS.get(img)
    cr = f'<span class="cv-cr">写真：{esc(c["artist"] or "Wikimedia Commons")}（{esc(c["license"])}・Wikimedia Commons）</span>' if c else ""
    return f'<figure class="cv"><img src="{base}assets/img/{img}" alt="" width="960" height="540">{cr}</figure>'


def page(path, title, desc, crumb, h1, lead, body, base, cv=""):
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
<main class="gin ok rkp">
  <nav class="crumb" aria-label="現在地">{crumb}</nav>
  {cv}<header class="ok-hd"><h1>{h1}</h1><p>{lead}</p></header>
  {body}
  <p class="fine">※{COND_PLAN}（2名合計・税込）。{KY}年{KM}月泊の料金で計算（年末年始・過ぎた日は除く）。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。宿の写真：楽天トラベル</p>
</main>
""" + footer(base) + tabbar(base, "") + "</body></html>\n"


def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(s)


made = []
by_area = {}
for h in H.values(): by_area.setdefault(h["area"], []).append(h["no"])
for a in AREAS:
    nos = by_area.get(a["key"])
    if not nos or len(nos) < 5: continue
    gap, pen, near = rank_sets(nos)
    if not gap and not pen: continue
    base = "../../"
    nm = a["name"]
    body = when_block(nos)
    body += ranking_block("gap", "ずらすだけで、浮く。", "土曜の予定を神日にずらしたときの差額。", gap, F_GAP, base, quip=Q_GAP)
    body += ranking_block("pen", "土曜でも、ほぼ平日。", "土日しか休めない人の味方。土曜の値上がりが小さい宿。", pen, F_PEN, base, quip=Q_PEN)
    body += ranking_block("cospa", "★4.5以上なのに、この値段。", "口コミ★4.5以上の宿を、神日の料金が安い順に。いわゆるコスパの良い宿。", cospa(nos), F_COSPA, base, quip=Q_COSPA)
    body += ranking_block("near", "いつ行っても、だいたい安い。", "神日に近い料金の日が多い宿。日程を選ばない。", near, F_NEAR, base, quip=Q_NEAR)
    body += f'<a class="c-apply" href="{base}?area={a["key"]}#search">{esc(nm)}の宿を、日付・予算で探す</a>'
    title = f"{nm}の宿ランキング｜ずらし甲斐・土曜ペナルティ・神日の多さ（{KY}年{KM}月）｜YASUMIBI"
    desc = f"{nm}の人気宿{len(nos)}軒の料金を全日調べて、日をずらすと安くなる宿、土曜でも高くならない宿をランキング。毎日更新。"
    crumb = f'<a href="{base}">ホーム</a><span aria-hidden="true">›</span><a href="{base}ranking/">ランキング</a><span aria-hidden="true">›</span><span>{esc(nm)}</span>'
    write(f"{OUT}/areas/{a['key']}/index.html", page(f"areas/{a['key']}/", title, desc, crumb, f"{esc(nm)}、どの日に泊まる？",
                                                    f"{esc(nm)}の人気宿{len(nos)}軒、{KM}月の料金で比べました。毎日更新。", body, base, cover(a["key"], base)))
    made.append((a, len(nos), gap[:1]))

# 全国版
allnos = [no for no in H if not is_b(H[no]["area"])]   # 朝食付きで比べるエリアは、全国のランキングに混ぜない
gap, pen, near = rank_sets(allnos)
base = "../"
links = "".join(f'<li><a href="{base}areas/{a["key"]}/">{esc(a["name"])}<small>{n}軒</small></a></li>' for a, n, _ in made)
body = ranking_block("gap", "全国・ずらすだけで、浮く。", "土曜の予定を神日にずらしたときの差額。", gap, F_GAP, base, True, 5, quip=Q_GAP)
body += ranking_block("pen", "全国・土曜でも、ほぼ平日。", "土曜の値上がりが小さい宿。", pen, F_PEN, base, True, 5, quip=Q_PEN)
body += ranking_block("cospa", "全国・★4.5以上なのに、この値段。", "口コミ★4.5以上の宿を、神日の料金が安い順に。いわゆるコスパの良い宿。", cospa(allnos), F_COSPA, base, True, 5, quip=Q_COSPA)
body += f'<section class="rsec"><h2>エリア別のランキング</h2>' + (f'<p class="rlead">{B_AREA_LABEL}は1泊朝食付きの料金で比べているため、全国のランキングには入れず、エリア別だけで並べています。</p>' if B_AREA_NAMES else '') + f'<div class="reg"><ul>{links}</ul></div></section>'
write(f"{OUT}/ranking/index.html", page("ranking/", f"全国の宿ランキング｜ずらし甲斐・土曜ペナルティ・コスパ（{KY}年{KM}月）｜YASUMIBI",
      "全国の人気温泉地の宿の料金を全日調べて、日をずらすと安くなる宿、土曜でも高くならない宿をランキング。毎日更新。",
      f'<a href="{base}">ホーム</a><span aria-hidden="true">›</span><span>ランキング</span>', "日をずらすと、いくら浮く？",
      f"全国{len(made)}エリア・{len(allnos)}軒、{KM}月の料金で比べました。毎日更新。", body, base))
print("rank built", [(a["key"], n) for a, n, _ in made])
