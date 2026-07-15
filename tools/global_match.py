import json, re, math

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"

paths = json.load(open(SP + r"\red_paths.json"))
Tj = json.load(open(SP + r"\red_transform_pinned.json"))
s, th, tx, tz, mir = Tj["s"], Tj["th"], Tj["tx"], Tj["tz"], Tj["mir"]
ct, st = math.cos(th), math.sin(th)
def tf(pt):
    x, y = pt
    if mir: y = -y
    return (s*(x*ct - y*st) + tx, s*(x*st + y*ct) + tz)

for line in open(CUR, encoding="utf-8"):
    if line.startswith("const TRACE = ["):
        trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
        break

def dense(pts):
    out = []
    for i in range(len(pts)-1):
        (x0, z0), (x1, z1) = pts[i], pts[i+1]
        n = max(1, int(math.hypot(x1-x0, z1-z0)/4))
        for k in range(n):
            t = k/n
            out.append((x0+(x1-x0)*t, z0+(z1-z0)*t))
    return out

targets = {c["key"]: dense(c["pts"]) for c in trace}
bad = []
for i, pl in enumerate(paths):
    sc = [tf(p) for p in pl]
    best = None
    for key, tg in targets.items():
        d = sum(min(math.hypot(x-bx, z-bz) for bx, bz in tg) for x, z in sc)/len(sc)
        if best is None or d < best[0]:
            best = (d, key)
    if best[0] > 15:
        r0 = math.hypot(*sc[0]); r1 = math.hypot(*sc[-1])
        bad.append((best[0], i, best[1], len(sc), r0, r1))
bad.sort(reverse=True)
print(f"{len(bad)} polylines with best-match > 15 u:")
for d, i, key, n, r0, r1 in bad:
    print(f"  #{i:3d} ({n:3d} pts): best {key} at {d:5.1f} u   r {r0:.0f}->{r1:.0f}")
