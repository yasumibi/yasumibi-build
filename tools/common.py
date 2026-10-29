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


def _asset_v(name):
    import hashlib
    try: return hashlib.md5(open(f"{OUT}/assets/{name}", "rb").read()).hexdigest()[:8]
    except Exception: return "0"


def footer(base):
    return f"""<div class="wrap"><footer class="site">
  <nav aria-label="サイト情報"><a href="{base}about/">YASUMIBIについて</a><a href="{base}about/#operator">運営者情報</a><a href="{base}privacy/">プライバシーポリシー</a><a href="{base}disclosure/">広告の掲載について</a></nav>
  <nav aria-label="SNS" class="sns"><a href="https://www.instagram.com/yasumibi.travel/" target="_blank" rel="noopener">Instagram</a><a href="https://www.tiktok.com/@yasumibi.travel" target="_blank" rel="noopener">TikTok</a></nav>
  <div class="prnote">PR｜当サイトは広告（アフィリエイト）を利用しています。掲載している料金は調べた時点のもので、予約時の料金と異なる場合があります。</div>
  <div><a href="https://webservice.rakuten.co.jp/" target="_blank" rel="noopener">Supported by Rakuten Developers</a>　© YASUMIBI</div>
</footer></div><script src="{base}assets/ppl.js?v={_asset_v('ppl.js')}" defer></script>
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
# 書き添える用の短い表記：地方の全エリアが朝食付きなら地方名（沖縄）、そうでなければエリア名（京都、札幌…）を「、」でつなぐ
_bl = []
for _r in dict.fromkeys(x["region"] for x in AREAS):
    _in = [x for x in AREAS if x["region"] == _r]
    _b = [x["name"] for x in _in if int(x.get("meal", 2)) == 1]
    if _b: _bl += [_r] if len(_b) == len(_in) else _b
B_AREA_LABEL = "、".join(_bl)


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
COND_PLAN = ("大人2名・1室・1泊2食付き" + (f"（{B_AREA_LABEL}は1泊朝食付き）" if B_AREA_NAMES else "") + "の最安プラン")


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


# ハイクラス：この先半年の料金の中央値が、食事付き（2名1泊2食）9万円以上／朝食付き（2名1泊朝食）6万円以上の宿
HC_MIN = {2: 90000, 1: 60000}


def usual_price(no):
    """この先半年の料金の中央値（料金のある日が10日未満なら0）。"""
    t = TODAY.isoformat()
    v = sorted(int(p) for d, p in PRH.get(str(no), {}).items() if p and d > t)
    return v[len(v) // 2] if len(v) >= 10 else 0


def is_hc(no, area):
    u = usual_price(no)
    return bool(u) and u >= HC_MIN[MEAL.get(area, 2)]


def month_prices(no, y, m):
    src = PRH.get(str(no), {})
    return [int(src.get(f"{y}-{m:02d}-{d:02d}", 0) or 0) for d in range(1, calendar.monthrange(y, m)[1] + 1)]


def lowest_upcoming(no):
    """この先（明日から、表示している半年の終わりまで）でいちばん安い料金と、その日。無ければ None。タイトル・説明文に使う"""
    best = None
    for k, v in PRH.get(str(no), {}).items():
        try: v = int(v or 0)
        except (TypeError, ValueError): continue
        if not v: continue
        d = _dt.date.fromisoformat(k)
        if d <= TODAY or d < WINDOW_START or d > WINDOW_END: continue
        if best is None or v < best[0] or (v == best[0] and d < best[1]): best = (v, d)
    return best

WD_JA = "月火水木金土日"


# ---- 地区名（loc）
# 住所から地区名を決める決まり。エリアごとに分ける（箱根の「湯本」が、那須湯本・東山の湯本・長門湯本に当たらないように）
LOC_RULES = {
    "hakone": [("湯本", "箱根湯本温泉"), ("塔之沢", "塔之沢"), ("大平台", "大平台"), ("宮ノ下", "宮ノ下"), ("底倉", "底倉"), ("小涌谷", "小涌谷"),
               ("二ノ平", "二ノ平"), ("強羅", "強羅温泉"), ("宮城野", "宮城野"), ("仙石原", "仙石原"), ("芦之湯", "芦之湯"), ("元箱根", "芦ノ湖"),
               ("箱根町箱根", "芦ノ湖")],
    "atami": [("伊豆山", "伊豆山温泉"), ("網代", "網代温泉"), ("上多賀", "多賀"), ("下多賀", "多賀"), ("熱海", "熱海温泉")],
}
def loc_from_address(area, addr):
    """そのエリアの決まりで、住所から地区名を返す（決まりが無い・当たらないときは None＝今の地区名のまま）"""
    for k, v in LOC_RULES.get(area, []):
        if k in (addr or ""): return v
    return None

def _loc_owner():
    own = {}
    for a, rules in LOC_RULES.items():
        for _, v in rules: own.setdefault(v, set()).add(a)
    return own
_LOC_OWNER = _loc_owner()

def fix_loc(h):
    """ほかのエリア専用の地区名（例：那須の宿に「箱根湯本温泉」）が付いていたら、エリア名に戻す。直したら True"""
    own = _LOC_OWNER.get(h.get("loc"))
    if own and h.get("area") not in own:
        h["loc"] = AREA_JA.get(h.get("area"), h.get("loc")); return True
    return False

def _bare(s): return s[:-2] if len(s) > 2 and s.endswith("温泉") else s
def place(area_name, loc):
    """「エリア・地区」の表示。同じ名前が2回出るときは1回にする
    有馬＋有馬 → 有馬／熱海＋熱海温泉 → 熱海／白浜・南紀＋白浜 → 白浜（エリアが2つの名前のときは、宿のある方）"""
    loc = (loc or "").strip(); area_name = (area_name or "").strip()
    if not loc: return area_name
    if not area_name: return loc
    parts = [_bare(p) for p in area_name.split("・")]
    if _bare(loc) == _bare(area_name): return area_name
    if _bare(loc) in parts: return loc
    return f"{area_name}・{loc}"

def place_of(h):
    return place(AREA_JA.get(h.get("area"), ""), h.get("loc"))


HOTELS_ALL = json.load(open(f"{DATA}/hotels.json"))   # 宿の一覧（料金を取る対象）
for _h in HOTELS_ALL: fix_loc(_h)   # 念のため、ページを作るときにも直す（元データは fetch_info.py で正しく付ける）
# 掲載するのは「★4.3以上・口コミ50件以上」の宿だけ（毎週の評価の取り直しで下回ったら自動で外れる）
HOTELS = [h for h in HOTELS_ALL if ((h.get("avg") or 0) >= 4.3 and (h.get("cnt") or 0) >= 50) or (h.get("hc_slot") and (h.get("avg") or 0) >= 4.6 and (h.get("cnt") or 0) >= 20)]
# この先の空き日数（料金のある日）。空きの少ない人気宿も掲載は続ける（「空きが出た」こと自体に価値があるため）
def open_days(no):
    t = TODAY.isoformat()
    return sum(1 for d, p in PRH.get(str(no), {}).items() if p and d >= t)
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


# 写真のURLに中身のハッシュを付ける（同じ名前の写真を差し替えても、ブラウザが古い写真を使い続けないように）
import hashlib as _hl
_IMGV = {}
def img_v(name):
    if name not in _IMGV:
        try: _IMGV[name] = _hl.md5(open(f"{OUT}/assets/img/{name}", "rb").read()).hexdigest()[:8]
        except Exception: _IMGV[name] = "0"
    return _IMGV[name]
