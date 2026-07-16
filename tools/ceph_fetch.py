import urllib.request, urllib.parse

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
URL = "https://tapvizier.cds.unistra.fr/TAPVizieR/tap/sync"

def q(adql, fmt="csv"):
    data = urllib.parse.urlencode({"REQUEST": "doQuery", "LANG": "ADQL", "FORMAT": fmt, "QUERY": adql}).encode()
    with urllib.request.urlopen(urllib.request.Request(URL, data=data), timeout=300) as r:
        return r.read().decode()

csv_text = q('SELECT GLON, GLAT, Dist FROM "J/other/Sci/365.478/tables1" WHERE Dist IS NOT NULL')
open(SP + r"\cepheids.csv", "w").write(csv_text)
rows = csv_text.strip().split("\n")[1:]
print(f"{len(rows)} Cepheids with PL distances")

import math
entries = []
for ln in rows:
    l, b, d = ln.split(",")
    ly = float(d) * 3.26156
    entries.append(f"[{float(l):.2f},{float(b):.2f},{round(ly/10)*10}]")
js = "const CEPHEIDS=[" + ",".join(entries) + "];"
open(SP + r"\cepheids.js", "w").write(js)
print("js bytes:", len(js))
