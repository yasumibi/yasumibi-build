"""全ページに構造化データ（JSON-LD）を入れる。サイトを作ったあと、add_analytics.py の前に動かす。

・BreadcrumbList：ページのパンくず（nav.crumb）から作る。検索結果に「ホーム › 熱海 › 宿名」のように出やすくなる
・ItemList     ：宿の一覧（ol.rl の宿名リンク）があるページだけ。上位50軒まで
・見た目は変わらない。何度動かしても同じ結果（前に入れたものは入れ替える）
・宿の★（楽天の口コミ）は入れない（Googleの決まりで、よそのサイトの評価は構造化データに使えないため）
"""
import html, json, os, re, sys
from urllib.parse import urljoin

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.environ.get("YB_OUT") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "yasumibi-site")
SITE = "https://yasumibi.com/"
MARK_S, MARK_E = "<!--yb-jsonld-->", "<!--/yb-jsonld-->"
OLD = re.compile(re.escape(MARK_S) + r".*?" + re.escape(MARK_E) + r"\n?", re.S)
TAG = re.compile(r"<[^>]+>")


def text(s):
    return html.unescape(TAG.sub("", s)).strip()


def crumbs(page, url):
    m = re.search(r'<nav class="crumb"[^>]*>(.*?)</nav>', page, re.S)
    if not m: return None
    items = []
    for a in re.finditer(r'<a [^>]*href="([^"]*)"[^>]*>(.*?)</a>|<(?:b|span)(?: [^>]*)?>([^<]+)</(?:b|span)>', m.group(1), re.S):
        if a.group(1) is not None:
            items.append((text(a.group(2)), urljoin(url, html.unescape(a.group(1)))))
        else:
            t = text(a.group(3))
            if t and t not in ("›", ">"): items.append((t, url))
    items = [(n, u.split("#")[0]) for n, u in items if n]
    seen, uniq = set(), []
    for n, u in items:   # 同じURLが2回出るとき（例：「エリア」がトップへのリンク）は、あとのほうを外す
        if u in seen: continue
        seen.add(u); uniq.append((n, u))
    items = uniq
    if len(items) < 2: return None
    return {"@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(items)]}


def itemlist(page, url):
    m = re.search(r'<ol class="rl[^"]*">(.*?)</ol>', page, re.S)
    if not m: return None
    seen, items = set(), []
    for a in re.finditer(r'<a class="rn" href="([^"]*hotels/[^"]+)">(.*?)</a>', m.group(1), re.S):
        u = urljoin(url, html.unescape(a.group(1)))
        if u in seen: continue
        seen.add(u); items.append((text(a.group(2)), u))
        if len(items) >= 50: break
    if len(items) < 2: return None
    return {"@context": "https://schema.org", "@type": "ItemList", "numberOfItems": len(items),
            "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "url": u} for i, (n, u) in enumerate(items)]}


def main():
    n = nb = ni = 0
    for root, dirs, files in os.walk(OUT):
        dirs[:] = [d for d in dirs if d not in (".git", "assets")]
        for f in files:
            if f != "index.html": continue
            p = os.path.join(root, f)
            rel = os.path.relpath(root, OUT).replace(os.sep, "/")
            url = SITE if rel == "." else SITE + rel + "/"
            s = open(p, encoding="utf-8").read()
            if 'name="robots" content="noindex' in s: continue
            s0 = OLD.sub("", s)
            blocks = [b for b in (crumbs(s0, url), itemlist(s0, url)) if b]
            if not blocks:
                if s0 != s: open(p, "w", encoding="utf-8").write(s0)
                continue
            nb += any(b["@type"] == "BreadcrumbList" for b in blocks); ni += any(b["@type"] == "ItemList" for b in blocks)
            js = "".join('<script type="application/ld+json">' + json.dumps(b, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + "</script>"
                         for b in blocks)   # 文字の中の </script> で切れないように、JSONの中だけ </ を逃がす
            s1 = s0.replace("</head>", f"{MARK_S}{js}{MARK_E}\n</head>", 1)
            if s1 != s: open(p, "w", encoding="utf-8").write(s1)
            n += 1
    print(f"構造化データ：{n}ページ（パンくず {nb}・宿の一覧 {ni}）")


if __name__ == "__main__":
    main()
