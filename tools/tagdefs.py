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

# 街なかの温泉ホテル（2026/11/9）：朝食付きで比べる街のエリアの宿で、天然温泉があるもの。温泉ではない大浴場だけの宿や、外の温泉に案内している宿は入れない
_OFF = re.compile(r"温泉まで|近くの温泉|近隣の温泉|周辺の温泉|提携|利用券|割引|温泉街まで")
def machi_onsen(no):
    c = DET.get(no)
    if not c or not is_b(H[no]["area"]): return False
    f, intro = c[9], c[7]
    if "温泉" in f: return True                      # 楽天の設備の一覧を優先
    if _OFF.search(intro): return False
    return bool(re.search(r"天然温泉|温泉大浴場|源泉|温泉付", intro))


# rule：決め方。「|」で区切った短い項目（箇条書きで出す。長い文は読みにくいので 2026/11/17）
# q：検索する人の言い方（タグページの title・h1・説明文に使う。「熱海で犬と泊まれる宿」のように「◯◯で」に続けて自然な形）
TAGS = [
    dict(slug="hc", name="ハイクラス", q="高級旅館・ハイクラスの宿", h1="ハイクラスの宿が安くなる日", both=True,
         rule="ふだんの料金（この先半年）が、2食付き9万円以上・朝食付き6万円以上|宿ページの「ハイクラス」と同じ決まり|並びは、神日に安くなる額が大きい順",
         f=lambda no: is_hc(no, H[no]["area"]), sort="drop"),
    dict(slug="rotenburo", name="露天風呂付き客室", q="露天風呂付き客室のある宿", h1="露天風呂付き客室のある宿の、神日。",
         rule="紹介文や設備に「露天風呂付き客室」とある宿|全室に付いているとは限りません|予約のときに、客室のタイプを確かめてください",
         f=lambda no: re.search(r"露天風呂付|露天付|客室露天|部屋付.{0,3}露天|専用露天", text(no))),
    dict(slug="kashikiri", name="貸切風呂", q="貸切風呂のある宿", h1="貸切風呂のある宿の、神日。",
         rule="紹介文や設備に「貸切風呂」「家族風呂」などとある宿|有料・予約制の宿もあります",
         f=lambda no: re.search(r"貸切|貸し切り|家族風呂|プライベート風呂", text(no))),
    dict(slug="heyashoku", name="部屋食", q="部屋食の宿", h1="部屋食ができる宿の、神日。",
         rule="紹介文に「部屋食」「お部屋で夕食」などとある宿|部屋食は一部のプランだけ、という宿もあります",
         f=lambda no: re.search(r"部屋食|お部屋で.{0,6}(夕食|食事)|お部屋食", text(no))),
    dict(slug="umi", name="海が見える", q="海が見える宿", h1="海が見える宿の、神日。",
         rule="紹介文や設備に「オーシャンビュー」などとある宿|海が見えない部屋もあります",
         f=lambda no: any(k in text(no) for k in SEA)),
    dict(slug="pet", name="ペットと泊まれる", q="犬と泊まれる宿", h1="ペットと泊まれる宿の、神日。",
         rule="設備に「ペット同宿可」がある宿|動物の種類・大きさ、部屋の数は宿ごとに違います",
         f=lambda no: "ペット同宿可" in fac(no)),
    dict(slug="gohan", name="ごはんが評判", q="ごはんがおいしいと評判の宿", h1="ごはんが評判の宿の、神日。",
         rule="口コミの「食事」の評価が4.7以上の宿",
         f=lambda no: meal(no) >= 4.7, sub=lambda no: f"食事の評価 ★{meal(no):.2f}"),
    dict(slug="onsen", name="温泉に入れるホテル", q="温泉に入れるホテル", h1="街なかで、温泉に入れるホテルの神日。", both=True, min=3,
         rule="街のエリア（朝食付きで比べるエリア）のホテル|設備に「温泉」、または紹介文に「天然温泉」「源泉」などとある宿|温泉ではない大浴場だけの宿は入れていません",
         f=machi_onsen),
    dict(slug="1man", name="1人1万円台", q="1人1万円台で泊まれる宿", h1="1人1万円台で泊まれる宿の、神日。",
         rule="2名1泊2食で4万円未満（1人2万円未満）の日がある宿",
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
