import json, re

PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
K = 0.535/0.52  # new SUN_D fraction / old — uniform pixel↔ly recalibration for R0=8.2 kpc

with open(PATH, encoding="utf-8") as f:
    lines = f.read().split("\n")

idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
line = lines[idx]
m = re.match(r"const TRACE = (\[.*\]);$", line)
assert m, "TRACE line shape unexpected"
trace = json.loads(m.group(1))
assert len(trace) == 21, f"expected 21 chains, got {len(trace)}"

def r1(v):  # one decimal, no trailing .0 noise beyond json default
    return round(v, 1)

for ch in trace:
    ch["width"] = r1(ch["width"] * K)
    ch["pts"] = [[r1(x * K), r1(z * K)] for x, z in ch["pts"]]

out = json.dumps(trace, separators=(",", ":"))
lines[idx] = f"const TRACE = {out};"

with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))

# sanity: max radius before/after
old = json.loads(m.group(1))
mx_old = max(max((p[0]**2+p[1]**2)**.5 for p in c["pts"]) for c in old)
mx_new = max(max((p[0]**2+p[1]**2)**.5 for p in c["pts"]) for c in trace)
print(f"chains: {len(trace)}  scale: {K:.6f}  max radius: {mx_old:.1f} -> {mx_new:.1f}")
