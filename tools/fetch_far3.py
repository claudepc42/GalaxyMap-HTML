import urllib.request, urllib.parse, math, csv, io
SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
URL = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
def q(adql):
    data = urllib.parse.urlencode({"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"csv","QUERY":adql}).encode()
    with urllib.request.urlopen(urllib.request.Request(URL, data=data), timeout=300) as r:
        return r.read().decode()

# globulars
gcs = []
for row in csv.DictReader(io.StringIO(q('SELECT ID, Name, GLON, GLAT, Rsun FROM "VII/202/catalog"'))):
    try:
        l, b, rs = float(row["GLON"]), float(row["GLAT"]), float(row["Rsun"])
    except (ValueError, TypeError):
        continue
    name = (row.get("Name") or "").strip() or row["ID"].strip()
    gcs.append((row["ID"].strip(), name, round(l,2), round(b,2), round(rs*3261.6)))
print("globulars:", len(gcs))
js = "const GLOBULARS=[" + ",".join(f'["{i}","{n}",{l},{b},{ly}]' for i,n,l,b,ly in gcs) + "];"
open(SP + r"\globulars.js", "w").write(js)
print("gc bytes:", len(js), "| sample:", gcs[0], "| max dist:", max(g[4] for g in gcs))

# WISE HII with distances, sorted by physical radius (prominence)
neb = []
for row in csv.DictReader(io.StringIO(q('SELECT Name, GLON, GLAT, Dist, Rad FROM "J/ApJS/212/1/wisecat" WHERE Dist IS NOT NULL'))):
    try:
        l, b, d = float(row["GLON"]), float(row["GLAT"]), float(row["Dist"])
        rad = float(row["Rad"]) if row["Rad"] else 1.0
    except (ValueError, TypeError):
        continue
    ly = d*3261.6
    size_ly = 2*ly*math.tan(math.radians(rad/60.0))  # arcmin -> physical
    neb.append((round(l,2), round(b,2), round(ly), round(size_ly,1)))
neb.sort(key=lambda x: -x[3])
print("wise nebulae with distance:", len(neb), "| biggest:", neb[0], "| median size:", neb[len(neb)//2][3])
js2 = "const NEBULAE=[" + ",".join(f"[{l},{b},{ly},{sz}]" for l,b,ly,sz in neb) + "];"
open(SP + r"\nebulae.js", "w").write(js2)
print("neb bytes:", len(js2))
