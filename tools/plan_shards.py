"""毎日の取得を、エリアごとのまとまり（1回6時間以内）に分ける。GitHub Actions の matrix に渡す。"""
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import DATA

LIMIT = int(os.environ.get("YB_SHARD_HOTELS", "600"))   # 1回の実行で扱う宿の数の目安
cnt = {}
for h in json.load(open(f"{DATA}/hotels.json")):
    cnt[h["area"]] = cnt.get(h["area"], 0) + 1
order = [a["key"] for a in json.load(open(f"{DATA}/areas.json")) if a["key"] in cnt]
shards, cur, n = [], [], 0
for a in order:
    if cur and n + cnt[a] > LIMIT:
        shards.append(",".join(cur)); cur, n = [], 0
    cur.append(a); n += cnt[a]
if cur: shards.append(",".join(cur))
out = json.dumps(shards)
print(out)
if os.environ.get("GITHUB_OUTPUT"):
    open(os.environ["GITHUB_OUTPUT"], "a").write(f"shards={out}\n")
