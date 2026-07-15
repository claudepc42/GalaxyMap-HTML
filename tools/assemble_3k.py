"""Assemble the two 3-kpc lanes from red fragments, smooth, transform, write into TRACE."""
import json, re, math
import numpy as np

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

def assemble(idx_list):
    """Concatenate fragments in order, flipping each so it continues from the last
    end, and trimming incoming points that overlap the path built so far (parallel
    double-strokes from the thinning split would otherwise zigzag)."""
    out = [list(p) for p in paths[idx_list[0]]]
    for i in idx_list[1:]:
        frag = [list(p) for p in paths[i]]
        d_end = math.hypot(frag[0][0]-out[-1][0], frag[0][1]-out[-1][1])
        d_rev = math.hypot(frag[-1][0]-out[-1][0], frag[-1][1]-out[-1][1])
        if d_rev < d_end:
            frag.reverse()
        frag = [p for p in frag
                if min(math.hypot(p[0]-q[0], p[1]-q[1]) for q in out) > 14]
        out.extend(frag)
    return out

def orient(idx, start_near):
    """Flip a starting fragment so its first point is nearest the given px point."""
    frag = [list(p) for p in paths[idx]]
    if math.hypot(frag[-1][0]-start_near[0], frag[-1][1]-start_near[1]) < \
       math.hypot(frag[0][0]-start_near[0], frag[0][1]-start_near[1]):
        frag.reverse()
    paths[idx] = frag

def chaikin(pts, rounds=2):
    for _ in range(rounds):
        out = [pts[0]]
        for i in range(len(pts)-1):
            p, q = pts[i], pts[i+1]
            out.append([0.75*p[0]+0.25*q[0], 0.75*p[1]+0.25*q[1]])
            out.append([0.25*p[0]+0.75*q[0], 0.25*p[1]+0.75*q[1]])
        out.append(pts[-1])
        pts = out
    return pts

def decimate(pts, n=30):
    cum = [0]
    for i in range(1, len(pts)):
        cum.append(cum[-1] + math.hypot(pts[i][0]-pts[i-1][0], pts[i][1]-pts[i-1][1]))
    L = cum[-1]
    out = []
    j = 0
    for k in range(n):
        t = L*k/(n-1)
        while j < len(cum)-2 and cum[j+1] < t: j += 1
        f = (t-cum[j])/max(1e-9, cum[j+1]-cum[j])
        out.append([pts[j][0]+(pts[j+1][0]-pts[j][0])*f, pts[j][1]+(pts[j+1][1]-pts[j][1])*f])
    return out

# Lane A (image px): lateral above bar -> top tip -> down right of core into hook
# (#32 is a parallel double-stroke of the same descent #12 starts with; skip it)
orient(26, (433, 356))   # start at its left end
A = assemble([26, 12])
# Lane B: core-left hook -> down left flank -> bottom tip -> lateral right -> up right flank
orient(18, (455, 335))   # start at the core hook
B = assemble([18, 25, 22])

for name, px in (("A", A), ("B", B)):
    sm = decimate(chaikin(px), 30)
    sc = [[round(x, 1), round(z, 1)] for x, z in (tf(p) for p in sm)]
    mid = sc[len(sc)//2]
    print(f"lane {name}: {len(px)} px pts -> 30 scene pts, mid=({mid[0]},{mid[1]}), "
          f"r range {min(math.hypot(*p) for p in sc):.0f}-{max(math.hypot(*p) for p in sc):.0f} u")
    if name == "A": scA = sc
    else: scB = sc

# near = Sun side (+z at mid-lateral). Lane B's lateral is Sun side in the image
# (below the bar, Sun below) -> check via mean z
zA = sum(p[1] for p in scA)/len(scA); zB = sum(p[1] for p in scB)/len(scB)
near, far = (scA, scB) if zA > zB else (scB, scA)
print(f"mean z: A={zA:.0f} B={zB:.0f} -> near is {'A' if zA>zB else 'B'}")

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
trace = json.loads(re.match(r"const TRACE = (\[.*\]);", lines[idx]).group(1))
for c in trace:
    if c["key"] == "3kn": c["pts"] = near
    if c["key"] == "3kf": c["pts"] = far
lines[idx] = "const TRACE = " + json.dumps(trace, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("TRACE written: 3kn/3kf now follow the drawn red lanes")
