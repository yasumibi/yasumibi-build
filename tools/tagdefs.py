"""タグ（露天風呂付き客室など）の判定だけを集めたもの。build_tags・build_rank・build_search から使う。

判定は楽天トラベルの施設情報（設備の一覧・宿の紹介文）と、口コミの点数・料金だけで行う。
1件の口コミの文章は使わない（その人の感想で、宿の設備とは限らないため）。
"""
import os, sys, json, re, statistics, datetime as dt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import is_b, is_hc, DATA, HOTELS, PRH, WINDOW_START, WINDOW_END, TODAY

INFO = json.load(open(f"{DATA}/hotel_info_20261021.json"))["hotels"]
H = {h["no"]: h for h in HOTELS if str(h["no"]) in INFO}

DET = {}
for ln in open(f"{DATA}/hotel_detail_20261021.tsv", encoding="utf-8"):
    c = ln.rstrip("\n").split("\t")
    if len(c) >= 10: DET[int(c[0])] = c


def nights(no):
    src = PRH.get(str(no), {})
    out = []
    for k, p in src.items():
        if not p or not (WINDOW_START.isoformat() <= k <= WINDOW_END.isoformat()): continue
        d = dt.date.fromisoformat(k)
        if d > TODAY: out.append((d, int(p)))
    return out




# ---- 判定
def text(no):
    c = DET.get(no)
    return (c[7] + " " + c[9]) if c else ""          # 宿の紹介文 + 設備（口コミ1件の文章は使わない）


def fac(no):
    c = DET.get(no)
    return c[9] if c else ""


def meal(no):
    try: return float(DET[no][3].split(",")[5])
    except Exception: return 0.0


SEA = ("オーシャンビュー", "海一望", "海を一望", "海が見え", "海を望", "相模湾", "海を見渡", "全室オーシャン", "海側", "海の見える")
MED = {no: statistics.median([p for _, p in nights(no)]) for no in H if len(nights(no)) >= 10}

# q：検索する人の言い方（タグページの title・h1・説明文に使う。「熱海で犬と泊まれる宿」のように「◯◯で」に続けて自然な形）
TAGS = [
    dict(slug="hc", name="ハイクラス", q="高級旅館・ハイクラスの宿", h1="ハイクラスの宿が、手の届く日。", both=True,
         rule="この先半年の料金の中央値が、食事付きの宿は2名1泊2食9万円以上、朝食付きの宿は2名1泊朝食6万円以上の宿だけ（宿ページの「ハイクラス」と同じ決まり）。神日にいつもよりどれだけ下がるかの大きい順です。",
         f=lambda no: is_hc(no, H[no]["area"]), sort="drop"),
    dict(slug="rotenburo", name="露天風呂付き客室", q="露天風呂付き客室のある宿", h1="露天風呂付き客室のある宿の、神日。",
         rule="宿の紹介文や設備に「露天風呂付き客室」と書かれている宿だけ。すべての部屋に付いているとは限りません。プランを選ぶときに、客室のタイプを確かめてください。",
         f=lambda no: re.search(r"露天風呂付|露天付|客室露天|部屋付.{0,3}露天|専用露天", text(no))),
    dict(slug="kashikiri", name="貸切風呂", q="貸切風呂のある宿", h1="貸切風呂のある宿の、神日。",
         rule="宿の紹介文や設備に「貸切風呂」「家族風呂」などと書かれている宿だけ。有料・予約制の宿もあります。",
         f=lambda no: re.search(r"貸切|貸し切り|家族風呂|プライベート風呂", text(no))),
    dict(slug="heyashoku", name="部屋食", q="部屋食の宿", h1="部屋食ができる宿の、神日。",
         rule="宿の紹介文に「部屋食」「お部屋で夕食」などと書かれている宿だけ。部屋食になるのは一部のプランだけ、という宿もあります。",
         f=lambda no: re.search(r"部屋食|お部屋で.{0,6}(夕食|食事)|お部屋食", text(no))),
    dict(slug="umi", name="海が見える", q="海が見える宿", h1="海が見える宿の、神日。",
         rule="宿の紹介文や設備に「オーシャンビュー」「相模湾一望」などの言葉がある宿だけ。海が見えない部屋がある宿もあります。",
         f=lambda no: any(k in text(no) for k in SEA)),
    dict(slug="pet", name="ペットと泊まれる", q="犬と泊まれる宿", h1="ペットと泊まれる宿の、神日。",
         rule="楽天トラベルの設備に「ペット同宿可」がある宿だけ。泊まれる動物の種類・大きさや、ペット可の部屋の数は宿ごとに違います。",
         f=lambda no: "ペット同宿可" in fac(no)),
    dict(slug="gohan", name="ごはんが評判", q="ごはんがおいしいと評判の宿", h1="ごはんが評判の宿の、神日。",
         rule="楽天トラベルの口コミで「食事」の評価が4.7以上の宿だけ。",
         f=lambda no: meal(no) >= 4.7, sub=lambda no: f"食事の評価 ★{meal(no):.2f}"),
    dict(slug="1man", name="1人1万円台", q="1人1万円台で泊まれる宿", h1="1人1万円台で泊まれる宿の、神日。",
         rule="2名1泊2食付きで4万円未満（1人2万円未満）になる日がある宿だけ。",
         f=lambda no: any(p < 40000 for _, p in nights(no)), per=True),
]


def tags_of(no, area=None):
    """その宿があてはまるタグ（slug）の一覧。エリアのページと同じ決まり：朝食付きのエリアの宿には、料金の基準があるタグ（1人1万円台）は付けない。ハイクラスは食事付き・朝食付きそれぞれの基準で付ける。"""
    out = []
    for t in TAGS:
        if is_b(H[no]["area"]) and not t.get("both") and (t.get("sort") == "drop" or t.get("per")): continue
        if not nights(no): continue
        if t["f"](no): out.append(t["slug"])
    return out
