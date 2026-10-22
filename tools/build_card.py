"""/rakuten-card/ — 楽天カードの紹介ページ（実際の宿の料金で試算）。"""
import os, sys, json, html, hashlib, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import site_header, tabbar, footer, og_meta, load_area, OUT, ASOF, CARD_AFF, KY, KM, AREA_JA

CHECKED = "2026年10月21日"  # 楽天カード公式ページで条件を確認した日
from common import SLUG
WD = "日月火水木金土"


def esc(s): return html.escape(str(s), quote=True)
def yen(v): return "¥{:,}".format(v)
def lab(d): return f"{KM}/{d}({WD[(datetime.date(KY, KM, d).weekday() + 1) % 7]})"
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


# ---- 実際の宿で試算（1月・土曜平均 → 神日 → 2.5% → 入会と利用の特典5,000pt）
area = load_area()
_INFO = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "hotel_info_20261021.json")))["hotels"]
area["hotels"] = [h for h in area["hotels"] if str(h["no"]) in _INFO]
rows = []
for h in area["hotels"]:
    p = h["p"]; vs = [v for v in p if v]
    if not vs: continue
    mn = min(vs); d = p.index(mn) + 1
    _nyr = lambda d: (KM == 1 and d <= 3) or (KM == 12 and d >= 29)   # 年末年始は除く
    sat = [p[i] for i in range(len(p)) if p[i] and not _nyr(i + 1) and (datetime.date(KY, KM, i + 1).weekday() == 5)]
    if not sat: continue
    sa = round(sum(sat) / len(sat))
    if sa <= mn: continue
    pts = mn * 25 // 1000
    rows.append(dict(h=h, mn=mn, d=d, sa=sa, pts=pts, real=mn - pts - 5000, save=sa - (mn - pts - 5000)))
ex = []
for tier in ("mid", "high"):
    c = sorted([r for r in rows if r["h"]["tier"] == tier], key=lambda r: -r["save"])
    if c: ex.append(c[0])


# 楽天アフィリエイトの公式素材（券面画像・200x200）と、その画像に紐づくリンク。加工せずそのまま使う。
CARD_IMG = {
    "card": ("https://hbb.afl.rakuten.co.jp/hsb/58adb89a.1783e5b6.58ad7ff2.3c792b49/?me_id=2101008&me_adv_id=373425&t=pict",
             "https://hb.afl.rakuten.co.jp/hsc/58adb89a.1783e5b6.58ad7ff2.3c792b49/?link_type=pict&ut=eyJwYWdlIjoic2hvcCIsInR5cGUiOiJwaWN0IiwiY29sIjoxLCJjYXQiOiIxIiwiYmFuIjozNzM0MjUsImFtcCI6ZmFsc2V9"),
    "premium": ("https://hbb.afl.rakuten.co.jp/hsb/58adb74a.9556203e.58ad7ff2.3c792b49/?me_id=2101014&me_adv_id=2084807&t=pict",
                "https://hb.afl.rakuten.co.jp/hsc/58adb74a.9556203e.58ad7ff2.3c792b49/?link_type=pict&ut=eyJwYWdlIjoic2hvcCIsInR5cGUiOiJwaWN0IiwiY29sIjoxLCJjYXQiOjEsImJhbiI6MjA4NDgwNywiYW1wIjpmYWxzZX0%3D"),
}


def bar(r):
    """土曜平均を100%とした横棒：実質（黒）＋特典（黄）＋ポイント（黄）＋神日の差（緑）"""
    sa = r["sa"]; seg = [("s-real", r["real"]), ("s-bonus", 5000), ("s-pts", r["pts"]), ("s-day", sa - r["mn"])]
    return '<div class="sbar" aria-hidden="true">' + "".join(f'<i class="{k}" style="width:{v / sa * 100:.2f}%"></i>' for k, v in seg) + "</div>"


def ex_card(r):
    h = r["h"]; slug, name, _ = SLUG[h["no"]]
    return f"""<article class="exc">
  <div class="exh"><a href="../hotels/{slug}/">{esc(name)}</a><span>{AREA_JA[h['area']]}・{esc(h['loc'])}｜{KY}年{KM}月・2名1泊2食</span></div>
  <div class="exn"><span>土曜泊の平均より</span><b>−{r['save']:,}<small>円</small></b></div>
  {bar(r)}
  <ul class="lg">
    <li><i class="s-day"></i>神日（{lab(r['d'])}）にずらす <b>−{r['sa'] - r['mn']:,}円</b></li>
    <li><i class="s-pts"></i>カード払いのポイント <b>−{r['pts']:,}pt</b></li>
    <li><i class="s-bonus"></i>入会と利用の特典 <b>−5,000pt</b></li>
    <li><i class="s-real"></i>実質 <b>{yen(r['real'])}</b><span class="from">（土曜の平均 {yen(r['sa'])}）</span></li>
  </ul>
</article>"""


def card_tile(key, name, fee, rate, who, extra=""):
    if key in CARD_IMG:
        img, link = CARD_IMG[key]
        face = f'<a class="face img" href="{link}" target="_blank" rel="nofollow sponsored noopener"><img src="{img}" alt="{esc(name)}の券面" width="200" height="200" loading="lazy"></a>'
    else:
        face = f'<div class="face" aria-hidden="true"><span>{esc(name)}</span></div>'
    return f"""<div class="ct{' main' if key == 'card' else ''}">
  {face}
  <div class="cn">{esc(name)}</div>
  <div class="cf"><span>年会費</span><b>{fee}</b></div>
  <div class="cr"><span>楽天トラベル</span><b>{rate}</b></div>
  <p class="cw">{who}</p>{extra}{('<a class="cl" href="' + CARD_IMG[key][1] + '" target="_blank" rel="nofollow sponsored noopener">申し込む →</a>') if key in CARD_IMG else ''}
</div>"""


ex_html = "".join(ex_card(r) for r in ex)
best = max(ex, key=lambda r: r["save"])
base = "../"
title = "楽天カードで旅費はいくら下がる？楽天トラベルのポイントと入会特典｜YASUMIBI"
desc = "楽天トラベルを楽天カードで事前決済するとポイント2.5倍。温泉宿の実際の料金で、神日と組み合わせた節約額を試算。入会特典や上位カードとの違いも。"
v1 = ver("site.css"); v2 = ver("hotel.css"); v3 = ver("top.css", "otoku.css")
apply = f'<a class="c-apply" href="{CARD_AFF}" target="_blank" rel="nofollow sponsored noopener">楽天カードを申し込む（年会費無料）</a>'
tiles = (card_tile("card", "楽天カード", "永年無料", "2.5倍", "年に数回の旅行なら、これで十分") +
         card_tile("premium", "楽天プレミアムカード", "11,000円", "3.5倍", "年110万円以上、または空港ラウンジをよく使う人向け", '<p class="cx">プライオリティ・パス 年5回</p>'))

page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{og_meta(esc(title), esc(desc), "rakuten-card/")}<link rel="canonical" href="https://yasumibi.com/rakuten-card/">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@100..125,600..900&display=swap">
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="stylesheet" href="{base}assets/otoku.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">
</head>
<body class="app top2 otk">
{site_header(base, "otoku")}
<main class="gin ok rcp">
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><a href="{base}otoku/">さらに安く</a><span aria-hidden="true">›</span><span>楽天カード</span></nav>

  <header class="rc-hero">
    <p class="eb">神日 × 楽天カード</p>
    <h1>同じ宿が、<br>土曜より <em>−{best['save']:,}円</em>。</h1>
    <p class="sub">{esc(SLUG[best['h']['no']][1])}（{KY}年{KM}月・2名1泊2食）の試算</p>
    <ol class="steps3">
      <li><b>1</b><span>神日に<br>泊まる</span></li>
      <li><b>2</b><span>楽天カードで<br>払う</span></li>
      <li><b>3</b><span>入会特典を<br>もらう</span></li>
    </ol>
  </header>

  <section class="sec" aria-labelledby="s1">
    <h2 id="s1">実際の宿で試算</h2>
    <div class="exgrid">{ex_html}</div>
    {apply}
  </section>

  <section class="sec" aria-labelledby="s2">
    <h2 id="s2">10万円の宿で、もらえるポイント</h2>
    <ul class="pbars">
      <li><span class="pl">楽天カード以外</span><span class="pb"><i style="width:28.6%"></i></span><b>1,000pt</b></li>
      <li class="hl"><span class="pl">楽天カード</span><span class="pb"><i style="width:71.4%"></i></span><b>2,500pt</b></li>
      <li><span class="pl">プレミアム</span><span class="pb"><i style="width:100%"></i></span><b>3,500pt</b></li>
    </ul>
    <details class="more"><summary>2.5倍になる条件</summary>
      <ul class="notes">
        <li>楽天トラベルのキャンペーンページで、チェックアウトより前にエントリー</li>
        <li>楽天カードで事前決済（現地払い・家族カードは対象外）</li>
        <li>国内の宿泊のみ（日帰り・デイユース・楽パック・海外は対象外）</li>
      </ul>
    </details>
  </section>

  <section class="sec" aria-labelledby="s3">
    <h2 id="s3">はじめての方は、合計5,000pt</h2>
    <div class="bn">
      <div><b>2,000<small>pt</small></b><span>入会</span></div>
      <div class="plus" aria-hidden="true">＋</div>
      <div><b>3,000<small>pt</small></b><span>3回使う</span></div>
    </div>
    <details class="more"><summary>もらえる条件</summary>
      <ul class="notes">
        <li>2,000pt：カードが届いたあと、楽天e-NAVIに初めて登録</li>
        <li>3,000pt（期間限定ポイント）：申し込みの翌月末までに3回以上使い、引き落とし口座を設定</li>
        <li>楽天カードを持っている・持っていたことがある方は対象外</li>
      </ul>
    </details>
  </section>

  <section class="sec" aria-labelledby="s4">
    <h2 id="s4">楽天カードとプレミアムの違い</h2>
    <div class="tiles">{tiles}</div>
    <details class="more"><summary>旅行保険など、くわしい違い</summary>
      <div class="tbl"><table>
        <thead><tr><th></th><th>楽天カード</th><th>プレミアム</th></tr></thead>
        <tbody>
          <tr><th>空港ラウンジ</th><td>—</td><td>国内 回数制限なし／海外 プライオリティ・パス年5回</td></tr>
          <tr><th>海外旅行傷害保険<small>最高額・利用条件あり</small></th><td class="n">2,000万円</td><td class="n">5,000万円</td></tr>
        </tbody>
      </table></div>
      <p class="fine">年会費の元が取れる目安は、楽天トラベルのポイント差だけで計算したものです（プレミアムは楽天カードより＋1%）。</p>
    </details>
  </section>

  <section class="sec last" aria-labelledby="s5">
    <h2 id="s5">まずは年会費無料の楽天カードから</h2>
    {apply}
    <ul class="notes small">
      <li>申し込みには審査があります。事前決済はカード払いに対応したプランで使えます。</li>
      <li>ポイント倍率・特典は時期によって変わります。{CHECKED}時点で楽天カードの公式ページを確認した内容です。</li>
      <li>試算は{ASOF}時点の楽天トラベルの料金。土曜泊の平均は年末年始を除き、1ポイント＝1円で計算。</li>
    </ul>
  </section>
</main>
""" + footer(base) + tabbar(base, "otoku") + "</body></html>\n"
os.makedirs(f"{OUT}/rakuten-card", exist_ok=True)
open(f"{OUT}/rakuten-card/index.html", "w", encoding="utf-8").write(page)
print("rakuten-card built", [(SLUG[r['h']['no']][1], r['save']) for r in ex])
