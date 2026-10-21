import json, re, sys
proj = sys.argv[1]
J = json.load(open(f"{proj}/assets/times.json"))
T, TOTAL = J["T"], J["TOTAL"]
bounds = [("S1", None, "L02"), ("S2", "L02", "L04a"), ("S3", "L04a", "L05"), ("S4", "L05", "L12a"), ("S5", "L12a", "L13a"),
          ("S6", "L13a", "L14a"), ("S7", "L14a", "L16"), ("S8", "L16", "L17a"), ("S9", "L17a", None)]
src = open(f"{proj}/../src3/template.html", encoding="utf-8").read()
src = src.replace("__TOTAL__", str(TOTAL))
for name, a, b in bounds:
    st = 0.0 if a is None else T[a][0]
    en = TOTAL if b is None else T[b][0]
    src = src.replace(f"__D_{name}__", f"{en - st:.3f}")
for k, v in T.items():
    src = src.replace(f"__S_{k}__", f"{v[0]:.3f}")
left = re.findall(r"__[A-Z0-9_a-z]+__", src)
assert not left, left
open(f"{proj}/index.html", "w", encoding="utf-8").write(src)
print("ok")
