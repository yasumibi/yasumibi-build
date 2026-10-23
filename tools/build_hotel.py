"""Build hotel pages (draft: 天悠) into yasumibi-site/hotels/<slug>/ plus the /otoku/ stub."""
import json, os, datetime, html, hashlib, calendar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # このリポジトリ
OUT = os.environ.get("YB_OUT", os.path.join(os.path.dirname(ROOT), "yasumibi-site"))  # 公開用リポジトリ（隣に置く）
INFO = json.load(open(f"{ROOT}/data/hotel_info_20261021.json"))["hotels"]
WD = "日月火水木金土"
AFF = "589faade.b97f81b7.589faadf.010fa421"
# 楽天アフィリエイトの公式素材（楽天カードの券面だけ・200x200）。加工せず縮めて表示する。
RK_FACE = ("https://hbb.afl.rakuten.co.jp/hsb/58adb89a.1783e5b6.58ad7ff2.3c792b49/?me_id=2101008&me_adv_id=373425&t=pict",
           "https://hb.afl.rakuten.co.jp/hsc/58adb89a.1783e5b6.58ad7ff2.3c792b49/?link_type=pict&ut=eyJwYWdlIjoic2hvcCIsInR5cGUiOiJwaWN0IiwiY29sIjoxLCJjYXQiOiIxIiwiYmFuIjozNzM0MjUsImFtcCI6ZmFsc2V9")


def logo_html(base, href=None):
    href = base if href is None else href
    return (f'<a class="brand" href="{href}" aria-label="YASUMIBI ホーム">'
            f'<img class="lg-l" src="{base}assets/img/logo.png" alt="YASUMIBI" width="714" height="120">'
            f'<img class="lg-d" src="{base}assets/img/logo-dark.png" alt="" width="714" height="120"></a>')

def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(v)
def wd(y, m, d): return WD[(datetime.date(y, m, d).weekday() + 1) % 7]

def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]

HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="{robots}">
<title>{title}</title>
<meta name="description" content="{desc}">
{og}<link rel="canonical" href="https://yasumibi.com/{canon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app">
"""

def footer(base):
    return f"""<div class="wrap"><footer class="site">
  <nav aria-label="サイト情報"><a href="{base}about/">YASUMIBIについて</a><a href="{base}about/#operator">運営者情報</a><a href="{base}privacy/">プライバシーポリシー</a><a href="{base}disclosure/">広告の掲載について</a></nav>
  <div>本サイトは楽天アフィリエイトを利用しています。掲載している料金は調べた時点のもので、予約時の料金と異なる場合があります。</div>
  <div><a href="https://webservice.rakuten.co.jp/" target="_blank" rel="noopener">Supported by Rakuten Developers</a>　© YASUMIBI</div>
</footer></div>
"""

def tabbar(base, cur):
    items = [("home", "ホーム", f"{base}", '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'),
             ("area", "エリア", f"{base}#kamibi", '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>'),
             ("date", "日付", f"{base}#kamibi", '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'),
             ("otoku", "さらに安く", f"{base}otoku/", '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v9M9.5 9.5h4a1.8 1.8 0 0 1 0 3.6h-3a1.8 1.8 0 0 0 0 3.6h4"/>')]
    a = "".join(f'<a href="{h}"{" aria-current=\"page\"" if k == cur else ""} class="t-{k}"><svg viewBox="0 0 24 24" aria-hidden="true">{p}</svg><span>{t}</span></a>' for k, t, h, p in items)
    return f'<nav class="tabbar" aria-label="メニュー">{a}</nav>'

import sys as _sys; _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, plan_s, plan_l, COND_PLAN
from common import CARD_CAMP, CARD_BONUS
from common import tabbar, footer, site_header, og_meta, load_area, logo_html, CARD_AFF, SLUG, jan_min, MONTHS, DEFAULT_YM, KY, KM, ASOF_BY_AREA, ASOF, AREA_JA, month_prices
AREA = load_area()

# ------------------------------------------------------------------ all hotels
TIER_JA = {"mid": "2人で5万円前後", "high": "2人で10万円前後"}
FEAT = {("hakone","mid"):"hakone-5man",("hakone","high"):"hakone-10man",("atami","mid"):"atami-5man",("atami","high"):"atami-10man"}
import urllib.parse
v1 = ver("site.css"); v2 = ver("hotel.css", "hotel.js")
base = "../../"

def months_for(h):
    out = []
    for (y, m) in MONTHS:
        nd = calendar.monthrange(y, m)[1]
        out.append(dict(y=y, m=m, days=nd, p=month_prices(h["no"], y, m)))
    return out, (ASOF_BY_AREA.get(h["area"]) or ASOF)

def peer_li(h):
    v = jan_min(h["p"]); ds = [i + 1 for i, x in enumerate(h["p"]) if x == v]
    dl = "・".join(f"{KM}/{d}({wd(KY, KM, d)})" for d in ds[:2]) + (f" ほか{len(ds)-2}日" if len(ds) > 2 else "")
    return (f'<li><a href="../{SLUG[h["no"]][0]}/"><img class="pth" src="{esc(INFO.get(str(h["no"]),{}).get("thumb",""))}" alt="" loading="lazy" width="72" height="48"><span class="pn">{esc(SLUG[h["no"]][1])}<small>{esc(h["loc"])}・口コミ {h["avg"]:.2f}</small></span>'
            f'<span class="pv">{yen(v)}<small>神日 {dl}</small></span></a></li>')


# ---- 楽天トラベル HotelDetailSearch（2026-10-21取得）
import re as _re
INTRO = {  # 宿の紹介文：期間限定の告知・順位の主張は省いて、宿の言葉のまま短く
 1727:"明治11年創業の箱根のクラシックホテル。", 7666:"旅館甲子園優勝の宿。", 15488:"熱海の老舗旅館で、心休まる寛ぎの時間をごゆっくりお過ごしください。",
 19786:"女性に優しい美肌の湯が自慢の縁結びの宿。", 75291:"全室源泉掛け流し半露天付き。こだわりの大人の隠れ家。",
 149439:"楽天ゴールドアワード＆日本の宿アワード受賞。新鮮な海の幸懐石。", 158501:"箱根の絶景を眺めるインフィニティ温泉と、全客室温泉露天風呂付き客室。",
 196679:"2026年3月31日グランドオープン。熱海の特等席に誕生したホテル。JR熱海駅より徒歩8分。"}
HILITE = {16108:"全客室露天風呂付き",151465:"全23室に源泉かけ流しの露天風呂",158501:"全客室露天風呂付き",165555:"全室露天風呂付き",
 149477:"全室露天風呂付き",75291:"全室半露天風呂付き",179729:"全室天然温泉風呂付き",1970:"源泉かけ流し",50826:"13種の湯処",7669:"日本庭園"}
SKIP_FAC = {"ファックス送信可","E-Mail送信可","モーニングコール","宅配便","パソコン利用可","自動販売機","禁煙ルーム","喫煙ルーム","綿棒","全館禁煙"}
PROMO = _re.compile(r"クーポン|セール|限定|OFF|ＯＦＦ|％|%|円[〜～]|ポイント|割引|特典|プレゼント|空室|残り|わずか|No\.?1|ＮＯ|NO\.?1|ランキング|受賞|アワード|キャンペーン|予約|最安|お得")
def promo_clean(t):
    """宿の紹介文から、期間限定の告知・順位・値引きの言葉を含むかたまりを外す。"""
    segs = [x.strip(" 　・") for x in _re.split(r"[★☆◆◇■□【】！!♪◎●]|\s{2,}", t or "")]
    keep = [x for x in segs if x and not PROMO.search(x)]
    s = "　".join(keep).strip()
    return s if len(s) >= 8 else ""
DET = {}
for ln in open(f"{ROOT}/data/hotel_detail_20261021.tsv", encoding="utf-8"):
    c = ln.rstrip("\n").split("\t")
    no = int(c[0]); rt = [float(x) for x in c[3].split(",")]
    ur = c[8]
    dm = _re.search(r"(\d{4})-(\d{2})-(\d{2}) \d{2}:\d{2}:\d{2}投稿", ur)
    body = _re.sub(r"\s*\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}投稿\s*$", "", ur)
    body = _re.sub(r"(クチコミの詳細はこちらから.*|他の画像やクチコミの.*|クチコミの詳…)$", "", body).rstrip("… ").rstrip()
    fac = [x.strip() for x in c[9].split("、")]
    fac = [x for x in fac if x and len(x) <= 12 and not _re.search(r"[。：:【＜※]", x) and x not in SKIP_FAC][:10]
    DET[no] = dict(ra=float(c[1] or 0), rc=int(c[2] or 0), rt=rt, ci=c[4], co=c[5], rn=int(c[6] or 0), intro=INTRO.get(no, promo_clean(c[7])),
                   rev=body, rdate=(f"{int(dm.group(2))}月{int(dm.group(3))}日" if dm else ""), fac=fac, hi=HILITE.get(no, ""))
RT_LABEL = ["サービス", "立地", "部屋", "設備・アメニティ", "風呂", "食事"]
NO_AREA = {h["no"]: h["area"] for h in AREA["hotels"]}
AREA_RT = {}
for _a in set(NO_AREA.values()):
    _rs = [DET[n]["rt"] for n, a in NO_AREA.items() if a == _a and n in DET]
    AREA_RT[_a] = [round(sum(r[i] for r in _rs if r[i]) / max(1, sum(1 for r in _rs if r[i])), 2) for i in range(6)] if _rs else [0] * 6


def strengths(no):
    """エリアの★4.3以上の宿の平均より0.1以上高い項目（高い順に2つまで）。"""
    d = DET.get(no); a = NO_AREA.get(no)
    if not d or not a: return []
    av = AREA_RT[a]
    gap = sorted(((d["rt"][i] - av[i], RT_LABEL[i]) for i in range(6) if d["rt"][i] and av[i]), reverse=True)
    return [l for g, l in gap if g >= 0.1][:2]

def feat_html(no, name, base_link_aff):
    d = DET.get(no)
    if not d: return ""
    rv_u = f"https://review.travel.rakuten.co.jp/hotel/voice/{no}/"
    rv_link = f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={urllib.parse.quote(rv_u, safe='')}&m={urllib.parse.quote(rv_u, safe='')}"
    top = max(d["rt"])
    av = AREA_RT.get(NO_AREA.get(no), [0] * 6)
    bars = "".join(f'<li{" class=\"tp\"" if v == top else ""}><span class="rl">{l}</span><span class="rb"><i style="width:{v/5*100:.1f}%"></i>{f'<em style="left:{a/5*100:.1f}%" title="エリア平均 {a:.2f}"></em>' if a else ''}</span><span class="rv">{v:.2f}</span></li>' for l, v, a in zip(RT_LABEL, d["rt"], av) if v)
    st = strengths(no); an = AREA_JA.get(NO_AREA.get(no), "")
    st_html = (f'<p class="strong"><b>この宿の強み</b>{"・".join(st)}が、{an}の★4.3以上の宿の平均より高い</p>' if st
               else f'<p class="strong"><b>この宿の評価</b>どの項目も、{an}の★4.3以上の宿の平均に近い</p>')
    hi = f'<span class="hi">{esc(d["hi"])}</span>' if d["hi"] else ""
    fac = "".join(f"<li>{esc(x)}</li>" for x in d["fac"])
    rev_html = (f"""<figure class="rev">
          <figcaption>最近の口コミ{('（' + d['rdate'] + '投稿）') if d['rdate'] else ''}</figcaption>
          <blockquote><p>{esc(d['rev'])}…</p></blockquote>
          <a href="{esc(rv_link)}" target="_blank" rel="noopener sponsored">口コミをもっと読む（楽天トラベル）<span aria-hidden="true">→</span></a>
        </figure>""" if d["rev"] else "")
    return f"""
        {('<blockquote class="intro"><p>' + esc(d['intro']) + '</p><cite>宿の紹介文より（楽天トラベル）</cite></blockquote>') if d['intro'] else ''}
        <ul class="facts">{('<li>' + hi + '</li>') if hi else ''}<li><span>客室数</span><b>{d['rn']}室</b></li><li><span>チェックイン</span><b>{d['ci']}</b></li><li><span>チェックアウト</span><b>{d['co']}</b></li></ul>
        <div class="rate">
          <div class="rate-hd"><h3>泊まった人の評価</h3><span><b>{d['ra']:.2f}</b>／5（{d['rc']:,}件）</span></div>
          {st_html}
          <ul class="bars">{bars}</ul>
          <p class="bars-lg"><i></i>{an}の★4.3以上の宿の平均</p>
        </div>
{rev_html}
        {('<div class="fac"><h3>館内の施設</h3><ul>' + fac + '</ul></div>') if fac else ''}"""

built = 0
for meta in AREA["hotels"]:
    if str(meta["no"]) not in INFO: continue   # 写真・アクセスがまだ無い宿は、施設情報を取ってから作る
    slug, name, full = SLUG[meta["no"]]
    months, asof = months_for(meta)
    H = dict(slug=slug, no=meta["no"], name=name, full=full, area=AREA_JA[meta["area"]], sub=meta["loc"], tier=TIER_JA[meta["tier"]],
             avg=meta["avg"], cnt=meta["cnt"], asof=asof, aff=AFF, months=months)
    info = INFO[str(meta["no"])]
    H["thumb"] = info.get("thumb", ""); H["areaKey"] = meta["area"]; H["loc"] = meta["loc"]
    PS, PL = plan_s(meta["area"]), plan_l(meta["area"]); H["plan"] = PS
    # 同じ日なら、こっちも安い：同じエリアで★が近い（−0.1まで）宿
    _al = [h for h in AREA["hotels"] if h["area"] == meta["area"] and h["no"] != meta["no"] and str(h["no"]) in INFO and h["avg"] >= meta["avg"] - 0.1]
    _al.sort(key=lambda h: abs(h["avg"] - meta["avg"]))
    H["alts"] = [dict(no=h["no"], slug=SLUG[h["no"]][0], name=SLUG[h["no"]][1], loc=h["loc"], avg=h["avg"],
                      thumb=INFO[str(h["no"])].get("thumb", ""), p=[month_prices(h["no"], mm["y"], mm["m"]) for mm in months]) for h in _al[:15]]
    _iu = f"https://travel.rakuten.co.jp/HOTEL/{meta['no']}/{meta['no']}.html"
    info_link = f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={urllib.parse.quote(_iu, safe='')}&m={urllib.parse.quote(_iu, safe='')}"
    dmi = next((i for i, mm in enumerate(months) if (mm["y"], mm["m"]) == DEFAULT_YM), 0)
    H["dm"] = dmi
    H["camp"] = dict(bookEnd=CARD_CAMP["book_end"], outLast=CARD_CAMP["out_last"], bonus=CARD_BONUS)
    m0 = months[dmi]
    mn0 = min([v for v in m0["p"] if v] or [0])
    kd = [i + 1 for i, v in enumerate(m0["p"]) if v == mn0]
    pts0 = mn0 * 2 // 100
    diff0 = pts0 - mn0 // 100
    feat_slug = FEAT.get((meta["area"], meta["tier"]))
    crumb_area = f'{base}features/{feat_slug}/' if feat_slug else f'{base}areas/{meta["area"]}/'
    _mine = jan_min(meta["p"])   # 同じエリアで、1月の神日が近い価格の宿を6軒
    peers = sorted([h for h in AREA["hotels"] if h["area"] == meta["area"] and h["no"] != meta["no"] and str(h["no"]) in INFO and jan_min(h["p"])],
                   key=lambda h: abs(jan_min(h["p"]) - _mine))[:6]
    peers.sort(key=lambda h: jan_min(h["p"]))
    peer_html = "".join(peer_li(h) for h in peers)
    room_html = (f'<figure class="room"><a href="{esc(info_link)}" target="_blank" rel="noopener sponsored"><img src="{esc(info["room"])}" alt="{esc(name)}の客室（楽天トラベル掲載写真）" loading="lazy"></a><figcaption>客室の一例（写真：楽天トラベル）</figcaption></figure>' if info.get("room") else "")
    kdl = "・".join(f"{KM}/{d}({wd(KY,KM,d)})" for d in kd[:3])
    title = f"{name}（{H['area']}・{meta['loc']}）の神日カレンダー｜いちばん安い日と料金｜YASUMIBI"
    desc = f"{full}の宿泊料金を全日調査。{KM}月の神日は{kdl}の{yen(mn0)}（2名{PS}）。楽天カードで払った場合のポイントも試算。"
    page = HEAD.format(robots="index,follow", title=esc(title), desc=esc(desc), canon=f"hotels/{H['slug']}/", base=base, v1=v1, v2=v2, og=og_meta(esc(title), esc(desc), f"hotels/{H['slug']}/",
            f"https://yasumibi.com/assets/og/{slug}.jpg" if os.path.exists(f"{OUT}/assets/og/{slug}.jpg") else None)) + f"""
    {site_header(base)}
    <div class="wrap">
      <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span>›</span><a href="{crumb_area}">{H['area']}</a><span>›</span><b>{esc(H['name'])}</b></nav>
    </div>

    <header class="hhero">
      <a class="hphoto" href="{esc(info_link)}" target="_blank" rel="noopener sponsored" aria-label="楽天トラベルで{esc(H['name'])}の写真と詳細を見る">
        <img src="{esc(info.get('img',''))}" alt="{esc(H['name'])}の外観・館内（楽天トラベル掲載写真）" fetchpriority="high">
        <span class="credit">写真：楽天トラベル</span>
      </a>
      <div class="wrap">
        <div class="hcard">
          <div class="chips"><span>{H['area']}・{esc(H['sub'])}</span><span class="star43"><i aria-hidden="true">★</i>{H['avg']:.2f}<small>口コミ{H['cnt']:,}件</small></span></div>
          <h1>{esc(H['name'])}<small>{esc(H['full'])}</small></h1>
          <div class="hk">
            <div class="kl"><span class="tag">神日</span><span id="k-days"></span></div>
            <div class="kp"><span id="k-price" class="num"></span><span class="u">2名{PS}・税込</span></div>
          </div>
          <div class="hact">
            <button type="button" class="fav" id="fav" aria-pressed="false"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 20.5s-7.5-4.6-9.2-9.3C1.6 7.8 3.9 4.5 7.3 4.5c2 0 3.6 1.1 4.7 2.7 1.1-1.6 2.7-2.7 4.7-2.7 3.4 0 5.7 3.3 4.5 6.7-1.7 4.7-9.2 9.3-9.2 9.3z"/></svg><span>お気に入り</span></button>
          </div>
        </div>
      </div>
    </header>

    <div class="wrap">
      <section class="sv" aria-labelledby="sv-h">
    <div class="sv-hd"><h2 id="sv-h">この宿をいちばん安く泊まるには</h2><span class="pr">PR</span></div>
    <ol class="sv-rows" id="sv-rows"></ol>
    <div class="sv-total"><span id="sv-tl">神日の宿代</span><b id="sv-total"></b></div>
    <div class="sv-card">
      <a href="{esc(RK_FACE[1])}" target="_blank" rel="nofollow sponsored noopener"><img src="{esc(RK_FACE[0])}" alt="楽天カードの券面" width="200" height="200" loading="lazy"></a>
      <div><b>楽天カードで払うと</b><small>年会費永年無料<br>ポイントは宿代とは別に戻ってきます</small></div>
    </div>
    <ol class="sv-rows sv-pts" id="sv-pts"></ol>
    <div class="sv-total"><span>戻ってくるポイント</span><b id="sv-ptotal"></b></div>
    <p class="sv-note" id="sv-note">ポイントは目安です。2.5倍は予約前のエントリーと楽天カードでの事前決済が条件で、{CARD_CAMP["book_end_ja"]}までの予約・{CARD_CAMP["out_last_ja"]}チェックアウトまでの宿泊が対象です（楽天トラベルのキャンペーン）。特典分は税抜料金で計算されます。入会特典は初めて楽天カードを作る方が対象で、3,000ポイントは期間限定・3回以上の利用などの条件があります（{CARD_CAMP["checked"]}時点）。</p>
    <a class="sv-apply" href="{CARD_AFF}" target="_blank" rel="nofollow sponsored noopener">楽天カードを申し込む（年会費無料）</a>
    <a class="sv-go" href="{base}rakuten-card/">楽天カードについて詳しく見る <span aria-hidden="true">→</span></a>
  </section>

      <section class="blk" aria-labelledby="calh">
        <div class="sh"><h2 id="calh">神日カレンダー</h2><span class="j">日付を押すと料金が下に出ます</span></div>
        <div class="mtabs" role="tablist" aria-label="月">{''.join(f'<button type="button" role="tab" data-mi="{i}" aria-selected="{str(i==dmi).lower()}">{mm["m"]}月</button>' for i, mm in enumerate(months))}{'' if len(months) >= 5 else '<span class="soon">ほかの月は準備中</span>'}</div>
        <div class="pills" role="group" aria-label="泊まる曜日">
          <button type="button" data-wd="all" aria-pressed="true">すべて</button>
          <button type="button" data-wd="sat" aria-pressed="false">土曜泊</button>
          <button type="button" data-wd="wk" aria-pressed="false">日〜木泊</button>
        </div>
        <div class="hcal" id="hcal"></div>
        <div class="legend"><span><i style="background:var(--marker);border:1px solid var(--ink)"></i>神日</span><span><i style="background:var(--near)"></i>+15%まで</span><span><i style="background:var(--warm)"></i>+35%まで</span><span><i style="background:var(--high-bar)"></i>それ以上</span><span><i style="background:repeating-linear-gradient(135deg,var(--sold) 0 3px,transparent 3px 6px)"></i>満室</span></div>
      </section>

      <section class="blk alt" aria-labelledby="alth" id="alt" hidden>
        <div class="sh"><h2 id="alth">同じ日なら、こっちも安い</h2><span class="j" id="alt-j"></span></div>
        <ul class="peers" id="alt-list"></ul>
        <p class="note" id="alt-note"></p>
      </section>

      <section class="blk" aria-labelledby="rgh">
        <div class="sh"><h2 id="rgh">料金の幅</h2><span class="j" id="rg-month"></span></div>
        <div class="range" id="range"></div>
      </section>

      <section class="blk" aria-labelledby="fth">
        <div class="sh"><h2 id="fth">宿の特徴</h2></div>
        {feat_html(meta["no"], name, info_link)}
        {room_html}
        <dl class="acc"><dt>アクセス</dt><dd>{esc(info.get('access',''))}</dd><dt>最寄り駅</dt><dd>{esc(info.get('station',''))}</dd></dl>
        <p class="note">※宿の情報・評価・口コミは楽天トラベルの掲載内容です（2026年10月21日時点）。</p>
      </section>

      <section class="blk" aria-labelledby="prh">
        <div class="sh"><h2 id="prh">近くの宿の神日</h2><span class="j">{H['area']}・同じ価格帯の宿（{KY}年{KM}月）</span></div>
        <ul class="peers">{peer_html}</ul>
      </section>

      <div class="cond">※大人2名・1室・{PL}の最安プラン（2名合計・税込）。{H['asof']}時点の楽天トラベルの料金。予約前に最新の料金をご確認ください。ポイントは、楽天カードで事前決済すると楽天カード以外で払うより多くもらえる分の目安です（エントリーが必要。2.5倍は{CARD_CAMP["out_last_ja"]}チェックアウトまでの宿泊）。条件は楽天トラベルのキャンペーンページでご確認ください。宿の写真：楽天トラベル</div>
    </div>
    """ + footer(base) + f"""
    <div class="bar" id="bar">
      <div class="bi">
        <div class="bw" id="b-when"></div>
        <div class="ba"><span id="b-amt"></span><small id="b-real"></small></div>
      </div>
      <a class="bcta" id="b-cta" href="#" target="_blank" rel="noopener sponsored">予約へ</a>
    </div>
    {tabbar(base, "")}

    <div class="scrim" id="scrim" hidden></div>
    <section class="bsheet" id="bsheet" role="dialog" aria-modal="true" aria-labelledby="bs-h" hidden>
      <div class="grab" aria-hidden="true"></div>
      <h2 id="bs-h">この予約、もっと得にできます</h2>
      <ol class="ksteps">
        <li><b>神日に泊まる</b><span id="bs-1"></span></li>
        <li class="hot"><b>楽天カードで事前決済</b><span id="bs-2"></span></li>
        <li><b>普段の支払いは2枚目で</b><span>マイルや還元を、次の旅費に回す</span></li>
      </ol>
      <p class="bs-note">楽天トラベルでは「{PL}」のプランを選ぶと、表示の料金になります（素泊まりなど他のプランが先に表示されることがあります）。</p>
      <a class="bs-main" href="{CARD_AFF}" target="_blank" rel="nofollow sponsored noopener">先に楽天カードを申し込む（年会費無料）</a>
      <a class="bs-skip" id="bs-skip" href="#" target="_blank" rel="noopener sponsored">このまま楽天トラベルで予約する →</a>
      <button type="button" class="bs-x" id="bs-x" aria-label="閉じる">×</button>
    </section>

    <script>window.HOTEL = {json.dumps(H, ensure_ascii=False, separators=(",", ":"))};</script>
    <script src="{base}assets/hotel.js?v={v2}"></script>
    </body></html>
    """
    os.makedirs(f"{OUT}/hotels/{slug}", exist_ok=True)
    open(f"{OUT}/hotels/{slug}/index.html", "w", encoding="utf-8").write(page)
    # お気に入りの比較ページ用（その宿の料金だけの小さなデータ）
    json.dump({k: H[k] for k in ("slug", "no", "name", "area", "areaKey", "loc", "avg", "cnt", "thumb", "months", "aff", "plan")},
              open(f"{OUT}/hotels/{slug}/data.json", "w"), ensure_ascii=False, separators=(",", ":"))
    built += 1
mn0 = built; kd = []; pts0 = diff0 = 0

# ------------------------------------------------------------------ /otoku/
ob = "../"
TOPU = ob
v3 = ver("top.css", "otoku.css")
_ot, _od = "旅費を下げる3つの方法｜YASUMIBI", "神日に泊まる、楽天カードで払う、2枚目を選ぶ。旅費を下げる3つの方法と、楽天カードの還元の試算。"
ohead = HEAD.format(robots="index,follow", title=_ot, desc=_od, canon="otoku/", base=ob, v1=v1, v2=v2, og=og_meta(_ot, _od, "otoku/"))
ohead = ohead.replace('<body class="app">', f'<link rel="stylesheet" href="{ob}assets/top.css?v={v3}">\n<link rel="stylesheet" href="{ob}assets/otoku.css?v={v3}">\n</head>\n<body class="app top2 otk">').replace("</head>\n<link", "<link", 1)
otabs = tabbar(ob, "otoku")
otoku = ohead + f"""
{site_header(ob, "otoku")}

<main class="gin ok">
  <nav class="crumb" aria-label="現在地"><a href="{TOPU}">ホーム</a><span aria-hidden="true">›</span><span>さらに安く</span></nav>
  <header class="ok-hd">
    <h1>旅費を、もう一段下げる。</h1>
    <p>同じ宿でも、泊まる日と払い方で旅費は変わります。YASUMIBIがすすめるのは、この3つの順番です。</p>
  </header>

  <ol class="ksteps">
    <li>
      <span class="sn">01</span>
      <div class="sb">
        <h2>神日に泊まる</h2>
        <p>同じ宿でも、泊まる日で料金は大きく変わります。まずは、その月でいちばん安い日を選びます。</p>
        <a class="lk" href="{TOPU}#search">神日を探す<span aria-hidden="true">→</span></a>
      </div>
    </li>
    <li id="rakuten">
      <span class="sn">02</span>
      <div class="sb">
        <h2>楽天カードで払う</h2>
        <p>楽天トラベルでエントリーして楽天カードで事前決済すると、国内宿泊のポイントは2.5倍。楽天カード以外で払うと1倍です（2.5倍は{CARD_CAMP["out_last_ja"]}チェックアウトまでの宿泊）。はじめての方は、入会と利用で合計5,000ポイントの特典もあります。ポイントは宿代とは別に戻ってきます。</p>
        <section class="calc2" aria-labelledby="ch">
          <div class="c-hd"><h3 id="ch">戻ってくるポイントを計算する</h3><span class="pr">PR</span></div>
          <label class="c-in" for="cv"><span>宿代（2名分・税込）</span><span class="ci"><span aria-hidden="true">¥</span><input id="cv" inputmode="numeric" value="50,000" autocomplete="off"></span></label>
          <ol class="c-rows" id="cr" aria-live="polite"></ol>
          <div class="c-total"><span>戻ってくるポイント</span><b id="ct"></b></div>
          <p class="c-note">楽天カードで事前決済した場合（エントリーが必要・2.5倍）の目安です。特典分は税抜料金で計算されます。入会特典は初めて楽天カードを作る方が対象で、3,000ポイントは期間限定・3回以上の利用などの条件があります（{CARD_CAMP["checked"]}時点）。</p>
          <a class="c-apply" href="{CARD_AFF}" target="_blank" rel="nofollow sponsored noopener">楽天カードを申し込む（年会費無料）</a>
          <p class="c-fine">申し込み・審査・特典の条件は、楽天カードの公式ページでご確認ください。</p>
          <a class="ok-more" href="{ob}rakuten-card/">実際の宿での試算と、上位カードとの違いを見る →</a>
        </section>
      </div>
    </li>
    <li>
      <span class="sn">03</span>
      <div class="sb">
        <h2>2枚目のカードを選ぶ</h2>
        <p>旅以外の支払いにも、合うカードは人によって違います。宿の予約は楽天カード、ふだんの支払いはもう1枚、という分け方がおすすめです。</p>
        <a class="lk" href="{ob}cards/">カードを見る<span aria-hidden="true">→</span></a>
      </div>
    </li>
  </ol>

  <p class="ok-note">※ポイント率は通常分の目安です。キャンペーンや利用条件で変わることがあります。最新の条件は楽天の公式ページでご確認ください。</p>
</main>
""" + footer(ob) + otabs + """
<script>
(function(){const i=document.getElementById('cv'),r=document.getElementById('cr'),t=document.getElementById('ct');
const n=(v)=>v.toLocaleString('ja-JP');
function f(){const v=parseInt((i.value||'').replace(/[^0-9]/g,''),10)||0;const tb=Math.floor(v*10/11),b=Math.floor(tb/100),x=Math.floor(v/100)+Math.floor(tb/200);
if(!v){r.innerHTML='<li><span>金額を入れてください</span></li>';t.textContent='—';return;}
r.innerHTML='<li><span>楽天カード以外で払っても（1倍）</span><b>'+n(b)+'円分</b></li>'+
'<li class="dn"><span>楽天カードで事前決済すると増える分</span><b>+'+n(x)+'円分</b></li>'+
'<li class="dn"><span>はじめての方：入会特典</span><b>+2,000円分</b></li>'+
'<li class="dn"><span>はじめての方：3回利用の特典（期間限定）</span><b>+3,000円分</b></li>';
t.textContent=n(b+x+5000)+'円分';}
i.addEventListener('input',f);i.addEventListener('blur',()=>{const v=parseInt((i.value||'').replace(/[^0-9]/g,''),10);if(v)i.value=n(v);});f();})();
</script>
</body></html>
"""
os.makedirs(f"{OUT}/otoku", exist_ok=True)
open(f"{OUT}/otoku/index.html", "w", encoding="utf-8").write(otoku)
print("hotel + otoku built", mn0, kd, pts0, diff0)
