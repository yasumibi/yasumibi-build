import json, re, sys
proj, tmpl = sys.argv[1], sys.argv[2]
J = json.load(open(f"{proj}/assets/times.json")); T, TOTAL = J["T"], J["TOTAL"]
clips = json.load(open(f"{proj}/assets/clips.json"))
bounds = [("S0", None, "L03"), ("S1", "L03", "L05"), ("S2", "L05", "L07"), ("S3", "L07", "L09"), ("S4", "L09", "L11"), ("S5", "L11", "L14"), ("S6", "L14", None)]
src = open(tmpl, encoding="utf-8").read().replace("__TOTAL__", str(TOTAL))
src = src.replace("__VIDEOS__", "\n".join(f'      <video id="{c["name"]}" class="clip bg" src="assets/v/{c["name"]}.mp4" muted playsinline data-start="{c["start"]}" data-duration="{c["dur"]}" data-track-index="0"></video>' for c in clips))
for n, a, b in bounds:
    st = 0.0 if a is None else T[a][0]; en = TOTAL if b is None else T[b][0]
    src = src.replace(f"__D_{n}__", f"{en - st:.3f}")
for k, v in T.items(): src = src.replace(f"__S_{k}__", f"{v[0]:.3f}")
assert not re.findall(r"__[A-Za-z0-9_]+__", src)
open(f"{proj}/index.html", "w", encoding="utf-8").write(src); print("ok")
