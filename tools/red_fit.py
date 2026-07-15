"""Stage 3: similarity transform px->scene via ICP against existing TRACE outer chains."""
import json, re, math
import numpy as np

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"

paths = json.load(open(SP + r"\red_paths.json"))
for line in open(CUR, encoding="utf-8"):
    if line.startswith("const TRACE = ["):
        trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
        break

# dense target cloud from TRACE, excluding 3kn/3kf (currently wrong ovals) and
# the rebuilt Bezier tails (last/first 9 pts of sct,nor,per,f7)
tgt = []
for c in trace:
    if c["key"] in ("3kn", "3kf"): continue
    pts = c["pts"]
    if c["key"] in ("sct", "nor", "per"): pts = pts[:-9]
    if c["key"] == "f7": pts = pts[9:]
    for i in range(len(pts)-1):
        (x0, z0), (x1, z1) = pts[i], pts[i+1]
        L = math.hypot(x1-x0, z1-z0)
        n = max(1, int(L/5))
        for k in range(n):
            t = k/n
            tgt.append((x0+(x1-x0)*t, z0+(z1-z0)*t))
tgt = np.array(tgt)
print("target cloud:", len(tgt))

src = np.array([p for pl in paths for p in pl], float)  # pixel coords (x,y)
print("source points:", len(src))

# init: mirror-y + rotate+scale mapping (like the clean image), GC at (449,493)
GCr = np.array([479.9, 455.1])  # core white dot, verified visually (red_gc_qc.png)
def apply(T, pts):
    s, th, tx, tz, mir = T
    x = pts[:, 0].copy(); y = pts[:, 1].copy()
    if mir: y = -y
    ct, st = math.cos(th), math.sin(th)
    return np.column_stack([s*(x*ct - y*st) + tx, s*(x*st + y*ct) + tz])

def umeyama(A, B, mir):
    # find s,R,t mapping A->B (A pre-mirrored outside)
    Am = A.mean(0); Bm = B.mean(0)
    A0 = A - Am; B0 = B - Bm
    C = A0.T @ B0 / len(A)
    U, D, Vt = np.linalg.svd(C)
    S = np.eye(2)
    if np.linalg.det(U @ Vt) < 0: S[1, 1] = -1
    R = (U @ S @ Vt).T
    s = np.trace(np.diag(D) @ S) / (A0**2).sum() * len(A)
    t = Bm - s * (R @ Am)
    th = math.atan2(R[1, 0], R[0, 0])
    return s, th, t[0], t[1]

# landmark-pinned init: GC->(0,0), Sun->(0,267.5); rotation fixed by GC->Sun axis
SUNr = np.array([478.8, 684.5])
d = SUNr - GCr
best = None
for mir in (True, False):
    dm = np.array([d[0], -d[1]]) if mir else d
    ang = math.atan2(dm[1], dm[0])
    th = math.pi/2 - ang           # rotate GC->Sun direction onto +z
    s = 267.5 / np.hypot(*d)
    gx, gy = (GCr[0], -GCr[1]) if mir else (GCr[0], GCr[1])
    tx = -s*(gx*math.cos(th) - gy*math.sin(th))
    tz = -s*(gx*math.sin(th) + gy*math.cos(th))
    T = (s, th, tx, tz, mir)
    m = apply(T, src[::6])
    d2 = ((m[:, None, :] - tgt[None, ::10, :])**2).sum(2)
    cost = np.sqrt(d2.min(1)).mean()
    print(f"mir={mir}: landmark init cost {cost:.1f} u (rot {math.degrees(th):.1f}, scale {s:.4f})")
    if best is None or cost < best[0]:
        best = (cost, T)
print(f"chosen: mir={best[1][4]}")

T = best[1]
mir = T[4]
sub = src[::4]
for it in range(12):
    m = apply(T, sub)
    d2 = ((m[:, None, :] - tgt[None, ::6, :])**2).sum(2)
    idx = d2.argmin(1)
    dist = np.sqrt(d2[np.arange(len(m)), idx])
    keep = dist < np.percentile(dist, 70)
    A = sub[keep].copy()
    if mir: A[:, 1] = -A[:, 1]
    B = tgt[::6][idx[keep]]
    s, th, tx, tz = umeyama(A, B, mir)
    T = (s, th, tx, tz, mir)
    print(f"iter {it}: kept {keep.sum()} mean resid {dist[keep].mean():.2f} u  scale={s:.4f} rot={math.degrees(th):.2f}")

json.dump({"s": T[0], "th": T[1], "tx": T[2], "tz": T[3], "mir": bool(T[4])}, open(SP + r"\red_transform.json", "w"))
# sanity: where do GC and image go?
gc_scene = apply(T, GCr[None, :])[0]
print(f"GC pixel maps to scene ({gc_scene[0]:.1f}, {gc_scene[1]:.1f})  [expect ~(0,0)]")
