"""宿ページの上の写真（楽天トラベルの写真）の縦横の大きさを調べて、data/img_sizes.json に保存する。

なぜ：写真の大きさがページに書いていないと、写真が届いた瞬間に下の情報が押し下げられる（CLS）。
      大きさを前もって書いておけば、ブラウザが場所を空けて待つので、ずれない。見た目は変わらない。
・まだ調べていない写真だけを調べる（写真のURLが変わった宿も調べ直す）。
・写真の頭の部分（最大64KB）だけを読む。画像全体はダウンロードしない。
・失敗した写真は飛ばす（ページは今までどおり表示される）。
"""
import json, os, struct, sys, urllib.request
from concurrent.futures import ThreadPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = f"{ROOT}/data"
INFO_F = f"{DATA}/hotel_info_20261021.json"
OUT_F = f"{DATA}/img_sizes.json"


def size_of(b):
    """画像の頭のバイト列から (幅, 高さ) を返す。JPEG・PNG・GIF・WebP。わからなければ None"""
    if b[:8] == b"\x89PNG\r\n\x1a\n" and len(b) >= 24:
        return struct.unpack(">II", b[16:24])
    if b[:6] in (b"GIF87a", b"GIF89a") and len(b) >= 10:
        return struct.unpack("<HH", b[6:10])
    if b[:4] == b"RIFF" and b[8:12] == b"WEBP" and len(b) >= 30:
        if b[12:16] == b"VP8X": return (int.from_bytes(b[24:27], "little") + 1, int.from_bytes(b[27:30], "little") + 1)
        if b[12:16] == b"VP8 ": return (struct.unpack("<H", b[26:28])[0] & 0x3FFF, struct.unpack("<H", b[28:30])[0] & 0x3FFF)
        if b[12:16] == b"VP8L":
            v = int.from_bytes(b[21:25], "little"); return ((v & 0x3FFF) + 1, ((v >> 14) & 0x3FFF) + 1)
    if b[:2] == b"\xff\xd8":   # JPEG：SOFマーカーを探す
        i = 2
        while i + 9 < len(b):
            if b[i] != 0xFF: i += 1; continue
            mk = b[i + 1]
            if mk in (0xD8, 0x01) or 0xD0 <= mk <= 0xD7: i += 2; continue
            ln = struct.unpack(">H", b[i + 2:i + 4])[0]
            if mk in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                h, w = struct.unpack(">HH", b[i + 5:i + 9]); return (w, h)
            i += 2 + ln
    return None


def fetch(url):
    try:
        req = urllib.request.Request(url, headers={"Range": "bytes=0-65535", "User-Agent": "yasumibi-img-size/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            wh = size_of(r.read(65536))
        if wh and wh[0] > 0 and wh[1] > 0: return url, [int(wh[0]), int(wh[1])]
    except Exception as e:
        print(f"  取得できず {url[:80]}：{type(e).__name__}", flush=True)
    return url, None


def main():
    info = json.load(open(INFO_F))["hotels"]
    try: sizes = json.load(open(OUT_F))
    except FileNotFoundError: sizes = {}
    urls = sorted({v.get("img") for v in info.values() if v.get("img")})
    todo = [u for u in urls if u not in sizes]
    print(f"写真の大きさ：全{len(urls)}枚・調べる {len(todo)}枚", flush=True)
    got = 0
    with ThreadPoolExecutor(max_workers=8) as ex:
        for url, wh in ex.map(fetch, todo):
            if wh: sizes[url] = wh; got += 1
    keep = set(urls)
    sizes = {u: wh for u, wh in sorted(sizes.items()) if u in keep}   # 使われなくなった写真は消す
    json.dump(sizes, open(OUT_F, "w"), ensure_ascii=False, separators=(",", ":"))
    print(f"写真の大きさ：{got}枚を追加（合計 {len(sizes)}枚）", flush=True)


if __name__ == "__main__":
    main()
