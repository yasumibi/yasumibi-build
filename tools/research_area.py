"""エリアの宿を楽天トラベルから全件取り、YASUMIBIに載せる候補を選ぶ（根拠つき）。

使い方（GitHub Actions の「候補調査」から）:
    YB_AREAS=kusatsu,yufuin YB_ADD=1 python3 tools/research_area.py

選び方（箱根・熱海と同じ基準）
 1. 楽天トラベルに登録されているそのエリアの宿を全件取得
 2. 口コミ50件以上・評価4.3以上
 3. 先の平日（水曜）6日で「大人2名・1泊2食付き」のプランがあるか確認（満室の宿も、別の日で拾えるよう日付を散らす）
 4. ペット特化・民宿・ペンション・ゲストハウスは除く
 5. 補正スコア（口コミが少ない宿は平均4.4に寄せる）の高い順に、最大 YB_MAX 軒（既定60）
結果は data/candidates/<エリア>.tsv に全件（理由つき）を残し、YB_ADD=1 のときは選ばれた宿を data/hotels.json に足す。
"""
import json, os, re, sys, time, datetime, unicodedata

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA, TODAY, MONTHS, _add_months
import fetch_prices as fp

ENGINE = "https://openapi.rakuten.co.jp/engine/api/Travel/"
MIN_RC, MIN_RA = int(os.environ.get("YB_MIN_RC", "50")), float(os.environ.get("YB_MIN_RA", "4.3"))
MAX_ADD = int(os.environ.get("YB_MAX", "60"))
EXCL = ("民宿", "ペンション", "ゲストハウス", "ペット", "dogs", "dog", "ドッグ", "犬", "わんわん", "わんこ", "わん", "カプセル", "ホステル", "グランピング", "glamping", "ファミリーロッジ", "cabinity", "global cabin", "stay villa", "一棟", "プールヴィラ", "pool villa", "luxury villa", "cottage", "森のコテージ", "グランコテージ", "貸別荘", "guest house", "guesthouse", "hostel")


def api(path, params):
    old = fp.API; fp.API = ENGINE + path
    try:
        return fp.call(params)
    finally:
        fp.API = old
        time.sleep(fp.WAIT)


def resolve(area):
    """areas.json の middle/small/detail が無ければ、名前（match）から楽天のエリアコードを探す。"""
    if area.get("small"): return [(area["middle"], area["small"], area.get("detail"))]
    if area.get("codes"): return [tuple(c) for c in area["codes"]]
    r = api("GetAreaClass/20131024", {})
    if not r or "areaClasses" not in r:
        print(f"::warning::楽天のエリア一覧が取れませんでした（{str(r)[:150]}）", flush=True)
    out = []
    def walk(o, mid=None, sm=None):
        if isinstance(o, list):
            for x in o: walk(x, mid, sm)
        elif isinstance(o, dict):
            for k, v in o.items():
                if k == "middleClass" and isinstance(v, (dict, list)):
                    items = v if isinstance(v, list) else [v]
                    for it in items:
                        if isinstance(it, dict) and "middleClassCode" in it: mid = it["middleClassCode"]
                if k == "smallClass" and isinstance(v, (dict, list)):
                    items = v if isinstance(v, list) else [v]
                    for it in items:
                        if isinstance(it, dict) and "smallClassCode" in it:
                            sm = it["smallClassCode"]
                            if any(m in it.get("smallClassName", "") for m in area["match"]): out.append((mid, sm, None))
                if k == "detailClass" and isinstance(v, (dict, list)):
                    items = v if isinstance(v, list) else [v]
                    for it in items:
                        if isinstance(it, dict) and "detailClassCode" in it and any(m in it.get("detailClassName", "") for m in area["match"]):
                            out.append((mid, sm, it["detailClassCode"]))
                walk(v, mid, sm)
    walk(r)
    # detail が見つかったら、同じ small 全体は使わない
    dsm = {(m, s) for m, s, d in out if d}
    out = [x for x in out if x[2] or (x[0], x[1]) not in dsm]
    return sorted(set(out), key=lambda x: (x[0] or "", x[1] or "", x[2] or ""))


def list_hotels(codes):
    seen = {}
    for mid, sm, det in codes:
        page, pc = 1, 1
        while page <= pc:
            q = dict(largeClassCode="japan", middleClassCode=mid, smallClassCode=sm, hits=30, page=page, responseType="large")
            if det: q["detailClassCode"] = det
            try:
                r = api("SimpleHotelSearch/20170426", q) or {}
            except SystemExit as e:   # まちがったエリアコードは飛ばして、ほかのコードで続ける
                print(f"::warning::エリアコード {mid}/{sm}/{det} は使えません：{str(e)[:120]}", flush=True); break
            pc = (r.get("pagingInfo") or {}).get("pageCount", 1)
            for h in r.get("hotels", []):
                parts = h if isinstance(h, list) else [h]
                o = {}
                for p in parts:
                    b = p.get("hotelBasicInfo")
                    if b: o.update(no=b["hotelNo"], name=b.get("hotelName", ""), rc=b.get("reviewCount") or 0, ra=b.get("reviewAverage") or 0,
                                   addr=(b.get("address1") or "") + (b.get("address2") or ""))
                    rt = p.get("hotelRatingInfo")
                    if rt: o.update(meal=rt.get("mealAverage") or 0, bath=rt.get("bathAverage") or 0)
                    f = p.get("hotelFacilitiesInfo")
                    if f: o["rn"] = f.get("hotelRoomNum") or 0
                if o.get("no"): seen[o["no"]] = o
            page += 1
    return list(seen.values())


def check_dates():
    """先の月の水曜を6日（2か月先〜5か月先、各月1〜2日）。祝日や年末年始は避ける。"""
    ds = []
    for k in (2, 3, 4, 5):
        y, m = _add_months(TODAY.year, TODAY.month, k)
        weds = [datetime.date(y, m, d) for d in range(8, 26) if datetime.date(y, m, d).weekday() == 2]
        ds += weds[:2] if k in (2, 4) else weds[:1]
    return ds[:6]


def clean_name(n):
    n = unicodedata.normalize("NFKC", n)
    n = re.sub(r"[（(<＜].*?[)）>＞]", "", n).strip()
    n = re.sub(r"^\S*温泉\s+", "", n) if len(re.sub(r"^\S*温泉\s+", "", n)) >= 3 else n
    return n.strip()


def main():
    areas = {a["key"]: a for a in json.load(open(f"{DATA}/areas.json"))}
    want = [x for x in (os.environ.get("YB_AREAS") or "").split(",") if x]
    hotels = json.load(open(f"{DATA}/hotels.json"))
    have = {h["no"] for h in hotels}
    # 個別に外した宿（貸別荘・一棟貸しなど、ほかの宿と比べ方が違う宿）。data/blocklist.json に {施設番号: 理由}
    try: BLOCK = {int(k): v for k, v in json.load(open(f"{DATA}/blocklist.json")).items()}
    except Exception: BLOCK = {}
    os.makedirs(f"{DATA}/candidates", exist_ok=True)
    dates = check_dates()
    print("確認する日：", ", ".join(map(str, dates)), flush=True)
    added_total = 0
    for key in want:
        try:
            a = areas[key]
            codes = resolve(a)
            if not codes:
                print(f"::warning::[{key}] 楽天のエリアが見つかりません（match={a.get('match')}）"); continue
            a["codes"] = codes
            allh = list_hotels(codes)
            if a.get("addr"):   # 楽天のエリアが広いときは、住所で絞る（例：草津町）
                allh = [o for o in allh if any(x in o.get("addr", "") for x in a["addr"])]
            print(f"[{key}] 楽天に登録 {len(allh)}軒（エリアコード {codes}）", flush=True)
            print(f"::notice::[{key}] エリアコード {codes}", flush=True)
            cand = [o for o in allh if o["rc"] >= MIN_RC and o["ra"] >= MIN_RA]
            fp.MEAL_NOW["v"] = int(a.get("meal", 2))      # 京都・沖縄・北海道の街などは1泊朝食付きで調べる
            best = {}
            nos = [o["no"] for o in cand]
            seen_any = set()
            for d in dates:
                got = fp.fetch_date(nos, d)
                for no, v in got.items():
                    if v and (no not in best or v < best[no]): best[no] = v
            rows = []
            for o in allh:
                reason = ""
                if o["rc"] < MIN_RC: reason = f"口コミ{MIN_RC}件未満"
                elif o["ra"] < MIN_RA: reason = f"評価{MIN_RA}未満"
                elif not best.get(o["no"]): reason = ("2食付き" if fp.MEAL_NOW["v"] == 2 else "朝食付き") + "の空きが見つからない"
                elif any(x in unicodedata.normalize("NFKC", o["name"]).lower() for x in EXCL): reason = "民宿・ペンション・ペット特化・グランピング・一棟貸し・コテージなど"
                elif o["no"] in BLOCK: reason = "個別に除外：" + BLOCK[o["no"]]
                o["price"] = best.get(o["no"], 0)
                o["score"] = (o["ra"] * o["rc"] + 4.4 * 150) / (o["rc"] + 150)
                o["reason"] = reason
                rows.append(o)
            ok = sorted([o for o in rows if not o["reason"]], key=lambda o: -o["score"])
            pick = ok[:MAX_ADD]
            for o in ok[MAX_ADD:]: o["reason"] = f"上位{MAX_ADD}軒の外"
            with open(f"{DATA}/candidates/{key}.tsv", "w", encoding="utf-8") as fh:
                fh.write("採用\t施設番号\t宿名\t口コミ件数\t評価\t食事\t風呂\t客室数\t2食の目安\t補正スコア\t理由\n")
                for o in sorted(rows, key=lambda o: (o["reason"] != "", -o["score"])):
                    fh.write("\t".join(map(str, ["○" if o in pick else "", o["no"], o["name"], o["rc"], f'{o["ra"]:.2f}', f'{o.get("meal", 0) or 0:.2f}', f'{o.get("bath", 0) or 0:.2f}', o.get("rn", 0),
                                                 o["price"], f"{o['score']:.3f}", o["reason"]])) + "\n")
            print(f"::notice::[{key}] 楽天{len(allh)}軒・口コミ基準{len(cand)}軒・基準を満たす {len(ok)}軒 → 採用 {len(pick)}軒（すでに掲載 {sum(1 for o in pick if o['no'] in have)}軒）", flush=True)
            print(f"[{key}] 基準を満たす {len(ok)}軒 → 採用 {len(pick)}軒（すでに掲載 {sum(1 for o in pick if o['no'] in have)}軒）", flush=True)
            if os.environ.get("YB_ADD") == "1":
                for o in pick:
                    if o["no"] in have: continue
                    hotels.append(dict(no=o["no"], area=key, slug=f"h{o['no']}", name=clean_name(o["name"]), full=unicodedata.normalize("NFKC", o["name"]),
                                       loc=a["name"], tier="mid" if o["price"] < 70000 else "high", avg=o["ra"], cnt=o["rc"],
                                       added=TODAY.isoformat(), ref_price=o["price"]))
                    have.add(o["no"]); added_total += 1
        except BaseException as e:   # 1つのエリアで失敗しても、ほかのエリアは続ける（理由はGitHubの画面に出す）
            import traceback
            tb = traceback.format_exc().strip().splitlines()
            print(f"::warning::[{key}] 調べられませんでした：{type(e).__name__}: {str(e)[:200]} ／ {tb[-3] if len(tb) >= 3 else ''}", flush=True)
    json.dump(list(areas.values()), open(f"{DATA}/areas.json", "w"), ensure_ascii=False, indent=1)
    if os.environ.get("YB_ADD") == "1":
        json.dump(hotels, open(f"{DATA}/hotels.json", "w"), ensure_ascii=False, indent=1)
    print(f"追加した宿：{added_total}軒（合計 {len(hotels)}軒）")


if __name__ == "__main__":
    main()
