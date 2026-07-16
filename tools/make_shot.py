import sys

SRC = r"C:\Users\ClaudePC\Desktop\Claude\Galaxy Map\galaxy-map.html"
DST = r"C:\Users\ClaudePC\AppData\Local\Temp\claude\C--Users-ClaudePC-Desktop-Claude\583c61fd-6c7b-4236-a88e-112472cbc3ad\scratchpad\shot.html"

# zoom mode: 'full' = whole disk, 'core' = inner region around the bar
mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
h = {'full': 1600, 'mid': 950, 'core': 520, 'spine': 950}[mode]

spine_params = ""
if mode == 'spine':
    # the user's arm-spine QC recipe: black background, thin bright centerlines
    spine_params = """
  Object.assign(PARAMS, {minPt:1.6, sizeMult:0.5, hazeOp:0, dustOp:0, gaiaBias:0.15,
    gaiaDim:0.3, widthMult:0.3, armLum:2.5, armScatter:0.3, hotMult:2.5, clumpFrac:0,
    fray:0.01, armShare:0.8, starCount:400000, bulgeShare:0.3, zSpread:0.3, diskGlow:0,
    nebDensity:0, hiiCount:0, hazeCount:0, edgeStart:0.5});
  bloom.strength = 0;
  state.clouds=false; state.background=false; state.bloom=false; state.gaia=true;
  buildGalaxy(); applyLive();"""

inject = f"""
<script>
setTimeout(()=>{{
  document.getElementById('help').classList.add('hidden');
  ['panel','devpanel','legend','help-btn','fps'].forEach(id=>{{
    const e=document.getElementById(id); if(e) e.style.display='none';
  }});
  state.labels=false; state.markers=false; state.fps=false; applyState();
  galaxy.rotation.y = 0;{spine_params}
  camera.position.set(0, -{h}, 0.001);  // below the plane = NASA orientation
  controls.target.set(0,0,0); controls.update();
  applyState();
}}, 800);
</script>
"""
with open(SRC, encoding="utf-8") as f:
    s = f.read()
s = s.replace("</body>", inject + "</body>")
with open(DST, "w", encoding="utf-8", newline="\n") as f:
    f.write(s)
print("shot.html written, mode=" + mode)
