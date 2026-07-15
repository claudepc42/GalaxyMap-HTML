import json, re, math

CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
BAK = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.backup-2026-07-15.html"
BAR = math.pi/2 - math.radians(30)
LONG = BAR + math.radians(6)
R = 500
TIPS = {
    "GB+": ( math.cos(BAR)*0.20*R*1.05,  math.sin(BAR)*0.20*R*1.05, BAR),
    "GB-": (-math.cos(BAR)*0.20*R*1.05, -math.sin(BAR)*0.20*R*1.05, BAR),
    "LB+": ( math.cos(LONG)*0.26*R,  math.sin(LONG)*0.26*R, LONG),
    "LB-": (-math.cos(LONG)*0.26*R, -math.sin(LONG)*0.26*R, LONG),
}

def load(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("const TRACE = ["):
            return json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))

cur = load(CUR)
bak = {c["key"]: c for c in load(BAK)}
by = {c["key"]: c for c in cur}

def bezier_tail(pts_orig, end, tip_key, K=9):
    pts = [list(p) for p in pts_orig]
    if end == "start":
        pts.reverse()
    tx, tz, axis = TIPS[tip_key]
    p0 = pts[-(K+1)]                    # join point (kept)
    pj = pts[-(K+2)]                    # point before join, for incoming tangent
    t0 = math.atan2(p0[1]-pj[1], p0[0]-pj[0])
    # end travel direction: the bar-axis direction closest to the join->tip heading
    h = math.atan2(tz-p0[1], tx-p0[0])
    cands = [axis, axis+math.pi]
    t3 = min(cands, key=lambda a: abs((h-a+math.pi) % (2*math.pi) - math.pi))
    L = math.hypot(tx-p0[0], tz-p0[1])
    c1 = (p0[0] + math.cos(t0)*L*0.4, p0[1] + math.sin(t0)*L*0.4)
    c2 = (tx - math.cos(t3)*L*0.4,  tz - math.sin(t3)*L*0.4)
    out = []
    for i in range(1, K+1):
        t = i/K
        mt = 1-t
        x = mt**3*p0[0] + 3*mt*mt*t*c1[0] + 3*mt*t*t*c2[0] + t**3*tx
        z = mt**3*p0[1] + 3*mt*mt*t*c1[1] + 3*mt*t*t*c2[1] + t**3*tz
        out.append([round(x,1), round(z,1)])
    pts[-K:] = out
    if end == "start":
        pts.reverse()
    a, b = (out[-2], out[-1]) if end != "start" else (out[-2], out[-1])
    fin = math.atan2(b[1]-a[1], b[0]-a[0])
    rel = math.degrees((fin - axis) % math.pi)
    if rel > 90: rel = 180 - rel
    return pts, rel

for key, end, tip in (("sct","end","LB-"), ("nor","end","LB-"), ("per","end","LB+"), ("f7","start","GB+")):
    pts, ang = bezier_tail(bak[key]["pts"], end, tip)
    by[key]["pts"] = pts
    e = pts[-1] if end == "end" else pts[0]
    print(f"{key:4s}: root rebuilt as Bezier into {tip}; end angle vs bar axis {ang:.1f} deg, endpoint=({e[0]},{e[1]})")

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
lines[idx] = "const TRACE = " + json.dumps(cur, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("written")
