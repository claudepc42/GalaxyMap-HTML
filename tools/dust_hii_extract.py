"""Extract dust filaments (dark ridges) and HII knots (pink) from NASA.webp,
convert to scene coords, emit compact JS consts + a QC overlay."""
from PIL import Image, ImageDraw
import numpy as np, math, json

DIR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map"
SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"

im = Image.open(DIR + r"\NASA.webp").convert("RGB")
a = np.asarray(im).astype(float)
H, W = a.shape[:2]
GC = (545.6, 548.1); SUN = (541.6, 754.9)

# clean-image -> scene transform (mirror + rotate, GC pinned to origin), same
# chirality convention as the red-image fit
scale = 267.5 / math.hypot(SUN[0]-GC[0], SUN[1]-GC[1])
dm = (SUN[0]-GC[0], -(SUN[1]-GC[1]))          # mirrored GC->Sun
th = math.pi/2 - math.atan2(dm[1], dm[0])
ct, st = math.cos(th), math.sin(th)
def tf(x, y):
    yy = -y
    dx, dy = x-GC[0], yy-(-GC[1])
    return (scale*(dx*ct - dy*st), scale*(dx*st + dy*ct))
# sanity
sx, sz = tf(*SUN)
print(f"transform check: Sun -> ({sx:.1f},{sz:.1f}) expect (0,267.5)")

lum = a.sum(2)/3
k = 31
pad = np.pad(lum, (k//2+1, k//2), mode='edge')
cs = np.pad(pad.cumsum(0).cumsum(1), ((1,0),(1,0)))
base = (cs[k:, k:] - cs[:-k, k:] - cs[k:, :-k] + cs[:-k, :-k])/(k*k)
base = base[:H, :W]

yy, xx = np.mgrid[0:H, 0:W]
rpx = np.hypot(xx-GC[0], yy-GC[1])
in_disk = rpx < 430

r, g, b = a[:, :, 0], a[:, :, 1], a[:, :, 2]

# ---- dust: darker than surroundings, brownish, inside a lit region ----
dark = (base - lum > 8) & (base > 48) & in_disk & (r >= g - 4) & (rpx > 115)
print("dust pixels:", dark.sum())
# ---- HII knots: pink (red high, green suppressed, blue mid) ----
pink = (r > 135) & (r - g > 28) & (b - g > 0) & in_disk
print("pink pixels:", pink.sum())

def bin_cells(mask, cell, min_px, val=None):
    out = []
    for cy in range(0, H, cell):
        for cx in range(0, W, cell):
            m = mask[cy:cy+cell, cx:cx+cell]
            n = m.sum()
            if n >= min_px:
                ys, xs = np.where(m)
                px, py = cx + xs.mean(), cy + ys.mean()
                strength = min(1.0, n/(cell*cell*0.5))
                out.append((px, py, strength))
    return out

dust_cells = bin_cells(dark, 10, 9)
pink_cells = bin_cells(pink, 8, 3)
print(f"dust cells: {len(dust_cells)}, pink cells: {len(pink_cells)}")

dust_sc = [(round(tf(px, py)[0], 1), round(tf(px, py)[1], 1), round(s, 2)) for px, py, s in dust_cells]
pink_sc = [(round(tf(px, py)[0], 1), round(tf(px, py)[1], 1), round(s, 2)) for px, py, s in pink_cells]

js_dust = "const IMG_DUST=[" + ",".join(f"[{x},{z},{s}]" for x, z, s in dust_sc) + "];"
js_hii = "const IMG_HII=[" + ",".join(f"[{x},{z},{s}]" for x, z, s in pink_sc) + "];"
open(SP + r"\img_layers.js", "w").write(js_dust + "\n" + js_hii + "\n")
print(f"JS size: {len(js_dust)+len(js_hii)} bytes")

qc = im.copy(); d = ImageDraw.Draw(qc)
for px, py, s in dust_cells: d.ellipse([px-2, py-2, px+2, py+2], outline=(80, 255, 80))
for px, py, s in pink_cells: d.ellipse([px-2, py-2, px+2, py+2], outline=(0, 200, 255))
qc.save(SP + r"\dust_hii_qc.png")
print("QC saved")
