import json, re, sys
proj, src_t = sys.argv[1], sys.argv[2]
J = json.load(open(f"{proj}/assets/times.json")); T, TOTAL = J["T"], J["TOTAL"]
clips = json.load(open(f"{proj}/assets/clips.json"))
bounds = [("S1", None, "L02"), ("S2", "L02", "L04a"), ("S3", "L04a", "L05"), ("S4", "L05", "L12a"), ("S5", "L12a", "L13a"),
          ("S6", "L13a", "L14a"), ("S7", "L14a", "L16"), ("S8", "L16", "L17a"), ("S9", "L17a", None)]
src = open(src_t, encoding="utf-8").read().replace("__TOTAL__", str(TOTAL))
vids = "\n".join(f'      <video id="{c["name"]}" class="clip bg" src="assets/v/{c["name"]}.mp4" muted playsinline data-start="{c["start"]}" data-duration="{c["dur"]}" data-track-index="0"></video>' for c in clips)
src = src.replace("__VIDEOS__", vids)
for name, a, b in bounds:
    st = 0.0 if a is None else T[a][0]; en = TOTAL if b is None else T[b][0]
    src = src.replace(f"__D_{name}__", f"{en - st:.3f}")
for k, v in T.items(): src = src.replace(f"__S_{k}__", f"{v[0]:.3f}")
assert not re.findall(r"__[A-Za-z0-9_]+__", src)
open(f"{proj}/index.html", "w", encoding="utf-8").write(src); print("ok")
