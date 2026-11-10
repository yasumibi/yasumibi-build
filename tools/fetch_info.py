"""楽天トラベル施設情報API（HotelDetailSearch）で、宿ページ用の情報を取り直す。

- data/hotels.json の宿のうち、写真・アクセス（hotel_info）や紹介文・評価・口コミ（hotel_detail）がまだ無い宿を取る。
- YB_INFO_ALL=1 のときは全宿を取り直す（口コミ・評価を新しくする。週1回程度）。
- 認証情報は環境変数から読む（fetch_prices.py と同じ）。
"""
import json, os, re, sys, time, datetime, html as _html

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, loc_from_address, fix_loc
import fetch_prices as fp

API = "https://openapi.rakuten.co.jp/engine/api/Travel/HotelDetailSearch/20170426"
INFO_F = f"{ROOT}/data/hotel_info_20261021.json"
DET_F = f"{ROOT}/data/hotel_detail_20261021.tsv"
HOTELS_F = f"{ROOT}/data/hotels.json"
EXTRA_F = f"{ROOT}/data/hotel_extra.json"   # 宿ページの「お風呂・食事の場所・駐車場・評価の内訳」（2026/11/10〜）
JST = datetime.timezone(datetime.timedelta(hours=9))

# 住所から地区名を決める決まりは common.py の LOC_RULES（エリアごと。箱根の決まりはほかのエリアに使わない）


def clean(s):
    s = re.sub(r"<[^>]+>[^<]*</a>", "", s or "")
    s = re.sub(r"<[^>]+>", "", s)
    return _html.unescape(s).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def flat(v):
    """API の値が文字列・リスト・{"item": …} のどれでも、文字列にする（リストは「、」でつなぐ）。"""
    if v is None: return ""
    if isinstance(v, str): return clean(v)
    if isinstance(v, dict): return "、".join(x for x in (flat(y) for y in v.values()) if x)
    if isinstance(v, list): return "、".join(x for x in (flat(y) for y in v) if x)
    return clean(str(v))


def collect(v, out=None, key=""):
    """入れ子（リスト・{"bathType": …} など）をたどって、項目名ごとの値の一覧にする。"""
    out = {} if out is None else out
    if isinstance(v, dict):
        for k, y in v.items(): collect(y, out, k)
    elif isinstance(v, list):
        for y in v: collect(y, out, key)
    elif v not in (None, "") and key:
        t = clean(str(v))
        if t and t not in out.setdefault(key, []): out[key].append(t)
    return out


_SHOWN = []


def get(no):
    q = dict(hotelNo=no, responseType="large", datumType=1)   # 緯度経度は世界測地系・度で
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
    extra = json.load(open(EXTRA_F)) if os.path.exists(EXTRA_F) else {}
    det = {}
    for ln in open(DET_F, encoding="utf-8"):
        if ln.strip(): det[int(ln.split("\t", 1)[0])] = ln.rstrip("\n")
    all_ = os.environ.get("YB_INFO_ALL") == "1"
    areas = [x for x in (os.environ.get("YB_AREAS") or "").split(",") if x]
    todo = [h for h in hotels if (not areas or h["area"] in areas) and (all_ or str(h["no"]) not in info["hotels"] or h["no"] not in det or "lat" not in info["hotels"][str(h["no"])] or (os.environ.get("YB_EXTRA_FILL") == "1" and extra.get(str(h["no"]), {}).get("v") != 2))]
    print(f"施設情報を取得：{len(todo)}軒", flush=True)
    changed = False
    for h in todo:
        got = get(h["no"])
        if not got:
            print(f"  {h['no']} 取得できず"); continue
        b, rt, d, f = got
        thumb = (b.get("hotelThumbnailUrl") or "").replace("/HIMG/90/", "/HIMG/300/") or b.get("hotelImageUrl", "")
        info["hotels"][str(h["no"])] = {k: v for k, v in dict(img=b.get("hotelImageUrl", ""), room=b.get("roomImageUrl") or None,
                                         station=b.get("nearestStation", ""), access=clean(b.get("access", "")), thumb=thumb,
                                         lat=b.get("latitude"), lng=b.get("longitude")).items() if v}
        rts = ",".join(str(rt.get(k, 0) or 0) for k in ("serviceAverage", "locationAverage", "roomAverage", "equipmentAverage", "bathAverage", "mealAverage"))
        fac = "、".join(x.get("item", "") for x in (f.get("hotelFacilities") or []))
        det[h["no"]] = "\t".join(map(str, [h["no"], b.get("reviewAverage") or 0, b.get("reviewCount") or 0, rts, d.get("checkinTime", ""), d.get("checkoutTime", ""),
                                           f.get("hotelRoomNum") or 0, clean(b.get("hotelSpecial", "")), clean(b.get("userReview", "")), clean(fac)]))
        cb = collect(f.get("aboutBath")); cb.update({k: v for k, v in collect({k: f.get(k) for k in ("bathType", "bathQuality", "bathBenefits")}).items() if v})
        cm = collect(f.get("aboutMealPlace")); cm.update({k: v for k, v in collect({k: f.get(k) for k in ("dinnerPlace", "breakfastPlace")}).items() if v})
        if not _SHOWN:   # 1軒目だけ、項目名をログに出す（中身は出さない）
            _SHOWN.append(1); print("  お風呂:", sorted(cb), "食事:", sorted(cm), "評価:", sorted(rt.keys()), flush=True)
        j = lambda xs: "、".join(xs or [])
        ex = dict(bath_t=j(cb.get("bathType")), bath_q=j(cb.get("bathQuality")), bath_b=j(cb.get("bathBenefits")),
                  bath=j([x for k, xs in cb.items() if k not in ("bathType", "bathQuality", "bathBenefits") for x in xs]),
                  dinner=j(cm.get("dinnerPlace")), breakfast=j(cm.get("breakfastPlace")),
                  meal=j([x for k, xs in cm.items() if k not in ("dinnerPlace", "breakfastPlace") for x in xs]),
                  parking=flat(b.get("parkingInformation")), special=flat(b.get("hotelSpecial")), room_img=b.get("roomImageUrl") or "",
                  rt={k: rt.get(k) for k in ("bathAverage", "dinnerAverage", "breakfastAverage", "roomAverage", "mealAverage") if rt.get(k)})
        extra[str(h["no"])] = dict({k: v for k, v in ex.items() if v}, v=2)
        addr = (b.get("address1", "") or "") + (b.get("address2", "") or "")
        if h.get("added") != "2026-10-19":   # 最初の20軒の地区名は手で付けたものを残す
            v = loc_from_address(h["area"], addr)   # そのエリアの決まりだけを使う
            if v: h["loc"] = v
        fix_loc(h)   # ほかのエリア専用の地区名が付いていたら、エリア名に戻す
        if b.get("reviewAverage"): h["avg"] = float(b["reviewAverage"])
        if b.get("reviewCount"): h["cnt"] = int(b["reviewCount"])
        changed = True
    if changed:
        info["fetched"] = datetime.datetime.now(JST).strftime("%Y-%m-%d")
        json.dump(info, open(INFO_F, "w"), ensure_ascii=False, indent=1)
        json.dump(extra, open(EXTRA_F, "w"), ensure_ascii=False, indent=0, sort_keys=True)
        open(DET_F, "w", encoding="utf-8").write("\n".join(det[k] for k in det) + "\n")
        json.dump(hotels, open(HOTELS_F, "w"), ensure_ascii=False, indent=1)
    print("施設情報 完了")


if __name__ == "__main__":
    main()
