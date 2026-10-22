"""宿ごとのシェア画像（OGP 1200×630）を作る。まだ無い宿だけ（料金は入れない＝毎日作り直さない）。
楽天の写真は使わない（直リンクでしか使えないため）。宿名・エリア・★・ロゴだけの文字の画像。
"""
import os, sys, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, HOTELS, AREA_JA
from PIL import Image, ImageDraw, ImageFont


def font(kind, size):
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
    W, H_ = 1200, 630
    im = Image.new("RGB", (W, H_), "#f6f1e6"); d = ImageDraw.Draw(im)
    d.rectangle([40, 40, W - 40, H_ - 40], outline="#e3d8c2", width=2)
    sans = font("sans", 30); small = font("sans", 26)
    d.text((96, 92), f"{AREA_JA.get(h['area'], '')}・{h.get('loc', '')}", font=sans, fill="#6b6f6c")
    name = h["name"]
    for size in (88, 76, 64, 54):
        ft = font("serif", size); ls = wrap(d, name, ft, W - 192)
        if len(ls) <= 2: break
    y = 150
    for ln in ls[:2]: d.text((96, y), ln, font=ft, fill="#15171c"); y += int(size * 1.3)
    d.text((96, y + 18), f"★ {h.get('avg', 0):.2f}　口コミ {h.get('cnt', 0):,}件", font=sans, fill="#a8772a")
    d.text((96, H_ - 128), "この宿がいちばん安い日（神日）がわかる", font=small, fill="#3d413e")
    if logo:
        lw = 330; lh = int(logo.height * lw / logo.width)
        im.paste(logo.resize((lw, lh), Image.LANCZOS), (W - 96 - lw, H_ - 96 - lh), logo.resize((lw, lh), Image.LANCZOS))
    im.save(path, "JPEG", quality=84, optimize=True, progressive=True)


def main():
    if not font("serif", 20) or not font("sans", 20):
        print("日本語のフォントがないため、シェア画像は作りません"); return
    os.makedirs(f"{OUT}/assets/og", exist_ok=True)
    logo = Image.open(f"{OUT}/assets/img/logo.png").convert("RGBA")
    n = 0
    for h in HOTELS:
        p = f"{OUT}/assets/og/{h['slug']}.jpg"
        if os.path.exists(p) and os.environ.get("YB_OG_ALL") != "1": continue
        make(h, logo, p); n += 1
    print("og images", n)


if __name__ == "__main__":
    main()
