import sys

SRC = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
DST = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad\shot.html"

# zoom mode: 'full' = whole disk, 'core' = inner region around the bar
mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
h = {'full': 1600, 'core': 520}[mode]

inject = f"""
<script>
setTimeout(()=>{{
  document.getElementById('help').classList.add('hidden');
  ['panel','devpanel','legend','help-btn','fps'].forEach(id=>{{
    const e=document.getElementById(id); if(e) e.style.display='none';
  }});
  state.labels=false; state.markers=false; state.fps=false; applyState();
  galaxy.rotation.y = 0;
  camera.position.set(0, {h}, 0.001);
  controls.target.set(0,0,0); controls.update();
}}, 800);
</script>
"""
with open(SRC, encoding="utf-8") as f:
    s = f.read()
s = s.replace("</body>", inject + "</body>")
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    f.write(s)
print("shot.html written, mode=" + mode)
