"""タグ×エリアのページ（/tags/<タグ>/<エリア>/）が、どのエリア・どの宿にあるか。
build_tags.py の rows_for と同じ決まり（エリアに2軒以上で、ページを作る）。エリアのページ・宿のページからリンクを張るのに使う。"""
from tagdefs import TAGS, H, nights
from common import is_b

MIN_N = 2   # build_tags.py と同じ：エリアに2軒以上あるタグだけ、ページを作る


def _in(t, no, area):
    if H[no]["area"] != area: return False
    if is_b(area) and not t.get("both") and (t.get("sort") == "drop" or t.get("per")): return False
    return bool(nights(no)) and bool(t["f"](no))


_CACHE = {}
def pages_for_area(area):
    """そのエリアのタグ×エリアのページ：[(slug, name, q, 軒数)]"""
    if area not in _CACHE:
        nos = [no for no in H if H[no]["area"] == area]
        out = []
        for t in TAGS:
            n = sum(1 for no in nos if _in(t, no, area))
            if n >= MIN_N: out.append((t["slug"], t["name"], t["q"], n))
        _CACHE[area] = out
    return _CACHE[area]


def pages_for_hotel(no):
    """その宿が入っている、そのエリアのタグ×エリアのページ：[(slug, name, q, 軒数)]"""
    if no not in H: return []
    area = H[no]["area"]
    ok = {s for s, *_ in pages_for_area(area)}
    return [(t["slug"], t["name"], t["q"], n) for t in TAGS for s, _, _, n in pages_for_area(area) if s == t["slug"] and s in ok and _in(t, no, area)]
