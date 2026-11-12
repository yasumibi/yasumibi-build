"""assets/img の写真（.jpg）から、一覧のタイル用に軽い WebP を作る（480px と 640px 幅。タイルは画面で最大272px・2〜3倍の画面でも足りる幅）。2026/11/12

・元の JPG はそのまま残す（エリアページの大きな写真などで使う）
・画質を落とさないよう、WebP は quality 84・method 6（いちばんていねいな圧縮）。色・明るさは変えない
・すでにあって、元の JPG より新しいものは作り直さない
使い方: python3 tools/make_webp.py <サイトのフォルダ>
"""
import os, sys, glob
from PIL import Image

SIZES = (480, 640)
QUALITY = 84


def make(src):
    stem = src[:-4]; im = None; made = 0
    for w in SIZES:
        dst = f"{stem}-{w}.webp"
        if os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src): continue
        if im is None:
            im = Image.open(src); im.load()
            icc = im.info.get("icc_profile"); im = im.convert("RGB")
        r = im if im.width <= w else im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
        r.save(dst, "WEBP", quality=QUALITY, method=6, **({"icc_profile": icc} if icc else {}))
        made += 1
    return made


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("YB_OUT", "../yasumibi-site")
    n = sum(make(f) for f in sorted(glob.glob(f"{root}/assets/img/*.jpg")) if not f.endswith(("-hero.jpg",)))
    print("webp made", n)
