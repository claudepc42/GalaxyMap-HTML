from PIL import Image, ImageDraw
import numpy as np

DIR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map"
SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"

im = Image.open(DIR + r"\NASA.webp").convert("RGB")
a = np.asarray(im).astype(float)
GC = (545.6, 548.1)
SUN = (541.6, 754.9)

# whiteness-excess map: min channel minus 21px box-smoothed baseline
wht = a.min(2)
k = 21
H, W = wht.shape
pad = np.pad(wht, (k//2 + 1, k//2), mode='edge')
cs = np.pad(pad.cumsum(0).cumsum(1), ((1,0),(1,0)))
base = (cs[k:, k:] - cs[:-k, k:] - cs[k:, :-k] + cs[:-k, :-k]) / (k*k)
E = wht - base[:H, :W]
E = np.clip(E, 0, 25)  # cap so text blobs can't dominate

TH = np.linspace(0, 2*np.pi, 360, endpoint=False)
CT, ST = np.cos(TH), np.sin(TH)

def score(cx, cy, ma, mi, tilt):
    tr = np.radians(tilt)
    x = cx + CT*ma*np.cos(tr) - ST*mi*np.sin(tr)
    y = cy + CT*ma*np.sin(tr) + ST*mi*np.cos(tr)
    xi = np.clip(x.astype(int), 0, W-1); yi = np.clip(y.astype(int), 0, H-1)
    return E[yi, xi].mean()

# coarse grid search around GC
best = None
for ma in range(78, 118, 3):
    for mi in range(30, 62, 3):
        if mi >= ma: continue
        for tilt in range(-70, -35, 3):
            for dx in (-4, 0, 4):
                for dy in (-4, 0, 4):
                    s = score(GC[0]+dx, GC[1]+dy, ma, mi, tilt)
                    if best is None or s > best[0]:
                        best = (s, GC[0]+dx, GC[1]+dy, ma, mi, tilt)
print("coarse:", [round(v,1) for v in best])

# local refine (coordinate descent, finer steps)
s0, cx, cy, ma, mi, tilt = best
step = [1.5, 1.5, 1.5, 1.5, 1.5]
for _ in range(60):
    improved = False
    for i, (lo, hi) in enumerate([(cx-8,cx+8),(cy-8,cy+8),(70,125),(25,68),(-75,-30)]):
        for d in (-step[i], step[i]):
            cand = [cx, cy, ma, mi, tilt]
            cand[i] += d
            if not (lo <= cand[i] <= hi): continue
            s = score(*cand)
            if s > s0:
                s0 = s; cx, cy, ma, mi, tilt = cand; improved = True
    if not improved:
        step = [x*0.6 for x in step]
        if max(step) < 0.2: break
print(f"refined: score={s0:.2f} center=({cx:.1f},{cy:.1f}) axes=({ma:.1f},{mi:.1f}) tilt={tilt:.1f} deg")
print(f"center offset from GC: ({cx-GC[0]:.1f},{cy-GC[1]:.1f}) px")

# scene conversion summary
upp = 267.5/np.hypot(SUN[0]-GC[0], SUN[1]-GC[1])
print(f"scene units/px = {upp:.4f}: semi-major {ma*upp:.1f} u ({ma*upp/32.82:.2f} kpc), semi-minor {mi*upp:.1f} u ({mi*upp/32.82:.2f} kpc)")
# bar direction in image: GC->Sun is +z scene; tilt vs that axis
sun_ang = np.degrees(np.arctan2(SUN[1]-GC[1], SUN[0]-GC[0]))
print(f"GC->Sun image angle: {sun_ang:.1f} deg; ellipse tilt relative to Sun axis: {tilt-sun_ang:.1f} deg")

qc = im.copy(); d = ImageDraw.Draw(qc)
tr = np.radians(tilt)
for t in np.linspace(0, 2*np.pi, 500):
    x = cx + np.cos(t)*ma*np.cos(tr) - np.sin(t)*mi*np.sin(tr)
    y = cy + np.cos(t)*ma*np.sin(tr) + np.sin(t)*mi*np.cos(tr)
    d.point((x, y), fill=(255, 0, 255))
d.ellipse([GC[0]-2, GC[1]-2, GC[0]+2, GC[1]+2], outline=(255, 0, 0))
qc.crop((int(GC[0])-190, int(GC[1])-190, int(GC[0])+190, int(GC[1])+190)).resize((570, 570), Image.NEAREST).save(SP + r"\ellipse_qc2.png")
print("QC saved")
