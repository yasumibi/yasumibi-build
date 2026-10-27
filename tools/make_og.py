"""宿ごとのシェア画像（OGP 1200×630）を作る。
楽天の写真は使わない（直リンクでしか使えないため）。地区（エリア）・宿名・ロゴだけの文字の画像。

・画像に入れるのは「変わらない文字」だけ（★や口コミ件数は毎週変わるので入れない）。
・どの文字で作ったかを assets/og/manifest.json に残し、画像が無い宿と、文字（宿名・地区名・デザインの版）が
  変わった宿だけを作り直す。デザインを変えたら OG_VERSION を上げる（全部作り直しになる）。
・python3 tools/make_og.py --need ：作り直す画像があれば 0、無ければ 1 で終わる（画像は作らない。公開の手順で使う）
"""
import os, sys, glob, json, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, HOTELS, AREA_JA, place_of

OG_VERSION = "2026-10-27"   # デザインの版
MANIFEST = f"{OUT}/assets/og/manifest.json"


def key_of(h):
    return hashlib.md5(f"{OG_VERSION}|{place_of(h)}|{h['name']}".encode()).hexdigest()[:12]


def load_manifest():
    try: return json.load(open(MANIFEST))
    except (FileNotFoundError, ValueError): return {}


def todo_list():
    man = load_manifest()
    return [h for h in HOTELS if os.environ.get("YB_OG_ALL") == "1" or man.get(h["slug"]) != key_of(h)
            or not os.path.exists(f"{OUT}/assets/og/{h['slug']}.jpg")]


def font(kind, size):
    from PIL import ImageFont
    pats = {"serif": ["/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc", "/usr/share/fonts/**/NotoSerifCJK*Bold*"],
            "sans": ["/usr/share/fonts/opentype/noto/NotoSansCJK-Medium.ttc", "/usr/share/fonts/**/NotoSansCJK*Medium*", "/usr/share/fonts/**/NotoSansCJK*Regular*"]}[kind]
    for p in pats:
        for f in glob.glob(p, recursive=True):
            for i in range(10):
                try:
                    ft = ImageFont.truetype(f, size, index=i)
                    if "JP" in " ".join(ft.getname()): return ft
                except Exception: break
    return None


def wrap(d, text, ft, width):
    """英単語は途中で切らない（日本語は1文字ずつ）。"""
    import re
    lines, cur = [], ""
    for tk in re.findall(r"[A-Za-z0-9&'.\-]+|\s+|.", text):
        if d.textlength(cur + tk, font=ft) > width and cur.strip():
            lines.append(cur.rstrip()); cur = tk.lstrip()
        else: cur += tk
    return lines + ([cur] if cur else [])


def make(h, logo, path):
    from PIL import Image, ImageDraw
    W, H_ = 1200, 630
    im = Image.new("RGB", (W, H_), "#f6f1e6"); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H_ - 40], outline="#e3d8c2", width=2)
    sans = font("sans", 30); small = font("sans", 26)
    d.text((96, 92), place_of(h), font=sans, fill="#6b6f6c")
    name = h["name"]
    for size in (88, 76, 64, 54):
        ft = font("serif", size); ls = wrap(d, name, ft, W - 192)
        if len(ls) <= 2: break
    y = 150
    for ln in ls[:2]: d.text((96, y), ln, font=ft, fill="#15171c"); y += int(size * 1.3)
    d.text((96, y + 18), "★ 口コミ4.3以上の宿だけ", font=sans, fill="#a8772a")   # 全宿に当てはまる、変わらない一文（宿ごとの★・件数は入れない）
    d.text((96, H_ - 128), "この宿がいちばん安い日（神日）がわかる", font=small, fill="#3d413e")
    if logo:
        lw = 330; lh = int(logo.height * lw / logo.width)
        im.paste(logo.resize((lw, lh), Image.LANCZOS), (W - 96 - lw, H_ - 96 - lh), logo.resize((lw, lh), Image.LANCZOS))
    im.save(path, "JPEG", quality=84, optimize=True, progressive=True)


def main():
    todo = todo_list()
    if "--need" in sys.argv:
        print(f"作り直すシェア画像：{len(todo)}枚"); sys.exit(0 if todo else 1)
    if not todo:
        print("og images 0（作り直す画像なし）"); return
    from PIL import Image
    if not font("serif", 20) or not font("sans", 20):
        print("日本語のフォントがないため、シェア画像は作りません"); return
    os.makedirs(f"{OUT}/assets/og", exist_ok=True)
    logo = Image.open(f"{OUT}/assets/img/logo.png").convert("RGBA")
    man = load_manifest()
    for h in todo:
        make(h, logo, f"{OUT}/assets/og/{h['slug']}.jpg"); man[h["slug"]] = key_of(h)
    live = {h["slug"] for h in HOTELS}
    man = {k: v for k, v in sorted(man.items()) if k in live}
    json.dump(man, open(MANIFEST, "w"), ensure_ascii=False, separators=(",", ":"))
    print("og images", len(todo))


if __name__ == "__main__":
    main()
