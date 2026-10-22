// Sitka render two viewer. Bundled to cad/viewer/sitka_viewer.bundle.js (classic script, works from file://).
// Data comes from cad/viewer/sitka_data.js (window.SITKA_DATA: base64 GLBs + pose transforms).
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

const D = window.SITKA_DATA;
const Q = new URLSearchParams(location.search);
const state = {
  pose: Q.get('pose') || 'stand',
  basic: Q.get('basic') !== '0',
  coupling: Q.get('coupling') !== '0',
  upgrade: Q.get('upg') || 'ghost',      // off | ghost | on
  body: Q.get('body') || 'on',           // on | ghost | off
  explode: parseFloat(Q.get('explode') || '0'),
  labels: Q.get('labels') !== '0',
  view: Q.get('view') || '34',
};

// ---------- renderer / scene ----------
const wrap = document.getElementById('stage');
const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.toneMapping = THREE.AgXToneMapping;
renderer.toneMappingExposure = 1.05;
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
wrap.appendChild(renderer.domElement);

const scene = new THREE.Scene();
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;
scene.environmentIntensity = 0.55;

// soft studio gradient backdrop
{
  const c = document.createElement('canvas'); c.width = 2; c.height = 256;
  const g = c.getContext('2d'); const gr = g.createLinearGradient(0, 0, 0, 256);
  gr.addColorStop(0, '#d9dde2'); gr.addColorStop(0.62, '#b9bfc6'); gr.addColorStop(1, '#9ea5ad');
  g.fillStyle = gr; g.fillRect(0, 0, 2, 256);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace;
  scene.background = t;
}
const camera = new THREE.PerspectiveCamera(30, 1, 0.05, 50);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.08;
controls.target.set(0, 0.95, 0);
controls.minDistance = 0.4; controls.maxDistance = 9;

const hemi = new THREE.HemisphereLight(0xf4f6ff, 0x5a5550, 0.55); scene.add(hemi);
const key = new THREE.DirectionalLight(0xfff4ea, 2.2);
key.position.set(-2.2, 4.2, 2.6); key.castShadow = true;
key.shadow.mapSize.set(2048, 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
Object.assign(key.shadow.camera, { left: -1.4, right: 1.4, top: 2.2, bottom: -0.3, near: 0.5, far: 10 });
scene.add(key);
const rim = new THREE.DirectionalLight(0xe8f0ff, 1.3); rim.position.set(1.5, 2.8, -3.2); scene.add(rim);
const fill = new THREE.DirectionalLight(0xffffff, 0.5); fill.position.set(3, 1.5, 2); scene.add(fill);
const ground = new THREE.Mesh(new THREE.CircleGeometry(4, 64), new THREE.ShadowMaterial({ opacity: 0.22 }));
ground.rotation.x = -Math.PI / 2; ground.receiveShadow = true; scene.add(ground);
const disc = new THREE.Mesh(new THREE.RingGeometry(0.0, 1.1, 96),
  new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.10 }));
disc.rotation.x = -Math.PI / 2; disc.position.y = 0.0005; scene.add(disc);

// ---------- materials: matte PBR studio look ----------
function tuneMaterial(m, name) {
  if (!m) return m;
  const n = (m.name || name || '').toLowerCase();
  if (n === 'carbon' || n === 'carbon_gloss') {
    m.color.set(n === 'carbon' ? 0x1d1f23 : 0x17191c);
    m.roughness = n === 'carbon' ? 0.42 : 0.28; m.metalness = 0.0;
    if ('clearcoat' in m) { m.clearcoat = 0.8; m.clearcoatRoughness = 0.18; }
  } else if (n === 'alu') { m.color.set(0xa8adb3); m.metalness = 1; m.roughness = 0.32; }
  else if (n === 'accent') { m.color.set(0xd2602a); m.metalness = 0.75; m.roughness = 0.36; }
  else if (n === 'leaf') { m.color.set(0x253a52); m.metalness = 0.0; m.roughness = 0.3; if ('clearcoat' in m) m.clearcoat = 1; }
  else if (n === 'foam') { m.color.set(0x8f959c); m.roughness = 0.95; m.metalness = 0; }
  else if (n === 'fabric') { m.color.set(0x2b2f35); m.roughness = 0.9; m.metalness = 0; }
  else if (n === 'cable') { m.color.set(0xdca540); m.roughness = 0.45; m.metalness = 0.1; }
  else if (n === 'band') { m.color.set(0x2e918b); m.roughness = 0.55; m.metalness = 0; }
  else if (n === 'latex') { m.color.set(0xcb7d38); m.roughness = 0.45; }
  else if (n === 'bowden') { m.color.set(0x0e0f11); m.roughness = 0.3; }
  else if (n === 'motor') { m.color.set(0x41464d); m.metalness = 1; m.roughness = 0.38; }
  else if (n === 'electronics') { m.color.set(0x27292e); m.roughness = 0.45; }
  else if (n === 'rubber') { m.color.set(0x141516); m.roughness = 0.85; }
  else if (n === 'shoe') { m.color.set(0x60656c); m.roughness = 0.88; }
  else if (n === 'body') { m.color.set(0xcfc8bf); m.roughness = 0.78; m.metalness = 0; }
  m.envMapIntensity = 1.0;
  return m;
}
const ghostMat = new THREE.MeshStandardMaterial({ color: 0x7fb2ff, transparent: true, opacity: 0.28, roughness: 0.4, depthWrite: false });
const bodyGhost = new THREE.MeshStandardMaterial({ color: 0xcfc8bf, transparent: true, opacity: 0.22, roughness: 0.8, depthWrite: false });

// ---------- load ----------
const loader = new GLTFLoader();
function b64(s) { const bin = atob(s); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u.buffer; }
function loadGLB(s) { return new Promise((res, rej) => loader.parse(b64(s), '', res, rej)); }

const ZUP = new THREE.Matrix4().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1); // blender z-up -> three y-up
const ZUPi = ZUP.clone().invert();
const parts = {};       // name -> {obj, meta, dirLocal}
const bodies = {}, cables = {};
const partRoot = new THREE.Group(); scene.add(partRoot);
let ready = false;

function prepMeshes(root, cast = true) {
  root.traverse(o => {
    if (o.isMesh) {
      o.castShadow = cast; o.receiveShadow = true;
      o.material = tuneMaterial(o.material);
      o.userData.baseMat = o.material;
    }
  });
}

async function init() {
  const g = await loadGLB(D.parts);
  // every top-level node is a part in its local (segment) frame
  const kids = [...g.scene.children];
  for (const o of kids) {
    const meta = (D.poses.parts_meta || {})[o.name] || o.userData || {};
    prepMeshes(o);
    const holder = new THREE.Group(); holder.name = o.name; holder.matrixAutoUpdate = false;
    // the glTF exporter converted the local frame to y-up: undo it so pose matrices (z-up) apply directly
    o.applyMatrix4(ZUPi);
    holder.add(o);
    partRoot.add(holder);
    const box = new THREE.Box3().setFromObject(o);
    const c = box.getCenter(new THREE.Vector3());
    let dir = new THREE.Vector3(c.x, c.y, 0);
    if (o.name.startsWith('strut')) dir.set(0, 0, 0);
    if (dir.length() < 1e-4) dir.set(0, 0, 0); else dir.normalize();
    parts[o.name] = { obj: holder, meta: { ...o.userData, ...meta }, dirLocal: dir, centerLocal: c };
  }
  for (const p of Object.keys(D.bodies)) {
    const gb = await loadGLB(D.bodies[p]); prepMeshes(gb.scene); gb.scene.visible = false; scene.add(gb.scene); bodies[p] = gb.scene;
    const gc = await loadGLB(D.cables[p]); prepMeshes(gc.scene); gc.scene.visible = false; scene.add(gc.scene); cables[p] = gc.scene;
  }
  partRoot.matrixAutoUpdate = false; partRoot.matrix.copy(ZUP);
  ready = true;
  buildUI(); buildAnimUI(); apply(); setView(state.view, true);
  document.getElementById('loading').style.display = 'none';
  if (!Q.get('anim')) window.__ready = true;
}

function moduleVisible(mod, requires) {
  const v = m => m === 'basic' ? state.basic : m === 'coupling' ? state.coupling : m === 'upgrade' ? state.upgrade !== 'off' : true;
  if (!v(mod)) return false;
  if (requires && !v(requires)) return false;
  return true;
}
function isGhost(mod, requires) { return (mod === 'upgrade' || requires === 'upgrade') && state.upgrade === 'ghost'; }

function apply() {
  if (!ready) return;
  if (anim.on) { renderAnimAt(anim.t); updateButtons(); return; }
  const P = state.pose;
  const T = D.poses.parts[P];
  const ex = state.explode;
  for (const [name, p] of Object.entries(parts)) {
    const m = T[name];
    const mod = p.meta.module || 'basic';
    const show = !!m && (mod === 'body' ? state.body !== 'off' : moduleVisible(mod, p.meta.requires));
    p.obj.visible = show;
    if (!m) continue;
    const M = new THREE.Matrix4().set(...m.flat());
    if (ex > 0 && p.dirLocal.lengthSq() > 0) {
      const d = p.dirLocal.clone().transformDirection(M).multiplyScalar(ex * 0.16);
      M.premultiply(new THREE.Matrix4().makeTranslation(d.x, d.y, d.z));
    }
    p.obj.matrix.copy(M); p.obj.matrixWorldNeedsUpdate = true;
    const ghost = isGhost(mod, p.meta.requires);
    p.obj.traverse(o => { if (o.isMesh) { o.material = ghost ? ghostMat : o.userData.baseMat; o.castShadow = !ghost; } });
  }
  for (const [p, b] of Object.entries(bodies)) {
    b.visible = p === P && state.body !== 'off';
    b.traverse(o => { if (o.isMesh) { o.material = state.body === 'ghost' ? bodyGhost : o.userData.baseMat; o.castShadow = state.body === 'on'; } });
  }
  for (const [p, c] of Object.entries(cables)) {
    c.visible = p === P && ex < 0.02;
    c.traverse(o => {
      if (!o.isMesh) return;
      const ud = o.userData && Object.keys(o.userData).length ? o.userData : (o.parent && o.parent.userData) || {};
      const mod = ud.module || 'basic';
      o.visible = moduleVisible(mod, ud.requires);
      const ghost = isGhost(mod, ud.requires);
      o.material = ghost ? ghostMat : o.userData.baseMat; o.castShadow = !ghost;
    });
  }
  // the shoe belongs with the body toggle
  updateReadout(); updateButtons();
}

// ---------- views ----------
const VIEWS = { front: [0, 0.08, 1], side: [1, 0.06, 0], back: [0, 0.10, -1], '34': [0.78, 0.30, 0.78], top: [0.2, 1.6, 0.4] };
function bodyBox() {
  const b = bodies[state.pose]; const box = new THREE.Box3();
  if (b) box.setFromObject(b); else box.set(new THREE.Vector3(-0.4, 0, -0.4), new THREE.Vector3(0.4, 1.9, 0.4));
  return box;
}
function setView(v, instant) {
  state.view = v;
  const box = bodyBox(); const c = box.getCenter(new THREE.Vector3()); const s = box.getSize(new THREE.Vector3());
  const d = new THREE.Vector3(...VIEWS[v]).normalize();
  const fit = Math.max(s.y, s.x * 1.2, s.z * 1.2) * 0.5 / Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * 1.12;
  controls.target.copy(c);
  camera.position.copy(c).addScaledVector(d, fit + 0.2);
  camera.updateProjectionMatrix(); controls.update();
  updateButtons();
}
const camQ = Q.get('cam');
function applyCamParam() {
  if (!camQ) return;
  const v = camQ.split(',').map(Number);
  camera.position.set(v[0], v[1], v[2]); controls.target.set(v[3], v[4], v[5]); controls.update();
}

// ---------- labels ----------
const labelLayer = document.getElementById('labels');
const svg = document.getElementById('leaders');
function drawLabels() {
  labelLayer.innerHTML = ''; svg.innerHTML = '';
  if (!state.labels || !ready) return;
  const W = renderer.domElement.clientWidth, H = renderer.domElement.clientHeight;
  const items = [];
  const seen = new Set();
  const consider = (name, label, obj, worldPos) => {
    if (!label || seen.has(label)) return;
    const p = worldPos.clone().project(camera);
    if (p.z > 1 || Math.abs(p.x) > 1.05 || Math.abs(p.y) > 1.05) return;
    seen.add(label);
    items.push({ label, x: (p.x + 1) / 2 * W, y: (1 - p.y) / 2 * H });
  };
  const KEY = /^(thigh_shell|seat_cup_[lr]$|strut_tube0|knee_arc|knee_manifold|sit_leaf_[lr]$|hip_belt|back_panel$|m2_leaf$|whiffletree|knee_hub_lat|ptb_shell|thigh_cuff_[lr]$|p1_motor|m5_cassette|m4_heelclip|ea_clutch)/;
  const KEYC = /^(t1_tendon|t3_tendon|m3_band|crazycreek|hamstring_band|running_band|harness_l|bowden_l)/;
  for (const [name, p] of Object.entries(parts)) {
    if (!p.obj.visible || !p.meta.label || !KEY.test(name)) continue;
    if (p.meta.module === 'upgrade' && state.upgrade === 'off') continue;
    // label the side facing the camera: prefer _l in side views facing +x, else whichever is nearer
    const wp = p.centerLocal.clone().applyMatrix4(p.obj.matrix).applyMatrix4(partRoot.matrix);
    items.push({ label: p.meta.label, x: 0, y: 0, wp, name, dist: wp.distanceTo(camera.position) });
  }
  const c = cables[state.pose];
  if (c && c.visible) c.traverse(o => {
    if (!o.isMesh || !o.visible) return;
    const ud = Object.keys(o.userData || {}).length ? o.userData : (o.parent && o.parent.userData) || {};
    if (!ud.label || !KEYC.test(o.name)) return;
    o.geometry.computeBoundingBox();
    const bb = o.geometry.boundingBox; const ctr = bb.getCenter(new THREE.Vector3());
    const wp = ctr.applyMatrix4(o.matrixWorld);
    items.push({ label: ud.label + (ud.state ? ' · ' + ud.state : ''), wp, name: o.name, dist: wp.distanceTo(camera.position) });
  });
  // one label per text, nearest instance wins
  const best = {};
  for (const it of items) { if (!it.wp) continue; if (!best[it.label] || it.dist < best[it.label].dist) best[it.label] = it; }
  const list = [];
  for (const it of Object.values(best)) {
    const p = it.wp.clone().project(camera);
    if (p.z > 1 || Math.abs(p.x) > 1.0 || Math.abs(p.y) > 1.0) continue;
    list.push({ ...it, x: (p.x + 1) / 2 * W, y: (1 - p.y) / 2 * H });
  }
  const cx = W / 2;
  const left = list.filter(i => i.x < cx).sort((a, b) => a.y - b.y);
  const right = list.filter(i => i.x >= cx).sort((a, b) => a.y - b.y);
  const lh = 22;
  const place = (arr, side) => {
    let y = 70;
    for (const it of arr) { it.ly = Math.max(y, it.y); y = it.ly + lh; }
    const over = y - (H - 20);
    if (over > 0) for (const it of arr) it.ly -= over * (it.ly / y);
    for (const it of arr) {
      const el = document.createElement('div'); el.className = 'lbl ' + side; el.textContent = it.label;
      labelLayer.appendChild(el);
      const lx = side === 'l' ? 16 : W - 16 - el.offsetWidth;
      el.style.left = lx + 'px'; el.style.top = (it.ly - 10) + 'px';
      const ex = side === 'l' ? lx + el.offsetWidth : lx;
      const ln = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      ln.setAttribute('d', `M${ex},${it.ly} L${ex + (side === 'l' ? 14 : -14)},${it.ly} L${it.x},${it.y}`);
      svg.appendChild(ln);
      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', it.x); dot.setAttribute('cy', it.y); dot.setAttribute('r', 2.6);
      svg.appendChild(dot);
    }
  };
  place(left, 'l'); place(right, 'r');
}

// ---------- hover ----------
const ray = new THREE.Raycaster(); const mouse = new THREE.Vector2(); const tip = document.getElementById('tip');
renderer.domElement.addEventListener('pointermove', e => {
  const r = renderer.domElement.getBoundingClientRect();
  mouse.set((e.clientX - r.left) / r.width * 2 - 1, -(e.clientY - r.top) / r.height * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const objs = [partRoot, cables[state.pose]].filter(Boolean);
  const hit = ray.intersectObjects(objs, true).find(h => h.object.visible && isVis(h.object));
  if (hit) {
    let o = hit.object; let name = o.name; let ud = o.userData || {};
    while (o && !parts[o.name] && o.parent && o.parent !== partRoot) o = o.parent;
    if (parts[o.name]) { name = o.name; ud = parts[o.name].meta; }
    const lbl = ud.label || ud.group || name;
    tip.style.display = 'block'; tip.style.left = (e.clientX + 14) + 'px'; tip.style.top = (e.clientY + 10) + 'px';
    tip.innerHTML = `<b>${lbl}</b><span>${name} · ${ud.module || ''}${ud.state ? ' · ' + ud.state : ''}</span>`;
  } else tip.style.display = 'none';
});
function isVis(o) { while (o) { if (!o.visible) return false; o = o.parent; } return true; }

// ---------- UI ----------
function btn(parent, text, on, cls = '') { const b = document.createElement('button'); b.textContent = text; b.className = cls; b.onclick = on; parent.appendChild(b); return b; }
const ui = {};
function buildUI() {
  const pr = document.getElementById('poses');
  ui.poses = {};
  for (const p of Object.keys(D.poses.poses)) ui.poses[p] = btn(pr, D.poses.poses[p].label, () => { state.pose = p; apply(); });
  const vr = document.getElementById('views'); ui.views = {};
  for (const [k, t] of [['front', 'Front'], ['side', 'Side'], ['back', 'Back'], ['34', '3/4']]) ui.views[k] = btn(vr, t, () => setView(k));
  const mr = document.getElementById('mods');
  ui.basic = btn(mr, 'Basic (passive)', () => { state.basic = !state.basic; apply(); });
  ui.coupling = btn(mr, 'Couplings', () => { state.coupling = !state.coupling; apply(); });
  ui.upgrade = btn(mr, 'Upgrades: ghost', () => { state.upgrade = { off: 'ghost', ghost: 'on', on: 'off' }[state.upgrade]; apply(); });
  ui.body = btn(mr, 'Full body: on', () => { state.body = { on: 'ghost', ghost: 'off', off: 'on' }[state.body]; apply(); });
  ui.labels = btn(mr, 'Labels', () => { state.labels = !state.labels; updateButtons(); });
  const ex = document.getElementById('explode'); ex.value = state.explode;
  ex.oninput = () => { state.explode = parseFloat(ex.value); apply(); };
}
function updateButtons() {
  if (!ui.poses) return;
  for (const [p, b] of Object.entries(ui.poses)) b.classList.toggle('on', p === state.pose);
  for (const [v, b] of Object.entries(ui.views)) b.classList.toggle('on', v === state.view);
  ui.basic.classList.toggle('on', state.basic); ui.coupling.classList.toggle('on', state.coupling);
  ui.upgrade.textContent = 'Upgrades: ' + state.upgrade; ui.upgrade.classList.toggle('on', state.upgrade !== 'off');
  ui.body.textContent = 'Full body: ' + state.body; ui.body.classList.toggle('on', state.body !== 'off');
  ui.labels.classList.toggle('on', state.labels);
}
function updateReadout() {
  const P = D.poses.poses[state.pose];
  const C = D.poses.cables[state.pose] || {};
  const pick = (k) => (C[k + '_l'] || C[k] || {}).state || '';
  const rows = [
    ['Mode', P.mode],
    ['Knee tendon T1', pick('t1_tendon')],
    ['Lift tendon M2', pick('t3_tendon')],
    ['Hip band M3', pick('m3_band')],
    ['Strut', P.mode === 'SIT' ? 'deployed, 4° back, 9° out' : 'stowed along the thigh'],
    ['Crazy Creek', pick('crazycreek')],
    ['Hamstring band', state.coupling ? pick('hamstring_band') : 'not docked'],
  ];
  if (C.running_band) rows.push(['Running band', C.running_band.state]);
  document.getElementById('readout').innerHTML = `<div class="ttl">${P.label}</div>` +
    rows.filter(r => r[1]).map(r => `<div class="row"><span>${r[0]}</span><b>${r[1]}</b></div>`).join('');
}


// =====================================================================================
// ANIMATION: walk / run cycles, sit-down, stand-up, stoop-lift (baked frames from Blender:
// cad/viewer/sitka_anim.js) and a viewer-side "kit" sequence where the modules dock one by one.
// =====================================================================================
const SEQS = [['walk', 'Walk cycle'], ['run', 'Run cycle'], ['sitdown', 'Sit down'], ['standup', 'Stand up'], ['stoop', 'Stoop lift'], ['kit', 'Kit: modules dock']];
const SEQ_FPS = { walk: 28, run: 30, sitdown: 14, standup: 14, stoop: 14 };
const anim = { on: false, seq: null, t: 0, playing: false, speed: 1, data: null, body: null, cables: {}, root: null };
const animRoot = new THREE.Group(); animRoot.matrixAutoUpdate = false; animRoot.matrix.copy(ZUP); scene.add(animRoot);
const GLOW = { load: new THREE.Color(0xff7a1a), ret: new THREE.Color(0x27e0c0), lock: new THREE.Color(0xff3344), gate: new THREE.Color(0x46a8ff), band: new THREE.Color(0x3fe0a8), strap: new THREE.Color(0xffc233) };

function loadAnimData() {
  return new Promise((res, rej) => {
    if (window.SITKA_ANIM) return res(window.SITKA_ANIM);
    const sc = document.createElement('script'); sc.src = 'cad/viewer/sitka_anim.js';
    sc.onload = () => res(window.SITKA_ANIM); sc.onerror = rej; document.head.appendChild(sc);
  });
}
function i16(b64) { const b = b64ToU8(b64); return new Int16Array(b.buffer, b.byteOffset, b.byteLength / 2); }
function i8(b64) { const b = b64ToU8(b64); return new Int8Array(b.buffer, b.byteOffset, b.byteLength); }
function b64ToU8(s) { const bin = atob(s); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u; }

let AD = null;
async function ensureAnim() {
  if (AD) return AD;
  document.getElementById('loading').style.display = 'grid'; document.getElementById('loading').textContent = 'Loading animation…';
  const A = await loadAnimData();
  AD = { A, body: i16(A.body_b64), cab: i16(A.cab_b64), nrm: A.nrm_b64 ? i8(A.nrm_b64) : new Int8Array(0) };
  // body mesh
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(new Float32Array(A.nv * 3), 3));
  g.setIndex(A.tris);
  const bm = tuneMaterial(new THREE.MeshStandardMaterial({ name: 'body' }));
  anim.body = new THREE.Mesh(g, bm); anim.body.castShadow = true; anim.body.receiveShadow = true;
  anim.body.userData.baseMat = bm;
  animRoot.add(anim.body);
  // cables
  for (const [name, c] of Object.entries(A.cables)) {
    const seg = c.r ? 10 : 8; const n = A.nres;
    const geo = new THREE.BufferGeometry();
    geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(n * seg * 3), 3));
    const idx = [];
    for (let i = 0; i < n - 1; i++) for (let k = 0; k < seg; k++) {
      const a = i * seg + k, b = i * seg + (k + 1) % seg, c2 = (i + 1) * seg + (k + 1) % seg, d = (i + 1) * seg + k;
      idx.push(a, b, c2, a, c2, d);
    }
    geo.setIndex(idx);
    const m = tuneMaterial(new THREE.MeshStandardMaterial({ name: c.mat }));
    const mesh = new THREE.Mesh(geo, m); mesh.castShadow = true; mesh.frustumCulled = false;
    mesh.userData = { ...c, baseMat: m, name };
    anim.cables[name] = mesh; animRoot.add(mesh);
  }
  document.getElementById('loading').style.display = 'none';
  return AD;
}

const _v = new THREE.Vector3(), _n = new THREE.Vector3(), _t = new THREE.Vector3(), _b = new THREE.Vector3();
function cablePoints(off, f) { return off; }
function setCable(mesh, P, N) {
  const c = mesh.userData; const n = AD.A.nres; const pos = mesh.geometry.attributes.position.array;
  const seg = c.r ? 10 : 8;
  let prevSide = null;
  for (let i = 0; i < n; i++) {
    const i0 = Math.max(0, i - 1), i1 = Math.min(n - 1, i + 1);
    _t.set(P[i1 * 3] - P[i0 * 3], P[i1 * 3 + 1] - P[i0 * 3 + 1], P[i1 * 3 + 2] - P[i0 * 3 + 2]);
    if (_t.lengthSq() < 1e-14) _t.set(0, 0, 1);
    _t.normalize();
    if (N) _n.set(N[i * 3], N[i * 3 + 1], N[i * 3 + 2]);
    else if (prevSide) _n.copy(prevSide);
    else { _n.set(0, 0, 1); if (Math.abs(_t.z) > 0.9) _n.set(1, 0, 0); }
    _n.addScaledVector(_t, -_n.dot(_t)); if (_n.lengthSq() < 1e-10) _n.set(1, 0, 0); _n.normalize();
    prevSide = prevSide || new THREE.Vector3(); prevSide.copy(_n);
    _b.crossVectors(_t, _n).normalize();
    for (let k = 0; k < seg; k++) {
      const a = 2 * Math.PI * (k + 0.5) / seg;
      let ex, ey;
      if (c.r) { ex = Math.cos(a) * c.r; ey = Math.sin(a) * c.r; }
      else { const cx = Math.cos(a), cy = Math.sin(a); ex = Math.sign(cx) * Math.pow(Math.abs(cx), 0.35) * c.w / 2; ey = Math.sign(cy) * Math.pow(Math.abs(cy), 0.35) * c.t / 2; }
      const o = (i * seg + k) * 3;
      pos[o] = P[i * 3] + _b.x * ex + _n.x * ey; pos[o + 1] = P[i * 3 + 1] + _b.y * ex + _n.y * ey; pos[o + 2] = P[i * 3 + 2] + _b.z * ex + _n.z * ey;
    }
  }
  mesh.geometry.attributes.position.needsUpdate = true;
  mesh.geometry.computeVertexNormals();
  mesh.geometry.computeBoundingSphere();
}

const _m0 = new THREE.Matrix4(), _m1 = new THREE.Matrix4(), _p0 = new THREE.Vector3(), _p1 = new THREE.Vector3(),
  _q0 = new THREE.Quaternion(), _q1 = new THREE.Quaternion(), _s = new THREE.Vector3();
function m12(a) { return _m0.set(a[0], a[1], a[2], a[3], a[4], a[5], a[6], a[7], a[8], a[9], a[10], a[11], 0, 0, 0, 1); }

function applyAnimFrame(seqName, tf) {
  const S = AD.A.seqs[seqName]; const n = S.n;
  let i0 = Math.floor(tf), fr = tf - i0;
  let i1 = i0 + 1;
  if (S.loop) { i0 = ((i0 % n) + n) % n; i1 = (i0 + 1) % n; }
  else { i0 = Math.min(n - 1, Math.max(0, i0)); i1 = Math.min(n - 1, i0 + 1); if (tf >= n - 1) fr = 0; }
  // body
  const NV = AD.A.nv, pos = anim.body.geometry.attributes.position.array, B = AD.body;
  const o0 = (S.start + i0) * NV * 3, o1 = (S.start + i1) * NV * 3;
  for (let k = 0; k < NV * 3; k++) pos[k] = (B[o0 + k] * (1 - fr) + B[o1 + k] * fr) * 1e-4;
  anim.body.geometry.attributes.position.needsUpdate = true;
  anim.body.geometry.computeVertexNormals(); anim.body.geometry.computeBoundingSphere();
  // parts
  const names = AD.A.parts, F0 = S.parts[i0], F1 = S.parts[i1];
  for (let k = 0; k < names.length; k++) {
    const p = parts[names[k]]; if (!p) continue;
    m12(F0[k]).decompose(_p0, _q0, _s); _m1.set(...F1[k], 0, 0, 0, 1).decompose(_p1, _q1, _s);
    _p0.lerp(_p1, fr); _q0.slerp(_q1, fr);
    p.obj.matrix.compose(_p0, _q0, _s.set(1, 1, 1)); p.obj.matrixWorldNeedsUpdate = true;
  }
  // cables (present in both frames -> blend, else take the nearer)
  const C0 = S.cables[i0], C1 = S.cables[i1];
  const map1 = {}; for (const c of C1) map1[c.name] = c;
  const nres = AD.A.nres; const P = new Float32Array(nres * 3); const N = new Float32Array(nres * 3);
  const seen = new Set();
  for (const c of (fr < 0.5 ? C0 : C1)) seen.add(c.name);
  for (const [name, mesh] of Object.entries(anim.cables)) {
    if (!seen.has(name)) { mesh.visible = false; continue; }
    const a = C0.find(x => x.name === name), b = map1[name];
    const A0 = a || b, A1 = b || a; const w = (a && b) ? fr : 0;
    for (let k = 0; k < nres * 3; k++) P[k] = (AD.cab[A0.o + k] * (1 - w) + AD.cab[A1.o + k] * w) * 1e-4;
    let useN = null;
    if (A0.no !== undefined) { for (let k = 0; k < nres * 3; k++) N[k] = AD.nrm[A0.no + k] / 127; useN = N; }
    setCable(mesh, P, useN);
    const ud = mesh.userData;
    mesh.visible = moduleVisible(ud.module, ud.requires);
    mesh.material = isGhost(ud.module, ud.requires) ? ghostMat : ud.animMat || ud.baseMat;
  }
  // engagement glow
  const st = S.states[fr < 0.5 ? i0 : i1] || {};
  glow(st);
  hud(seqName, st, i0, n);
}

const GLOW_TARGETS = {
  ea_l: [['ea_clutch_l'], 'gate'], ea_r: [['ea_clutch_r'], 'gate'],
  m3_l: [['~m3_band_l'], 'band'], m3_r: [['~m3_band_r'], 'band'],
  ham_l: [['~hamstring_band_l'], 'band'], ham_r: [['~hamstring_band_r'], 'band'],
  runband: [['~running_band'], 'band'],
  sit_leaf: [['sit_leaf_l', 'sit_leaf_r', 'sit_leaf_link_l', 'sit_leaf_link_r', '~t1_tendon_l', '~t1_tendon_r'], 'load'],
  sit_leaf_lift: [['sit_leaf_l', 'sit_leaf_r'], 'load'],
  sit_return: [['sit_leaf_l', 'sit_leaf_r', 'sit_leaf_link_l', 'sit_leaf_link_r', '~t1_tendon_l', '~t1_tendon_r'], 'ret'],
  lock: [['knee_manifold_l', 'knee_manifold_r', 'mode_lever_l', 'mode_lever_r'], 'lock'],
  cc: [['~crazycreek_l', '~crazycreek_r'], 'strap'],
  t3_load: [['m2_leaf', 'whiffletree', '~t3_tendon_l', '~t3_tendon_r'], 'load'],
  t3_return: [['m2_leaf', 'whiffletree', '~t3_tendon_l', '~t3_tendon_r'], 'ret'],
};
const glowMats = new Map();
function glowMat(obj) {
  if (!glowMats.has(obj)) {
    const ms = [];
    obj.traverse(o => { if (o.isMesh) { const m = (o.userData.baseMat || o.material).clone(); o.userData.animMat = m; ms.push(m); } });
    glowMats.set(obj, ms);
  }
  return glowMats.get(obj);
}
function glow(st) {
  for (const ms of glowMats.values()) for (const m of ms) { m.emissive && m.emissive.setRGB(0, 0, 0); m.emissiveIntensity = 0; }
  for (const [k, v] of Object.entries(st)) {
    const tg = GLOW_TARGETS[k]; if (!tg || !(v > 0.01)) continue;
    for (const name of tg[0]) {
      const obj = name.startsWith('~') ? anim.cables[name.slice(1)] : (parts[name] && parts[name].obj);
      if (!obj) continue;
      for (const m of glowMat(obj)) { m.emissive.copy(GLOW[tg[1]]); m.emissiveIntensity = 0.25 + 1.6 * v; }
      obj.traverse(o => { if (o.isMesh && o.userData.animMat && o.material !== ghostMat) o.material = o.userData.animMat; });
      if (obj.userData && obj.userData.animMat && obj.material !== ghostMat) obj.material = obj.userData.animMat;
    }
  }
}
const HUD_TXT = {
  walk: 'Walking: no motor. Hip bands stretch in late stance and swing the leg; the stance clutch gates the knee leaf (smart tier); the hamstring band brakes late swing.',
  run: 'Running: every clutch open. The shin-to-shin running band (−6.4%) and the hip bands do the work.',
  sitdown: 'Sit down: the strut swings down and plants; the sit leaf loads 44 J through the 80 mm arc; the cam locks with no power; the Crazy Creek straps take the 10° recline.',
  standup: 'Stand up: the cam opens, the sit leaf gives ~40 J back (28 Nm per knee), the strut retracts and stows along the thigh.',
  stoop: 'Stoop lift: the lift tendon is slack until 35°, then loads the M2 leaf through the whiffletree (60 Nm, the box feels ~12 kg lighter) and gives it back on the lift.',
  kit: 'Kit: everything docks to the hub. Dock → M1 knee/seat → M2 lift → M3 hip → couplings → upgrades.',
};
const HUD_ROWS = [['sit_leaf', 'Sit leaf loading'], ['sit_return', 'Sit leaf returning'], ['lock', 'Cam clutch LOCKED'], ['cc', 'Crazy Creek straps'],
  ['t3_load', 'Lift tendon loading'], ['t3_return', 'Lift tendon returning'], ['m3_l', 'Hip band L'], ['m3_r', 'Hip band R'],
  ['ea_l', 'Stance clutch L'], ['ea_r', 'Stance clutch R'], ['ham_l', 'Hamstring band L'], ['ham_r', 'Hamstring band R'], ['runband', 'Running band']];
function hud(seqName, st, i, n) {
  const el = document.getElementById('hud');
  const rows = HUD_ROWS.filter(([k]) => st[k] > 0.01).map(([k, t]) => `<div class="hrow"><span>${t}</span><i><b style="width:${Math.round(100 * Math.min(1, st[k]))}%"></b></i></div>`).join('');
  el.innerHTML = `<div class="ttl">${SEQS.find(s => s[0] === seqName)[1]}</div><div class="cap">${HUD_TXT[seqName]}</div>${rows}`;
  el.style.display = 'block';
}

// ---------------- kit (viewer side) ----------------
const KIT = [
  ['Dock: back panel + hip belt, 6 cable ports', n => /^(hip_belt|belt_|lumbar_plate|back_panel|port_)/.test(n), ['harness_l', 'harness_r', 'sternum_strap', 'panelstrap_l', 'panelstrap_r', 'cupstrap_l', 'cupstrap_r', 'crazycreek_l', 'crazycreek_r']],
  ['M1 knee / seat: shells, hinge, 80 mm arc, cam clutch, sit leaf, seat cup, strut', n => /^(thigh_|shin_|knee_(hub|arc|yoke|manifold)|condyle|mode_lever|tendon_fairlead|sit_leaf|seat_cup|strut|ptb|calf_|dring_cc|dring_t3|runband)/.test(n), ['t1_tendon_l', 't1_tendon_r']],
  ['M2 back / lift: leaf, whiffletree, lift tendons', n => /^(m2_|whiffletree|panel_guide|lumbar_standoff|glute_guide)/.test(n), ['t3_tendon_l', 't3_tendon_r']],
  ['M3 hip: hip-flexor bands', n => /^(m3_|dring_m3)/.test(n), ['m3_band_l', 'm3_band_r']],
  ['Couplings: hamstring band (appears when M1 + M3 dock)', n => /^(knee_guide|dring_ham)/.test(n), ['hamstring_band_l', 'hamstring_band_r']],
  ['Upgrades: stance clutches, one motor + Bowden, M4 ankle, M5 shoulder', n => /^(ea_|p1_|bowden|m4_|m5_)/.test(n), ['bowden_l', 'bowden_r', 'm5_lever_l', 'm5_lever_r', 'm4_cable_l', 'm4_cable_r', 'calf_band_l', 'calf_band_r']],
];
const KIT_STEP = 2.2;
function kitFrame(t) {
  // static standing pose, parts fly in group by group
  const T = D.poses.parts['stand'];
  let caption = KIT[0][0];
  for (const [name, p] of Object.entries(parts)) {
    if (p.meta.module === 'body') { p.obj.visible = state.body !== 'off'; continue; }
    const g = KIT.findIndex(k => k[1](name));
    const m = T[name]; if (!m) continue;
    const M = new THREE.Matrix4().set(...m.flat());
    const local = g < 0 ? 1 : (t - g * KIT_STEP) / (KIT_STEP * 0.8);
    const k = Math.max(0, Math.min(1, local));
    const e = 1 - Math.pow(1 - k, 3);
    p.obj.visible = k > 0 && moduleVisible(p.meta.module || 'basic', p.meta.requires);
    if (k < 1) {
      const d = (p.dirLocal.lengthSq() > 0 ? p.dirLocal.clone() : new THREE.Vector3(0, -1, 0)).transformDirection(M);
      d.multiplyScalar((1 - e) * 0.55); d.z += (1 - e) * 0.25;
      M.premultiply(new THREE.Matrix4().makeTranslation(d.x, d.y, d.z));
    }
    p.obj.matrix.copy(M); p.obj.matrixWorldNeedsUpdate = true;
    const ghost = isGhost(p.meta.module, p.meta.requires);
    p.obj.traverse(o => { if (o.isMesh) o.material = ghost ? ghostMat : o.userData.baseMat; });
  }
  const gi = Math.min(KIT.length - 1, Math.floor(t / KIT_STEP)); caption = KIT[gi][0];
  const c = cables['stand'];
  if (c) {
    c.visible = true;
    c.traverse(o => {
      if (!o.isMesh) return;
      const g = KIT.findIndex(k => k[2].includes(o.name));
      const ud = o.userData || {};
      o.visible = g >= 0 && t > g * KIT_STEP + KIT_STEP * 0.8 && moduleVisible(ud.module || 'basic', ud.requires);
    });
  }
  for (const [p, b] of Object.entries(bodies)) b.visible = p === 'stand' && state.body !== 'off';
  const el = document.getElementById('hud');
  el.innerHTML = `<div class="ttl">Kit: modules dock to the hub</div><div class="cap">${gi + 1} / ${KIT.length} · ${caption}</div>`;
  el.style.display = 'block';
}
const KIT_LEN = KIT.length * KIT_STEP + 1.0;

function seqLen(name) { return name === 'kit' ? KIT_LEN : (AD.A.seqs[name].n - (AD.A.seqs[name].loop ? 0 : 1)) / SEQ_FPS[name]; }
async function startSeq(name) {
  if (name !== 'kit') await ensureAnim();
  anim.on = true; anim.seq = name; anim.t = 0; anim.playing = true;
  for (const b of Object.values(bodies)) b.visible = false;
  for (const c of Object.values(cables)) c.visible = false;
  if (anim.body) anim.body.visible = name !== 'kit' && state.body !== 'off';
  for (const m of Object.values(anim.cables)) m.visible = name !== 'kit';
  if (name === 'kit') for (const m of Object.values(anim.cables)) m.visible = false;
  state.labels = false; updateButtons(); updateAnimUI();
}
function stopAnim() {
  anim.on = false; anim.playing = false;
  if (anim.body) anim.body.visible = false;
  for (const m of Object.values(anim.cables)) m.visible = false;
  document.getElementById('hud').style.display = 'none';
  for (const ms of glowMats.values()) for (const m of ms) m.emissiveIntensity = 0;
  for (const p of Object.values(parts)) p.obj.traverse(o => { if (o.isMesh) o.material = o.userData.baseMat; });
  apply(); updateAnimUI();
}
function animTick(dt) {
  if (!anim.on) return;
  if (anim.playing) {
    anim.t += dt * anim.speed;
    const L = seqLen(anim.seq);
    if (anim.t > L) { if (anim.seq === 'walk' || anim.seq === 'run') anim.t -= L; else { anim.t = L; anim.playing = false; updateAnimUI(); } }
  }
  renderAnimAt(anim.t);
  const sc = document.getElementById('scrub'); if (sc && !sc.matches(':active')) sc.value = anim.t / seqLen(anim.seq);
}
function renderAnimAt(t) {
  if (anim.seq === 'kit') kitFrame(t);
  else {
    if (anim.body) anim.body.visible = state.body !== 'off';
    anim.body.material = state.body === 'ghost' ? bodyGhost : anim.body.userData.baseMat;
    for (const [n, p] of Object.entries(parts)) {
      const mod = p.meta.module || 'basic';
      p.obj.visible = mod === 'body' ? state.body !== 'off' : moduleVisible(mod, p.meta.requires);
      if (!glowMats.has(p.obj)) { const g = isGhost(mod, p.meta.requires); p.obj.traverse(o => { if (o.isMesh) o.material = g ? ghostMat : o.userData.baseMat; }); }
    }
    applyAnimFrame(anim.seq, t * SEQ_FPS[anim.seq]);
  }
}
function updateAnimUI() {
  if (!ui.seqs) return;
  for (const [k, b] of Object.entries(ui.seqs)) b.classList.toggle('on', anim.on && anim.seq === k);
  ui.play.textContent = anim.playing ? 'Pause' : 'Play';
  document.getElementById('animbar').classList.toggle('live', anim.on);
  document.getElementById('readout').style.display = anim.on ? 'none' : 'block';
}
function buildAnimUI() {
  const r = document.getElementById('anims'); ui.seqs = {};
  for (const [k, t] of SEQS) ui.seqs[k] = btn(r, t, () => startSeq(k));
  ui.play = btn(document.getElementById('animctl'), 'Play', () => { if (!anim.on) startSeq('walk'); else { if (!anim.playing && anim.t >= seqLen(anim.seq)) anim.t = 0; anim.playing = !anim.playing; updateAnimUI(); } });
  btn(document.getElementById('animctl'), '½×', () => { anim.speed = anim.speed === 1 ? 0.5 : anim.speed === 0.5 ? 0.25 : 1; event.target.textContent = anim.speed === 1 ? '½×' : anim.speed === 0.5 ? '¼×' : '1×'; });
  btn(document.getElementById('animctl'), 'Stop', () => stopAnim());
  const sc = document.getElementById('scrub');
  sc.oninput = () => { if (!anim.on) return; anim.playing = false; anim.t = parseFloat(sc.value) * seqLen(anim.seq); updateAnimUI(); };
}
window.SITKA_ANIM_API = { startSeq, stopAnim, anim, seek: (f) => { anim.playing = false; anim.t = f * seqLen(anim.seq); } };

// ---------- loop ----------
function resize() {
  const w = wrap.clientWidth, h = wrap.clientHeight;
  renderer.setSize(w, h, false); renderer.domElement.style.width = w + 'px'; renderer.domElement.style.height = h + 'px';
  camera.aspect = w / h; camera.updateProjectionMatrix();
  svg.setAttribute('width', w); svg.setAttribute('height', h);
}
window.addEventListener('resize', resize); resize();
let lastLbl = 0, lastT = 0;
function loop(t) {
  requestAnimationFrame(loop);
  const dt = Math.min(0.1, (t - lastT) / 1000 || 0); lastT = t;
  animTick(dt);
  controls.update();
  renderer.render(scene, camera);
  if (t - lastLbl > 120) { drawLabels(); lastLbl = t; }
}
init().then(async () => {
  applyCamParam(); requestAnimationFrame(loop);
  const sq = Q.get('anim');
  if (sq) { window.__ready = false; await startSeq(sq); if (Q.get('at')) { anim.playing = false; anim.t = parseFloat(Q.get('at')) * seqLen(sq); } window.__ready = true; }
}).catch(e => {
  document.getElementById('loading').textContent = 'Load error: ' + e; window.__errs = [String(e)]; console.error(e);
});
window.SITKA = { state, apply, setView };
