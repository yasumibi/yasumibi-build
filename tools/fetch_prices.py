"""楽天トラベル空室検索APIから、全宿・全日付の「大人2名・1室・1泊2食付きの最安値（税込）」を取り直す。

使い方（GitHub Actions から毎日実行）:
    RAKUTEN_APP_ID=... RAKUTEN_ACCESS_KEY=... python3 tools/fetch_prices.py

- 認証情報は環境変数からだけ読む（ファイルに書かない）。
- 取得できた日付だけ上書きする。通信エラーの日付は前回の値を残す。
- 今日より前の日付は取り直さない（過去の値はそのまま残す）。
- 楽天の目安に合わせて、1秒に1回以下で呼ぶ。
"""
import json, os, sys, time, datetime, urllib.parse, urllib.request, urllib.error

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, DATA, MONTHS, WINDOW_START, WINDOW_END, price_file, PRICE_DIR

API = "https://openapi.rakuten.co.jp/engine/api/Travel/VacantHotelSearch/20170426"
APP_ID = os.environ.get("RAKUTEN_APP_ID", "")
ACCESS_KEY = os.environ.get("RAKUTEN_ACCESS_KEY", "")
REFERER = os.environ.get("YB_REFERER", "https://yasumibi.com/")
WAIT = float(os.environ.get("YB_WAIT", "1.1"))      # 1回ごとの待ち時間（秒）
GROUP = 15                                          # 1回に問い合わせる宿の数（APIの上限）
JST = datetime.timezone(datetime.timedelta(hours=9))
T0 = time.time()
BUDGET = float(os.environ.get("YB_BUDGET_MIN", "0") or 0) * 60   # これを超えたら、取れた分だけ保存して終える（0＝制限なし）
STAT = {"calls": 0}


def out_of_time():
    return BUDGET > 0 and time.time() - T0 > BUDGET


def hotels_by_area():
    out = {}
    for h in json.load(open(f"{DATA}/hotels.json")):
        out.setdefault(h["area"], []).append(h["no"])
    return out


SQUEEZE = {"on": os.environ.get("YB_SQUEEZE", "1") == "1"}   # 朝食・夕食ありで絞って、返ってくるプランを減らす


def call(params, tries=4):
    if SQUEEZE["on"] and "checkinDate" in params: params = dict(params, squeezeCondition="breakfast,dinner")
    q = dict(params, applicationId=APP_ID, accessKey=ACCESS_KEY, format="json", formatVersion=2)
    url = API + "?" + urllib.parse.urlencode(q)
    STAT["calls"] += 1
    req = urllib.request.Request(url, headers={"Referer": REFERER, "Origin": REFERER.rstrip("/"), "User-Agent": "yasumibi-price-fetch/1.0"})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            if e.code == 404 and "not_found" in body:          # その日は空室・プランなし
                return {"hotels": []}
            if e.code == 400 and "squeezeCondition" in params:   # 絞り込みが使えないときは外してやり直す
                SQUEEZE["on"] = False; print("squeezeCondition を外して続けます", flush=True)
                return call({k: v for k, v in params.items() if k != "squeezeCondition"}, tries)
            if e.code in (400, 401, 403):                      # 認証・設定の問題はやり直しても同じ
                raise SystemExit(f"API error {e.code}: {body}")
            time.sleep(WAIT * (2 ** (i + 1)))
        except Exception:
            time.sleep(WAIT * (2 ** (i + 1)))
    return None


def cheapest_two_meal(resp):
    """{hotelNo: 最安の2食付き合計} を返す。roomInfo は [基本情報, 料金, 基本情報, 料金, ...] の並び。"""
    out = {}
    for h in resp.get("hotels", []):
        parts = h if isinstance(h, list) else [h]
        no = None; rooms = []
        for part in parts:
            if "hotelBasicInfo" in part: no = part["hotelBasicInfo"]["hotelNo"]
            if "roomInfo" in part: rooms = part["roomInfo"]
        basic = None
        for r in rooms:
            if "roomBasicInfo" in r: basic = r["roomBasicInfo"]
            elif "dailyCharge" in r and basic:
                if basic.get("withDinnerFlag") == 1 and basic.get("withBreakfastFlag") == 1:
                    t = r["dailyCharge"].get("total")
                    if t and (no not in out or t < out[no]): out[no] = int(t)
                basic = None
    return out


def fetch_date(nos, d):
    """1日分。成功したら {hotelNo: 価格 or 0}、失敗した宿は含めない。"""
    nd = d + datetime.timedelta(days=1)
    result = {}
    for i in range(0, len(nos), GROUP):
        grp = nos[i:i + GROUP]
        best = {}; page = 1; ok = True
        while True:
            resp = call(dict(hotelNo=",".join(map(str, grp)), checkinDate=d.isoformat(), checkoutDate=nd.isoformat(),
                             adultNum=2, roomNum=1, searchPattern=1, hits=30, page=page, sort="+roomCharge"))
            time.sleep(WAIT)
            if resp is None: ok = False; break
            for no, v in cheapest_two_meal(resp).items():
                if no not in best or v < best[no]: best[no] = v
            pc = (resp.get("pagingInfo") or {}).get("pageCount", 1)
            if page >= pc: break
            page += 1
        if ok:
            for no in grp: result[no] = best.get(no, 0)
    return result


def due(d, today):
    """その日付を今日取り直すか。近い日ほど頻繁に。"""
    gap = (d - today).days
    near = int(os.environ.get("YB_NEAR", "45"))      # ここまでは毎日
    mid = int(os.environ.get("YB_MID", "90"))        # ここまでは YB_EVERY 日に1回
    every = int(os.environ.get("YB_EVERY", "3"))
    far = int(os.environ.get("YB_FAR_EVERY", "7"))   # それより先は週1回
    if gap <= near: return True
    if gap <= mid: return d.toordinal() % every == today.toordinal() % every
    return d.toordinal() % far == today.toordinal() % far


def run_area(area, nos, today, lim, force):
    f = price_file(area)
    pr = json.load(open(f)) if os.path.exists(f) else {"hotels": {}}
    hotels = pr.setdefault("hotels", {})
    old = json.loads(json.dumps(hotels))
    known = set(pr.get("hotel_set", []))
    fetched = pr.setdefault("fetched", {})            # 日付ごとに、最後に取った日
    for k in [k for k in fetched if k < WINDOW_START.isoformat()]: fetched.pop(k)
    new = [n for n in nos if n not in known]          # 新しく足した宿は、全日付を取る
    upto = pr.setdefault("new_upto", {})              # 新しい宿を、どの日付まで取り終えたか（時間切れで途中になったとき用）
    start = max(today, WINDOW_START); end = WINDOW_END
    if lim > 0: end = min(end, start + datetime.timedelta(days=lim - 1))
    # 期間より前の古い料金は消す（ファイルを小さく保つ）
    for v in hotels.values():
        for k in [k for k in v if k < WINDOW_START.isoformat()]: v.pop(k)
    print(f"[{area}] {len(nos)}軒（新規 {len(new)}軒）／ {start}〜{end}", flush=True)
    d = start; calls_days = 0; fails = 0; tried = 0; t1 = time.time(); c1 = STAT["calls"]; cut = False
    while d <= end:
        if out_of_time():
            cut = True; print(f"[{area}] 時間切れのため {d} 以降は次回に回します（取れた分は保存）", flush=True); break
        ds = d.isoformat()
        targets = nos if (force or lim > 0 or ds not in fetched or due(d, today)) else [n for n in new if upto.get(str(n), "") < ds]
        if targets:
            got = fetch_date(targets, d); tried += 1
            if len(got) < len(targets): fails += 1
            for no, v in got.items():
                hotels.setdefault(str(no), {})
                if v: hotels[str(no)][d.isoformat()] = v
                else: hotels[str(no)].pop(d.isoformat(), None)
            calls_days += 1
            if targets is nos and len(got) == len(targets): fetched[ds] = today.isoformat()
            for no in got:
                if no in new: upto[str(no)] = ds
        d += datetime.timedelta(days=1)
    rng = lambda h: sum(1 for x in h.values() for k in x if start.isoformat() <= k <= end.isoformat())
    prev_n, new_n = rng(old), rng(hotels)
    sec = time.time() - t1; calls = STAT["calls"] - c1
    print(f"[{area}] 取得した日 {calls_days}／料金のある宿×日 前回 {prev_n} → 今回 {new_n}／失敗した日 {fails}"
          f"／API {calls}回・{sec/60:.1f}分（1回あたり{sec/max(1,calls):.2f}秒）", flush=True)
    if prev_n and new_n < prev_n * 0.5 and not cut:
        print(f"[{area}] 取れた料金が前回の半分未満です。APIの異常の可能性があるため、このエリアは保存しません。"); return False
    if tried and fails > tried * 0.1:
        print(f"[{area}] 取得できなかった日が多すぎます（{fails}/{tried}）。このエリアは保存しません。"); return False
    pr["asof"] = f"{today.year}年{today.month}月{today.day}日"; pr["asof_date"] = today.isoformat()
    if lim == 0 and not cut: pr["hotel_set"] = sorted(set(nos)); pr.pop("new_upto", None)
    pr["source"] = "楽天トラベル 空室検索API（VacantHotelSearch）"
    pr["condition"] = "大人2名・1室・1泊2食付きプランの最安値（2名合計・税込）"
    os.makedirs(PRICE_DIR, exist_ok=True)
    json.dump(pr, open(f, "w"), ensure_ascii=False, separators=(",", ":"))
    return True


def main():
    if not APP_ID or not ACCESS_KEY:
        raise SystemExit("RAKUTEN_APP_ID / RAKUTEN_ACCESS_KEY が設定されていません")
    today = datetime.datetime.now(JST).date()
    lim = int(os.environ.get("YB_DAYS", "0") or 0)    # お試し用：先頭から何日分だけ取るか（0＝全部）
    force = os.environ.get("YB_FULL") == "1"
    by = hotels_by_area()
    want = [a for a in (os.environ.get("YB_AREAS") or ",".join(by)).split(",") if a in by]
    ok = [a for a in want if not out_of_time() and run_area(a, by[a], today, lim, force)]
    print(f"保存したエリア：{','.join(ok) or 'なし'}（対象 {len(want)}）")
    if want and not ok:
        raise SystemExit("どのエリアも保存できませんでした。公開を止めます。")


if __name__ == "__main__":
    main()
