"""Pack the 439k Gaia bubble into the 8-byte record format and swap into the HTML."""
import csv, math, struct, base64, re

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
PATH = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"

recs = []
skipped = 0
with open(SP + r"\gaia_bubble.csv") as f:
    for row in csv.DictReader(f):
        try:
            l = math.radians(float(row["l"])); b = math.radians(float(row["b"]))
            par = float(row["parallax"]); g = float(row["phot_g_mean_mag"])
        except (ValueError, KeyError):
            skipped += 1; continue
        bprp = row.get("bp_rp", "")
        bprp = float(bprp) if bprp not in ("", None) else 0.65
        d_ly = 3261.6/par
        u = d_ly/100.0  # scene units
        X = u*math.cos(b)*math.cos(l)   # toward GC
        Y = u*math.cos(b)*math.sin(l)   # east
        Z = u*math.sin(b)               # north
        absM = g + 5*math.log10(par) - 10
        xi = max(-32767, min(32767, round(X*400)))
        yi = max(-32767, min(32767, round(Y*400)))
        zi = max(-32767, min(32767, round(Z*400)))
        ci = max(-127, min(127, round(bprp*40)))
        mi = max(0, min(255, round((absM + 5)*10)))
        recs.append(struct.pack("<hhhbB", xi, yi, zi, ci, mi))

n = len(recs)
blob = b"".join(recs)
b64 = base64.b64encode(blob).decode()
print(f"packed {n} stars ({skipped} skipped), binary {len(blob)/1e6:.2f} MB, base64 {len(b64)/1e6:.2f} MB")

s = open(PATH, encoding="utf-8").read()
s = re.sub(r'const GAIA_B64="[^"]*"', 'const GAIA_B64="' + b64 + '"', s, count=1)
s = re.sub(r'const GAIA_N=\d+;', f'const GAIA_N={n};', s, count=1)
open(PATH, "w", encoding="utf-8", newline="\n").write(s)
print(f"HTML updated, new size {len(s)/1e6:.2f} MB")
