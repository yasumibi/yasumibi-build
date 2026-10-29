"""/cards/ — 旅の支払いに使うカード（楽天カード＋2枚目の候補：三井住友カード（NL）・エポスカード）。

三井住友カード（NL）の記載は、A8のガイドライン（2025/11/20版）で掲載が許されている項目・文言だけを使う。
 - 名称は「三井住友カード（NL）」（全角かっこ）
 - スペック・メリット・デメリットは許可された項目のみ。他社カードとの優劣比較・「最強」等の修飾・キャンペーン訴求はしない
 - 還元率を書く近くに、指定の注釈を一字一句そのまま置く
 - バナーは自作しない（提携後は公式素材のみ）
"""
import os, sys, html, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, plan_s, plan_l, COND_PLAN
from common import site_header, tabbar, footer, og_meta, OUT, CARD_AFF
from common import CARD_CAMP, CARD_BONUS, camp_live

CHECKED = "2026年10月23日"
# 提携が通るまでは公式ページへのふつうのリンク。提携後にアフィリエイトリンクへ差し替える。
NL_URL = "https://www.smbc-card.com/nyukai/card/numberless.jsp"
NL_NOTE = ("※カード現物のタッチ決済、iD、カードの差し込み、磁気取引は対象外です。"
           "※商業施設内にある店舗などでは、一部ポイント付与の対象となりません。"
           "※一定金額（原則1万円）を超えると、タッチ決済でなく、決済端末にカードを挿しお支払いただく場合がございます。その場合のお支払い分は、タッチ決済分のポイント還元の対象となりませんので、ご了承ください。上記、タッチ決済とならない金額の上限は、ご利用される店舗によって異なる場合がございます。"
           "※スマホのタッチ決済対象店舗とモバイルオーダーの対象店舗は異なります。詳しくはサービス詳細ページをご確認ください。"
           "※通常のポイント分を含んだ還元率です。"
           "※ポイント還元率は利用金額に対する獲得ポイントを示したもので、ポイントの交換方法によっては、1ポイント1円相当にならない場合があります。"
           "※Google Pay™ 、Samsung Payで、Mastercard®タッチ決済はご利用いただけません。ポイント還元は受けられませんので、ご注意ください。")
# エポスカード（A8.net・2026/10/23提携）。テキスト素材ID 001。計測用の1x1画像も一緒に置く。
EPOS_URL = "https://px.a8.net/svt/ejp?a8mat=4BEMLP+7L9ZG2+38L8+5YJRM"
EPOS_PX = "https://www18.a8.net/0.gif?a8mat=4BEMLP+7L9ZG2+38L8+5YJRM"
# 券面だけの素材（素材ID 040・745×1180）。加工せず縮めて表示する。キャンペーン文字が入っていないので古くならない。
EPOS_FACE = ("https://px.a8.net/svt/ejp?a8mat=4BEMLP+7L9ZG2+38L8+66WOX",
             "https://www25.a8.net/svt/bgt?aid=261022957459&wid=001&eno=01&mid=s00000015110001040000&mc=1",
             "https://www19.a8.net/0.gif?a8mat=4BEMLP+7L9ZG2+38L8+66WOX")
RK_IMG = ("https://hbb.afl.rakuten.co.jp/hsb/58adb89a.1783e5b6.58ad7ff2.3c792b49/?me_id=2101008&me_adv_id=373425&t=pict",
          "https://hb.afl.rakuten.co.jp/hsc/58adb89a.1783e5b6.58ad7ff2.3c792b49/?link_type=pict&ut=eyJwYWdlIjoic2hvcCIsInR5cGUiOiJwaWN0IiwiY29sIjoxLCJjYXQiOiIxIiwiYmFuIjozNzM0MjUsImFtcCI6ZmFsc2V9")


def esc(s): return html.escape(str(s), quote=True)
def ver(*files):
    h = hashlib.md5()
    for f in files: h.update(open(f"{OUT}/assets/{f}", "rb").read())
    return h.hexdigest()[:8]


def spec(rows): return '<dl class="cspec">' + "".join(f"<dt>{k}</dt><dd>{v}</dd>" for k, v in rows) + "</dl>"
def ul(cls, items): return f'<ul class="{cls}">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


base = "../"
title = "旅の支払いに使うカード｜楽天カードと、もう1枚｜YASUMIBI"
desc = "楽天トラベルの予約は楽天カード。ふだんの支払いには、もう1枚。年会費・ポイント・旅行保険を、公式の条件どおりにまとめました。"
v1 = ver("site.css"); v2 = ver("hotel.css"); v3 = ver("top.css", "otoku.css")

rakuten = f"""<article class="cd" id="rakuten">
  <p class="role">楽天トラベルの予約に</p>
  <div class="cd-hd">
    <a class="cd-face" href="{RK_IMG[1]}" target="_blank" rel="nofollow sponsored noopener"><img src="{RK_IMG[0]}" alt="楽天カードの券面" width="200" height="200" loading="lazy"></a>
    <div><h2>楽天カード</h2><p class="cd-lead">はじめての方は、入会と3回の利用で<b class="big">{CARD_BONUS:,}円分</b>のポイント。</p></div>
  </div>
  {spec([("年会費", "永年無料"), ("入会特典", "5,000ポイント<small>うち3,000は期間限定ポイント・3回以上の利用などの条件あり</small>"),
         ("楽天トラベル", (f"ポイント2.5倍<small>エントリー・事前決済が必要。{CARD_CAMP['book_end_ja']}までの予約・{CARD_CAMP['out_last_ja']}チェックアウトまでの宿泊</small>" if camp_live()
                    else "事前決済でポイントが増える<small>カード利用100円につき1ポイント（楽天カード以外で払うより多い分）</small>"))])}
  <a class="c-apply" href="{CARD_AFF}" target="_blank" rel="nofollow sponsored noopener">楽天カードを申し込む（年会費無料）</a>
  <a class="ok-more" href="{base}rakuten-card/">実際の宿で、いくら戻るかを見る →</a>
</article>"""

nl = f"""<article class="cd" id="nl">
  <p class="role">ふだんのコンビニ・飲食店に</p>
  <div class="cd-hd"><div><h2>三井住友カード（NL）</h2>
    <p class="cd-lead">対象のコンビニ・飲食店でスマホのタッチ決済またはモバイルオーダーで支払うと7％ポイント還元</p></div></div>
  {spec([("年会費", "永年無料"), ("申込条件", "18歳以上（高校生を除く）"), ("ポイント還元率", "0.5%〜7％※"),
         ("発行スピード", "最短10秒<small>※即時発行できない場合があります。</small>"), ("海外旅行傷害保険", "最高2,000万円まで利用付帯にて補償")])}
  <p class="cnote">{esc(NL_NOTE)}</p>
  <div class="pc">
    <div><h3>よいところ</h3>{ul("pros", ["年会費永年無料", "対象のコンビニ・飲食店でスマホのタッチ決済で最大7％ポイント還元", "貯まったVポイントの使い道が豊富", "最短10秒で即時発行できる", "ナンバーレスで安心のセキュリティ"])}</div>
    <div><h3>気をつけたいところ</h3>{ul("cons", ["基本のポイント還元率は高くない", "カード番号の確認に本人認証が必要", "国内旅行傷害保険やショッピング保険の付帯がない"])}</div>
  </div>
  <a class="c-apply nl" href="{NL_URL}" target="_blank" rel="noopener">三井住友カード（NL）の公式サイトを見る</a>
</article>"""

epos = f"""<article class="cd" id="epos">
  <p class="role">海外旅行の保険に</p>
  <div class="cd-hd">
    <a class="cd-face" href="{esc(EPOS_FACE[0])}" target="_blank" rel="nofollow sponsored noopener"><img src="{esc(EPOS_FACE[1])}" alt="エポスカードの券面" class="tall" width="745" height="1180" loading="lazy"></a><img src="{esc(EPOS_FACE[2])}" width="1" height="1" alt="" style="position:absolute;width:1px;height:1px;border:0">
    <div><h2>エポスカード</h2><p class="cd-lead">空港までの電車・バス代などをこのカードで払うと、海外旅行の保険が付きます。</p></div>
  </div>
  {spec([("年会費", "入会金・年会費とも永年無料"), ("海外旅行傷害保険", "傷害死亡・後遺傷害 最高3,000万円（利用付帯）"),
         ("病気の治療費用", "270万円まで（1疾病の限度額）"), ("けがの治療費用", "200万円まで（1事故の限度額）")])}
  <p class="cnote">※保険は、旅行代金（募集型企画旅行の代金、または航空券・電車・バス・タクシーなど公共交通の料金）をエポスカードで支払った場合に適用されます。個人で手配した宿泊料金だけの支払いでは適用されません。補償の詳細は公式ページでご確認ください。</p>
  <div class="pc">
    <div><h3>よいところ</h3>{ul("pros", ["入会金・年会費とも永年無料", "空港までの交通費などを払うだけで、海外旅行の保険が付く", "マルイの年4回のセールで10％オフ"])}</div>
    <div><h3>気をつけたいところ</h3>{ul("cons", ["保険は利用付帯。旅行代金をカードで払わないと付かない", "宿泊代だけの支払いでは、保険の対象にならない", "保険の対象はカードを持つ本人のみ（家族は対象外）"])}</div>
  </div>
  <a class="c-apply nl" href="{EPOS_URL}" target="_blank" rel="nofollow sponsored noopener">エポスカードの公式サイトを見る</a><img src="{EPOS_PX}" width="1" height="1" alt="" style="position:absolute;width:1px;height:1px;border:0">
</article>"""

page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="index,follow">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
{og_meta(esc(title), esc(desc), "cards/")}<link rel="canonical" href="https://yasumibi.com/cards/">
<link rel="stylesheet" href="{base}assets/site.css?v={v1}">
<link rel="stylesheet" href="{base}assets/hotel.css?v={v2}">
<link rel="stylesheet" href="{base}assets/top.css?v={v3}">
<link rel="stylesheet" href="{base}assets/otoku.css?v={v3}">
<link rel="icon" href="{base}assets/img/favicon-48.png" sizes="48x48" type="image/png"><link rel="icon" href="{base}assets/img/favicon-192.png" sizes="192x192" type="image/png">
<link rel="apple-touch-icon" href="{base}assets/img/apple-touch-icon.png">\n<link rel="manifest" href="{base}manifest.webmanifest">\n<meta name="theme-color" content="#ffffff">\n<meta name="apple-mobile-web-app-title" content="YASUMIBI">
</head>
<body class="app top2 otk">
{site_header(base, "otoku")}
<main class="gin ok cdp">
  <p class="prtop"><span>PR</span></p>
  <nav class="crumb" aria-label="現在地"><a href="{base}">ホーム</a><span aria-hidden="true">›</span><a href="{base}otoku/">さらに安く</a><span aria-hidden="true">›</span><span>カード</span></nav>
  <header class="ok-hd">
    <h1>神日に泊まって、楽天カードで払う。</h1>
    <p>楽天トラベルの予約は楽天カード。ふだんの支払いには、使い方に合うもう1枚。条件は各社の公式ページのとおりにまとめています。</p>
  </header>
  {rakuten}
  {nl}
  {epos}
  <ul class="notes small">
    <li>カードの申し込みには審査があります。</li>
    <li>内容は{CHECKED}時点で各社の公式ページ・広告主の案内を確認したものです。最新の条件は公式ページでご確認ください。</li>
  </ul>
</main>
""" + footer(base) + tabbar(base, "otoku") + "</body></html>\n"
os.makedirs(f"{OUT}/cards", exist_ok=True)
open(f"{OUT}/cards/index.html", "w", encoding="utf-8").write(page)
print("cards built")
