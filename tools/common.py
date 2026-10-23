"""YASUMIBI 共通パーツ（全ページ同じヘッダー・PR表示・タブ・フッター・OG）。"""
import json, os, calendar

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # このリポジトリ
OUT = os.environ.get("YB_OUT", os.path.join(os.path.dirname(ROOT), "yasumibi-site"))  # 公開用リポジトリ（隣に置く）
SITE = "https://yasumibi.com/"
OG_IMG = SITE + "assets/img/og.png"


def logo_html(base, href=None):
    href = base if href is None else href
    return (f'<a class="brand" href="{href}" aria-label="YASUMIBI ホーム">'
            f'<img class="lg-l" src="{base}assets/img/logo.png" alt="YASUMIBI" width="714" height="120">'
            f'<img class="lg-d" src="{base}assets/img/logo-dark.png" alt="" width="714" height="120"></a>')


def site_header(base, cur=""):
    def a(key, href, label, extra=""):
        return f'<a href="{href}"{extra}{" aria-current=\"page\"" if key == cur else ""}>{label}</a>'
    nav = (a("areas", f"{base}#areas", "エリアから探す") + a("date", f"{base}#date", "日付から探す")
           + a("features", f"{base}features/", "特集") + a("fav", f"{base}favorites/", "お気に入り") + a("otoku", f"{base}otoku/", "さらに安く", ' class="ot"'))
    return f"""<header class="gh">
  <div class="gin">
    {logo_html(base)}
    <span class="gtag">休み日を、安い日に。</span>
    <nav class="gnav" aria-label="メインメニュー">{nav}</nav>
  </div>
</header>
"""


def tabbar(base, cur):
    items = [("home", "ホーム", f"{base}", '<path d="M3 11l9-7 9 7v9a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z"/>'),
             ("area", "エリア", f"{base}#areas", '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>'),
             ("date", "日付", f"{base}#date", '<rect x="3.5" y="5" width="17" height="15.5" rx="2"/><path d="M3.5 10h17M8 3v4M16 3v4"/>'),
             ("fav", "お気に入り", f"{base}favorites/", '<path d="M12 20.5s-7.5-4.6-9.2-9.3C1.6 7.8 3.9 4.5 7.3 4.5c2 0 3.6 1.1 4.7 2.7 1.1-1.6 2.7-2.7 4.7-2.7 3.4 0 5.7 3.3 4.5 6.7-1.7 4.7-9.2 9.3-9.2 9.3z"/>'),
             ("otoku", "さらに安く", f"{base}otoku/", '<circle cx="12" cy="12" r="8.5"/><path d="M12 7.5v9M9.5 9.5h4a1.8 1.8 0 0 1 0 3.6h-3a1.8 1.8 0 0 0 0 3.6h4"/>')]
    a = "".join(f'<a href="{h}"{" aria-current=\"page\"" if k == cur else ""} class="t-{k}"{" data-tab=\"date\"" if k == "date" else ""}><svg viewBox="0 0 24 24" aria-hidden="true">{p}</svg><span>{t}</span></a>' for k, t, h, p in items)
    return f'<nav class="tabbar" aria-label="メニュー">{a}</nav>'


def footer(base):
    return f"""<div class="wrap"><footer class="site">
  <nav aria-label="サイト情報"><a href="{base}about/">YASUMIBIについて</a><a href="{base}about/#operator">運営者情報</a><a href="{base}privacy/">プライバシーポリシー</a><a href="{base}disclosure/">広告の掲載について</a></nav>
  <nav aria-label="SNS" class="sns"><a href="https://www.instagram.com/yasumibi.travel/" target="_blank" rel="noopener">Instagram</a><a href="https://www.tiktok.com/@yasumibi.travel" target="_blank" rel="noopener">TikTok</a></nav>
  <div class="prnote">PR｜当サイトは広告（アフィリエイト）を利用しています。掲載している料金は調べた時点のもので、予約時の料金と異なる場合があります。</div>
  <div><a href="https://webservice.rakuten.co.jp/" target="_blank" rel="noopener">Supported by Rakuten Developers</a>　© YASUMIBI</div>
</footer></div>
"""


def og_meta(title, desc, path, img=None):
    return (f'<meta property="og:type" content="website">\n<meta property="og:site_name" content="YASUMIBI 神日カレンダー">\n'
            f'<meta property="og:title" content="{title}">\n<meta property="og:description" content="{desc}">\n'
            f'<meta property="og:url" content="{SITE}{path}">\n<meta property="og:image" content="{img or OG_IMG}">\n'
            f'<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
            f'<meta name="twitter:card" content="summary_large_image">\n')


# ---- データ（yasumibi-data リポジトリを data/ に置く）
import datetime as _dt
DATA = f"{ROOT}/data"
JST = _dt.timezone(_dt.timedelta(hours=9))
TODAY = _dt.datetime.now(JST).date()

AREAS = json.load(open(f"{DATA}/areas.json"))            # エリアの一覧（key, name, region, 楽天のエリアコード）
AREA_JA = {a["key"]: a["name"] for a in AREAS}
# 食事の条件：基本は1泊2食付き。京都・沖縄・北海道の街など、2食付きの宿が少ないエリアは1泊朝食付きで比べる（areas.json の meal: 1）
MEAL = {a["key"]: int(a.get("meal", 2)) for a in AREAS}
B_AREA_NAMES = [a["name"] for a in AREAS if int(a.get("meal", 2)) == 1]


def is_b(area):
    """そのエリアが1泊朝食付きで比べるエリアか。"""
    return MEAL.get(area, 2) == 1


def plan_s(area):
    """短い表記：1泊2食／1泊朝食"""
    return "1泊朝食" if is_b(area) else "1泊2食"


def plan_l(area):
    """長い表記：1泊2食付き／1泊朝食付き"""
    return "1泊朝食付き" if is_b(area) else "1泊2食付き"


# 注記に使う条件の文（朝食付きのエリアがあれば、どこかを書き添える）
COND_PLAN = ("大人2名・1室・1泊2食付き" + (f"（{'・'.join(B_AREA_NAMES)}は1泊朝食付き）" if B_AREA_NAMES else "") + "の最安プラン")


def _add_months(y, m, k):
    m0 = y * 12 + (m - 1) + k
    return m0 // 12, m0 % 12 + 1


# 掲載する期間：今月から6か月分（毎月、自動で先へ進む）
_left = calendar.monthrange(TODAY.year, TODAY.month)[1] - TODAY.day + 1
_s = 0 if _left >= 14 else 1                     # 今月の残りが2週間未満なら来月から
MONTHS = [_add_months(TODAY.year, TODAY.month, _s + k) for k in range(6)]
# 最初に開く月：だいたい2〜3か月先（早めの予約を考える月）
_k = TODAY + _dt.timedelta(days=75)
DEFAULT_YM = (_k.year, _k.month) if (_k.year, _k.month) in MONTHS else MONTHS[0]
KY, KM = DEFAULT_YM
WINDOW_START = _dt.date(*MONTHS[0], 1)
_ly, _lm = _add_months(*MONTHS[-1], 1)
WINDOW_END = _dt.date(_ly, _lm, 1) - _dt.timedelta(days=1)

PRICE_DIR = f"{DATA}/prices"


def price_file(area):
    return f"{PRICE_DIR}/{area}.json"


def load_prices():
    """エリアごとの料金ファイルをまとめて読む。{no(str): {date: price}}, {area: asof表示}, {area: asof日付}"""
    hotels, asof, asof_d = {}, {}, {}
    if os.path.isdir(PRICE_DIR):
        for fn in sorted(os.listdir(PRICE_DIR)):
            if not fn.endswith(".json"): continue
            d = json.load(open(f"{PRICE_DIR}/{fn}"))
            k = fn[:-5]
            hotels.update(d.get("hotels", {}))
            asof[k] = d.get("asof", ""); asof_d[k] = d.get("asof_date", "")
    return hotels, asof, asof_d


PRH, ASOF_BY_AREA, ASOF_DATE_BY_AREA = load_prices()
# サイト全体の「時点」は、いちばん古いエリアの取得日（正直に、古い方を出す）
_old = min((v, k) for k, v in ASOF_DATE_BY_AREA.items() if v) if any(ASOF_DATE_BY_AREA.values()) else ("", "")
ASOF = ASOF_BY_AREA.get(_old[1], "") or next(iter(ASOF_BY_AREA.values()), "")


def month_prices(no, y, m):
    src = PRH.get(str(no), {})
    return [int(src.get(f"{y}-{m:02d}-{d:02d}", 0) or 0) for d in range(1, calendar.monthrange(y, m)[1] + 1)]


HOTELS_ALL = json.load(open(f"{DATA}/hotels.json"))   # 宿の一覧（料金を取る対象）
# 掲載するのは「★4.3以上・口コミ50件以上」の宿だけ（毎週の評価の取り直しで下回ったら自動で外れる）
HOTELS = [h for h in HOTELS_ALL if (h.get("avg") or 0) >= 4.3 and (h.get("cnt") or 0) >= 50]
SLUG = {h["no"]: (h["slug"], h["name"], h["full"]) for h in HOTELS}


def jan_min(p):
    """月の料金リストの最安（0は満室・プランなし）。名前は昔の名残。"""
    v = [x for x in p if x]
    return min(v) if v else 0


def load_area():
    """宿の一覧に、最初に開く月（DEFAULT_YM）の料金と最新の口コミ数・平均を付けて返す（期間内に料金が1日も無い宿は除く）。"""
    det = {}
    try:
        for ln in open(f"{DATA}/hotel_detail_20261021.tsv", encoding="utf-8"):
            if not ln.strip(): continue
            c = ln.rstrip("\n").split("\t"); det[int(c[0])] = (float(c[1] or 0), int(c[2] or 0))
    except FileNotFoundError:
        pass
    hs = []
    for h0 in HOTELS:
        h = dict(h0)
        if not any(any(month_prices(h["no"], y, m)) for y, m in MONTHS): continue
        h["p"] = month_prices(h["no"], KY, KM)
        if det.get(h["no"], (0, 0))[0]: h["avg"], h["cnt"] = det[h["no"]]
        hs.append(h)
    return {"asof": ASOF, "hotels": hs}

# 楽天カード（楽天アフィリエイト・リンクのみ／2026-10-21取得）
CARD_AFF = "https://hb.afl.rakuten.co.jp/hsc/58ad7ff1.00560306.58ad7ff2.3c792b49/?link_type=hybrid_url&ut=eyJwYWdlIjoic2hvcCIsInR5cGUiOiJoeWJyaWRfdXJsIiwiY29sIjoxLCJjYXQiOjEsImJhbiI6MTY3NDAxLCJhbXAiOmZhbHNlfQ%3D%3D"

# ---- 楽天トラベル×楽天カードのポイント（2026年10月23日に公式ページで確認）
# https://travel.rakuten.co.jp/card/campaign/ ：エントリー＆楽天カードで事前決済で合計2.5倍
#   通常1倍（税抜100円につき1pt・誰でも）＋楽天カード通常分1倍（カード利用100円につき1pt）＋特典0.5倍（税抜200円につき1pt）
#   予約 2026/8/31 10:00〜2026/11/30 9:59、宿泊 チェックアウト2027/1/31まで。国内宿泊のみ。
# https://www.rakuten-card.co.jp/campaign/rakuten_card/corp/ ：新規入会で2,000pt＋3回利用などで3,000pt（期間限定）
# 「実質◯円」とは書かない。ポイントは宿代とは別に「◯円分戻る」と書き、楽天カードを使って増える分だけを示す。
# キャンペーンが変わったら、ここを直す（hotel.js・top.js はページに埋めたこの値を使う）。
CARD_CAMP = {"book_end": "2026-11-30T09:59:00+09:00", "out_last": "2027-01-31", "checked": "2026年10月23日",
             "book_end_ja": "2026年11月30日9:59", "out_last_ja": "2027年1月31日"}
CARD_BONUS = 5000  # 新規入会特典（2,000＋3,000・うち3,000は期間限定）


def camp_ok(checkin):
    """その日に泊まる予約が、楽天カードの2.5倍の対象か（いま予約する場合）。"""
    now = _dt.datetime.now(JST)
    end = _dt.datetime.fromisoformat(CARD_CAMP["book_end"])
    out = checkin + _dt.timedelta(days=1)
    return now < end and out <= _dt.date.fromisoformat(CARD_CAMP["out_last"])


def card_extra(v, checkin):
    """楽天カードで事前決済すると、楽天カード以外で払うより多くもらえるポイント（目安）。"""
    return v // 100 + ((v * 10 // 11) // 200 if camp_ok(checkin) else 0)
