import json, re, math

PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
SUN_D = 0.535*500
UPK = SUN_D/8.15
SUN_ANGLE = math.pi/2

REID = {
    "3kn":  (15, 18, 15, 3.52, -4.2, -4.2),
    "nor":  (5, 54, 18, 4.46, -1.0, 19.5),
    "sct":  (0, 104, 23, 4.91, 14.1, 12.1),
    "sgr":  (2, 97, 24, 6.04, 17.1, 1.0),
    "spur": (-8, 34, 9, 8.26, 11.4, 11.4),
    "per":  (-23, 115, 40, 8.87, 10.3, 8.7),
    "out":  (-16, 71, 18, 12.24, 3.0, 9.4),
}

def curve(bmin, bmax, bk, rk, plt_, pgt):
    pts = []
    for i in range(201):
        b = math.radians(bmin + (bmax-bmin)*i/200)
        bkr = math.radians(bk)
        psi = math.radians(plt_ if b <= bkr else pgt)
        Rr = rk*math.exp(-(b-bkr)*math.tan(psi))*UPK
        th = SUN_ANGLE - b
        pts.append((math.cos(th)*Rr, math.sin(th)*Rr))
    return pts

with open(PATH, encoding="utf-8") as f:
    for line in f:
        if line.startswith("const TRACE = ["):
            trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
            break
chains = {c["key"]: c["pts"] for c in trace}

def beta_of(x, z):  # scene point -> Reid azimuth (deg), given theta = sunAngle - beta
    th = math.atan2(z, x)
    b = math.degrees(SUN_ANGLE - th)
    while b < -180: b += 360
    while b > 180: b -= 360
    return b

for key, prm in REID.items():
    tp = chains[key]
    rc = curve(*prm)
    tr = [math.hypot(x,z)/UPK for x,z in tp]
    tb = [beta_of(x,z) for x,z in tp]
    rr = [math.hypot(x,z)/UPK for x,z in rc]
    print(f"{key:5s} TRACE: R {min(tr):5.2f}-{max(tr):5.2f} kpc  beta {min(tb):7.1f}..{max(tb):7.1f}"
          f"   REID: R {min(rr):5.2f}-{max(rr):5.2f} kpc  beta {prm[0]}..{prm[1]}")
    # radial offset where azimuth ranges overlap
    lo, hi = max(prm[0], min(tb)), min(prm[1], max(tb))
    if lo < hi:
        offs = []
        for (x,z), b, r in zip(tp, tb, tr):
            if lo <= b <= hi:
                bkr = math.radians(prm[2])
                br = math.radians(b)
                psi = math.radians(prm[4] if br <= bkr else prm[5])
                r_reid = prm[3]*math.exp(-(br-bkr)*math.tan(psi))
                offs.append(r - r_reid)
        if offs:
            mo = sum(offs)/len(offs)
            print(f"      overlap beta {lo:.0f}..{hi:.0f}: TRACE radially {'outside' if mo>0 else 'inside'} Reid by mean {abs(mo):.2f} kpc over {len(offs)} pts")
