"""週1回のアクセス集計：GA4 と Cloudflare Web Analytics から、先週（月〜日・日本時間）の数字を取り出して保存する。

保存先：data/analytics/<年>-W<週>.json（非公開の yasumibi-data。公開リポジトリには置かない）
鍵：GitHub Secrets だけ（GA4_SA_KEY・CF_API_TOKEN・CF_ACCOUNT_ID）。ファイルやログに鍵を出さない。
片方が失敗しても、もう片方は保存する。失敗の理由はファイルの "errors" に残す（鍵の中身は残さない）。

使い方：python3 tools/fetch_analytics.py            … 先週分
        python3 tools/fetch_analytics.py 2026-10-19 … その日を含む週（月曜はじまり）
"""
import datetime as dt, json, os, sys, urllib.request, urllib.error

GA4_PROPERTY = os.environ.get("GA4_PROPERTY_ID") or "560462271"   # GA4のプロパティID（数字。秘密ではない）
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.environ.get("YB_DATA", os.path.join(ROOT, "data"))
JST = dt.timezone(dt.timedelta(hours=9))
CF_SITE_TAG = os.environ.get("CF_SITE_TAG") or "0a93914d9d3d4e50838308c6548442f3"   # Cloudflare Web Analytics のサイト（yasumibi-site.pages.dev +2。秘密ではない）
EVENTS = ["rakuten_travel", "rakuten_card", "other_card", "favorite_add", "search"]

# ---- 対象の週
if len(sys.argv) > 1:
    d = dt.date.fromisoformat(sys.argv[1]); start = d - dt.timedelta(days=d.weekday())
else:
    today = dt.datetime.now(JST).date(); start = today - dt.timedelta(days=today.weekday() + 7)
end = start + dt.timedelta(days=6)
iso = start.isocalendar()
OUTF = os.path.join(DATA, "analytics", f"{iso[0]}-W{iso[1]:02d}.json")
out = {"week": f"{iso[0]}-W{iso[1]:02d}", "from": start.isoformat(), "to": end.isoformat(),
       "fetched_at": dt.datetime.now(JST).isoformat(timespec="minutes"), "ga4": {}, "cloudflare": {}, "errors": []}

def err(where, e):
    msg = str(e)
    for k in ("GA4_SA_KEY", "CF_API_TOKEN"):        # 念のため、鍵の文字列がまざらないように
        v = os.environ.get(k)
        if v: msg = msg.replace(v, "***")
    out["errors"].append({"where": where, "error": msg[:800]})
    print(f"[失敗] {where}: {msg[:300]}")

# ================= GA4 =================
def ga4():
    key = os.environ.get("GA4_SA_KEY")
    if not key or not GA4_PROPERTY:
        raise RuntimeError("GA4_SA_KEY または GA4_PROPERTY_ID がありません")
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    cred = service_account.Credentials.from_service_account_info(json.loads(key), scopes=["https://www.googleapis.com/auth/analytics.readonly"])
    s = AuthorizedSession(cred)
    url = f"https://analyticsdata.googleapis.com/v1beta/properties/{GA4_PROPERTY}:runReport"
    rng = [{"startDate": start.isoformat(), "endDate": end.isoformat()}]

    def run(dims, mets, limit=50, order=None, flt=None):
        body = {"dateRanges": rng, "dimensions": [{"name": x} for x in dims], "metrics": [{"name": x} for x in mets], "limit": limit}
        if order: body["orderBys"] = [{"metric": {"metricName": order}, "desc": True}]
        if flt: body["dimensionFilter"] = flt
        r = s.post(url, json=body, timeout=60)
        if r.status_code != 200: raise RuntimeError(f"{r.status_code} {r.text[:500]}")
        j = r.json()
        return [dict(zip(dims + mets, [v["value"] for v in row.get("dimensionValues", [])] + [_num(v["value"]) for v in row["metricValues"]]))
                for row in j.get("rows", [])]

    g = out["ga4"]
    tot = run([], ["screenPageViews", "sessions", "totalUsers", "newUsers", "engagedSessions", "averageSessionDuration"])
    g["totals"] = tot[0] if tot else {}
    g["daily"] = sorted(run(["date"], ["screenPageViews", "sessions"], 10), key=lambda r: r["date"])
    g["channels"] = run(["sessionDefaultChannelGroup"], ["sessions"], 20, "sessions")
    g["sources"] = run(["sessionSource", "sessionMedium"], ["sessions"], 30, "sessions")
    g["pages"] = run(["pagePath"], ["screenPageViews", "sessions"], 40, "screenPageViews")
    g["devices"] = run(["deviceCategory"], ["sessions", "screenPageViews"], 10, "sessions")
    ev_f = {"filter": {"fieldName": "eventName", "inListFilter": {"values": EVENTS}}}
    g["events"] = run(["eventName"], ["eventCount"], 20, "eventCount", ev_f)
    # どのページ・どの場所から：カスタムディメンション（GA4で登録したもの）。未登録なら、ここだけ飛ばす
    try:
        g["events_by_place"] = run(["eventName", "customEvent:page_type", "customEvent:place"], ["eventCount"], 200, "eventCount", ev_f)
    except Exception as e:
        err("ga4.events_by_place（カスタムディメンション未登録の可能性）", e)
    try:
        g["travel_by_hotel"] = run(["customEvent:hotel_no"], ["eventCount"], 30, "eventCount",
                                   {"filter": {"fieldName": "eventName", "stringFilter": {"value": "rakuten_travel"}}})
    except Exception as e:
        err("ga4.travel_by_hotel", e)

def _num(v):
    try: return int(v)
    except ValueError:
        try: return round(float(v), 2)
        except ValueError: return v

# ================= Cloudflare =================
def cf_query(q, var):
    tok, acc = os.environ.get("CF_API_TOKEN"), os.environ.get("CF_ACCOUNT_ID")
    if not tok or not acc: raise RuntimeError("CF_API_TOKEN または CF_ACCOUNT_ID がありません")
    var = dict(var, acc=acc)
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=json.dumps({"query": q, "variables": var}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try:
        j = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code} {e.read()[:300]!r}")
    if j.get("errors"): raise RuntimeError(json.dumps(j["errors"], ensure_ascii=False)[:800])
    return j["data"]["viewer"]["accounts"][0]

def cloudflare():
    c = out["cloudflare"]
    t0 = dt.datetime.combine(start, dt.time(0), JST).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t1 = dt.datetime.combine(end + dt.timedelta(days=1), dt.time(0), JST).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    # 1つのサイトだけ・ボットを除く（Cloudflareの画面の「ボットを除外する」と同じ）
    F = '{ AND: [{ datetime_geq: $t0, datetime_lt: $t1, siteTag: "' + CF_SITE_TAG + '", bot: 0 }] }'
    grp = lambda dim, n: f'{dim}: rumPageloadEventsAdaptiveGroups(filter: {F}, limit: {n}, orderBy: [count_DESC]) {{ count sum {{ visits }} dimensions {{ m: {dim} }} }}'
    q = ('query($acc: String!, $t0: Time!, $t1: Time!) { viewer { accounts(filter: { accountTag: $acc }) { '
         f'total: rumPageloadEventsAdaptiveGroups(filter: {F}, limit: 1) {{ count sum {{ visits }} }} '
         f'site: rumPageloadEventsAdaptiveGroups(filter: {F}, limit: 10, orderBy: [count_DESC]) {{ count dimensions {{ m: siteTag h: requestHost }} }} '
         + grp("requestPath", 40) + " " + grp("refererHost", 20) + " " + grp("deviceType", 10) + " } } }")
    a = cf_query(q, {"t0": t0, "t1": t1})
    tot = a["total"][0] if a["total"] else {"count": 0, "sum": {"visits": 0}}
    c["totals"] = {"pageviews": tot["count"], "visits": tot["sum"]["visits"]}
    c["site_tag"] = CF_SITE_TAG
    c["sites"] = [{"siteTag": r["dimensions"]["m"], "host": r["dimensions"]["h"], "pageviews": r["count"]} for r in a["site"]]
    for k in ("requestPath", "refererHost", "deviceType"):
        c[k] = [{"value": r["dimensions"]["m"], "pageviews": r["count"], "visits": r["sum"]["visits"]} for r in a[k]]
    # 表示の速さ（Core Web Vitals の75パーセンタイル）。ページ全体と、遅いページ
    try:
        Q = ("quantiles { largestContentfulPaintP75 cumulativeLayoutShiftP75 interactionToNextPaintP75 firstContentfulPaintP75 }")
        q2 = ('query($acc: String!, $t0: Time!, $t1: Time!) { viewer { accounts(filter: { accountTag: $acc }) { '
              f'all: rumWebVitalsEventsAdaptiveGroups(filter: {F}, limit: 1) {{ count {Q} }} '
              f'dev: rumWebVitalsEventsAdaptiveGroups(filter: {F}, limit: 5, orderBy: [count_DESC]) {{ count {Q} dimensions {{ deviceType }} }} '
              f'path: rumWebVitalsEventsAdaptiveGroups(filter: {F}, limit: 25, orderBy: [count_DESC]) {{ count {Q} dimensions {{ requestPath }} }} '
              '} } }')
        b = cf_query(q2, {"t0": t0, "t1": t1})
        conv = lambda r: {"samples": r["count"], **{k.replace("P75", "_p75"): v for k, v in (r.get("quantiles") or {}).items()},
                          **(r.get("dimensions") or {})}
        c["web_vitals"] = {"all": [conv(r) for r in b["all"]], "by_device": [conv(r) for r in b["dev"]], "by_path": [conv(r) for r in b["path"]]}
    except Exception as e:
        err("cloudflare.web_vitals", e)

for name, fn in (("ga4", ga4), ("cloudflare", cloudflare)):
    try: fn()
    except Exception as e: err(name, e)

os.makedirs(os.path.dirname(OUTF), exist_ok=True)
json.dump(out, open(OUTF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"保存：{os.path.relpath(OUTF, DATA)}（{out['from']}〜{out['to']}）エラー {len(out['errors'])} 件")
