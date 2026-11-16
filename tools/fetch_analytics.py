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
EVENTS = ["rakuten_travel", "rakuten_card", "other_card", "favorite_add", "search", "sheet_open", "card_holder", "card_entry"]

# ---- 対象の週
if len(sys.argv) > 1:
    d = dt.date.fromisoformat(sys.argv[1]); start = d - dt.timedelta(days=d.weekday())
else:
    today = dt.datetime.now(JST).date(); start = today - dt.timedelta(days=today.weekday() + 7)
end = start + dt.timedelta(days=6)
iso = start.isocalendar()
OUTF = os.path.join(DATA, "analytics", f"{iso[0]}-W{iso[1]:02d}.json")
out = {"week": f"{iso[0]}-W{iso[1]:02d}", "from": start.isoformat(), "to": end.isoformat(),
       "fetched_at": dt.datetime.now(JST).isoformat(timespec="minutes"), "ga4": {}, "cloudflare": {}, "ai_crawlers": {}, "search_console": {}, "errors": []}

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
    # 流入元ごと：どのページに着地したか（各流入元の上位20）と、楽天・カードまで進んだか（2026/11/9 戦略部屋の依頼）
    try:
        rows = run(["sessionSource", "landingPage"], ["sessions", "engagedSessions"], 1000, "sessions")
        by = {}
        for r in rows:
            by.setdefault(r["sessionSource"], [])
            if len(by[r["sessionSource"]]) < 20: by[r["sessionSource"]].append({"landingPage": r["landingPage"], "sessions": r["sessions"], "engagedSessions": r["engagedSessions"]})
        g["landing_by_source"] = by
    except Exception as e:
        err("ga4.landing_by_source", e)
    try:
        g["events_by_source"] = run(["sessionSource", "eventName"], ["eventCount"], 300, "eventCount",
                                    {"filter": {"fieldName": "eventName", "inListFilter": {"values": ["rakuten_travel", "rakuten_card", "other_card", "sheet_open"]}}})
    except Exception as e:
        err("ga4.events_by_source", e)
    # カードの欄の見せ方ごと（2026/11/9）：rakuten_card・card_entry の view、card_holder の choice。GA4にカスタムディメンション view・choice の登録が必要
    try:
        g["card_by_view"] = run(["eventName", "customEvent:view"], ["eventCount"], 100, "eventCount",
                                {"filter": {"fieldName": "eventName", "inListFilter": {"values": ["rakuten_card", "card_entry"]}}})
    except Exception as e:
        err("ga4.card_by_view（GA4にカスタムディメンション view を登録すると取れる）", e)
    try:
        g["card_holder"] = run(["customEvent:choice", "customEvent:place"], ["eventCount"], 50, "eventCount",
                               {"filter": {"fieldName": "eventName", "stringFilter": {"value": "card_holder"}}})
    except Exception as e:
        err("ga4.card_holder（GA4にカスタムディメンション choice を登録すると取れる）", e)
    # 運営者の端末（?owner=1 → traffic_type=internal）が見分けられているか。GA4のフィルタが「テスト」の間だけ取れる
    try:
        g["internal_test"] = run(["testDataFilterName"], ["sessions", "screenPageViews"], 10, "sessions")
    except Exception as e:
        err("ga4.internal_test（フィルタが有効・無効のときは取れない）", e)
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

# ================= Cloudflare：AIクローラー（2026/11/16） =================
# ChatGPT などAI検索の動きを毎週見るため。ゾーン（yasumibi.com）の HTTP リクエスト（httpRequestsAdaptiveGroups）を、
# ユーザーエージェントでクローラーごとに分けて数える。無料プランでも31日分さかのぼれ、1回で30日分まで取れる（2026/10〜）。
# 権限：APIトークンに「ゾーン → アナリティクス → 読み取り」（yasumibi.com）。ゾーンIDは CF_ZONE_ID か、名前から探す（「ゾーン → ゾーン → 読み取り」）。
# ユーザーエージェントは名乗っているだけなので、なりすましも数に入る（Cloudflare の画面の「AIクロール制御」は検証済みのボットだけを数える）。
AI_BOTS = ["OAI-SearchBot", "ChatGPT-User", "GPTBot", "PerplexityBot", "Perplexity-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
           "bingbot", "Googlebot", "Applebot", "Amazonbot", "Bytespider", "meta-externalagent", "meta-externalfetcher",
           "CCBot", "DuckAssistBot", "MistralAI-User", "cohere-ai", "YouBot", "Google-CloudVertexBot", "PetalBot", "TikTokSpider"]
CF_ZONE_NAME = os.environ.get("CF_ZONE_NAME") or "yasumibi.com"


def cf_zone_tag():
    z = os.environ.get("CF_ZONE_ID")
    if z: return z
    req = urllib.request.Request(f"https://api.cloudflare.com/client/v4/zones?name={CF_ZONE_NAME}",
                                 headers={"Authorization": f"Bearer {os.environ.get('CF_API_TOKEN', '')}"})
    try: j = json.load(urllib.request.urlopen(req, timeout=60))
    except urllib.error.HTTPError as e: raise RuntimeError(f"ゾーンIDを探せない：HTTP {e.code} {e.read()[:200]!r}")
    if not j.get("result"): raise RuntimeError("ゾーンIDを探せない（トークンに「ゾーン → ゾーン → 読み取り」が無いか、CF_ZONE_ID を入れる）")
    return j["result"][0]["id"]


def cf_zone_query(q, var):
    tok = os.environ.get("CF_API_TOKEN")
    if not tok: raise RuntimeError("CF_API_TOKEN がありません")
    req = urllib.request.Request("https://api.cloudflare.com/client/v4/graphql", data=json.dumps({"query": q, "variables": var}).encode(),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    try: j = json.load(urllib.request.urlopen(req, timeout=90))
    except urllib.error.HTTPError as e: raise RuntimeError(f"HTTP {e.code} {e.read()[:300]!r}")
    if j.get("errors"): raise RuntimeError(json.dumps(j["errors"], ensure_ascii=False)[:800])
    return j["data"]["viewer"]["zones"][0]


def _bot_of(ua):
    u = (ua or "").lower()
    for b in AI_BOTS:
        if b.lower() in u: return b
    return None


def ai_crawlers(t_from=None, t_to=None):
    """先週7日分（月〜日・日本時間）。t_from/t_to を渡すと、その期間（確かめ用）。"""
    t0 = t_from or dt.datetime.combine(start, dt.time(0), JST)
    t1 = t_to or dt.datetime.combine(end + dt.timedelta(days=1), dt.time(0), JST)
    z = cf_zone_tag()
    utc = lambda t: t.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    base = f'{{ datetime_geq: "{utc(t0)}", datetime_lt: "{utc(t1)}", requestSource: "eyeball" }}'
    parts = []
    for i, b in enumerate(AI_BOTS):   # クローラーごと：1時間ごと×ステータス
        parts.append(f'b{i}: httpRequestsAdaptiveGroups(filter: {{ AND: [{base}, {{ userAgent_like: "%{b}%" }}] }}, limit: 5000) '
                     '{ count dimensions { datetimeHour edgeResponseStatus } }')
    q = "query($z: String!) { viewer { zones(filter: { zoneTag: $z }) { " + " ".join(parts) + " } } }"
    a = cf_zone_query(q, {"z": z})
    res = {"from": t0.isoformat(timespec="minutes"), "to": t1.isoformat(timespec="minutes"), "source": "httpRequestsAdaptiveGroups（userAgent で判定）",
           "bots": {}, "daily": {}}
    for i, b in enumerate(AI_BOTS):
        rows = a[f"b{i}"]
        if not rows: continue
        st = {"2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}; day = {}
        for r in rows:
            c = r["count"]; s = r["dimensions"]["edgeResponseStatus"]; k = f"{s // 100}xx"
            if k in st: st[k] += c
            dd = dt.datetime.fromisoformat(r["dimensions"]["datetimeHour"].replace("Z", "+00:00")).astimezone(JST).date().isoformat()
            day[dd] = day.get(dd, 0) + c
        name = {"bingbot": "BingBot", "meta-externalagent": "Meta-ExternalAgent", "meta-externalfetcher": "Meta-ExternalFetcher"}.get(b, b)
        res["bots"][name] = {"total": sum(st.values()), "ok_2xx": st["2xx"], "not_ok": st["3xx"] + st["4xx"] + st["5xx"],
                             "3xx": st["3xx"], "4xx": st["4xx"], "5xx": st["5xx"]}
        res["daily"][name] = dict(sorted(day.items()))
    res["bots"] = dict(sorted(res["bots"].items(), key=lambda x: -x[1]["total"]))
    # ChatGPT のよく読んだページ／4xx のページ／一覧にない「bot」らしいユーザーエージェント
    or_ai = "{ OR: [" + ", ".join(f'{{ userAgent_like: "%{b}%" }}' for b in AI_BOTS) + "] }"
    q2 = ("query($z: String!) { viewer { zones(filter: { zoneTag: $z }) { "
          f'oai: httpRequestsAdaptiveGroups(filter: {{ AND: [{base}, {{ userAgent_like: "%OAI-SearchBot%" }}] }}, limit: 20, orderBy: [count_DESC]) {{ count dimensions {{ clientRequestPath }} }} '
          f'cgu: httpRequestsAdaptiveGroups(filter: {{ AND: [{base}, {{ userAgent_like: "%ChatGPT-User%" }}] }}, limit: 20, orderBy: [count_DESC]) {{ count dimensions {{ clientRequestPath }} }} '
          f'e4: httpRequestsAdaptiveGroups(filter: {{ AND: [{base}, {or_ai}, {{ edgeResponseStatus_geq: 400, edgeResponseStatus_lt: 500 }}] }}, limit: 200, orderBy: [count_DESC]) {{ count dimensions {{ clientRequestPath userAgent edgeResponseStatus }} }} '
          f'other: httpRequestsAdaptiveGroups(filter: {{ AND: [{base}, {{ OR: [{{ userAgent_like: "%bot%" }}, {{ userAgent_like: "%Bot%" }}, {{ userAgent_like: "%crawler%" }}, {{ userAgent_like: "%spider%" }}, {{ userAgent_like: "%-User%" }}, {{ userAgent_like: "%AI%" }}] }}] }}, limit: 100, orderBy: [count_DESC]) {{ count dimensions {{ userAgent }} }} '
          "} } }")
    b2 = cf_zone_query(q2, {"z": z})
    res["top_paths"] = {"OAI-SearchBot": [{"path": r["dimensions"]["clientRequestPath"], "count": r["count"]} for r in b2["oai"]],
                        "ChatGPT-User": [{"path": r["dimensions"]["clientRequestPath"], "count": r["count"]} for r in b2["cgu"]]}
    e4 = {}
    for r in b2["e4"]:
        p = r["dimensions"]["clientRequestPath"]; bot = _bot_of(r["dimensions"]["userAgent"]) or "?"
        x = e4.setdefault(p, {"path": p, "count": 0, "bots": {}, "status": {}})
        x["count"] += r["count"]; x["bots"][bot] = x["bots"].get(bot, 0) + r["count"]
        sc = str(r["dimensions"]["edgeResponseStatus"]); x["status"][sc] = x["status"].get(sc, 0) + r["count"]
    res["paths_4xx"] = sorted(e4.values(), key=lambda x: -x["count"])[:20]
    res["other_bot_uas"] = [{"user_agent": r["dimensions"]["userAgent"][:200], "count": r["count"]} for r in b2["other"]
                            if not _bot_of(r["dimensions"]["userAgent"])][:30]
    return res


def ai_crawlers_save():
    out["ai_crawlers"] = ai_crawlers()
    if os.environ.get("YB_AI_CHECK"):   # 確かめ用：いまから過去7日間（Cloudflare の画面の「過去7日間」とくらべる）
        now = dt.datetime.now(JST)
        chk = ai_crawlers(now - dt.timedelta(days=7), now)
        out["ai_crawlers_check_last7"] = {k: v["total"] for k, v in chk["bots"].items()}

# ================= Search Console =================
# 同じサービスアカウント（GA4_SA_KEY）を、Search Console に「制限付き」以上で追加しておく。
# Search Console のデータは2〜3日遅れで確定する。月曜の集計では先週の終わり2〜3日がまだ途中なので、
# 「fresh」（途中を含む）で取って "provisional_days" に途中の日を残し、翌週の集計で先々週の分を確定値に取り直す。
SC_SITES = [os.environ.get("SC_SITE") or "sc-domain:yasumibi.com", "https://yasumibi.com/"]

def sc_session():
    key = os.environ.get("GA4_SA_KEY")
    if not key: raise RuntimeError("GA4_SA_KEY がありません")
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    cred = service_account.Credentials.from_service_account_info(json.loads(key), scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    return AuthorizedSession(cred)

def sc_fetch(s, d0, d1):
    import urllib.parse
    last = None
    for site in SC_SITES:
        url = f"https://searchconsole.googleapis.com/webmasters/v3/sites/{urllib.parse.quote(site, safe='')}/searchAnalytics/query"
        def q(dims, limit):
            body = {"startDate": d0.isoformat(), "endDate": d1.isoformat(), "dimensions": dims, "rowLimit": limit, "dataState": "all", "type": "web"}
            r = s.post(url, json=body, timeout=60)
            if r.status_code != 200: raise RuntimeError(f"{r.status_code} {r.text[:300]}")
            return [dict(zip(dims, row.get("keys", [])), clicks=row["clicks"], impressions=row["impressions"],
                         ctr=round(row["ctr"], 4), position=round(row["position"], 1)) for row in r.json().get("rows", [])]
        try:
            tot = q([], 1)
            return {"site": site, "totals": tot[0] if tot else {"clicks": 0, "impressions": 0},
                    "daily": sorted(q(["date"], 10), key=lambda r: r["date"]),
                    "queries": q(["query"], 100), "pages": q(["page"], 100), "devices": q(["device"], 5)}
        except Exception as e:
            last = e   # ドメインのプロパティで無ければ、URLのプロパティで試す
    raise last

def search_console():
    s = sc_session()
    sc = sc_fetch(s, start, end)
    today = dt.datetime.now(JST).date()
    sc["provisional_days"] = [d.isoformat() for d in (end - dt.timedelta(days=i) for i in range(7)) if (today - d).days <= 3]
    out["search_console"] = sc
    # 先々週のファイルがあれば、Search Console の分を確定値で取り直す
    p0 = start - dt.timedelta(days=7); iso0 = p0.isocalendar()
    f0 = os.path.join(DATA, "analytics", f"{iso0[0]}-W{iso0[1]:02d}.json")
    if os.path.exists(f0):
        try:
            prev = json.load(open(f0, encoding="utf-8"))
            if (prev.get("search_console") or {}).get("provisional_days") or "search_console" not in prev:
                fin = sc_fetch(s, p0, p0 + dt.timedelta(days=6)); fin["provisional_days"] = []
                prev["search_console"] = fin
                json.dump(prev, open(f0, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
                print(f"Search Console：{os.path.basename(f0)} を確定値に更新")
        except Exception as e:
            err("search_console.prev_week", e)

for name, fn in (("ga4", ga4), ("cloudflare", cloudflare), ("ai_crawlers", ai_crawlers_save), ("search_console", search_console)):
    try: fn()
    except Exception as e: err(name, e)

os.makedirs(os.path.dirname(OUTF), exist_ok=True)
json.dump(out, open(OUTF, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"保存：{os.path.relpath(OUTF, DATA)}（{out['from']}〜{out['to']}）エラー {len(out['errors'])} 件")
