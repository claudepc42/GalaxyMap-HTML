"""Center rebuild v2: 3kn = #18+#25 only (no forced #22 connection);
#22 becomes standalone fragment f17. 3kf = #26+#12 (unchanged, it was good)."""
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
    return [s*(x*ct - y*st) + tx, s*(x*st + y*ct) + tz]

def catmull(p0,p1,p2,p3,n):
    out=[]
    for k in range(1,n):
        t=k/n
        out.append([0.5*((2*p1[i])+(-p0[i]+p2[i])*t+(2*p0[i]-5*p1[i]+4*p2[i]-p3[i])*t*t+(-p0[i]+3*p1[i]-3*p2[i]+p3[i])*t**3) for i in (0,1)])
    return out

def join(ids, start_near):
    segs = [[list(p) for p in paths[i]] for i in ids]
    if math.hypot(segs[0][-1][0]-start_near[0], segs[0][-1][1]-start_near[1]) < \
       math.hypot(segs[0][0][0]-start_near[0], segs[0][0][1]-start_near[1]):
        segs[0].reverse()
    out = segs[0]
    for seg in segs[1:]:
        if math.hypot(seg[-1][0]-out[-1][0], seg[-1][1]-out[-1][1]) < \
           math.hypot(seg[0][0]-out[-1][0], seg[0][1]-out[-1][1]):
            seg.reverse()
        gap = math.hypot(seg[0][0]-out[-1][0], seg[0][1]-out[-1][1])
        if gap > 10:
            out = out + catmull(out[-2], out[-1], seg[0], seg[1], max(2, int(gap/9)))
        out = out + seg
    return out

def chaikin(pts, rounds=2):
    for _ in range(rounds):
        o=[pts[0]]
        for i in range(len(pts)-1):
            p,q=pts[i],pts[i+1]
            o.append([0.75*p[0]+0.25*q[0],0.75*p[1]+0.25*q[1]])
            o.append([0.25*p[0]+0.75*q[0],0.25*p[1]+0.75*q[1]])
        o.append(pts[-1]); pts=o
    return pts
def decim(pts,n):
    cum=[0]
    for i in range(1,len(pts)): cum.append(cum[-1]+math.hypot(pts[i][0]-pts[i-1][0],pts[i][1]-pts[i-1][1]))
    L=cum[-1]; out=[]; j=0
    for k in range(n):
        t=L*k/(n-1)
        while j<len(cum)-2 and cum[j+1]<t: j+=1
        f=(t-cum[j])/max(1e-9,cum[j+1]-cum[j])
        out.append([pts[j][0]+(pts[j+1][0]-pts[j][0])*f, pts[j][1]+(pts[j+1][1]-pts[j][1])*f])
    return out
def sc(px, n):
    return [[round(x,1),round(z,1)] for x,z in (tf(p) for p in decim(chaikin(px), n))]

near = sc(join([18, 25], (439, 454)), 26)   # hook -> left flank -> bottom lateral
far  = sc(join([26, 12], (433, 356)), 30)   # top lateral -> descent -> core hook
f17  = sc([list(p) for p in paths[22]], 10) # standalone right-flank stroke

zn = sum(p[1] for p in near)/len(near); zf = sum(p[1] for p in far)/len(far)
if zn < zf: near, far = far, near
print(f"near mid-z {sum(p[1] for p in near)/len(near):.0f}, far {sum(p[1] for p in far)/len(far):.0f}")
print(f"GC closest: near {min(math.hypot(*p) for p in near):.1f} u, far {min(math.hypot(*p) for p in far):.1f} u")

for line in open(CUR, encoding="utf-8"):
    if line.startswith("const TRACE = ["):
        trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
        break
by = {c["key"]: c for c in trace}
by["3kn"]["pts"] = near
by["3kf"]["pts"] = far
if "f17" not in by:
    trace.append({"key":"f17","width":10,"hot":0.12,"wt":1.0,"dim":0.9,"lt":0.5,"pts":f17})
else:
    by["f17"]["pts"] = f17

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
lines[idx] = "const TRACE = " + json.dumps(trace, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print(f"written; chains now {len(trace)}")
