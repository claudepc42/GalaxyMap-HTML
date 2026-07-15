"""Parse Reid 2019 Table 1: G-name (encodes l,b) + parallax + arm code -> JS const."""
import re
from pypdf import PdfReader

SP = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad"
r = PdfReader(SP + r"\reid2019.pdf")

text = ""
for i, p in enumerate(r.pages):
    t = p.extract_text() or ""
    if "Table 1" in t or (30 <= i <= 50):
        text += t + "\n"

# entries like: G305.20+00.01 ... 0 .250 ± 0.050 ... CtN
# pypdf inserts a space inside decimals: "0 .250"
pat = re.compile(
    r"G(\d{3}\.\d{2})([+−\-]\d{2}\.\d{2})"      # l, b from the name
    r".{0,80}?"                                        # alias + RA + Dec (same line)
    r"(\d)\s*\.\s*(\d{3})\s*±\s*\d+\.\d+",        # parallax "0 .250 ± 0.050"
    re.S)
arm_pat = re.compile(r"\b(3kN|3kF|Nor|ScN|ScS|CtN|CtF|OSC|SgN|SgS|CrN|CrF|Per|Loc|LoS|Out|AqS|AqR|GC|CnN|CnX|\?\?\?)\b")

ARM_COLOR = {  # Reid Fig.1 palette-ish (color index)
    "3kN": 0, "3kF": 0,                       # yellow
    "Nor": 1, "Out": 1,                       # red (Norma-Outer)
    "ScN": 2, "ScS": 2, "CtN": 2, "CtF": 2, "OSC": 2,  # blue (Sct-Cen-OSC)
    "SgN": 3, "SgS": 3, "CrN": 3, "CrF": 3,   # purple (Sgr-Car)
    "Loc": 4, "LoS": 4,                        # cyan (Local)
    "Per": 5,                                  # white (Perseus)
}
out = []
lines = text.split("\n")
for i, ln in enumerate(lines):
    m = pat.search(ln)
    if not m:
        continue
    l = float(m.group(1))
    b = float(m.group(2).replace("−", "-"))
    par = float(m.group(3) + "." + m.group(4))
    if par < 0.04:  # nonsense/too far
        continue
    am = arm_pat.findall(ln[m.end():]) or (arm_pat.findall(lines[i+1]) if i+1 < len(lines) else [])
    ci = ARM_COLOR.get(am[0], 6) if am else 6  # 6 = gray/unassigned
    ly = round(3261.6 / par)
    out.append((l, b, ly, ci))

print(f"parsed {len(out)} masers")
from collections import Counter
print("color counts:", Counter(c for _, _, _, c in out))
js = "const MASERS=[" + ",".join(f"[{l},{b},{ly},{c}]" for l, b, ly, c in out) + "];"
open(SP + r"\masers.js", "w").write(js)
print("js bytes:", len(js))
