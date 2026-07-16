"""Item 9 data: GLOBULARS (Baumgardt), NEBULAE (WISE), dwarfs, curated far objects."""
import urllib.request, urllib.parse, math, csv, io, re

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"

FAMOUS = {"NGC_104":"47 Tucanae","NGC_5139":"Omega Centauri","NGC_6205":"M13 (Hercules Cluster)",
  "NGC_6656":"M22","NGC_6121":"M4","NGC_5904":"M5","NGC_7078":"M15","NGC_6341":"M92",
  "NGC_5272":"M3","NGC_7089":"M2","NGC_2808":"NGC 2808","NGC_6752":"NGC 6752",
  "NGC_6397":"NGC 6397","NGC_6809":"M55","Ter_5":"Terzan 5","Terzan_5":"Terzan 5","NGC_6715":"M54"}

gcs = []
for ln in open(SP + r"\gc_baumgardt.txt"):
    if ln.startswith("#") or not ln.strip(): continue
    p = ln.split()
    try:
        name, l, b, rsun = p[0], float(p[3]), float(p[4]), float(p[5])
    except (ValueError, IndexError):
        continue
    gcs.append((name, round(l,2), round(b,2), round(rsun*3261.6)))
print("globulars:", len(gcs))
gj = "const GLOBULARS=[" + ",".join(
    f'["{FAMOUS.get(n, n.replace("_"," "))}",{l},{b},{ly},{1 if n in FAMOUS else 0}]' for n,l,b,ly in gcs) + "];"

URL = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"
def q(adql):
    data = urllib.parse.urlencode({"REQUEST":"doQuery","LANG":"ADQL","FORMAT":"csv","QUERY":adql}).encode()
    with urllib.request.urlopen(urllib.request.Request(URL, data=data), timeout=300) as r:
        return r.read().decode()
neb = []
for row in csv.DictReader(io.StringIO(q('SELECT GLON, GLAT, Dist, Rad FROM "J/ApJS/212/1/wisecat" WHERE Dist IS NOT NULL'))):
    try:
        l, b, d = float(row["GLON"]), float(row["GLAT"]), float(row["Dist"])
        rad = float(row["Rad"]) if row["Rad"] else 60.0
    except (ValueError, TypeError):
        continue
    ly = d*3261.6
    size = 2*ly*math.tan(math.radians(rad/3600.0))  # Rad in arcsec
    neb.append((round(l,2), round(b,2), round(ly), round(min(9, max(0.5, size/100)),1)))
neb.sort(key=lambda x: -x[3])
print("nebulae:", len(neb), "biggest scene size:", neb[0][3] if neb else "n/a")
nj = "const NEBULAE=[" + ",".join(f"[{l},{b},{ly},{sz}]" for l,b,ly,sz in neb) + "];"

s = open(CUR, encoding="utf-8").read()
anchor = "// ---------- measured maser parallaxes (Reid et al. 2019, Table 1) ----------"
block = f"""// ---------- globular clusters (Baumgardt & Vasiliev, holger-baumgardt.de) ----------
// the full Milky Way globular system: [name, l, b, dist_ly, famousFlag].
// These swarm above/below the disk and behind the core — real 3D halo depth.
{gj}
// ---------- WISE H II star-forming regions with known distances ----------
// (Anderson et al. 2014, J/ApJS/212/1): [l, b, dist_ly, scene_size].
// Sorted biggest-first; the 'nebula density' slider takes a prefix.
{nj}
{anchor}"""
assert s.count(anchor) == 1 and "GLOBULARS" not in s
s = s.replace(anchor, block)

# drop superseded hand-typed gc entries from REAL_DSO
for nm in ("Omega Centauri","47 Tucanae","M13 (Hercules Cluster)","M22","M4","M5","M15"):
    s = re.sub(r"\n\s*\{n:'" + re.escape(nm) + r"'[^\n]*\},", "", s, count=1)
# extend camera reach for outer dwarfs
s = s.replace("controls.minDistance = 25; controls.maxDistance = 3000;",
              "controls.minDistance = 25; controls.maxDistance = 9000;")
# more dwarf satellites (McConnachie 2012 values)
s = s.replace("""  {n:'Sagittarius Dwarf',      l:5.6,   b:-14.2, ly:65000,  s:30, d:'dwarf galaxy being torn apart behind the core'},
];""", """  {n:'Sagittarius Dwarf',      l:5.6,   b:-14.2, ly:65000,  s:30, d:'dwarf galaxy being torn apart behind the core'},
  {n:'Fornax Dwarf',   l:237.1, b:-65.7, ly:460000, s:22, d:'bright dwarf spheroidal with its own globulars'},
  {n:'Sculptor Dwarf', l:287.5, b:-83.2, ly:290000, s:16, d:'first dwarf spheroidal ever found'},
  {n:'Draco Dwarf',    l:86.4,  b:34.7,  ly:260000, s:14, d:'dark-matter-dominated dwarf'},
  {n:'Ursa Minor Dwarf', l:105.0, b:44.8, ly:225000, s:14, d:'faint northern dwarf spheroidal'},
  {n:'Carina Dwarf',   l:260.1, b:-22.2, ly:330000, s:14, d:'dwarf with episodic star formation'},
  {n:'Sextans Dwarf',  l:243.5, b:42.3,  ly:290000, s:14, d:'very diffuse dwarf spheroidal'},
  {n:'Leo I',          l:226.0, b:49.1,  ly:820000, s:16, d:'distant dwarf on the Milky Way frontier'},
  {n:'Leo II',         l:220.2, b:67.2,  ly:690000, s:14, d:'remote companion dwarf'},
];""")
open(CUR, "w", encoding="utf-8", newline="\n").write(s)
print("injected; file", len(s)/1e6, "MB")
