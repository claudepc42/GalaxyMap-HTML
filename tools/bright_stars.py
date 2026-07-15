import csv, math

# ICRS (J2000) -> galactic rotation matrix rows: gal x (l=0,b=0), gal y (l=90), gal z (NGP)
M = [
    [-0.0548755604, -0.8734370902, -0.4838350155],
    [ 0.4941094279, -0.4448296300,  0.7469822445],
    [-0.8676661490, -0.1980763734,  0.4559837762],
]

def galactic(ra_deg, dec_deg):
    ra, dec = math.radians(ra_deg * 15.0), math.radians(dec_deg)  # HYG ra is in hours
    v = [math.cos(dec)*math.cos(ra), math.cos(dec)*math.sin(ra), math.sin(dec)]
    g = [sum(M[i][j]*v[j] for j in range(3)) for i in range(3)]
    l = math.degrees(math.atan2(g[1], g[0])) % 360
    b = math.degrees(math.asin(max(-1, min(1, g[2]))))
    return l, b

def ballesteros(bv):
    return 4600*(1/(0.92*bv+1.7) + 1/(0.92*bv+0.62))

rows = []
with open(r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad\hyg.csv", encoding="utf-8") as f:
    for r in csv.DictReader(f):
        if r["proper"] == "Sol":
            continue
        try:
            mag, dist = float(r["mag"]), float(r["dist"])
        except ValueError:
            continue
        if mag > 2.0 or dist <= 0 or dist > 90000:
            continue
        ci = float(r["ci"]) if r["ci"] else 0.5
        l, b = galactic(float(r["ra"]), float(r["dec"]))
        t = max(2500, min(30000, ballesteros(ci)))
        ly = dist * 3.26156
        name = r["proper"] or r["bf"] or ("HIP " + r["hip"])
        rows.append((mag, name, l, b, ly, t, float(r["absmag"])))

rows.sort()
print(f"{len(rows)} stars with V <= 2.0")
entries = []
for mag, name, l, b, ly, t, am in rows:
    entries.append(f"[{l:.1f},{b:.1f},{ly:.0f},{t:.0f},{am:.2f}]  // {name} V={mag:.2f}")
# compact JS array (no comments) + a commented listing for review
compact = ",".join(f"[{l:.1f},{b:.1f},{ly:.0f},{t:.0f},{am:.2f}]" for mag, name, l, b, ly, t, am in rows)
print("const BRIGHT=[" + compact + "];")
print()
for e in entries:
    print(e)
