import json, re, math

PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
SUN_D = 0.535*500          # scene units
UPK = SUN_D/8.15           # scene units per kpc, normalized so Reid R0 lands on the scene Sun
SUN_ANGLE = math.pi/2

# Reid et al. 2019 Table 2: name, beta_min, beta_max, beta_kink, R_kink, psi_lt, psi_gt (deg, kpc)
REID = {
    "3kn":  (15, 18, 15, 3.52, -4.2, -4.2),
    "nor":  (5, 54, 18, 4.46, -1.0, 19.5),
    "sct":  (0, 104, 23, 4.91, 14.1, 12.1),
    "sgr":  (2, 97, 24, 6.04, 17.1, 1.0),
    "spur": (-8, 34, 9, 8.26, 11.4, 11.4),
    "per":  (-23, 115, 40, 8.87, 10.3, 8.7),
    "out":  (-16, 71, 18, 12.24, 3.0, 9.4),
}

def reid_curve(bmin, bmax, bk, rk, plt_, pgt, sign):
    pts = []
    n = 200
    for i in range(n+1):
        b = math.radians(bmin + (bmax-bmin)*i/n)
        bkr = math.radians(bk)
        psi = math.radians(plt_ if b <= bkr else pgt)
        # ln(R/Rk) = -(b - bk) tan(psi)
        Rr = rk*math.exp(-(b-bkr)*math.tan(psi)) * UPK
        th = SUN_ANGLE + sign*b
        pts.append((math.cos(th)*Rr, math.sin(th)*Rr))
    return pts

with open(PATH, encoding="utf-8") as f:
    for line in f:
        if line.startswith("const TRACE = ["):
            trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
            break

chains = {c["key"]: c["pts"] for c in trace}

def mean_nn(a, b):  # mean over a of nearest distance to b
    tot = 0.0
    for x, z in a:
        tot += min(math.hypot(x-bx, z-bz) for bx, bz in b)
    return tot/len(a)

print(f"scene units/kpc = {UPK:.2f}   (1 unit = 100 ly)")
for sign in (1, -1):
    print(f"\n--- azimuth sign {sign:+d} ---")
    for key, prm in REID.items():
        if key not in chains: continue
        rc = reid_curve(*prm, sign)
        tp = chains[key]
        d_t2r = mean_nn(tp, rc)   # trace -> reid
        d_r2t = mean_nn(rc, tp)   # reid -> trace
        print(f"{key:5s} trace->reid {d_t2r:6.1f} u ({d_t2r/UPK:4.2f} kpc)   reid->trace {d_r2t:6.1f} u ({d_r2t/UPK:4.2f} kpc)")
