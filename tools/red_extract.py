"""Stage 1+2: red mask -> components -> Zhang-Suen thinning -> ordered polylines (pixel space)."""
from PIL import Image, ImageDraw
import numpy as np, json

DIR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map"
SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"

im = Image.open(DIR + r"\NASA with Red lines.webp").convert("RGB")
a = np.asarray(im).astype(int)
H, W = a.shape[:2]
r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]
mask = (r > 140) & (g < 100) & (b < 100)
print("red pixels:", mask.sum())

# Zhang-Suen thinning (vectorized passes)
def neighbors(img):
    p = np.pad(img, 1)
    P2 = p[:-2, 1:-1]; P3 = p[:-2, 2:]; P4 = p[1:-1, 2:]; P5 = p[2:, 2:]
    P6 = p[2:, 1:-1]; P7 = p[2:, :-2]; P8 = p[1:-1, :-2]; P9 = p[:-2, :-2]
    return P2, P3, P4, P5, P6, P7, P8, P9

def thin(img):
    img = img.copy().astype(bool)
    while True:
        changed = False
        for phase in (0, 1):
            P2, P3, P4, P5, P6, P7, P8, P9 = neighbors(img)
            B = P2.astype(int)+P3+P4+P5+P6+P7+P8+P9
            seq = [P2, P3, P4, P5, P6, P7, P8, P9, P2]
            A = sum(((~seq[i]) & seq[i+1]).astype(int) for i in range(8))
            if phase == 0:
                c1 = (~(P2 & P4 & P6)) & (~(P4 & P6 & P8))
            else:
                c1 = (~(P2 & P4 & P8)) & (~(P2 & P6 & P8))
            rem = img & (B >= 2) & (B <= 6) & (A == 1) & c1
            if rem.any():
                img[rem] = False
                changed = True
        if not changed:
            return img

skel = thin(mask)
print("skeleton pixels:", skel.sum())

# split at junctions, walk simple paths
p = np.pad(skel, 1)
ncount = sum(p[1+dy:H+1+dy, 1+dx:W+1+dx].astype(int) for dy in (-1,0,1) for dx in (-1,0,1) if (dy,dx)!=(0,0))
deg = np.where(skel, ncount, 0)
junc = skel & (deg >= 3)
simple = skel & ~junc

lab = np.zeros((H, W), int)
paths = []
visited = np.zeros((H, W), bool)
ys, xs = np.where(simple)
pixset = simple
def nbrs(y, x, img):
    out = []
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0: continue
            ny, nx = y+dy, x+dx
            if 0 <= ny < H and 0 <= nx < W and img[ny, nx]:
                out.append((ny, nx))
    return out

# endpoints of simple sub-paths
for y0, x0 in zip(ys, xs):
    if visited[y0, x0]: continue
    nb = [n for n in nbrs(y0, x0, simple) if not visited[n[0], n[1]]]
    if len([n for n in nbrs(y0, x0, simple)]) > 1:
        continue  # start only from endpoints first
    path = [(y0, x0)]; visited[y0, x0] = True
    cur = (y0, x0)
    while True:
        nxt = [n for n in nbrs(*cur, simple) if not visited[n[0], n[1]]]
        if not nxt: break
        cur = nxt[0]; visited[cur[0], cur[1]] = True
        path.append(cur)
    if len(path) >= 8:
        paths.append(path)
# any leftover loops (no endpoints)
for y0, x0 in zip(ys, xs):
    if visited[y0, x0]: continue
    path = [(y0, x0)]; visited[y0, x0] = True
    cur = (y0, x0)
    while True:
        nxt = [n for n in nbrs(*cur, simple) if not visited[n[0], n[1]]]
        if not nxt: break
        cur = nxt[0]; visited[cur[0], cur[1]] = True
        path.append(cur)
    if len(path) >= 8:
        paths.append(path)

print("simple paths >=8px:", len(paths), " total length:", sum(len(p) for p in paths))

# join paths across junctions when roughly collinear
def enddir(path, at_end):
    seg = path[-6:] if at_end else path[:6][::-1]
    dy, dx = seg[-1][0]-seg[0][0], seg[-1][1]-seg[0][1]
    n = max(1e-9, (dy*dy+dx*dx)**0.5)
    return dy/n, dx/n

jys, jxs = np.where(junc)
juncs = list(zip(jys, jxs))
merged = True
while merged:
    merged = False
    for jy, jx in juncs:
        cand = []
        for pi, path in enumerate(paths):
            for at_end in (True, False):
                e = path[-1] if at_end else path[0]
                if abs(e[0]-jy) <= 2 and abs(e[1]-jx) <= 2:
                    cand.append((pi, at_end))
        if len(cand) < 2: continue
        best = None
        for i in range(len(cand)):
            for j in range(i+1, len(cand)):
                (pa, ea), (pb, eb) = cand[i], cand[j]
                if pa == pb: continue
                da = enddir(paths[pa], ea); db = enddir(paths[pb], eb)
                dot = -(da[0]*db[0] + da[1]*db[1])  # want continuation: opposite directions
                if best is None or dot > best[0]:
                    best = (dot, pa, ea, pb, eb)
        if best and best[0] > 0.80:  # <=~35 deg bend
            _, pa, ea, pb, eb = best
            A = paths[pa] if ea else paths[pa][::-1]
            Bp = paths[pb] if not eb else paths[pb][::-1]
            newp = A + [(jy, jx)] + Bp
            for idx in sorted((pa, pb), reverse=True):
                paths.pop(idx)
            paths.append(newp)
            merged = True
            break

paths.sort(key=len, reverse=True)
print("after junction joins:", len(paths), "paths; top lengths:", [len(p) for p in paths[:25]])

# decimate to every 9 px, save as json [x,y] pixel coords
out = [[[int(px), int(py)] for py, px in path[::9]] + [[int(path[-1][1]), int(path[-1][0])]] for path in paths if len(path) >= 25]
json.dump(out, open(SP + r"\red_paths.json", "w"))
print("saved", len(out), "polylines (>=25px)")

# QC overlay
qc = im.copy(); d = ImageDraw.Draw(qc)
cols = [(0,255,0),(0,200,255),(255,255,0),(255,0,255),(0,128,255),(128,255,0),(255,128,0),(200,0,255)]
for i, pl in enumerate(out):
    c = cols[i % len(cols)]
    for x, y in pl: d.ellipse([x-1, y-1, x+1, y+1], fill=c)
qc.save(SP + r"\red_paths_qc.png")
print("QC saved")
