"""Rebuild per's root from drawn strokes #13+#44; add unrepresented edge arcs as new fragments."""
import json, re, math

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
BAK = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.backup-2026-07-15.html"

paths = json.load(open(SP + r"\red_paths.json"))
Tj = json.load(open(SP + r"\red_transform_pinned.json"))
s, th, tx, tz, mir = Tj["s"], Tj["th"], Tj["tx"], Tj["tz"], Tj["mir"]
ct, st = math.cos(th), math.sin(th)
def tf(pt):
    x, y = pt
    if mir: y = -y
    return [round(s*(x*ct - y*st) + tx, 1), round(s*(x*st + y*ct) + tz, 1)]

def load(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("const TRACE = ["):
            return json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))

cur = load(CUR)
bak = {c["key"]: c for c in load(BAK)}
by = {c["key"]: c for c in cur}

# ---- per root: body (minus old traced tail) + drawn wrap (#13 then #44) ----
body = [list(p) for p in bak["per"]["pts"]][:-9]
w13 = [tf(p) for p in paths[13]]
w44 = [tf(p) for p in paths[44]]
end = body[-1]
if math.hypot(w13[-1][0]-end[0], w13[-1][1]-end[1]) < math.hypot(w13[0][0]-end[0], w13[0][1]-end[1]):
    w13.reverse()
tail = w13
if math.hypot(w44[0][0]-tail[-1][0], w44[0][1]-tail[-1][1]) > math.hypot(w44[-1][0]-tail[-1][0], w44[-1][1]-tail[-1][1]):
    w44.reverse()
tail = tail + w44
print(f"per: body ends ({end[0]},{end[1]}), wrap {tail[0]} ... {tail[-1]}, gap to body {math.hypot(tail[0][0]-end[0], tail[0][1]-end[1]):.1f} u")
by["per"]["pts"] = body + tail

# ---- new edge fragments from unmatched drawn arcs ----
edge_ids = [5, 7, 29, 41]
# group by continuity: merge those whose endpoints are within 30 px
frs = {i: [list(p) for p in paths[i]] for i in edge_ids}
groups = [[5], [7], [29], [41]]
merged = True
while merged:
    merged = False
    for gi in range(len(groups)):
        for gj in range(gi+1, len(groups)):
            A = frs[groups[gi][-1]]; B = frs[groups[gj][0]]
            ds = [math.hypot(A[a][0]-B[b][0], A[a][1]-B[b][1]) for a in (0, -1) for b in (0, -1)]
            if min(ds) < 35:
                groups[gi] += groups[gj]; groups.pop(gj); merged = True
                break
        if merged: break
print("edge arc groups:", groups)

newfrags = []
fnum = 14
for grp in groups:
    pts = []
    for i in grp:
        frag = [list(p) for p in frs[i]]
        if pts:
            if math.hypot(frag[-1][0]-pts[-1][0], frag[-1][1]-pts[-1][1]) < math.hypot(frag[0][0]-pts[-1][0], frag[0][1]-pts[-1][1]):
                frag.reverse()
        pts.extend(frag)
    sc = [tf(p) for p in pts]
    if len(sc) < 5: continue
    newfrags.append({"key": f"f{fnum}", "width": 14.4, "hot": 0.15, "wt": 0.5, "dim": 0.8, "lt": 0.5, "pts": sc})
    print(f"f{fnum}: {len(sc)} pts, r {min(math.hypot(*p) for p in sc):.0f}-{max(math.hypot(*p) for p in sc):.0f} u")
    fnum += 1
cur.extend(newfrags)

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
lines[idx] = "const TRACE = " + json.dumps(cur, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print(f"written: per root from drawing, +{len(newfrags)} edge fragments, total chains {len(cur)}")
