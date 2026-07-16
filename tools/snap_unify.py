"""Item 5: snap IMG_HII/IMG_DUST toward nearest arm spine (75% within 25u).
Item 6: fragments get dim 0.95 + length-proportional star weights."""
import json, re, math

CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
s = open(CUR, encoding="utf-8").read()

trace = json.loads(re.search(r"const TRACE = (\[.*?\]);", s).group(1))
dense = []
for c in trace:
    pts = c["pts"]
    for i in range(len(pts)-1):
        (x0,z0),(x1,z1) = pts[i], pts[i+1]
        n = max(1, int(math.hypot(x1-x0, z1-z0)/6))
        for k in range(n):
            t = k/n
            dense.append((x0+(x1-x0)*t, z0+(z1-z0)*t))
print("spine samples:", len(dense))

def snap_arr(name):
    m = re.search(r"const " + name + r"=(\[.*?\]);", s)
    arr = json.loads(m.group(1))
    moved = 0
    out = []
    for x, z, st in arr:
        best = min(dense, key=lambda p: (p[0]-x)**2 + (p[1]-z)**2)
        d = math.hypot(best[0]-x, best[1]-z)
        if d < 25:
            x = x + (best[0]-x)*0.75; z = z + (best[1]-z)*0.75
            moved += 1
        out.append([round(x,1), round(z,1), st])
    print(f"{name}: {moved}/{len(arr)} snapped")
    return m.group(0), "const " + name + "=" + json.dumps(out, separators=(",", ":")) + ";"

o1, n1 = snap_arr("IMG_HII")
s = s.replace(o1, n1)
o2, n2 = snap_arr("IMG_DUST")
s = s.replace(o2, n2)

# fragment unify: dim 0.95, wt proportional to length (density matched to sct)
def chain_len(pts):
    return sum(math.hypot(pts[i+1][0]-pts[i][0], pts[i+1][1]-pts[i][1]) for i in range(len(pts)-1))
sct = next(c for c in trace if c["key"] == "sct")
density = sct["wt"]/chain_len(sct["pts"])
for c in trace:
    if re.match(r"f\d+$", c["key"]):
        c["dim"] = 0.95
        c["wt"] = round(max(0.3, chain_len(c["pts"])*density), 2)
print("fragment weights:", {c["key"]: c["wt"] for c in trace if re.match(r"f\d+$", c["key"])})
s = re.sub(r"const TRACE = \[.*?\];", "const TRACE = " + json.dumps(trace, separators=(",", ":")) + ";", s, count=1)

open(CUR, "w", encoding="utf-8", newline="\n").write(s)
print("written")
