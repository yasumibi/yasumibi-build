"""Build the YASUMIBI static site from data/area_jan2027.json into yasumibi-site/."""
import json, os, datetime, html

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # このリポジトリ
OUT = os.environ.get("YB_OUT", os.path.join(os.path.dirname(ROOT), "yasumibi-site"))  # 公開用リポジトリ（隣に置く）
import sys; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import img_v
from common import B_AREA_NAMES, B_AREA_LABEL, is_b, plan_s, plan_l, COND_PLAN
from common import site_header, tabbar, footer as cfooter, og_meta, load_area
D = load_area()
from common import month_prices
D["hotels"] = [h for h in D["hotels"] if h.get("added") == "2026-10-19"]   # 特集4本は最初の20軒で組んだ記事（2027年1月）
for _h in D["hotels"]: _h["p"] = month_prices(_h["no"], 2027, 1)
INFO = json.load(open(f"{ROOT}/data/hotel_info_20261021.json"))["hotels"]

def logo_html(base, href=None):
    href = base if href is None else href
    return (f'<a class="brand" href="{href}" aria-label="YASUMIBI ホーム">'
            f'<img class="lg-l" src="{base}assets/img/logo.png" alt="YASUMIBI" width="714" height="120">'
            f'<img class="lg-d" src="{base}assets/img/logo-dark.png" alt="" width="714" height="120"></a>')

def img_of(no): return INFO.get(str(no), {}).get("img", "")
def thumb_of(no): return INFO.get(str(no), {}).get("thumb", "")
ASOF = D.get("asof", "2026年10月20日")
Y, M, ND = 2027, 1, 31
ISSUE = "No.001"
MONTH_EN = "JANUARY 2027"
WD = "日月火水木金土"
AREA_JA = {"hakone": "箱根", "atami": "熱海"}
TIER_JA = {"mid": "2人で5万円前後", "high": "2人で10万円前後"}

FEATURES = [
    dict(slug="hakone-5man", area="hakone", tier="mid", no="01", title="箱根の神日", sub="2人で5万円前後の人気宿5軒、1月の最安日",
         img="hakone-fuji-ship.jpg", credit="Photo: Guilhem Vellut / CC BY 2.0"),
    dict(slug="hakone-10man", area="hakone", tier="high", no="02", title="箱根、10万円の夜", sub="天悠、富士屋ホテルほか5軒の最安日",
         img="hakone-torii.jpg", credit="Photo: Guilhem Vellut / CC BY 2.0"),
    dict(slug="atami-5man", area="atami", tier="mid", no="03", title="熱海の神日", sub="2人で5万円前後の人気宿5軒、1月の最安日", img="atami-panorama.jpg", credit="Photo: Photos of Japan / CC0"),
    dict(slug="atami-10man", area="atami", tier="high", no="04", title="熱海、10万円の夜", sub="迎賓館、大観荘ほか5軒の最安日", img="atami-fireworks.jpg", credit="Photo: Izunosuke / CC BY 3.0（明るさ・切り抜きを調整）"),
]

def wd(d): return WD[(datetime.date(Y, M, d).weekday() + 1) % 7]
def lab(d): return f"{M}/{d}({wd(d)})"
def yen(v): return "¥{:,}".format(v)
def esc(s): return html.escape(s, quote=True)

def stats(hs):
    mins = {h["no"]: min(v for v in h["p"] if v) for h in hs}
    best_day, best_cnt = None, -1
    for d in range(1, ND + 1):
        c = sum(1 for h in hs if h["p"][d - 1] == mins[h["no"]])
        if c > best_cnt: best_day, best_cnt = d, c
    gaps = []
    for h in hs:
        vs = [(v, i + 1) for i, v in enumerate(h["p"]) if v]
        hi = max(vs); lo = min(vs, key=lambda x: (x[0], x[1]))
        gaps.append((hi[0] - lo[0], h, hi, lo))
    gaps.sort(key=lambda x: -x[0])
    sat_same = [h for h in hs if any(h["p"][d - 1] == mins[h["no"]] for d in range(1, ND + 1) if wd(d) == "土")]
    return dict(mins=mins, best_day=best_day, best_cnt=best_cnt, gap=gaps[0], sat_same=sat_same)

def findings(s):
    gap, gh, hi, lo = s["gap"]
    li = [f'<li><b>{lab(s["best_day"])}泊</b>5軒中{s["best_cnt"]}軒がその宿の最安値（神日）</li>',
          f'<li><b>最大の価格差</b>{esc(gh["name"])}：{lab(hi[1])}泊 {yen(hi[0])} → {lab(lo[1])}泊 {yen(lo[0])}（差額 {gap:,}円）</li>']
    if s["sat_same"]:
        li.append(f'<li><b>土曜泊</b>神日と同額で泊まれるのは{"・".join(esc(h["name"]) for h in s["sat_same"])}のみ</li>')
    else:
        li.append('<li><b>土曜泊</b>5軒とも神日より割高</li>')
    return '<ul class="find">' + "".join(li) + "</ul>"

import hashlib
VER = hashlib.md5((open(f"{OUT}/assets/site.css","rb").read() + open(f"{OUT}/assets/feature.js","rb").read())).hexdigest()[:8]

HEAD = """<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
{og}<link rel="canonical" href="https://yasumibi.com/{canon}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={ver}">
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body{bodycls}>
"""

def _old_footer(base):
    return f"""<div class="wrap">
<footer class="site">
  <nav aria-label="サイト情報"><a href="{base}about/">YASUMIBIについて</a><a href="{base}about/#operator">運営者情報</a><a href="{base}privacy/">プライバシーポリシー</a><a href="{base}disclosure/">広告の掲載について</a></nav>
  <nav aria-label="SNS" class="sns"><a href="https://www.instagram.com/yasumibi.travel/" target="_blank" rel="noopener">Instagram</a><a href="https://www.tiktok.com/@yasumibi.travel" target="_blank" rel="noopener">TikTok</a></nav>
  <div>本サイトは楽天アフィリエイトを利用しています。掲載している料金は調べた時点のもので、予約時の料金と異なる場合があります。</div>
  <div><a href="https://webservice.rakuten.co.jp/" target="_blank" rel="noopener">Supported by Rakuten Developers</a>　© YASUMIBI</div>
</footer>
</div>
"""

def runhead(base, page):
    return site_header(base) + '<div class="wrap">\n'

def footer(base):
    return cfooter(base)

def write(path, s):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(s)

def photo_block(f, base, seal=None):
    style = f' style="background-image:url({base}assets/img/{f["img"]}?v={img_v(f["img"])})"' if f["img"] else ""
    cr = f'<span class="credit">{esc(f["credit"])}</span>' if f["credit"] else ""
    sl = f'<div class="stat">{seal}</div>' if seal else ""
    t = f["title"]
    return f'<div class="photo"{style} role="img" aria-label="{esc(t)}"><span class="label lbl">特集</span>{sl}<p class="ttl">{esc(t)}<span>。</span></p>{cr}</div>'

# ---------------- feature pages ----------------
for f in FEATURES:
    hs = [h for h in D["hotels"] if h["area"] == f["area"] and h["tier"] == f["tier"]]
    s = stats(hs)
    gap, gh, hi, lo = s["gap"]
    bd = s["best_day"]
    n = s["best_cnt"]
    h1 = f"{lab(bd)}泊、5軒中{n}軒が神日。" if n >= 2 else f"{AREA_JA[f['area']]}の5軒、{M}月の神日。"
    lede = h1
    finds = findings(s)
    spec = (f'<dl class="spec"><dt>対象</dt><dd>{AREA_JA[f["area"]]}・{TIER_JA[f["tier"]]}の人気宿5軒</dd>'
            f'<dt>期間</dt><dd>{Y}年{M}月1日〜{ND}日泊（{ND}日分）</dd>'
            f'<dt>条件</dt><dd>大人2名・1室・1泊2食付きの最安プラン（税込）</dd>'
            f'<dt>調査日</dt><dd>{ASOF}</dd></dl>')
    pct = round(lo[0] / hi[0] * 100)
    rows = ""
    for h in sorted(hs, key=lambda h: s["mins"][h["no"]]):
        mn = s["mins"][h["no"]]
        cells = ""
        for d in range(1, ND + 1):
            v = h["p"][d - 1]
            t = "so" if not v else ("t0" if v <= mn else "t1" if v / mn <= 1.15 else "t2" if v / mn <= 1.35 else "t3")
            sat = " sat" if wd(d) == "土" else ""
            cells += f'<td class="c {t}{sat}" title="{lab(d)} {yen(v) if v else "満室"}">{f"{v/10000:.1f}" if v else ""}</td>'
        rows += f'<tr><th scope="row">{esc(h["name"].replace("小田急 ","").replace("箱根仙石原プリンスホテル","仙石原プリンス").replace("ホテルグランバッハ熱海クレッシェンド","グランバッハ熱海"))}</th>{cells}</tr>'
    head = "".join(f'<td class="{ {"土": "sa", "日": "su"}.get(wd(d), "") }">{d}<small>{wd(d)}</small></td>' for d in range(1, ND + 1))
    foot = ""
    data = {"year": Y, "month": M, "days": ND, "hotels": [dict(no=h["no"], name=h["name"], loc=h["loc"], avg=h["avg"], cnt=h["cnt"], p=h["p"], img=img_of(h["no"])) for h in hs]}
    base = "../../"
    title = f"{AREA_JA[f['area']]}の神日カレンダー（{TIER_JA[f['tier']]}・{Y}年{M}月）｜YASUMIBI"
    desc = f"{AREA_JA[f['area']]}の人気宿5軒の神日カレンダー。{lede}{Y}年{M}月泊の料金を全日調査。"
    page = HEAD.format(ver=VER, canon=f"features/{f['slug']}/", title=esc(title), desc=esc(desc), base=base, bodycls=' class="has-sheet"', og=og_meta(esc(title), esc(desc), f"features/{f['slug']}/")) + runhead(base, "") + f"""
<div class="cover">
  {photo_block(f, base)}
  <div class="lede">
    <div class="eyebrow">特集{f['no']}｜{AREA_JA[f['area']]}・{TIER_JA[f['tier']]}・{Y}年{M}月泊</div>
    <h1>{esc(h1)}</h1>
    {finds}
    <div class="figs">
      <div><div class="n">{ND*5}</div><div class="t">調査した料金<br>（5軒×{ND}日）</div></div>
      <div><div class="n">{n}/5</div><div class="t">{lab(bd)}泊が<br>神日の宿</div></div>
      <div><div class="n">{pct}%</div><div class="t">最大差の宿の<br>最高値比の料金</div></div>
    </div>
    {spec}
  </div>
</div>

<section class="blk" aria-labelledby="mh">
  <div class="sh"><h2 id="mh">料金マップ</h2><span class="j">数字は1泊2名の料金（万円）。色は宿ごとの最安が基準</span></div>
  <div class="mx"><table>
    <thead><tr><th></th>{head}</tr></thead>
    <tbody>{rows}</tbody>
  </table></div>
  <div class="legend mxl"><span><i class="t0"></i>神日（その宿の最安）</span><span><i class="t1"></i>+15%まで</span><span><i class="t2"></i>+35%まで</span><span><i class="t3"></i>それ以上</span><span><i style="background:repeating-linear-gradient(135deg,var(--sold) 0 3px,transparent 3px 6px)"></i>満室・プランなし</span></div>
</section>

<section class="blk" aria-labelledby="hh">
  <div class="sh"><h2 id="hh">神日カレンダー</h2><span class="j">宿をタップして日付を選ぶ</span></div>
  <div class="pills" role="group" aria-label="泊まる曜日">
    <button type="button" data-wd="all" aria-pressed="true">すべての日</button>
    <button type="button" data-wd="sat" aria-pressed="false">土曜泊だけ</button>
    <button type="button" data-wd="wk" aria-pressed="false">日〜木泊だけ</button>
  </div>
  <div class="hotels" id="hotels"></div>
  <div class="cond">※大人2名・1室・1泊2食付きの最安プラン（2名合計・税込）。{ASOF}時点の楽天トラベルの料金。予約前に最新料金をご確認ください。宿の写真：楽天トラベル</div>
</section>
</div>
""" + footer(base) + f"""
<div class="sheet" aria-live="polite"><div class="in">
  <div class="who" id="s-who"></div>
  <a class="cta" id="s-cta" href="#" target="_blank" rel="noopener sponsored">楽天トラベルで<br>空室を見る</a>
  <div class="when" id="s-when"></div>
  <div class="amt" id="s-amt"></div>
</div></div>
<script>window.FEATURE = {json.dumps(data, ensure_ascii=False)};</script>
<script src="{base}assets/feature.js?v={VER}"></script>
</body></html>
"""
    write(f"{OUT}/features/{f['slug']}/index.html", page)
    f["stats"] = s

# ---------------- top page ----------------
AFF = "589faade.b97f81b7.589faadf.010fa421"
def link_for(no, d):
    import urllib.parse
    d2 = datetime.date(Y, M, d) + datetime.timedelta(days=1)
    u = (f"https://hotel.travel.rakuten.co.jp/hotelinfo/plan/{no}?f_nen1={Y}&f_tuki1={M}&f_hi1={d}"
         f"&f_nen2={d2.year}&f_tuki2={d2.month}&f_hi2={d2.day}&f_heya_su=1&f_otona_su=2")
    q = urllib.parse.quote(u, safe="")
    return f"https://hb.afl.rakuten.co.jp/hgc/{AFF}/?pc={q}&m={q}"

boards = {}
for area in ("hakone", "atami"):
    items = []
    for tier in ("mid", "high"):
        hs = sorted([h for h in D["hotels"] if h["area"] == area and h["tier"] == tier], key=lambda h: min(v for v in h["p"] if v))
        for h in hs:
            mn = min(v for v in h["p"] if v)
            days = [i + 1 for i, v in enumerate(h["p"]) if v == mn]
            dt = "・".join(lab(d) for d in days[:3]) + (f" ほか{len(days)-3}日" if len(days) > 3 else "")
            items.append(f'<li><a href="{esc(link_for(h["no"], days[0]))}" target="_blank" rel="noopener sponsored"><img class="th" src="{esc(thumb_of(h["no"]))}" alt="" loading="lazy" width="300" height="200"><span class="bx"><span class="tier">{TIER_JA[tier]} ／ {esc(h["loc"])}</span>'
                         f'<span class="nm">{esc(h["name"])}<span class="dt"><span class="kami">神日</span>{dt}</span></span></span>'
                         f'<span class="p">{yen(mn)}<small>楽天トラベルで見る →</small></span></a></li>')
    boards[area] = "".join(items)

f1 = FEATURES[0]; s1 = f1["stats"]; g1 = s1["gap"]
toc = "".join(f'<li><a href="features/{f["slug"]}/"><span class="no">{f["no"]}</span><span class="tt">{esc(f["title"])}。<span class="sub">{esc(f["sub"])}</span></span><span class="ar" aria-hidden="true">→</span></a></li>' for f in FEATURES)
toc += '<li><div class="soonrow"><span class="no">05</span><span class="tt">旅費をカードで払うと、いくら戻る？<span class="sub">ポイント還元の試算</span></span><span class="soon">準備中</span></div></li>'
top = HEAD.format(ver=VER, canon="", title="神日カレンダー｜YASUMIBI 休み日を、安い日に。", desc="神日カレンダーは、人気宿の料金を全日調べて最安日（神日）を示すYASUMIBIのカレンダー。箱根・熱海の宿の安い日がひと目でわかる。", base="", bodycls="", og="") + f"""<div class="wrap">
  <h1 class="mast" aria-label="YASUMIBI">YASUMIBI</h1>
  <div class="tagrow"><span>休み日を、安い日に。</span><b>神日カレンダー</b></div>

  <div class="cover">
    {photo_block(f1, "", seal=f'<span class="k">最大の差</span><span class="v">¥{g1[0]:,}</span><span class="s">同じ宿、泊まる日だけの差</span>')}
    <div class="lede">
      <div class="eyebrow">今月の特集｜箱根</div>
      <h2>{lab(s1['best_day'])}泊、<span class="mk">5軒中{s1['best_cnt']}軒</span>が神日。</h2>
      {findings(s1)}
      <div class="figs">
        <div><div class="n">155</div><div class="t">調査した料金<br>（5軒×31日）</div></div>
        <div><div class="n">{s1['best_cnt']}/5</div><div class="t">{lab(s1['best_day'])}泊が<br>神日の宿</div></div>
        <div><div class="n">{round(g1[3][0]/g1[2][0]*100)}%</div><div class="t">最大差の宿の<br>最高値比の料金</div></div>
      </div>
      <a class="more" href="features/{f1['slug']}/">特集を読む <span aria-hidden="true">→</span></a>
    </div>
  </div>

  <section class="blk" id="kamibi" aria-labelledby="kh">
    <div class="sh"><h2 id="kh">神日カレンダー</h2><span class="j">{Y}年{M}月泊・{ASOF.split("年",1)[1]}更新</span></div>
    <div class="pills" role="group" aria-label="エリア">
      <button type="button" data-a="hakone" aria-pressed="true">箱根</button>
      <button type="button" data-a="atami" aria-pressed="false">熱海</button>
    </div>
    <ul class="board" id="b-hakone">{boards['hakone']}</ul>
    <ul class="board" id="b-atami" hidden>{boards['atami']}</ul>
    <div class="cond">※{COND_PLAN}（2名合計・税込）。{ASOF}時点の楽天トラベルの料金。予約前に最新料金をご確認ください。宿の写真：楽天トラベル</div>
  </section>

  <section class="blk" aria-labelledby="ch">
    <div class="sh"><h2 id="ch">特集一覧</h2><span class="j">エリアと価格帯ごと</span></div>
    <ol class="toc">{toc}</ol>
  </section>
</div>

<section class="band" aria-labelledby="ah">
  <div class="wrap"><div class="in">
    <div class="ma">YASUMIBI</div>
    <div>
      <h2 id="ah">休みは、安い日にずらせばいい。</h2>
      <p>宿の料金を実際に調べ、「泊まるならこの日」を示す旅の料金誌。休みを自分で調整できる二人に向けて、同じ宿の日ごとの料金差をカレンダーと数字で掲載。</p>
      <p><a href="about/">YASUMIBIについて →</a></p>
    </div>
  </div></div>
</section>
""" + footer("") + """<script>
  document.querySelectorAll("[data-a]").forEach((b) => b.addEventListener("click", () => {
    document.querySelectorAll("[data-a]").forEach((x) => x.setAttribute("aria-pressed", String(x === b)));
    document.getElementById("b-hakone").hidden = b.dataset.a !== "hakone";
    document.getElementById("b-atami").hidden = b.dataset.a !== "atami";
  }));
  function fitMast() {
    const m = document.querySelector(".mast"); if (!m) return; m.style.fontSize = "100px";
    const r = document.createRange(); r.selectNodeContents(m); const w = r.getBoundingClientRect().width;
    if (w) m.style.fontSize = Math.floor(100 * m.clientWidth / w * 0.995) + "px";
  }
  (document.fonts ? document.fonts.ready : Promise.resolve()).then(fitMast); fitMast();
  window.addEventListener("resize", fitMast);
</script>
</body></html>
"""
# 旧トップは廃止（新トップは build_top2.py が / に出力）

# ---------------- prose pages ----------------
OP_NAME = os.environ.get("OP_NAME", "YASUMIBI編集部")
OP_MAIL = os.environ.get("OP_MAIL", "contact@yasumibi.com")
prose = {
"about": ("YASUMIBIについて", "サイトについて", f"""
<h1>安い日に、休みを合わせる。</h1>
<p>YASUMIBI（ヤスミビ）は「休み日」と「安い日」をかけた名前。これまでは、休みの日に安い宿を探していました。YASUMIBIは逆。先に安い日を知って、休みをそこに合わせます。</p>
<h2>掲載する宿の基準</h2>
<p>載せるのは、次の3つをすべて満たす宿だけです。</p>
<dl><dt>★4.3以上</dt><dd>楽天トラベルの口コミ評価が4.3以上。安くても満足できる宿だけ</dd>
<dt>口コミ50件以上</dt><dd>身内の高評価だけで4.3、は除外。たくさんの人が泊まって、それでも高評価の宿</dd>
<dt>1泊2食付き</dt><dd>同じ条件で比べるため。朝ごはんと夕ごはんまで込みの料金です{("。ただし" + B_AREA_LABEL + "は、2食付きの宿が少ないため1泊朝食付きで比べます（ほかのエリアと同じランキングには入れません）") if B_AREA_NAMES else ""}</dd></dl>
<p>口コミ評価は毎週取り直しています。基準を下回った宿は、掲載から外します。広告の有無で、載せる宿や順位を変えることはありません。</p>
<h2>料金の調べ方</h2>
<dl><dt>データ元</dt><dd>楽天トラベル（楽天ウェブサービス）の公開データ</dd><dt>条件</dt><dd>{COND_PLAN}（2名合計・税込）</dd><dt>対象</dt><dd>上の基準を満たす宿（全国の温泉地・観光地）</dd><dt>更新</dt><dd>毎日自動で再取得。近い日付ほど頻繁に取り直し、各ページに調査日を記載。過ぎた日の料金は表示しません</dd></dl>
<p>料金・空室は日々変動します。予約前に楽天トラベルで最新の料金をご確認ください。</p>
<h2>用語</h2>
<dl><dt>神日（かみび）</dt><dd>その宿の、その月の最安値の日</dd><dt>料金</dt><dd>{COND_PLAN}の2名合計（税込）</dd></dl>
<h2 id="operator">運営者情報</h2>
<dl><dt>サイト名</dt><dd>YASUMIBI</dd><dt>運営者</dt><dd>{esc(OP_NAME)}</dd><dt>お問い合わせ</dt><dd>{esc(OP_MAIL)}</dd><dt>SNS</dt><dd><a href="https://www.instagram.com/yasumibi.travel/" target="_blank" rel="noopener">Instagram @yasumibi.travel</a><br><a href="https://www.tiktok.com/@yasumibi.travel" target="_blank" rel="noopener">TikTok @yasumibi.travel</a></dd></dl>
"""),
"privacy": ("プライバシーポリシー", "ポリシー", """
<h1>プライバシーポリシー</h1>
<h2>アクセス解析について</h2>
<p>当サイトでは、サイトの改善のために、次のアクセス解析ツールを利用しています。収集する情報に、氏名・メールアドレスなど個人を特定する情報は含みません。</p>
<h3>Google アナリティクス（Google LLC）</h3>
<p>Cookieを使って、閲覧したページ、参照元、おおよその地域、端末やブラウザの種類、サイト内でのクリック（楽天トラベルやカードへのリンク、お気に入りへの追加、検索など）の情報をGoogleに送信し、利用状況の集計に使います。Googleによるデータの扱いは<a href="https://policies.google.com/technologies/partner-sites?hl=ja" target="_blank" rel="noopener">「Google のサービスを使用するサイトやアプリから収集した情報の Google による使用」</a>をご覧ください。ブラウザのCookieを無効にするか、<a href="https://tools.google.com/dlpage/gaoptout?hl=ja" target="_blank" rel="noopener">Google アナリティクス オプトアウト アドオン</a>を使うと、収集を止められます。</p>
<h3>Cloudflare Web Analytics（Cloudflare, Inc.）</h3>
<p>ページの表示の速さと閲覧ページなどの統計を集計します。Cookieは使いません。</p>
<p>お気に入りに入れた宿は、お使いの端末（ブラウザ）の中だけに保存し、当サイトのサーバーには送信しません。</p>
<h2>アフィリエイトについて</h2>
<p>当サイトは楽天アフィリエイトなどのアフィリエイトプログラムを利用しています。当サイトのリンクから楽天トラベルやクレジットカード会社などのサイトに移動し、予約・申し込みが行われた場合、当サイトが紹介料を受け取ることがあります。リンク先での個人情報の取り扱いは、各サービスの規約に従います。</p>
<h2>掲載情報について</h2>
<p>掲載している料金・空室は調べた時点の情報で、予約時の内容と異なる場合があります。当サイトの情報によって生じた損害について、当サイトは責任を負いかねます。</p>
<h2>改定</h2>
<p>本ポリシーは、必要に応じて内容を改定することがあります。</p>
"""),
"disclosure": ("広告の掲載について", "広告について", """
<h1>広告の掲載について</h1>
<p>当サイトは、楽天アフィリエイトなどのアフィリエイトプログラムを利用した広告を掲載しています。宿の料金カレンダーや「楽天トラベルで見る」「予約へ」などのリンク、クレジットカードの紹介リンクを経由して予約・申し込みが行われた場合、当サイトに紹介料が支払われることがあります。</p>
<p>広告を含むページには、ページ上部に「PR」と表示しています。</p>
<p>紹介料の有無によって、掲載する宿の選び方や料金の表示を変えることはありません。料金はすべて楽天トラベルの公開データをそのまま掲載しています。</p>
"""),
}
for slug, (t, pg, bodyhtml) in prose.items():
    page = HEAD.format(ver=VER, canon=f"{slug}/", title=f"{t}｜YASUMIBI 神日カレンダー", desc=f"YASUMIBI {t}", base="../", bodycls="", og=og_meta(f"{t}｜YASUMIBI", f"YASUMIBI {t}", f"{slug}/")) + runhead("../", pg) + f'<article class="prose">{bodyhtml}</article>\n</div>\n' + footer("../") + "</body></html>\n"
    write(f"{OUT}/{slug}/index.html", page)

write(f"{OUT}/robots.txt", "User-agent: *\nAllow: /\nSitemap: https://yasumibi.com/sitemap.xml\n")
_hs = sorted(os.listdir(f"{OUT}/hotels")) if os.path.isdir(f"{OUT}/hotels") else []
_ar = sorted(os.listdir(f"{OUT}/areas")) if os.path.isdir(f"{OUT}/areas") else []
urls = [""] + [x for x in ("ranking/", "ranking/asa/", "renkyu/", "renkyu/2027/", "otoku-days/", "weekend/", "features/") if os.path.isdir(f"{OUT}/{x}")] + [f"areas/{x}/" for x in _ar] + [f"features/{x}/" for x in ("hakone-5man", "hakone-10man", "atami-5man", "atami-10man", "kusatsu-winter", "yufuin-2haku", "beppu-1man", "kinugawa-heijitsu", "gero-gohan", "noboribetsu-size", "arima-renkyu", "kyoto-koyo", "kyoto-asagohan", "kyoto-46", "okinawa-month", "okinawa-ritou", "sapporo-yukimatsuri", "sapporo-1man", "hakone-rotenburo", "atami-youbi", "yufuin-month", "beppu-doyou", "izukogen-pet", "karuizawa-luxury", "kinosaki-kani", "ito-1man", "akogare", "hc-hakone", "hc-kyoto", "hc-karuizawa", "hc-okinawa")] + [f"hotels/{h}/" for h in _hs] + ["otoku/", "rakuten-card/", "cards/", "about/", "privacy/", "disclosure/"]
urls += sorted(os.path.relpath(r, OUT) + "/" for r, ds, fs in os.walk(f"{OUT}/tags") if "index.html" in fs)
today = datetime.date.today().isoformat()
write(f"{OUT}/sitemap.xml", '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"  <url><loc>https://yasumibi.com/{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n")
print("built", len(FEATURES), "features")
