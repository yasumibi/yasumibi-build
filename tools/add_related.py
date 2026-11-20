"""宿ページに「この宿が載っている特集」を入れる（2026/11/20 決定：案B＋A）。
・案B：安い日の表のすぐ下に1行（いちばん順位の良い特集。エリアの特集を全国の特集より先に）
・案A：「宿の特徴」の中に、載っている特集をすべて
特集のページを作り終えたあとに動かす（build_specials・build_site のあと）。宿ページの <!--xf-b--> <!--xf-a--> を置き換える。
何度動かしても同じ結果になる。"""
import os, re, html, glob
from common import OUT

esc = lambda s: html.escape(str(s), quote=True)
TAG = re.compile(r"<[^>]+>")

# 特集の名前（特集一覧のカードの題名）と、全国の特集かどうか
idx = open(f"{OUT}/features/index.html", encoding="utf-8").read() if os.path.exists(f"{OUT}/features/index.html") else ""
TITLE, NATION = {}, set()
for s, ft, fs in re.findall(r'href="\.\./features/([a-z0-9-]+)/">.*?<span class="ft">(.*?)</span><span class="fs">(.*?)</span>', idx, re.S):
    TITLE.setdefault(s, TAG.sub("", ft).strip())
    if TAG.sub("", fs).startswith("全国"): NATION.add(s)

MAP = {}   # 宿のslug → [(特集slug, 題名, 順位 or None, 全国か)]
for f in sorted(glob.glob(f"{OUT}/features/*/index.html")):
    s = f.split("/")[-2]
    h = open(f, encoding="utf-8").read()
    if 'content="noindex' in h: continue   # お休み中の特集には送らない
    t = TITLE.get(s)
    if not t:
        m = re.search(r"<h1[^>]*>(.*?)</h1>", h, re.S)
        t = TAG.sub("", m.group(1)).strip() if m else s
    seen = {}
    for li in re.findall(r'<li class="ri[^"]*"(.*?)</li>', h, re.S):   # ランキングの形の特集：順位を取る
        m = re.search(r'hotels/([a-z0-9-]+)/', li)
        if m and m.group(1) not in seen:
            rk = re.search(r'class="rk">(\d+)', li)
            seen[m.group(1)] = int(rk.group(1)) if rk else None
    for sl in re.findall(r'hotels/([a-z0-9-]+)/', h):   # それ以外（料金マップの宿の名前など）は順位なし
        seen.setdefault(sl, None)
    for sl, rk in seen.items():
        MAP.setdefault(sl, []).append((s, t, rk, s in NATION))

def key(x):   # エリアの特集 → 順位の良い順 → 順位なし
    s, t, rk, nat = x
    return (nat, rk is None, rk or 0, s)

PB = re.compile(r"<!--xf-b-->(?:.*?<!--/xf-b-->)?", re.S)
PA = re.compile(r"<!--xf-a-->(?:.*?<!--/xf-a-->)?", re.S)
n = nb = 0
for f in glob.glob(f"{OUT}/hotels/*/index.html"):
    sl = f.split("/")[-2]
    s = open(f, encoding="utf-8").read()
    if "<!--xf-b-->" not in s and "<!--xf-a-->" not in s: continue
    fs = sorted(MAP.get(sl, []), key=key)
    if fs:
        top = fs[0]
        rk = f"で{top[2]}位" if top[2] else "で紹介"
        more = f"<small>（ほか{len(fs) - 1}本の特集に掲載）</small>" if len(fs) > 1 else ""
        b = (f'<a class="xf-b" href="../../features/{top[0]}/"><span class="l">特集</span>'
             f'<span class="t"><b>{esc(top[1])}</b>{rk}{more}</span><span aria-hidden="true">›</span></a>')
        a = ('<div class="xf-a"><h3>この宿が載っている特集</h3><ul>'
             + "".join(f'<li><a href="../../features/{x[0]}/">{esc(x[1])}{f"<small>この宿は{x[2]}位</small>" if x[2] else ""}</a></li>' for x in fs)
             + "</ul></div>")
        nb += 1
    else:
        b = a = ""
    t = PB.sub(lambda m: f"<!--xf-b-->{b}<!--/xf-b-->", s, 1)
    t = PA.sub(lambda m: f"<!--xf-a-->{a}<!--/xf-a-->", t, 1)
    if t != s: open(f, "w", encoding="utf-8").write(t); n += 1
print("この宿が載っている特集", nb, "軒（書き換え", n, "ページ）")
