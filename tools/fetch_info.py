"""楽天トラベル施設情報API（HotelDetailSearch）で、宿ページ用の情報を取り直す。

- data/hotels.json の宿のうち、写真・アクセス（hotel_info）や紹介文・評価・口コミ（hotel_detail）がまだ無い宿を取る。
- YB_INFO_ALL=1 のときは全宿を取り直す（口コミ・評価を新しくする。週1回程度）。
- 認証情報は環境変数から読む（fetch_prices.py と同じ）。
"""
import json, os, re, sys, time, datetime, html as _html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT
import fetch_prices as fp

API = "https://openapi.rakuten.co.jp/engine/api/Travel/HotelDetailSearch/20170426"
INFO_F = f"{ROOT}/data/hotel_info_20261021.json"
DET_F = f"{ROOT}/data/hotel_detail_20261021.tsv"
HOTELS_F = f"{ROOT}/data/hotels.json"
JST = datetime.timezone(datetime.timedelta(hours=9))

# 住所から地区名を決める（箱根・熱海）
LOC = [("湯本", "箱根湯本温泉"), ("塔之沢", "塔之沢"), ("大平台", "大平台"), ("宮ノ下", "宮ノ下"), ("底倉", "底倉"), ("小涌谷", "小涌谷"), ("二ノ平", "二ノ平"),
       ("強羅", "強羅温泉"), ("宮城野", "宮城野"), ("仙石原", "仙石原"), ("芦之湯", "芦之湯"), ("元箱根", "芦ノ湖"), ("箱根町箱根", "芦ノ湖"),
       ("伊豆山", "伊豆山温泉"), ("網代", "網代温泉"), ("上多賀", "多賀"), ("下多賀", "多賀"), ("熱海", "熱海温泉")]


def clean(s):
    s = re.sub(r"<[^>]+>[^<]*</a>", "", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return _html.unescape(s).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def get(no):
    q = dict(hotelNo=no, responseType="large")
    old = fp.API; fp.API = API
    try:
        r = fp.call(q)
    finally:
        fp.API = old
    time.sleep(fp.WAIT)
    if not r or not r.get("hotels"): return None
    h = r["hotels"][0]
    parts = h if isinstance(h, list) else [h]
    g = lambda k: next((p[k] for p in parts if k in p), {})
    return g("hotelBasicInfo"), g("hotelRatingInfo"), g("hotelDetailInfo"), g("hotelFacilitiesInfo")


def main():
    if not fp.APP_ID or not fp.ACCESS_KEY:
        raise SystemExit("RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY が設定されていません")
    hotels = json.load(open(HOTELS_F))
    info = json.load(open(INFO_F))
    det = {}
    for ln in open(DET_F, encoding="utf-8"):
        if ln.strip(): det[int(ln.split("\t", 1)[0])] = ln.rstrip("\n")
    all_ = os.environ.get("YB_INFO_ALL") == "1"
    areas = [x for x in (os.environ.get("YB_AREAS") or "").split(",") if x]
    todo = [h for h in hotels if (not areas or h["area"] in areas) and (all_ or str(h["no"]) not in info["hotels"] or h["no"] not in det)]
    print(f"施設情報を取得：{len(todo)}軒", flush=True)
    changed = False
    for h in todo:
        got = get(h["no"])
        if not got:
            print(f"  {h['no']} 取得できず"); continue
        b, rt, d, f = got
        thumb = (b.get("hotelThumbnailUrl") or "").replace("/HIMG/90/", "/HIMG/300/") or b.get("hotelImageUrl", "")
        info["hotels"][str(h["no"])] = {k: v for k, v in dict(img=b.get("hotelImageUrl", ""), room=b.get("roomImageUrl") or None,
                                         station=b.get("nearestStation", ""), access=clean(b.get("access", "")), thumb=thumb).items() if v}
        rts = ",".join(str(rt.get(k, 0) or 0) for k in ("serviceAverage", "locationAverage", "roomAverage", "equipmentAverage", "bathAverage", "mealAverage"))
        fac = "、".join(x.get("item", "") for x in (f.get("hotelFacilities") or []))
        det[h["no"]] = "\t".join(map(str, [h["no"], b.get("reviewAverage") or 0, b.get("reviewCount") or 0, rts, d.get("checkinTime", ""), d.get("checkoutTime", ""),
                                           f.get("hotelRoomNum") or 0, clean(b.get("hotelSpecial", "")), clean(b.get("userReview", "")), clean(fac)]))
        addr = (b.get("address1", "") or "") + (b.get("address2", "") or "")
        if h.get("added") != "2026-10-19":   # 最初の20軒の地区名は手で付けたものを残す
            for k, v in LOC:
                if k in addr: h["loc"] = v; break
        if b.get("reviewAverage"): h["avg"] = float(b["reviewAverage"])
        if b.get("reviewCount"): h["cnt"] = int(b["reviewCount"])
        changed = True
    if changed:
        info["fetched"] = datetime.datetime.now(JST).strftime("%Y-%m-%d")
        json.dump(info, open(INFO_F, "w"), ensure_ascii=False, indent=1)
        open(DET_F, "w", encoding="utf-8").write("\n".join(det[k] for k in det) + "\n")
        json.dump(hotels, open(HOTELS_F, "w"), ensure_ascii=False, indent=1)
    print("施設情報 完了")


if __name__ == "__main__":
    main()
