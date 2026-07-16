"""Red-lines gospel: restore the ORIGINAL traced sct/nor/f7 endings from the
pre-Bezier backup. The drawn strokes' sharp-turn/lateral behavior is correct."""
import json, re

CUR = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
BAK = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.backup-2026-07-15.html"

def load(path):
    for line in open(path, encoding="utf-8"):
        if line.startswith("const TRACE = ["):
            return json.loads(re.match(r"const TRACE = (\[.*\]);", line).group(1))

cur = load(CUR)
bak = {c["key"]: c for c in load(BAK)}
by = {c["key"]: c for c in cur}
for key in ("sct", "nor", "f7"):
    by[key]["pts"] = bak[key]["pts"]
    print(f"{key}: restored original traced pts ({len(bak[key]['pts'])})")

with open(CUR, encoding="utf-8") as f:
    lines = f.read().split("\n")
idx = next(i for i, l in enumerate(lines) if l.startswith("const TRACE = ["))
lines[idx] = "const TRACE = " + json.dumps(cur, separators=(",", ":")) + ";"
with open(CUR, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(lines))
print("written")
