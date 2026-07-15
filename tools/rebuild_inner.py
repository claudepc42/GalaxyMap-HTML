import json, re, math

PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
BAR = math.pi/2 - math.radians(30)   # scene barAngle
MA, MI = 120.3, 40.3                 # measured from NASA.webp pale ellipse (scene units)
TRIM = 0.16                          # rad trimmed off each end so arcs stop short of the tips

with open(PATH, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
trace = json.loads(re.match(r"const TRACE = (\[.*\]);", lines[idx]).group(1))
by = {c["key"]: c for c in trace}

def ell(t):
    ca, sa = math.cos(BAR), math.sin(BAR)
    ex, ey = MA*math.cos(t), MI*math.sin(t)
    return [round(ca*ex - sa*ey, 1), round(sa*ex + ca*ey, 1)]

# two half-ellipse arcs, split at the major axis (bar tips), trimmed short
n = 30
arc1 = [ell(TRIM + (math.pi - 2*TRIM)*i/(n-1)) for i in range(n)]
arc2 = [ell(math.pi + TRIM + (math.pi - 2*TRIM)*i/(n-1)) for i in range(n)]
# near = the half whose midpoint is on the Sun side (+z)
if arc1[n//2][1] > 0:
    near, far = arc1, arc2
else:
    near, far = arc2, arc1
by["3kn"]["pts"] = near
by["3kf"]["pts"] = far
print("3kn/3kf replaced with measured ellipse halves")
print(f"  near mid z={near[n//2][1]:.0f}, far mid z={far[n//2][1]:.0f}")

# ---- tangent-blend arm-root tails into the bar axis ----
def blend_tail(c, end, K=6, target_off=math.radians(15)):
    pts = [list(p) for p in c["pts"]]
    if end == "start":
        pts.reverse()
    tail = pts[-(K+1):]
    segs = []
    for i in range(len(tail)-1):
        dx, dz = tail[i+1][0]-tail[i][0], tail[i+1][1]-tail[i][1]
        segs.append((math.hypot(dx, dz), math.atan2(dz, dx)))
    cur = segs[-1][1]
    # target: bar axis direction (mod pi) closest to current heading, +/- offset toward current
    axis = BAR
    cands = [axis, axis+math.pi]
    base = min(cands, key=lambda a: abs((cur-a+math.pi) % (2*math.pi) - math.pi))
    diff = (cur - base + math.pi) % (2*math.pi) - math.pi
    tgt = base + (target_off if diff > 0 else -target_off)
    dtot = (tgt - cur + math.pi) % (2*math.pi) - math.pi
    # progressive rotation: smoothstep ramp over the tail
    p = tail[0][:]
    out = [p[:]]
    for i, (L, ang) in enumerate(segs):
        w = ((i+1)/len(segs))**2
        na = ang + dtot*w
        p = [p[0] + L*math.cos(na), p[1] + L*math.sin(na)]
        out.append([round(p[0], 1), round(p[1], 1)])
    pts[-(K+1):] = out
    if end == "start":
        pts.reverse()
    c["pts"] = pts
    return math.degrees(abs(diff)), math.degrees(abs((tgt-base+math.pi)%(2*math.pi)-math.pi))

for key, end in (("sct", "end"), ("nor", "end"), ("per", "end"), ("f7", "start")):
    was, now = blend_tail(by[key], end)
    print(f"{key:4s} {end:5s}: approach vs bar axis {was:5.1f} deg -> {now:4.1f} deg")

lines[idx] = "const TRACE = " + json.dumps(trace, separators=(",", ":")) + ";"
with open(PATH, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("TRACE written")
