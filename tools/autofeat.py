"""自動でつくる特集（型×エリア）。2026/11/10 戦略部屋の依頼・本人OK。

型（エリアページ・タグ×エリアのページと、検索の言葉がかぶらないものだけ）
 youbi   ◯◯、何曜日に泊まると安い？    いちばん安い曜日といちばん高い曜日の差（中央値）が25%以上
 5man    同じ5万円で、いちばん良い◯◯の宿  2名4〜5.5万円の日がある宿が8軒以上・★の差0.3以上（1泊2食のエリアだけ）
 2haku   ◯◯、2泊するならこの2日       いちばん安い2泊が、金土の2泊（中央値）より30%以上安い（宿ごとの中央値）
 doyou   土曜でも安い、◯◯の宿          エリアの土曜の上がり幅（中央値）20%以上で、上がり幅10%以内の宿が3軒以上
共通：エリアの宿が8軒以上。
「1人1万円台」「ハイクラス」は /tags/1man/◯◯/・/tags/hc/◯◯/ と同じ言葉なので、特集にはしない。

AUTO に並べたものだけを作る（週10本前後ずつ、本人OKのうえで足す）。
条件を外れた日は、ページ（URL）は残したまま noindex にして、一覧・リンクから外す。条件に戻れば自動で戻る。
"""
import os, json, statistics, datetime as dt
from common import HOTELS, PRH, TODAY, WINDOW_START, WINDOW_END, AREA_JA, DATA, is_b

# 公開する特集（エリア, 型）。第1弾 2026/11/10
AUTO = [("shimoda", "5man"), ("kinosaki", "youbi"), ("kobe", "youbi"), ("karuizawa", "5man"), ("miyazaki", "2haku"),
        ("kanazawa", "2haku"), ("hiroshima", "youbi"), ("izukogen", "5man"), ("tokyo", "doyou"), ("nagoya", "youbi")]
# 表紙の写真（assets/img にあって、credits.json にクレジットがあるもの）
IMG = {"shimoda": "shimoda-shirahama-beach.jpg", "kinosaki": "kinosaki-willow-day.jpg", "kobe": "kobe-port-tower.jpg",
       "karuizawa": "karuizawa-forest.jpg", "miyazaki": "miyazaki-aoshima.jpg", "kanazawa": "kanazawa-kenrokuen.jpg",
       "hiroshima": "hiroshima-castle-gate.jpg", "izukogen": "izukogen-jogasaki.jpg", "tokyo": "tokyo-skytree.jpg",
       "nagoya": "nagoya-castle.jpg"}
TYPE_LABEL = {"youbi": "曜日", "5man": "2人で5万円", "2haku": "連泊", "doyou": "土曜泊"}
MIN_HOTELS = 8
WD = "月火水木金土日"

_INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
H = {h["no"]: h for h in HOTELS if str(h["no"]) in _INFO}


def slug(area, t): return f"{area}-{t}"


def nyr(d): return (d.month == 12 and d.day >= 29) or (d.month == 1 and d.day <= 3)


def nights(no):
    src = PRH.get(str(no), {}); out = []
    d = max(TODAY + dt.timedelta(days=1), WINDOW_START)
    while d <= WINDOW_END:
        v = src.get(d.isoformat())
        if v and not nyr(d): out.append((d, int(v)))
        d += dt.timedelta(days=1)
    return out


def area_nos(a): return [no for no, h in H.items() if h["area"] == a]


_CACHE = {}


def evaluate(area, t):
    """{"ok": bool, ...型ごとの数字}。毎日の料金から判定する。"""
    k = (area, t)
    if k in _CACHE: return _CACHE[k]
    nos = area_nos(area); NS = {no: nights(no) for no in nos}
    r = {"ok": False, "n": len(nos)}
    if len(nos) >= MIN_HOTELS:
        if t == "youbi":
            byw = {}
            for no, ns in NS.items():
                for d, v in ns: byw.setdefault(d.weekday(), []).append(v)
            wr = {w: statistics.median(v) for w, v in byw.items() if len(v) >= 10}
            if len(wr) == 7:
                lo = min(wr, key=wr.get); hi = max(wr, key=wr.get); g = 1 - wr[lo] / wr[hi]
                r.update(ok=g >= 0.25, wr=wr, lo=lo, hi=hi, gap=g, yen=wr[hi] - wr[lo])
        elif t == "5man" and not is_b(area):
            rows = []
            for no in nos:
                c = [x for x in NS[no] if 40000 <= x[1] <= 55000]
                if c:
                    d, v = min(c, key=lambda x: (x[1], x[0]))
                    rows.append((H[no]["avg"], H[no]["cnt"], no, d, v, len(c)))
            rows.sort(key=lambda x: (-x[0], -x[1]))
            sp = rows[0][0] - rows[-1][0] if rows else 0
            r.update(ok=len(rows) >= 8 and sp >= 0.3, rows=rows, spread=sp)
        elif t == "2haku":
            rows = []
            for no, ns in NS.items():
                m = dict(ns); best = None; fs = []
                for d, v in m.items():
                    n2 = m.get(d + dt.timedelta(days=1))
                    if not n2: continue
                    tot = v + n2
                    if best is None or tot < best[0]: best = (tot, d)
                    if d.weekday() == 4: fs.append(tot)
                if best and len(fs) >= 3:
                    fm = statistics.median(fs); rows.append((best[0], no, best[1], fm))
            rows.sort(key=lambda x: (x[0], x[2]))
            if len(rows) >= 5:
                med = statistics.median(1 - b / f for b, _, _, f in rows); my = statistics.median(f - b for b, _, _, f in rows)
                r.update(ok=med >= 0.30, rows=rows, med=med, yen=my)
        elif t == "doyou":
            rows = []
            for no, ns in NS.items():
                sa = [x for x in ns if x[0].weekday() == 5]; wk = [v for d, v in ns if d.weekday() in (6, 0, 1, 2, 3)]
                if len(sa) >= 4 and len(wk) >= 10:
                    sm, wm = statistics.mean(v for _, v in sa), statistics.mean(wk)
                    d, v = min(sa, key=lambda x: (x[1], x[0]))
                    rows.append((sm / wm - 1, no, sm, wm, d, v))
            if rows:
                med = statistics.median(x[0] for x in rows)
                small = sorted([x for x in rows if x[0] <= 0.10], key=lambda x: (x[5], x[4]))   # いちばん安い土曜の料金が安い順
                r.update(ok=len(small) >= 3 and med >= 0.20, rows=small, med=med, all=len(rows))
    _CACHE[k] = r
    return r


def heading(area, t):
    a = AREA_JA[area]
    return {"youbi": f"{a}の宿の曜日ごとの料金", "5man": f"2人で5万円前後の{a}の宿（★の高い順）",
            "2haku": f"{a}で2泊の合計が安い日", "doyou": f"土曜泊でも料金が上がりにくい{a}の宿"}[t]


def live():
    """いま条件を満たしている特集：[(area, t, slug, 見出し)]"""
    return [(a, t, slug(a, t), heading(a, t)) for a, t in AUTO if evaluate(a, t)["ok"]]


def card_sub(area, t):
    """特集一覧のカードの小さい文字。"""
    a = AREA_JA[area]; r = evaluate(area, t)
    if t == "youbi": return f"{a}・{WD[r['lo']]}曜泊が土曜より{r['gap'] * 100:.0f}%安い"
    if t == "5man": return f"{a}・2人4〜5.5万円の{len(r['rows'])}軒を★順に"
    if t == "2haku": return f"{a}・金土の2泊より{r['med'] * 100:.0f}%安い2日"
    if t == "doyou": return f"{a}・土曜の値上がり10%以内の{len(r['rows'])}軒"
    return a


# 手で作った特集のエリア（エリアページから特集へのリンクに使う）
MANUAL = {"hakone": ["hakone-5man", "hakone-10man", "hakone-rotenburo", "hc-hakone"], "atami": ["atami-youbi", "atami-5man", "atami-10man"],
          "kusatsu": ["kusatsu-winter"], "yufuin": ["yufuin-2haku", "yufuin-month"], "beppu": ["beppu-1man", "beppu-doyou"],
          "kinugawa": ["kinugawa-heijitsu"], "gero": ["gero-gohan"], "noboribetsu": ["noboribetsu-size"], "arima": ["arima-renkyu"],
          "kyoto": ["kyoto-koyo", "kyoto-asagohan", "kyoto-46", "hc-kyoto"], "naha": ["okinawa-month"], "ishigaki": ["okinawa-ritou"],
          "onna": ["hc-okinawa"], "sapporo": ["sapporo-yukimatsuri", "sapporo-1man"], "izukogen": ["izukogen-pet"],
          "karuizawa": ["karuizawa-luxury", "hc-karuizawa"], "kinosaki": ["kinosaki-kani"], "ito": ["ito-1man"]}


# 手で作った特集（一覧のカード）：(href, 見出し, 小さい文字, 写真)
FEATURE_CARDS = [
    ("features/hakone-5man/", "2人で5万円前後の箱根の宿（★の高い順）", "箱根・予算を固定して★の高い順", "hakone-fuji-ship.jpg"),
    ("features/hakone-10man/", "箱根の10万円の宿が安くなる日", "箱根・高級宿の値下がり幅", "hakone-torii.jpg"),
    ("features/atami-5man/", "熱海の宿、金曜泊がいちばん安い日", "熱海・金曜泊がいちばん安い日", "atami-panorama.jpg"),
    ("features/atami-10man/", "熱海の海が見える宿の神日", "熱海・海が見える宿", "atami-panorama.jpg"),
    ("features/kusatsu-winter/", "冬の草津の宿がいちばん安い週", "草津・12〜3月を週ごとに", "kusatsu-yubatake.jpg"),
    ("features/yufuin-2haku/", "由布院で2泊の合計が安い日", "由布院・連泊の合計が安い2日", "yufuin-kinrinko-sunny.jpg"),
    ("features/beppu-1man/", "1人1万円台で泊まれる別府の宿", "別府・1人2万円未満の日がある宿", "beppu-chinoike.jpg"),
    ("features/kinugawa-heijitsu/", "鬼怒川の宿、平日でいちばん安い日", "鬼怒川・日〜木泊だけで", "kinugawa-cover.jpg"),
    ("features/gero-gohan/", "下呂の食事の評価が高い宿の神日", "下呂・食事の評価が高い順", "gero-cover.jpg"),
    ("features/noboribetsu-size/", "登別の宿の客室数と神日の料金", "登別・宿の大きさと料金", "noboribetsu-jigokudani-day.jpg"),
    ("features/arima-renkyu/", "有馬の宿、連休中でも安い日", "有馬・3連休以上の夜だけで", "arima-view.jpg"),
    ("features/kyoto-koyo/", "京都の宿、11月と1月の料金差", "京都・11月と1月の料金差", "kyoto-kiyomizu-autumn.jpg"),
    ("features/kyoto-asagohan/", "京都の朝食の評価が高い宿", "京都・食事の評価が高い順", "kyoto-inari.jpg"),
    ("features/kyoto-46/", "1人1万円台で泊まれる、京都の★4.6以上の宿", "京都・★4.6以上の宿だけ", "kyoto-inari.jpg"),
    ("features/okinawa-month/", "沖縄の宿がいちばん安い月", "沖縄・月ごとの神日", "ishigaki-bay.jpg"),
    ("features/okinawa-ritou/", "沖縄の離島と本島の神日の比較", "沖縄・宮古島・石垣と本島", "ishigaki-kabira.jpg"),
    ("features/sapporo-yukimatsuri/", "さっぽろ雪まつりの週と前後の週の料金", "札幌・2027年2月4日〜11日", "sapporo-snow.jpg"),
    ("features/sapporo-1man/", "1人7千円以下で泊まれる札幌の宿", "札幌・★4.3以上・朝食付き", "sapporo-odori-blue.jpg"),
    ("features/machi-onsen-2man/", "2人で2万円未満、温泉に入れる街なかのホテル", "東京・大阪・京都・札幌など・天然温泉", "tokyo-skytree.jpg"),
    ("features/hakone-rotenburo/", "箱根の露天風呂付き客室、土曜と平日の料金差", "箱根・露天風呂付き客室", "hakone-torii.jpg"),
    ("features/atami-youbi/", "熱海の宿の曜日ごとの料金", "熱海・曜日ごとの料金", "atami-panorama.jpg"),
    ("features/yufuin-month/", "由布院の宿がいちばん安い月", "由布院・月ごとの神日", "yufuin-kinrinko.jpg"),
    ("features/beppu-doyou/", "土曜泊でも料金が上がりにくい別府の宿", "別府・土曜泊", "beppu-chinoike.jpg"),
    ("features/izukogen-pet/", "ペットと泊まれる伊豆高原の宿の神日", "伊豆高原・ペット同宿可", "izukogen-jogasaki.jpg"),
    ("features/karuizawa-luxury/", "軽井沢の高級ホテルが安くなる日", "軽井沢・いつもより下がる順", "karuizawa-kumoba-pond.jpg"),
    ("features/kinosaki-kani/", "かにの季節（11〜3月）に城崎の宿が安い日", "城崎・11〜3月", "kinosaki-willow-day.jpg"),
    ("features/ito-1man/", "1人1万円台で泊まれる伊東の宿", "伊東・2食付きで1人2万円未満", "ito-okawa-river-day.jpg"),
    ("features/aki-rare/", "空きが出にくい人気宿の、空いている日", "全国・空きの少ない人気宿", "kusatsu-yubatake-night.jpg"),
    ("features/akogare/", "全国のハイクラスの宿が安くなる日", "全国・ハイクラスの宿の神日", "hakone-fuji-ship.jpg"),
    ("features/hc-hakone/", "箱根のハイクラスの宿が安くなる日", "箱根・ハイクラス", "hakone-torii.jpg"),
    ("features/hc-kyoto/", "京都のハイクラスのホテルが安くなる日", "京都・ハイクラス", "kyoto-kiyomizu-autumn.jpg"),
    ("features/hc-karuizawa/", "軽井沢のハイクラスの宿が安くなる日", "軽井沢・ハイクラス", "karuizawa-kumoba-pond.jpg"),
    ("features/hc-okinawa/", "沖縄のハイクラスのリゾートが安くなる日", "沖縄・ハイクラス", "onna-beach-sunny.jpg")]


def area_features(area):
    """そのエリアの特集（手で作ったもの＋条件を満たしている自動の特集）：[(slug, 見出し)]"""
    title = {c[0].split("/")[1]: c[1] for c in FEATURE_CARDS}
    out = [(s, title[s]) for s in MANUAL.get(area, []) if s in title]
    out += [(sl, hd) for a, t, sl, hd in live() if a == area]
    return out
