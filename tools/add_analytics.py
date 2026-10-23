"""全ページに アクセス解析（GA4）の読み込みを1行入れる。サイトを作ったあと、最後に動かす。

・どのページの作り方（build_*.py）から作られたページにも、ここ1か所で入る（入れ忘れを防ぐ）
・すでに入っていれば、版（?v=）だけ新しくする。何度動かしても同じ結果
・計測の中身は assets/ga.js（Googleのスクリプトは読み込みが終わってから読む）
"""
import hashlib, os, re, sys

GA_ID = "G-4YGG9LQXLM"   # 測定ID（ページに出る公開の値。秘密ではない）

OUT = os.environ.get("YB_OUT") or os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "yasumibi-site")
js = os.path.join(OUT, "assets", "ga.js")
if not os.path.exists(js):
    sys.exit("assets/ga.js がありません")
v = hashlib.md5(open(js, "rb").read()).hexdigest()[:8]
TAG = f'<script defer src="/assets/ga.js?v={v}" data-id="{GA_ID}"></script>'
OLD = re.compile(r'<script defer src="/assets/ga\.js\?v=[0-9a-f]+" data-id="[^"]*"></script>')

n_add = n_upd = n_same = 0
for root, dirs, files in os.walk(OUT):
    dirs[:] = [d for d in dirs if d not in (".git", "assets")]
    for f in files:
        if not f.endswith(".html"):
            continue
        p = os.path.join(root, f)
        s = open(p, encoding="utf-8").read()
        if TAG in s:
            n_same += 1
            continue
        if OLD.search(s):
            s = OLD.sub(TAG, s); n_upd += 1
        elif "</head>" in s:
            s = s.replace("</head>", TAG + "\n</head>", 1); n_add += 1
        else:
            continue
        open(p, "w", encoding="utf-8").write(s)
print(f"アクセス解析：追加 {n_add}・更新 {n_upd}・そのまま {n_same} ページ")
