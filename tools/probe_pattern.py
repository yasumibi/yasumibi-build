"""料金の取り方の比較テスト（searchPattern=1：プランごと／0：宿ごと）。
同じ宿・同じ日で、APIの回数と「2食付きの最安」が一致するかを確かめる。結果はログに出すだけ（データは保存しない）。
"""
import os, sys, json, time, datetime, random
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch_prices as fp
from common import DATA

H = json.load(open(f"{DATA}/hotels.json"))
random.seed(1)
areas = (os.environ.get("YB_AREAS") or "hakone,yufuin,beppu").split(",")
today = datetime.date.today()
dates = [today + datetime.timedelta(days=k) for k in (20, 45, 75, 110)]


def run(nos, d, pattern):
    nd = d + datetime.timedelta(days=1); best = {}; page = 1; calls = 0
    while True:
        r = fp.call(dict(hotelNo=",".join(map(str, nos)), checkinDate=d.isoformat(), checkoutDate=nd.isoformat(),
                         adultNum=2, roomNum=1, searchPattern=pattern, hits=30, page=page, sort="+roomCharge"))
        calls += 1; time.sleep(fp.WAIT)
        if r is None: return None, calls
        for no, v in fp.cheapest_two_meal(r).items():
            if no not in best or v < best[no]: best[no] = v
        pc = (r.get("pagingInfo") or {}).get("pageCount", 1)
        if page >= pc: break
        page += 1
    return best, calls


tot = {0: 0, 1: 0}; same = diff = only1 = only0 = 0; samples = []
for a in areas:
    nos = [h["no"] for h in H if h["area"] == a]
    random.shuffle(nos); grp = nos[:15]
    for d in dates:
        b1, c1 = run(grp, d, 1); b0, c0 = run(grp, d, 0)
        if b1 is None or b0 is None: print("error", a, d); continue
        tot[1] += c1; tot[0] += c0
        for no in grp:
            v1, v0 = b1.get(no), b0.get(no)
            if v1 and v0:
                if v1 == v0: same += 1
                else: diff += 1; samples.append((a, str(d), no, v1, v0))
            elif v1: only1 += 1
            elif v0: only0 += 1
        m=f"{a} {d} calls p1={c1} p0={c0} found p1={len(b1)} p0={len(b0)}"; print(m, flush=True); pass
msg=f"TOTAL calls p1={tot[1]} p0={tot[0]} / same={same} diff={diff} only_p1={only1} only_p0={only0}"
print(msg); print("::warning title=TOTAL::"+msg)
for x in samples[:20]: print("diff", x); print("::notice title=diff::"+str(x))
