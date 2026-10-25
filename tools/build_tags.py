"""タグ（露天風呂付き客室・部屋食・ペットなど）ごとの宿の一覧ページ（/tags/<slug>/ と /tags/<slug>/<area>/）。

判定は楽天トラベルの施設情報（設備の一覧・宿の紹介文）と、口コミの点数・料金だけで行う。
1件の口コミの文章は使わない（その人の感想で、宿の設備とは限らないため）。
"""
import os, sys, json, re, html, hashlib, statistics, datetime as dt, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, plan_s, plan_l, COND_PLAN, place_of
from common import (site_header, tabbar, footer, og_meta, OUT, DATA, AREA_JA, AREAS, HOTELS, PRH, ASOF,
                    WINDOW_START, WINDOW_END, TODAY)

AFF = "589faade.b97f81b7.589faadf.010fa421"
INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
WD = "月火水木金土日"
H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}
built = set(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else set()

from tagdefs import DET, nights, text, fac, meal, SEA, MED, TAGS


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(int(v))
def lab(d): return f"{d.month}/{d.day}({WD[d.weekday()]})"
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def rk_link(no, d):
    e = d + dt.timedelta(days=1)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={d.year}&f_tuki1={d.month}&f_hi1={d.day}"
         f"&f_nen2={e.year}&f_tuki2={e.month}&f_hi2={e.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"


def rows_for(t, area=None):
    out = []
    for no in H:
        if area and H[no]["area"] != area: continue
        if is_b(H[no]["area"]) and not t.get("both") and (not area or t.get("sort") == "drop" or t.get("per")): continue   # 朝食付きの宿は、全国版と料金の基準があるタグには入れない
        if not t["f"](no): continue
        ns = nights(no)
        if not ns: continue
        if t.get("per"): ns = [x for x in ns if x[1] < 40000] or ns
        d, p = min(ns, key=lambda x: (x[1], x[0]))
        med = MED.get(no, 0)
        out.append(dict(no=no, d=d, p=p, med=med, n=sum(1 for x in nights(no) if x[1] == p)))
    if t.get("sort") == "drop": out.sort(key=lambda r: -((r["med"] - r["p"]) / r["med"] if r["med"] else 0))
    else: out.sort(key=lambda r: (r["p"], -H[r["no"]]["avg"]))
    return out


def item(i, r, base, t):
    no = r["no"]; h = H[no]; info = INFO[str(no)]
    hp = f"{base}hotels/{h['slug']}/" if h["slug"] in built else None
    name = f'<a class="rn" href="{hp}">{esc(h["name"])}</a>' if hp else f'<span class="rn">{esc(h["name"])}</span>'
    big = f"1人 {yen(r['p'] // 2)}" if t.get("per") else yen(r["p"])
    more = f" ほか{r['n'] - 1}日" if r["n"] > 1 else ""
    sub = []
    if t.get("sub"): sub.append(t["sub"](no))
    if r["med"] and r["med"] > r["p"]: sub.append(f"いつもより <b>−{int(r['med'] - r['p']):,}円</b>")
    sub_html = f'<div class="rk2">{"・".join(sub)}</div>' if sub else ""
    return f"""<li class="ri">
  <span class="rk">{i}</span>
  <img class="rt" src="{esc(info.get('thumb',''))}" alt="" loading="lazy" width="96" height="64">
  <div class="rb">
    {name}<span class="rm">{esc(place_of(h))}｜★{h.get('avg',0):.2f}</span>
    <div class="rv"><b>{big}</b><span><i class="kd">神日</i>{lab(r['d'])}泊{more}・2名{plan_s(h['area'])}{'（2名で' + yen(r['p']) + '）' if t.get('per') else ''}</span></div>
    {sub_html}
  </div>
  <a class="rgo" href="{esc(rk_link(no, r['d']))}" target="_blank" rel="noopener sponsored">楽天トラベルで見る</a>
</li>"""


def chips(cur_slug, base, prefix):
    return '<nav class="tgc" aria-label="タグ"><ul>' + "".join(
        f'<li><a href="{base}{prefix}{t["slug"]}/"{" aria-current=page" if t["slug"] == cur_slug else ""}>{esc(t["name"])}</a></li>' for t in LIVE) + "</ul></nav>"


def page(path, title, desc, crumbs, body, base):
    v = ver("site.css"), ver("hotel.css"), ver("top.css", "otoku.css", "rank.css")
    cr = "".join(f'<span aria-hidden="true">›</span>' + (f'<a href="{u}">{esc(n)}</a>' if u else f"<span>{esc(n)}</span>") for n, u in crumbs)
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
{site_header(base, "")}
<main class="gin ok rkp gd tgp">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a>{cr}</nav>
  {body}
</main>
""" + footer(base) + tabbar(base, "") + "</body></html>\n"


def write(path, s):
    os.makedirs(f"{OUT}/{path}", exist_ok=True)
    open(f"{OUT}/{path}index.html", "w", encoding="utf-8").write(s)


FINE = (f'<p class="fine">※★4.3以上＝楽天トラベルの口コミ評価4.3以上（口コミ50件以上）の宿。{COND_PLAN}（2名合計・税込）。'
        f'「いつもより」＝その宿の、この先半年の料金の中央値との差。料金は楽天トラベルの{esc(ASOF)}時点のもので、毎日更新しています。宿の写真：楽天トラベル</p>')

LIVE = [t for t in TAGS if rows_for(t)]
made = []
for t in LIVE:
    rows = rows_for(t)
    areas = {a["key"]: len(rows_for(t, a["key"])) for a in AREAS}   # 朝食付きのエリアは全国版に入らないので、エリアごとに数える
    order = [a["key"] for a in AREAS if areas.get(a["key"], 0) >= 2]
    # 全エリア
    base = "../../"
    ach = "".join(f'<li><a href="{a}/">{esc(AREA_JA[a])}<small>{areas[a]}軒</small></a></li>' for a in order)
    body = f"""<header class="ok-hd"><p class="tg-eb">タグ</p><h1>{esc(t['h1'])}</h1>
  <p>★4.3以上の宿のうち、<b>{esc(t['name'])}</b>にあてはまる<b>{len(rows)}軒</b>。この先半年で、それぞれいちばん安い日（神日）を並べました。</p></header>
{chips(t['slug'], base, 'tags/')}
{f'<section class="rsec"><h2>エリアで絞る</h2><ul class="tg-ar">{ach}</ul></section>' if order else ''}
<section class="rsec"><h2>{esc(t['name'])}の宿・神日の安い順{'（値下がりの大きい順）' if t.get('sort') == 'drop' else ''}</h2>
  <ol class="rl">{''.join(item(i + 1, r, base, t) for i, r in enumerate(rows))}</ol></section>
<p class="tg-rule"><b>このタグの決め方</b>{esc(t['rule'])}</p>
{FINE}"""
    title = f"{t['name']}の宿の神日｜いちばん安い日がわかる｜YASUMIBI"
    desc = f"{t['name']}の、口コミ★4.3以上の宿{len(rows)}軒。宿ごとにいちばん安く泊まれる日（神日）と料金を、楽天トラベルの料金から毎日計算。"
    write(f"tags/{t['slug']}/", page(f"tags/{t['slug']}/", title, desc, [(t["name"], None)], body, base))
    made.append(f"tags/{t['slug']}/")
    # エリア別
    for a in order:
        ar = rows_for(t, a); base = "../../../"
        body = f"""<header class="ok-hd"><p class="tg-eb">{esc(AREA_JA[a])}・タグ</p><h1>{esc(AREA_JA[a])}で、{esc(t['h1'])}</h1>
  <p>{esc(AREA_JA[a])}の★4.3以上の宿のうち、<b>{esc(t['name'])}</b>にあてはまる<b>{len(ar)}軒</b>の神日です。</p></header>
{chips(t['slug'], base, 'tags/')}
<section class="rsec"><h2>{esc(AREA_JA[a])}・{esc(t['name'])}の宿</h2>
  <ol class="rl">{''.join(item(i + 1, r, base, t) for i, r in enumerate(ar))}</ol></section>
<p class="gd-next"><a href="{base}tags/{t['slug']}/">全エリアの{esc(t['name'])}の宿を見る →</a>　<a href="{base}areas/{a}/">{esc(AREA_JA[a])}の宿をすべて見る →</a></p>
<p class="tg-rule"><b>このタグの決め方</b>{esc(t['rule'])}</p>
{FINE}"""
        title = f"{AREA_JA[a]}の{t['name']}の宿｜いちばん安い日｜YASUMIBI"
        desc = f"{AREA_JA[a]}で{t['name']}の、口コミ★4.3以上の宿{len(ar)}軒。宿ごとにいちばん安く泊まれる日（神日）と料金を毎日更新。"
        write(f"tags/{t['slug']}/{a}/", page(f"tags/{t['slug']}/{a}/", title, desc, [(t["name"], f"{base}tags/{t['slug']}/"), (AREA_JA[a], None)], body, base))
        made.append(f"tags/{t['slug']}/{a}/")

# 条件から外れたタグ・エリアのページ（古いデータのまま残るもの）を消す
import shutil
_keep = set(made)
for _t in os.listdir(f"{OUT}/tags") if os.path.isdir(f"{OUT}/tags") else []:
    _d = f"{OUT}/tags/{_t}"
    if not os.path.isdir(_d): continue
    if f"tags/{_t}/" not in _keep: shutil.rmtree(_d); continue
    for _a in os.listdir(_d):
        if os.path.isdir(f"{_d}/{_a}") and f"tags/{_t}/{_a}/" not in _keep: shutil.rmtree(f"{_d}/{_a}")
json.dump([dict(slug=t["slug"], name=t["name"], n=len(rows_for(t))) for t in LIVE], open(f"{OUT}/tags/tags.json", "w"), ensure_ascii=False)
print("tags built", [(t["slug"], len(rows_for(t))) for t in LIVE], len(made), "pages")
