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
            f'</a>')   # 暗い色のロゴは使っていない（ダークモードなし）。読み込まないよう外した


def site_header(base, cur=""):
    def a(key, href, label, extra=""):
        return f'<a href="{href}"{extra}{" aria-current=\"page\"" if key == cur else ""}>{label}</a>'
    nav = (a("areas", f"{base}#areas", "エリアから探す") + a("date", f"{base}#date", "日付から探す")
           + a("features", f"{base}features/", "特集") + a("fav", f"{base}favorites/", "お気に入り") + a("otoku", f"{base}otoku/", "さらに安く", ' class="ot"'))
    return f"""<header class="gh">
  <div class="gin">
    {logo_html(base)}
    <span class="gtag">安い日に、休みを合わせる。</span>
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
    # 読みもの（特集・ランキングなど）は、宿・エリアのページからたどる道が少なかったので、全ページのフッターに入口を置く（2026/11/20）
    return f"""<div class="wrap"><footer class="site">
  <nav class="fr" aria-label="読みもの"><a href="{base}features/">特集</a><a href="{base}ranking/">ランキング</a><a href="{base}weekend/">今週末の神日</a><a href="{base}renkyu/">有給1日で連休</a><a href="{base}otoku-days/">さらに安くなる日</a><a href="{base}areas/">エリア一覧</a><a href="{base}tags/">こだわりで探す</a></nav>
  <nav aria-label="サイト情報"><a href="{base}about/">YASUMIBIについて</a><a href="{base}about/#operator">運営者情報</a><a href="{base}privacy/">プライバシーポリシー</a><a href="{base}disclosure/">広告の掲載について</a></nav>
  <div class="prnote">PR｜当サイトは広告（アフィリエイト）を利用しています。掲載している料金は調べた時点のもので、予約時の料金と異なる場合があります。</div>
  <div class="prnote">このサイトで掲載されている情報は、YASUMIBIの作成者により運営されています。価格、販売可能情報は、変更される場合があります。予約時に楽天トラベル（travel.rakuten.co.jp）に表示されている価格が、その宿泊に適用されます。</div>
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
COND_PLAN = ("大人2名・1室・1泊2食付き" + ("（街のエリアは1泊朝食付き。くわしくは「YASUMIBIについて」）" if B_AREA_NAMES else "") + "の最安プラン")   # エリア名を40個並べると読めないので短く（2026/11/12）


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
            FETCHED[k] = d.get("fetched", {})
    return hotels, asof, asof_d


FETCHED = {}   # {エリア: {泊まる日: 取得日時 "YYYY-MM-DDTHH:MM"（古い記録は "YYYY-MM-DD"）}}。楽天の規約に合わせ、料金のそばに取得日時を出すため
PRH, ASOF_BY_AREA, ASOF_DATE_BY_AREA = load_prices()


def fa_label(v):
    """取得日時の表示：「11/13 3:12」（時刻の記録がない古い分は「11/13」）。"""
    if not v: return ""
    y, m, d = v[:10].split("-"); t = v[11:16] if len(v) >= 16 else ""
    return f"{int(m)}/{int(d)}" + (f" {int(t[:2])}:{t[3:5]}" if t else "")


def fa_range(area, dates):
    """その日付たちの取得日時の範囲：「取得 11/10 4:01〜11/13 3:12」（同じなら1つ）。"""
    vs = sorted(v for v in (FETCHED.get(area, {}).get(k, "") for k in dates) if v)
    if not vs: return ""
    a, b = fa_label(vs[0]), fa_label(vs[-1])
    return f"取得 {a}" + (f"〜{b}" if b != a else "")


PRICE_NOTE = "about/#price-note"   # 「料金について」（楽天ウェブサービスの免責事項）
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


def camp_live():
    return _dt.datetime.now(JST) < _dt.datetime.fromisoformat(CARD_CAMP["book_end"])


def camp_html():
    """キャンペーンの期限の文（assets/bsheet.js の campHtml と同じ文）。期限を過ぎたら入会特典の文に変わる。"""
    if not camp_live():
        return f"楽天カードの入会特典：<b>最大{CARD_BONUS:,}円分</b>のポイント（条件あり）"
    e = _dt.datetime.fromisoformat(CARD_CAMP["book_end"]).astimezone(JST)
    return f"<b>{e.month}/{e.day} {e.hour}:{e.minute:02d}まで</b>の予約：楽天カードの事前決済でポイント<b>2.5倍</b>（要エントリー）"


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


def cover_img(base, img):
    """エリアページ・特集のいちばん上の写真（いちばん大きく見える要素＝LCP）。軽い WebP（640・960px）を出し分けて、先に読み込む。2026/11/16"""
    stem = img.rsplit(".", 1)[0]
    w = [x for x in (640, 960) if os.path.exists(f"{OUT}/assets/img/{stem}-{x}.webp")]
    if len(w) == 2:
        ss = ", ".join(f"{base}assets/img/{stem}-{x}.webp?v={img_v(f'{stem}-{x}.webp')} {x}w" for x in w)
        return (f'<img src="{base}assets/img/{stem}-960.webp?v={img_v(stem + "-960.webp")}" srcset="{ss}" sizes="(min-width: 760px) 720px, 100vw" '
                f'alt="" width="960" height="540" fetchpriority="high" decoding="async">')
    return f'<img src="{base}assets/img/{img}?v={img_v(img)}" alt="" width="960" height="540" fetchpriority="high">'


def tile_img(base, img, sizes, attrs=""):
    """一覧のタイル用の写真。軽い WebP（tools/make_webp.py で作る 480px・640px）があればそれを使い、なければ元の JPG。
    sizes は画面での表示幅（ブラウザが画面に合った大きさを選ぶ）。見た目は JPG と同じ"""
    stem = img.rsplit(".", 1)[0]
    w = [x for x in (480, 640) if os.path.exists(f"{OUT}/assets/img/{stem}-{x}.webp")]
    if len(w) == 2:
        ss = ", ".join(f"{base}assets/img/{stem}-{x}.webp?v={img_v(f'{stem}-{x}.webp')} {x}w" for x in w)
        return f'<img src="{base}assets/img/{stem}-640.webp?v={img_v(stem + "-640.webp")}" srcset="{ss}" sizes="{sizes}" alt="" loading="lazy" decoding="async"{attrs}>'
    return f'<img src="{base}assets/img/{img}?v={img_v(img)}" alt="" loading="lazy"{attrs}>'


# ---- その宿だけの「安い日のまとめ」（毎日の料金から作る文。宿ページの最初に出す）
def price_summary(no):
    """この先半年の料金から、いちばん安い日・土曜泊と日〜木泊の差・月ごとの差を出す。料金が少なければ None。"""
    days = []
    for k, v in PRH.get(str(no), {}).items():
        try: v = int(v or 0)
        except (TypeError, ValueError): continue
        if not v: continue
        d = _dt.date.fromisoformat(k)
        if d <= TODAY or d < WINDOW_START or d > WINDOW_END: continue
        days.append((v, d))
    if len(days) < 10: return None
    low = min(days, key=lambda x: (x[0], x[1]))
    sat = [x for x in days if x[1].weekday() == 5]
    wk = [x for x in days if x[1].weekday() in (6, 0, 1, 2, 3)]   # 日〜木泊
    sat_min = min(sat, key=lambda x: (x[0], x[1])) if sat else None
    wk_min = min(wk, key=lambda x: (x[0], x[1])) if wk else None
    bym = {}
    for v, d in days: bym.setdefault((d.year, d.month), []).append(v)
    mmin = {k: min(v) for k, v in bym.items() if len(v) >= 7}   # 料金のある日が少ない月は比べない
    return dict(low=low, sat=sat_min, wk=wk_min, mmin=mmin, days=days)


def _md(d): return f"{d.month}/{d.day}({WD_JA[d.weekday()]})"


def summary_text(no, name="", unit=""):
    """宿ページの最初に出す2〜3文（HTMLではなく文字だけ）。料金が少ない宿は空。"""
    s = price_summary(no)
    if not s: return []
    v, d = s["low"]
    n = sum(1 for x in s["days"] if x[0] == v)
    u = f"（{unit}）" if unit else ""
    if n > 1:
        out = [f"{name + 'が' if name else ''}この先半年でいちばん安いのは¥{v:,}{u}。この料金の日は{_md(d)}泊など、全部で{n}日あります。"]
    else:
        out = [f"{name + 'が' if name else ''}この先半年でいちばん安いのは、{_md(d)}泊の¥{v:,}{u}です。"]
    if s["sat"] and s["wk"]:
        sv, sd = s["sat"]; wv, wd_ = s["wk"]
        if sv - wv >= 1000:
            out.append(f"土曜泊はいちばん安い日でも¥{sv:,}（{_md(sd)}）。日〜木泊のいちばん安い日なら、¥{sv - wv:,}安くなります。")
        else:
            out.append(f"土曜泊でも、いちばん安い日は¥{sv:,}（{_md(sd)}）。曜日による差が小さい宿です。")
    mm = s["mmin"]
    if len(mm) >= 3:
        lv, hv = min(mm.values()), max(mm.values())
        los = sorted(k for k in mm if mm[k] == lv); his = sorted(k for k in mm if mm[k] == hv)
        if hv >= lv * 1.05 and len(los) <= 3 and len(his) <= 2:
            j = lambda ks: "・".join(f"{k[1]}月" for k in ks)
            out.append(f"月ごとの最安値で比べると、{j(los)}がいちばん安く、{j(his)}がいちばん高くなります。")
    return out


def summary_rows(no):
    """宿ページの「◯◯の安い日」を、スマホで読みやすい表（見出し・中身）にする。中身はHTML。料金が少ない宿は空。"""
    s = price_summary(no)
    if not s: return []
    v, d = s["low"]
    n = sum(1 for x in s["days"] if x[0] == v)
    rows = [("いちばん安い", f'<b>¥{v:,}</b>　{_md(d)}泊' + (f"など{n}日" if n > 1 else ""))]
    if s["sat"] and s["wk"]:
        sv, sd = s["sat"]; wv, wd_ = s["wk"]
        if sv - wv >= 1000:
            rows.append(("土曜泊", f"いちばん安くても ¥{sv:,}（{_md(sd)}）"))
            rows.append(("日〜木泊なら", f'<span class="g">土曜泊より {sv - wv:,}円安い</span>'))
        else:
            rows.append(("土曜泊", f"¥{sv:,}（{_md(sd)}）。曜日の差が小さい宿"))
    mm = s["mmin"]
    if len(mm) >= 3:
        lv, hv = min(mm.values()), max(mm.values())
        los = sorted(k for k in mm if mm[k] == lv); his = sorted(k for k in mm if mm[k] == hv)
        if hv >= lv * 1.05 and len(los) <= 3 and len(his) <= 2:
            def j(ks):   # 続く月は「1〜3月」にまとめる（年をまたぐ 12月・1月 もつながりとみなす）
                ms = [k[1] for k in ks]; out = []; i = 0
                while i < len(ms):
                    k2 = i
                    while k2 + 1 < len(ms) and (ms[k2] % 12) + 1 == ms[k2 + 1]: k2 += 1
                    out.append(f"{ms[i]}〜{ms[k2]}月" if k2 - i >= 2 else "・".join(f"{m}月" for m in ms[i:k2 + 1])); i = k2 + 1
                return "・".join(out)
            rows.append(("安い月", f"{j(los)}（高いのは{j(his)}）"))
    return rows


# ---- 予約前シート用：「楽天トラベルで見る」に付ける目印（料金・神日か・朝食付きか）。assets/bsheet.js が読む
_AREA_OF = {str(h["no"]): h["area"] for h in HOTELS_ALL}
def bk_attr(no, d, n=1):
    """宿番号と泊まる日（n泊）から、シートでポイントを計算するための data 属性を作る。料金が無ければ空。"""
    src = PRH.get(str(no), {})
    try:
        ps = [int(src.get((d + _dt.timedelta(days=i)).isoformat(), 0) or 0) for i in range(n)]
    except Exception:
        return ""
    if not all(ps): return ""
    p = sum(ps)
    mv = [v for v in month_prices(no, d.year, d.month) if v]
    k = n == 1 and mv and p == min(mv)
    area = _AREA_OF.get(str(no), "")
    # 土曜泊の平均（同じ月・年末年始を除く）。予約前シートで「土曜泊より −◯円」を出すのに使う（宿ページの satAvg と同じ考え方）
    sat = ""
    if n == 1:
        sv = [v for i, v in enumerate(mv, 1) if v and _dt.date(d.year, d.month, i).weekday() == 5 and not ((d.month == 12 and i >= 29) or (d.month == 1 and i <= 3))]
        if sv: sat = round(sum(sv) / len(sv))
    return f' data-p="{p}"' + (' data-k="1"' if k else "") + (' data-b="1"' if area and is_b(area) else "") + (f' data-s="{sat}"' if sat and sat > p else "")


# ---- エリアの「安い時期」のまとめ（エリアページの最初に出す答えの文。毎日の料金から作る）
def area_facts(area, nos):
    """エリアの宿（nos）の料金から、安い月・高い月・曜日の差・連休の差・いちばん安い宿と日を出す（まとめの表と文の元）。"""
    import statistics as _st
    byh = {}
    for no in nos:
        for k, v in PRH.get(str(no), {}).items():
            try: v = int(v or 0)
            except (TypeError, ValueError): continue
            if not v: continue
            d = _dt.date.fromisoformat(k)
            if d <= TODAY or d < WINDOW_START or d > WINDOW_END: continue
            byh.setdefault(no, []).append((v, d))
    if len(byh) < 2: return {}
    nyd = lambda d: (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)
    gwd = lambda d: (d.month == 4 and d.day == 29) or (d.month == 5 and d.day <= 4)
    f = {"n": len(byh)}
    # 月ごと：宿ごとの「その月のいちばん安い日の料金」の中央値（年末年始は除く・宿が3軒以上ある月だけ）
    mon = {}
    for no, xs in byh.items():
        mm = {}
        for v, d in xs:
            if not nyd(d): mm.setdefault((d.year, d.month), []).append(v)
        for k, vs in mm.items():
            if len(vs) >= 7: mon.setdefault(k, []).append(min(vs))
    mon = {k: _st.median(v) for k, v in mon.items() if len(v) >= max(2, min(3, len(byh)))}
    if len(mon) >= 3:
        order = sorted(mon, key=lambda k: (mon[k], k))
        lo, hi = order[0], order[-1]
        lo2 = [k for k in order[1:3] if mon[k] <= mon[lo] * 1.03]
        f["lows"] = [k[1] for k in sorted([lo] + lo2[:1])]
        f["high"] = hi[1]
        f["mdiff"] = int(round((mon[hi] - mon[lo]) / 100.0)) * 100
    v, d, no = min(((v, d, no) for no, xs in byh.items() for v, d in xs if not nyd(d)), key=lambda x: (x[0], x[1]), default=(0, None, None))
    if v:
        f["best"] = dict(v=v, d=d, name=next((h["name"] for h in HOTELS_ALL if h["no"] == no), ""))
    # 曜日：宿ごとの土曜泊と日〜木泊の中央値の差（年末年始は除く）
    sat, wk = [], []
    for xs in byh.values():
        s_ = [v for v, d in xs if d.weekday() == 5 and not nyd(d)]; w_ = [v for v, d in xs if d.weekday() in (6, 0, 1, 2, 3) and not nyd(d)]
        if len(s_) >= 3 and len(w_) >= 5: sat.append(_st.median(s_)); wk.append(_st.median(w_))
    if len(sat) >= 2:
        f["sat"] = int(round((_st.median(sat) - _st.median(wk)) / 100.0)) * 100
    # 連休：年末年始（12/29〜1/3泊）・GW（4/29〜5/4泊）の、同じ宿の日〜木泊との差（空室がある宿が3軒以上のときだけ）
    for key, fn, lab in (("ny", nyd, "年末年始"), ("gw", gwd, "ゴールデンウィーク")):
        g, cnt = [], 0
        for xs in byh.values():
            h_ = [v for v, d in xs if fn(d)]; w_ = [v for v, d in xs if d.weekday() in (6, 0, 1, 2, 3) and not nyd(d) and not gwd(d)]
            if h_ and len(w_) >= 5: g.append(_st.median(h_) - _st.median(w_)); cnt += 1
        if cnt >= 3 and len({d for xs in byh.values() for v, d in xs if fn(d)}) >= 4:   # 連休の夜が4日以上そろっているときだけ
            f[key] = dict(lab=lab, diff=int(round(_st.median(g) / 100.0)) * 100, cnt=cnt)
    return f


def area_summary(area, label, nos, unit=""):
    """エリアの宿（nos）の料金から、安い月・高い月・いちばん安い宿と日・土曜泊との差を出して、2〜3文にする。"""
    f = area_facts(area, nos)
    if not f: return []
    out = []
    if f.get("lows"):
        out.append(f"{label}の宿が安い時期は、{'と'.join(f'{m}月' for m in f['lows'])}です。" + (f"高い{f['high']}月と比べると、宿ごとのいちばん安い日の料金が¥{f['mdiff']:,}ほど安くなります。" if f["mdiff"] >= 1000 else ""))
    if f.get("best"):
        b = f["best"]; d = b["d"]
        out.append(f"いちばん安い日は、{b['name']}の{d.month}/{d.day}({WD_JA[d.weekday()]})泊・¥{b['v']:,}{'（' + unit + '）' if unit else ''}。")
    if f.get("sat", 0) >= 1000: out.append(f"土曜泊は、日〜木泊より¥{f['sat']:,}ほど高めです。")
    return out


# ---- 特集の宿カード：客室の写真と「おすすめ」3つ（2026/11/19。aumo型の宿カード）
# 楽天の説明文は書き換えずに使わない。口コミの項目別の点数・夕食の場所・設備などのデータから、こちらの言葉で作る
import re
_OSU = None
_SC_JA = ("サービス", "立地", "部屋", "設備", "風呂", "食事")   # 施設情報APIの評価の並び（service, location, room, equipment, bath, meal）


def _osu_load():
    global _OSU
    if _OSU is not None: return _OSU
    _OSU = {}
    try: ex = json.load(open(f"{DATA}/hotel_extra.json", encoding="utf-8"))
    except Exception: ex = {}
    det = {}
    try:
        for ln in open(f"{DATA}/hotel_detail_20261021.tsv", encoding="utf-8"):
            c = ln.rstrip("\n").split("\t")
            if len(c) >= 10 and c[0].isdigit(): det[int(c[0])] = c
    except Exception: pass
    for k, e in ex.items():
        if k.isdigit(): _OSU[int(k)] = {"ex": e, "det": det.get(int(k))}
    for no, c in det.items(): _OSU.setdefault(no, {"ex": {}, "det": c})
    return _OSU


def room_img(no):
    return (_osu_load().get(int(no), {}).get("ex") or {}).get("room_img") or ""


def osu_points(no):
    """宿の「おすすめ」を最大3つ。どれもデータから言えることだけ"""
    d = _osu_load().get(int(no)) or {}; e = d.get("ex") or {}; c = d.get("det")
    sp = c[7] if c else (e.get("special") or ""); fac = c[9] if c else ""
    pts = []
    if re.search(r"全(客)?室.{0,10}露天|露天.{0,14}全\d*(客)?室", sp): pts.append("全室に露天風呂")
    elif "露天風呂付" in sp: pts.append("露天風呂つきの客室あり")
    sc = []
    if c:
        try: sc = [(float(v), _SC_JA[i]) for i, v in enumerate(c[3].split(",")[:6]) if v]
        except Exception: sc = []
    if sc:
        top = sorted(sc, key=lambda x: -x[0])[:2]
        pts.append("口コミで高い項目：" + "・".join(f"{n} {v:.2f}" for v, n in top))
    dn = [x for x in re.split(r"[、,]", e.get("dinner") or "") if x]
    MAP = {"部屋": "部屋食", "個室": "個室", "レストラン(バイキング)": "ビュッフェ", "広間": "広間", "料亭": "料亭", "食事処": "食事処", "レストラン": "レストラン", "ダイニングルーム": "ダイニング", "炉端処": "炉端", "茶寮": "茶寮", "食堂": "食堂"}
    dn = [MAP.get(x, x) for x in dn if x != "コンベンションホール"][:2]
    ext = [w for w, k in (("大浴場", "大浴場"), ("サウナ", "サウナ"), ("送迎", "送迎")) if k in fac][:2]
    if dn: pts.append("夕食：" + "・".join(dict.fromkeys(dn)) + (f"／{'・'.join(ext)}あり" if ext and len(pts) >= 2 else ""))
    if len(pts) < 3 and ext and not any("あり" in p and "夕食" in p for p in pts): pts.append("・".join(ext) + "あり")
    if len(pts) < 3 and c:
        try: rooms = int(c[6] or 0)
        except Exception: rooms = 0
        if 0 < rooms <= 30: pts.append(f"全{rooms}室の小さな宿")
    return pts[:3]


# ---- 楽天トラベルのキャンペーン（2026/11/20）
# トップのコーナーと宿ページの予約バーに、いま開催中のものを1つだけ出す（ブラックフライデー → スーパーSALE → 5と0のつく日の順）。
# 期間の判定は開いた人のブラウザでする（ページの作り直しを待たずに、始まったら出て、終わったら消える）。
# 日程・割引の書き方は楽天の発表どおり。「最大◯%」の形で書き、推測の数字は使わない。
CAMPAIGNS = [
    {"key": "bf", "name": "楽天トラベル ブラックフライデー", "s": "2026-11-19T10:00:00+09:00", "e": "2026-12-01T09:59:00+09:00",
     "when": "12/1(火) 9:59まで", "when_bar": "〜12/1 9:59", "url": "https://travel.rakuten.co.jp/special/blackfriday/", "pct": 30,
     "short": "クーポン最大30%オフ", "cta": "クーポンを取る（楽天トラベル）",
     "pts": ["国内の宿：クーポン併用で<b>最大30%オフ</b>", "楽天トラベルクーポン 最大10%＋宿クーポン 最大20%"],
     "src": "楽天グループ 2026/11/19 発表"},
    # 楽天トラベルのSALEは楽天市場より長く続くことが多い（2026年3・6月は20日まで、9月は10/1まで）。終わりは開始後に公式ページで確かめて when に書く
    {"key": "ss", "name": "楽天トラベル スーパーSALE", "s": "2026-12-04T20:00:00+09:00", "e": "2026-12-20T23:59:00+09:00", "pre": "2026-12-01T10:00:00+09:00",
     "when": "", "when_pre": "12/4(金) 20時から", "url": "https://travel.rakuten.co.jp/special/supersale/", "pct": None,
     "short": "SALEプラン・クーポンあり", "cta": "SALEを見る（楽天トラベル）",
     "pts": ["SALE価格のプランと、割引クーポンが出ます", "まず神日を決めて、SALEのプランと見比べる"]},
    {"key": "f0", "name": "5と0のつく日", "daily": True, "url": "https://travel.rakuten.co.jp/camp/50luxday/", "pct": 20,
     "short": "クーポン最大20%オフ", "cta": "クーポンを取る（楽天トラベル）", "when": "今日23:59まで",
     "pts": ["ホテル・温泉宿：クーポンで<b>最大20%オフ</b>", "クーポンを取ってから予約する"]},
]
CARD_PT = "楽天カードで事前決済：ポイント<b>2.5倍</b>（要エントリー・" + CARD_CAMP["book_end_ja"].replace("2026年", "").replace("月", "/").replace("日", " ") + "まで）"


def camp_link(url):
    import urllib.parse
    return f"https://hb.afl.rakuten.co.jp/hgc/589faade.b97f81b7.589faadf.010fa421/?pc={urllib.parse.quote(url, safe='')}&m={urllib.parse.quote(url, safe='')}"


_EV_JS = ("<script>(function(){var n=Date.now(),d=new Date(n+324e5),day=d.getUTCDate(),f=day%5==0&&day<=30,hit=0;"
          "document.querySelectorAll('[data-ev-s]').forEach(function(x){if(hit&&x.getAttribute('data-ev-g')==hit)return x.remove();"
          "var ok=x.hasAttribute('data-ev-d')?f:(n>=+x.getAttribute('data-ev-s')&&n<=+x.getAttribute('data-ev-e'));"
          "if(ok){x.hidden=false;hit=x.getAttribute('data-ev-g')}else x.remove()})})();</script>")


def _ev_attr(c, g):
    if c.get("daily"): return f' data-ev-s="0" data-ev-d data-ev-g="{g}"'
    ts = lambda s: int(_dt.datetime.fromisoformat(s).timestamp() * 1000)
    return f' data-ev-s="{ts(c.get("pre") or c["s"])}" data-ev-e="{ts(c["e"])}" data-ev-g="{g}"'


def ev_example():
    """棒グラフの例：箱根・はつはな（16108）の、神日がある月の「高い日」と「神日」"""
    b = lowest_upcoming(16108)
    if not b: return None
    v, d = b; hi = max(month_prices(16108, d.year, d.month))
    return {"name": "はつはな（箱根）", "hi": hi, "kami": v, "d": d}


def ev_corner(base):
    """トップのキャンペーンコーナー（開催中のものを1つだけ）"""
    ex = ev_example(); out = []
    for c in CAMPAIGNS:
        if not c.get("daily") and _dt.datetime.fromisoformat(c["e"]) < _dt.datetime.now(JST): continue
        pre = c.get("pre")
        lv = '<span class="lv">開催中</span>'
        when = c["when"]
        if pre:   # 始まる前は「まもなく」と開始の日時
            out.append(_ev_block(c, base, ex, '<span class="lv pre">まもなく</span>', c["when_pre"], f' data-ev-s="{int(_dt.datetime.fromisoformat(pre).timestamp()*1000)}" data-ev-e="{int(_dt.datetime.fromisoformat(c["s"]).timestamp()*1000) - 1}" data-ev-g="top"'))
            out.append(_ev_block(c, base, ex, lv, when, f' data-ev-s="{int(_dt.datetime.fromisoformat(c["s"]).timestamp()*1000)}" data-ev-e="{int(_dt.datetime.fromisoformat(c["e"]).timestamp()*1000)}" data-ev-g="top"'))
        else:
            out.append(_ev_block(c, base, ex, lv, when, _ev_attr(c, "top")))
    return ("".join(out) + _EV_JS) if out else ""


def _yen(v): return f"¥{v:,}"


def _ev_block(c, base, ex, lv, when, attr):
    card = [CARD_PT] if _dt.datetime.now(JST) < _dt.datetime.fromisoformat(CARD_CAMP["book_end"]) else []
    pts = "".join(f"<li>{p}</li>" for p in c["pts"] + card)
    grf = ""
    if ex and c.get("pct"):
        cut = int(ex["kami"] * (100 - c["pct"]) / 100)
        w = lambda v: f"{max(8, round(v / ex['hi'] * 100, 1))}%"
        grf = (f'<details class="evx"><summary><span>神日と重ねると、いくらになる？</span><small>例：{ex["name"]}</small></summary>'
               f'<div class="ex"><small>{ex["name"]}・2名1泊・税込</small>'
               f'<div class="evb"><span>高い日</span><i style="width:100%"><span>{_yen(ex["hi"])}</span></i></div>'
               f'<div class="evb k"><span>神日 {ex["d"].month}/{ex["d"].day}</span><i style="width:{w(ex["kami"])}"><span>{_yen(ex["kami"])}</span></i></div>'
               f'<div class="evb c"><span>最大{c["pct"]}%オフなら</span><i style="width:{w(cut)}"><span>{_yen(cut)}</span></i></div>'
               f'<p class="nt">クーポンの割引率は宿によって違います。「最大{c["pct"]}%オフなら」は、上限まで使えた場合の計算です。</p></div></details>')
    w_ = f'<span class="ct">{when}</span>' if when else ""
    return (f'<section class="ev" aria-label="開催中のキャンペーン" hidden{attr}><div class="in">'
            f'<div class="hd">{lv}<b>{c["name"]}</b>{w_}</div><div class="bd"><ul>{pts}</ul>{grf}'
            f'<div class="go"><a class="p" href="{camp_link(c["url"])}" target="_blank" rel="noopener sponsored" data-ev="{c["key"]}">{c["cta"]}</a>'
            f'<a class="s" href="{base}#search">神日を探す</a></div></div></div></section>')


def ev_bar_line():
    """宿ページの予約バーの上に出す1行（開催中のものを1つだけ）"""
    out = []
    for c in CAMPAIGNS:
        if not c.get("daily") and _dt.datetime.fromisoformat(c["e"]) < _dt.datetime.now(JST): continue
        if c.get("pre"):
            attr = f' data-ev-s="{int(_dt.datetime.fromisoformat(c["s"]).timestamp()*1000)}" data-ev-e="{int(_dt.datetime.fromisoformat(c["e"]).timestamp()*1000)}" data-ev-g="bar"'
        else: attr = _ev_attr(c, "bar")
        when = f"・{c.get('when_bar') or c['when']}" if c.get("when") else ""
        out.append(f'<a class="bev" hidden{attr} href="{camp_link(c["url"])}" target="_blank" rel="noopener sponsored" data-ev="{c["key"]}">'
                   f'<span class="t"><b>{c["name"].replace("楽天トラベル ", "")}</b>{c["short"]}{when}</span><span aria-hidden="true">›</span></a>')
    return ("".join(out) + _EV_JS) if out else ""
