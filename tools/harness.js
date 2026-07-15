// Stub-DOM harness (HANDOFF §11 pattern): executes the full generation pipeline
// in Node and asserts structural invariants.
'use strict';
const fs = require('fs'), path = require('path');
const DIR = __dirname;

function ctx(){
  return new Proxy({}, { get(o,k){
    if (k === 'createRadialGradient' || k === 'createLinearGradient')
      return () => ({ addColorStop(){} });
    if (typeof k === 'string') return o[k] !== undefined ? o[k] : () => {};
  }, set(o,k,v){ o[k]=v; return true; }});
}
function el(){
  const t = { style:{}, children:[], dataset:{},
    classList:{ add(){}, remove(){}, toggle(){}, contains(){ return false; } } };
  return new Proxy(t, { get(o,k){
    if (k in o) return o[k];
    if (k === 'getContext') return () => ctx();
    if (k === 'querySelectorAll') return () => [];
    if (k === 'querySelector' || k === 'closest' || k === 'appendChild' || k === 'insertBefore')
      return (x) => x && typeof x === 'object' ? x : el();
    if (k === 'getBoundingClientRect') return () => ({left:0,top:0,width:100,height:20,right:100,bottom:20});
    if (k === Symbol.toPrimitive) return () => '';
    if (typeof k === 'string') return () => el();
  }, set(o,k,v){ o[k]=v; return true; }});
}

class V3 {
  constructor(x=0,y=0,z=0){ this.x=x; this.y=y; this.z=z; }
  set(x,y,z){ this.x=x; this.y=y; this.z=z; return this; }
  setScalar(s){ this.x=this.y=this.z=s; return this; }
  setY(y){ this.y=y; return this; }
  copy(v){ this.x=v.x; this.y=v.y; this.z=v.z; return this; }
  clone(){ return new V3(this.x,this.y,this.z); }
  add(v){ this.x+=v.x; this.y+=v.y; this.z+=v.z; return this; }
  sub(v){ this.x-=v.x; this.y-=v.y; this.z-=v.z; return this; }
  addScaledVector(v,s){ this.x+=v.x*s; this.y+=v.y*s; this.z+=v.z*s; return this; }
  multiplyScalar(s){ this.x*=s; this.y*=s; this.z*=s; return this; }
  negate(){ return this.multiplyScalar(-1); }
  length(){ return Math.hypot(this.x,this.y,this.z); }
  lengthSq(){ return this.x*this.x+this.y*this.y+this.z*this.z; }
  normalize(){ const l=this.length()||1; return this.multiplyScalar(1/l); }
  crossVectors(a,b){ this.x=a.y*b.z-a.z*b.y; this.y=a.z*b.x-a.x*b.z; this.z=a.x*b.y-a.y*b.x; return this; }
  distanceTo(v){ return Math.hypot(this.x-v.x,this.y-v.y,this.z-v.z); }
  applyMatrix4(){ return this; }
  project(){ this.z = 0.5; return this; }
  unproject(){ return this; }
}
class Group {
  constructor(){ this.children=[]; this.rotation={x:0,y:0,z:0}; this.position=new V3();
    this.matrixWorld={}; this.visible=true; }
  add(...o){ this.children.push(...o); return this; }
  remove(...o){ o.forEach(x=>{ const i=this.children.indexOf(x); if(i>=0) this.children.splice(i,1); }); return this; }
  clear(){ this.children.length=0; return this; }
  traverse(f){ f(this); this.children.forEach(c=>c.traverse&&c.traverse(f)); }
}
class Mat { constructor(p){ Object.assign(this,p||{}); this.uniforms=this.uniforms||{}; } dispose(){} }
class BufAttr { constructor(arr,sz){ this.array=arr; this.itemSize=sz; this.needsUpdate=false; } }
class BufGeo {
  constructor(){ this.attrs={}; }
  setAttribute(n,a){ this.attrs[n]=a; return this; }
  getAttribute(n){ return this.attrs[n]; }
  setFromPoints(pts){
    const arr = new Float32Array(pts.length*3);
    pts.forEach((p,i)=>{ arr[i*3]=p.x; arr[i*3+1]=p.y; arr[i*3+2]=p.z; });
    return this.setAttribute('position', new BufAttr(arr,3));
  }
  dispose(){}
}
class Obj3D extends Group {
  constructor(mat, geo){ super(); this.material=mat||new Mat(); this.geometry=geo||new BufGeo();
    this.userData={}; this.renderOrder=0; this.scale=new V3(1,1,1); }
}
const THREE = {
  Scene: Group, Group, Vector2: class{constructor(x,y){this.x=x;this.y=y;}}, Vector3: V3,
  PerspectiveCamera: class extends Group { constructor(){ super(); this.aspect=1; }
    updateProjectionMatrix(){} lookAt(){} getWorldDirection(v){ return v.set(0,0,-1); } },
  WebGLRenderer: class { constructor(){ this.domElement=el(); } setPixelRatio(){} setSize(){} render(){} },
  OrbitControls: class { constructor(){ this.target=new V3(); } update(){} },
  EffectComposer: class { constructor(){ this.passes=[]; } addPass(p){ this.passes.push(p); } setSize(){} render(){} },
  RenderPass: class {}, UnrealBloomPass: class { constructor(v,s,r,t){ this.strength=s; this.radius=r; this.threshold=t; } },
  CanvasTexture: class {}, ShaderMaterial: Mat, SpriteMaterial: Mat, PointsMaterial: Mat,
  BufferGeometry: BufGeo, BufferAttribute: BufAttr,
  Points: class extends Obj3D { constructor(g,m){ super(m,g); } },
  Sprite: class extends Obj3D { constructor(m){ super(m); } },
  Raycaster: class { constructor(){ this.params={Points:{}}; } setFromCamera(){} intersectObjects(){ return []; } },
  Clock: class { getDelta(){ return 0.016; } getElapsedTime(){ return 0; } },
  LineBasicMaterial: Mat,
  Line: class extends Obj3D { constructor(g, m){ super(m, g); } },
  AdditiveBlending:2, NormalBlending:1, CustomBlending:5,
  ReverseSubtractEquation:102, SrcAlphaFactor:204, OneFactor:201, Color: class { constructor(){} },
};

globalThis.THREE = THREE;
Object.defineProperty(globalThis, 'navigator', { value: { userAgent: 'node-harness' }, configurable: true });
globalThis.innerWidth = 1920; globalThis.innerHeight = 1080; globalThis.devicePixelRatio = 1;
globalThis.window = globalThis;
globalThis.document = new Proxy({ body: el(), documentElement: el() }, {
  get(o,k){ if (k in o) return o[k];
    if (k === 'createElement') return () => el();
    if (k === 'getElementById') return (id) => (o['#'+id] = o['#'+id] || el());
    if (k === 'querySelectorAll') return () => [];
    if (k === 'querySelector') return () => el();
    if (typeof k === 'string') return () => el();
  }, set(o,k,v){ o[k]=v; return true; }});
globalThis.localStorage = { getItem(){ return null; }, setItem(){}, removeItem(){} };
globalThis.addEventListener = () => {}; globalThis.removeEventListener = () => {};
globalThis.requestAnimationFrame = () => 0; globalThis.cancelAnimationFrame = () => {};
const _si = globalThis.setInterval; globalThis.setInterval = () => 0; globalThis.setTimeout = () => 0;
globalThis.performance = globalThis.performance || { now: () => 0 };

const s0 = fs.readFileSync(path.join(DIR,'script0.js'),'utf8');
const s1 = fs.readFileSync(path.join(DIR,'script1.js'),'utf8');

const verify = `
;(() => {
  const out = [];
  const N = PARAMS.starCount;
  let nan = 0; for (let i=0;i<N*3;i++) if (!Number.isFinite(pos[i])) nan++;
  out.push('stars=' + N + ' NaN=' + nan);
  let s1sum = 0; for (let i=0;i<N*3;i++) s1sum += pos[i];
  buildGalaxy();
  let s2sum = 0; for (let i=0;i<N*3;i++) s2sum += pos[i];
  out.push('determinism ' + (s1sum === s2sum ? 'OK' : 'FAIL ' + s1sum + ' vs ' + s2sum));
  out.push('chains=' + CHAINS.length + ' all-len>0=' + CHAINS.every(C=>C.len>0));
  const ga = gaiaPts.geometry.getAttribute('position').array;
  let gnan = 0; for (const x of ga) if (!Number.isFinite(x)) gnan++;
  out.push('gaiaPts=' + ga.length/3 + ' (expect ' + (GAIA_N + BRIGHT.length) + ') NaN=' + gnan);
  const i0 = GAIA_N*3;
  out.push('Sirius offset from Sun=' + Math.hypot(ga[i0]-SUN.x, ga[i0+1]-SUN.y, ga[i0+2]-SUN.z).toFixed(3) + ' u (expect ~0.09)');
  const nHII = (PARAMS.hiiCount|0) + Math.round(PARAMS.hiiCount*0.6) + REAL_HII.length + REAL_DSO.length + IMG_HII.length;
  out.push('hii sprites=' + hiiList.length + ' (expect ' + nHII + ')');
  out.push('landmarks=' + LANDMARKS.length);
  const spurC = CHAINS.find(c=>c.key==='spur');
  out.push('spur wt=' + spurC.wt + ' width=' + spurC.width + ' hot=' + spurC.hot);
  out.push('SUN=(' + SUN.x.toFixed(1) + ',' + SUN.y.toFixed(2) + ',' + SUN.z.toFixed(1) + ') SUN_D=' + SUN_D);
  // real-HII position spot check: W49A galactocentric radius ~7.6 kpc = ~250 u
  const w49 = hiiScenePos(43.2, 0.0, 36200);
  out.push('W49A R=' + Math.hypot(w49[0], w49[2]).toFixed(1) + ' u (expect ~250)');
  // live-lum: doubling armLum must double arm-star colors without touching others
  const armIdx = cat.findIndex(k=>k===1), othIdx = cat.findIndex(k=>k===0);
  const a0 = col[armIdx*3], o0 = col[othIdx*3];
  PARAMS.armLum *= 2; applyLumScale();
  const ok = Math.abs(col[armIdx*3] - a0*2) < 1e-6 && col[othIdx*3] === o0;
  out.push('live armLum recolor ' + (ok ? 'OK' : 'FAIL'));
  PARAMS.armLum /= 2; applyLumScale();
  out.push('recolor restore ' + (col[armIdx*3] === a0 ? 'OK' : 'FAIL'));
  // determinism must hold across a rebuild AFTER live recolors
  let s3 = 0; buildGalaxy(); for (let i=0;i<N*3;i++) s3 += col[i];
  PARAMS.armLum *= 1.5; applyLumScale(); PARAMS.armLum /= 1.5; applyLumScale();
  let s4 = 0; buildGalaxy(); for (let i=0;i<N*3;i++) s4 += col[i];
  out.push('color determinism after live recolor ' + (s3 === s4 ? 'OK' : 'FAIL'));
  // hii sprites carry base scale for the live hiiSize path
  out.push('hii scl stored on all sprites: ' + hiiList.every(s=>s.userData.scl !== undefined));
  console.log(out.join('\\n'));
})();
`;
try {
  eval(s0 + '\n' + s1 + '\n' + verify);
} catch (e) {
  console.error('HARNESS ERROR:', e && e.stack || e);
  process.exit(1);
}
