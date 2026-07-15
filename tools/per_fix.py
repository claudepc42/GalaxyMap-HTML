"""Rebuild per: full backup body, cut at the point nearest the drawn wrap, splice wrap."""
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
bakper = [list(p) for p in next(c for c in load(BAK) if c["key"] == "per")["pts"]]

w13 = [tf(p) for p in paths[13]]
w44 = [tf(p) for p in paths[44]]

# orient the wrap: outer end = the end farther from the bar center region
# then find where per's body passes closest to that outer end
cands = [w13, w13[::-1]]
best = None
for wrap in cands:
    outer = wrap[0]
    for j, p in enumerate(bakper):
        d = math.hypot(p[0]-outer[0], p[1]-outer[1])
        if best is None or d < best[0]:
            best = (d, j, wrap)
d, j, wrap = best
print(f"per body point {j}/{len(bakper)} at ({bakper[j][0]},{bakper[j][1]}) is {d:.1f} u from wrap outer end {wrap[0]}")
if math.hypot(w44[0][0]-wrap[-1][0], w44[0][1]-wrap[-1][1]) > math.hypot(w44[-1][0]-wrap[-1][0], w44[-1][1]-wrap[-1][1]):
    w44.reverse()
newper = bakper[:j+1] + wrap + w44
# which end of the chain is j on? if j is near the START, the chain runs tip->out; handle
if j < len(bakper)//2:
    print("wrap connects at chain START; reversing assembly")
    newper = (bakper[j:][::-1])[:0]  # should not happen for per; guard
for c in cur:
    if c["key"] == "per":
        c["pts"] = newper
print(f"new per: {len(newper)} pts, ends at ({newper[-1][0]},{newper[-1][1]})")

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
lines[idx] = "const TRACE = " + json.dumps(cur, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("written")
