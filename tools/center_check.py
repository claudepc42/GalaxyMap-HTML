import json, re, math

PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
with open(PATH, encoding="utf-8") as f:
    for line in f:
        if line.startswith("const TRACE = ["):
            trace = json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))
            break
chains = {c["key"]: c["pts"] for c in trace}

def fit_circle(pts):
    # Kasa algebraic circle fit: minimizes sum((x^2+y^2+D*x+E*y+F)^2)
    n = len(pts)
    sx = sum(p[0] for p in pts); sy = sum(p[1] for p in pts)
    sxx = sum(p[0]*p[0] for p in pts); syy = sum(p[1]*p[1] for p in pts)
    sxy = sum(p[0]*p[1] for p in pts)
    sxz = sum(p[0]*(p[0]**2+p[1]**2) for p in pts)
    syz = sum(p[1]*(p[0]**2+p[1]**2) for p in pts)
    sz = sum(p[0]**2+p[1]**2 for p in pts)
    # solve [[sxx,sxy,sx],[sxy,syy,sy],[sx,sy,n]] * [A,B,C] = [sxz,syz,sz]
    import itertools
    M = [[sxx,sxy,sx],[sxy,syy,sy],[sx,sy,n]]
    V = [sxz,syz,sz]
    # gaussian elim
    for i in range(3):
        piv = M[i][i]
        for j in range(i+1,3):
            f = M[j][i]/piv
            for k in range(3): M[j][k] -= f*M[i][k]
            V[j] -= f*V[i]
    X = [0,0,0]
    for i in (2,1,0):
        X[i] = (V[i] - sum(M[i][k]*X[k] for k in range(i+1,3)))/M[i][i]
    cx, cy = X[0]/2, X[1]/2
    r = math.sqrt(X[2] + cx*cx + cy*cy)
    return cx, cy, r

print("circle-fit centers (scene units; origin = bar center = Sgr A*):")
for key in ("3kn", "3kf", "nor", "sct", "sgr", "per", "out"):
    cx, cy, r = fit_circle(chains[key])
    off = math.hypot(cx, cy)
    print(f"{key:4s} center=({cx:7.1f},{cy:7.1f})  offset from origin={off:6.1f} u ({off:5.0f} ly)  fit radius={r:6.1f}")

both = chains["3kn"] + chains["3kf"]
cx, cy, r = fit_circle(both)
print(f"\n3kn+3kf combined: center=({cx:.1f},{cy:.1f}) offset={math.hypot(cx,cy):.1f} u, radius={r:.1f}")

# endpoint approach angles vs bar axis (barAngle = 60 deg from +x, i.e. pi/2 - 30deg)
barAngle = math.pi/2 - math.radians(30)
longAngle = barAngle + math.radians(6)
R = 500
tips = {
    "GB+": (math.cos(barAngle)*0.20*R*1.05, math.sin(barAngle)*0.20*R*1.05),
    "GB-": (-math.cos(barAngle)*0.20*R*1.05, -math.sin(barAngle)*0.20*R*1.05),
    "LB+": (math.cos(longAngle)*0.26*R, math.sin(longAngle)*0.26*R),
    "LB-": (-math.cos(longAngle)*0.26*R, -math.sin(longAngle)*0.26*R),
}
print("\nchain endpoints within 60 u of a bar tip -> approach angle vs bar axis:")
for c in trace:
    pts = c["pts"]
    for endname, (e, e2) in (("start", (pts[0], pts[1])), ("end", (pts[-1], pts[-2]))):
        for tn, (tx, tz) in tips.items():
            d = math.hypot(e[0]-tx, e[1]-tz)
            if d < 60:
                seg = math.atan2(e[1]-e2[1], e[0]-e2[0])
                axis = longAngle if tn.startswith("LB") else barAngle
                rel = math.degrees((seg - axis) % math.pi)
                if rel > 90: rel = 180 - rel
                print(f"{c['key']:4s} {endname:5s} near {tn} (d={d:4.1f} u): angle to bar axis = {rel:5.1f} deg  (0=parallel, 90=perpendicular)")
