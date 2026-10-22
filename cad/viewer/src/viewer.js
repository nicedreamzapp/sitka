// Sitka render two viewer. Bundled to cad/viewer/sitka_viewer.bundle.js (classic script, works from file://).
// Data comes from cad/viewer/sitka_data.js (window.SITKA_DATA: base64 GLBs + pose transforms).
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';

let D = window.SITKA_DATA;
const $ = id => document.getElementById(id);
const ROOT = document.documentElement;
// cache-busting: the page stamps its build; data files are fetched with ?v=<build> so phones never mix old and new
const BUILD = window.SITKA_BUILD || '';
// ---------- loading with progress (XHR so we can show %, script-tag fallback for file://) ----------
const EST = { 'cad/viewer/sitka_data.js': 22.1e6, 'cad/viewer/sitka_anim.js': 21.3e6 };
function showLoading(txt, frac) {
  $('loading').style.display = 'grid'; $('ldTxt').textContent = txt;
  const f = frac == null ? null : Math.max(0, Math.min(1, frac));
  $('ldFill').style.width = f == null ? '100%' : Math.round(f * 100) + '%';
  $('ldSub').textContent = f == null ? 'preparing…' : Math.round(f * 100) + '%';
}
function hideLoading() { $('loading').style.display = 'none'; }
function loadScript(src, txt, globalName, loud = () => true) {
  return new Promise((res, rej) => {
    if (window[globalName]) return res(window[globalName]);
    const viaTag = () => {
      if (loud()) showLoading(txt, null);
      const sc = document.createElement('script'); sc.src = src + (BUILD ? '?v=' + BUILD : '');
      sc.onload = () => res(window[globalName]); sc.onerror = rej; document.head.appendChild(sc);
    };
    if (location.protocol === 'file:') return viaTag();
    const x = new XMLHttpRequest(); x.open('GET', src + (BUILD ? '?v=' + BUILD : '')); x.responseType = 'text';
    x.onprogress = e => {
      const est = EST[src] || 2e7;
      const tot = e.lengthComputable && e.total >= e.loaded && e.total > est * 0.6 ? e.total : est;
      if (loud()) showLoading(txt, Math.min(0.99, e.loaded / tot));
    };
    x.onload = () => {
      if (x.status && x.status !== 200) return viaTag();
      if (loud()) showLoading(txt, 1);
      const sc = document.createElement('script'); sc.text = x.responseText; document.head.appendChild(sc);
      res(window[globalName]);
    };
    x.onerror = viaTag; x.send();
  });
}
const nextFrame = () => new Promise(r => requestAnimationFrame(() => setTimeout(r, 0)));
const Q = new URLSearchParams(location.search);
const state = {
  pose: Q.get('pose') || 'stand',
  basic: Q.get('basic') !== '0',
  coupling: Q.get('coupling') !== '0',
  upgrade: Q.get('upg') || 'ghost',      // off | ghost | on
  body: Q.get('body') || 'on',           // on | ghost | off
  explode: parseFloat(Q.get('explode') || '0'),
  labels: Q.get('labels') === '1',      // off by default; ?labels=1 or the Labels button
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
const SMALL = Math.min(screen.width, screen.height) <= 600;
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
key.shadow.mapSize.set(SMALL ? 1024 : 2048, SMALL ? 1024 : 2048); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.02;
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
  layout();
  if (!D) D = await loadScript('cad/viewer/sitka_data.js', 'Loading Sitka', 'SITKA_DATA');
  layout(); showLoading('Building the model', null); await nextFrame();
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
  hideLoading();
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

// ---------- layout: phone (compact) / phone landscape / desktop ----------
const ui = { open: { ctl: false, info: false } };
let lastMode = '';
function layout() {
  const W = Math.min(innerWidth, ROOT.clientWidth || innerWidth), H = innerHeight;
  const compact = W <= 600 || H <= 500;
  const land = compact && H <= 500 && W > H;
  const mode = compact ? (land ? 'land' : 'port') : (W >= 1000 ? 'wide' : 'mid');
  ROOT.classList.toggle('compact', compact); ROOT.classList.toggle('land', land);
  if (mode !== lastMode) {
    // default: side cards open on a wide desktop, everything closed on phones/tablets
    if (!lastMode) ui.open = { ctl: false, info: false };
    if (!lastMode && Q.get('open')) { const o = Q.get('open'); ui.open = { ctl: o === 'ctl', info: o === 'info' }; }
    if (mode === 'port' && ui.open.ctl && ui.open.info) ui.open.info = false;
    lastMode = mode;
  }
  syncSheets();
}
function syncSheets() {
  $('ctl').classList.toggle('closed', !ui.open.ctl);
  $('info').classList.toggle('closed', !ui.open.info);
  $('bCtl').classList.toggle('on', ui.open.ctl); $('bCtl').setAttribute('aria-expanded', ui.open.ctl);
  $('bInfo').classList.toggle('on', ui.open.info); $('bInfo').setAttribute('aria-pressed', ui.open.info);
  $('peek').classList.toggle('hide', ROOT.classList.contains('compact') && !ROOT.classList.contains('land') && (ui.open.ctl || ui.open.info));
  ROOT.style.setProperty('--dockh', $('dock').offsetHeight + 'px');
  updateOffset();
}
function toggleSheet(which, force) {
  const v = force === undefined ? !ui.open[which] : force;
  ui.open[which] = v;
  // phone portrait: one bottom sheet at a time
  if (v && ROOT.classList.contains('compact') && !ROOT.classList.contains('land')) ui.open[which === 'ctl' ? 'info' : 'ctl'] = false;
  syncSheets();
}
// the part of the screen the model can use (between the bars, beside any open side card)
function freeRect() {
  const W = innerWidth, H = innerHeight;
  const shown = el => el && getComputedStyle(el).display !== 'none';
  const compact = ROOT.classList.contains('compact'), land = ROOT.classList.contains('land');
  const touring = ROOT.classList.contains('touring');
  let l = 0, r = W, t = $('top').getBoundingClientRect().bottom + 6, b = H;
  if (touring && land) l = $('tour').getBoundingClientRect().right + 6;
  else for (const id of touring ? ['tour'] : ['dock', 'peek']) if (shown($(id))) b = Math.min(b, $(id).getBoundingClientRect().top - 6);
  if (!touring && !(compact && !land)) {
    if (ui.open.ctl) l = $('ctl').getBoundingClientRect().right + 6;
    if (ui.open.info) r = $('info').getBoundingClientRect().left - 6;
  }
  if (r - l < W * 0.35) { l = 0; r = W; }
  if (b - t < H * 0.18) { t = 0; b = H; }
  return { l, r, t, b, W, H };
}
// shift the projection so the orbit target sits in the middle of the free area
function updateOffset() {
  if (!camera) return;
  const f = freeRect();
  const cx = (f.l + f.r) / 2, cy = (f.t + f.b) / 2;
  camera.setViewOffset(f.W, f.H, f.W / 2 - cx, f.H / 2 - cy, f.W, f.H);
  camera.updateProjectionMatrix();
}

// ---------- views ----------
const VIEWS = { front: [0, 0.08, 1], side: [1, 0.06, 0], back: [0, 0.10, -1], '34': [0.78, 0.30, 0.78], top: [0.2, 1.6, 0.4] };
let framePoses = null;   // the tour can frame on several poses at once (e.g. standing + bent over)
function bodyBox() {
  const box = new THREE.Box3();
  for (const p of framePoses || [state.pose]) { const b = bodies[p]; if (b) { const v = b.visible; b.visible = true; box.expandByObject(b); b.visible = v; } }
  if (box.isEmpty()) box.set(new THREE.Vector3(-0.4, 0, -0.4), new THREE.Vector3(0.4, 1.9, 0.4));
  return box;
}
let camTween = null;
function setView(v, instant) {
  state.view = v;
  const box = bodyBox(); const c = box.getCenter(new THREE.Vector3()); const s = box.getSize(new THREE.Vector3());
  const d = new THREE.Vector3(...VIEWS[v]).normalize();
  // fit the body's height AND its on-screen width into the free area (tall narrow phones are width-bound)
  const f = freeRect(); const fw = f.r - f.l, fh = f.b - f.t;
  const tn = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const hz = Math.hypot(d.x, d.z) || 1, ax = Math.abs(d.x) / hz, az = Math.abs(d.z) / hz;
  const wide = (az * s.x + ax * s.z) * 1.04;                       // projected width for this view direction
  const tall = s.y * (0.15 + 0.85 * (1 - Math.abs(d.y))) + Math.abs(d.y) * Math.max(s.x, s.z);
  const dist = Math.max(tall * f.H / (2 * tn * fh), wide * f.H / (2 * tn * fw)) * 1.06 + Math.max(s.x, s.z) * 0.5;
  const pos = c.clone().addScaledVector(d, dist);
  updateOffset();
  if (instant || !ready) { camTween = null; controls.target.copy(c); camera.position.copy(pos); controls.update(); }
  else camTween = { p0: camera.position.clone(), t0: controls.target.clone(), p1: pos, t1: c, k: 0 };
  updateButtons();
}
function tweenTick(dt) {
  if (!camTween) return;
  const tw = camTween; tw.k = Math.min(1, tw.k + dt / 0.9);
  const e = tw.k < 0.5 ? 4 * tw.k ** 3 : 1 - Math.pow(-2 * tw.k + 2, 3) / 2;
  // swing around the target rather than cutting through the model
  const r0 = tw.p0.clone().sub(tw.t0), r1 = tw.p1.clone().sub(tw.t1);
  const len = r0.length() + (r1.length() - r0.length()) * e;
  const dir = r0.normalize().lerp(r1.normalize(), e).normalize();
  controls.target.lerpVectors(tw.t0, tw.t1, e);
  camera.position.copy(controls.target).addScaledVector(dir, len);
  if (tw.k >= 1) camTween = null;
}
controls.addEventListener('start', () => { camTween = null; controls.autoRotate = false; });
const camQ = Q.get('cam');
function applyCamParam() {
  if (!camQ) return;
  const v = camQ.split(',').map(Number);
  camera.position.set(v[0], v[1], v[2]); controls.target.set(v[3], v[4], v[5]); controls.update();
}

// ---------- labels ----------
const labelLayer = $('labels');
const svg = $('leaders');
// plain names for visitors; the technical name lives in the tooltip / details small print
const SHORT = [[/^thigh_shell/, 'Thigh shell'], [/^knee_manifold/, 'Knee lock'], [/^sit_leaf_[lr]$/, 'Knee spring'], [/^seat_cup_[lr]$/, 'Seat cup'],
  [/^strut_tube0/, 'Seat pole'], [/^back_panel$/, 'Back panel'], [/^m2_leaf$/, 'Back tendon'], [/^hip_belt/, 'Hip belt'],
  [/^t1_tendon/, 'Knee tendon'], [/^m3_band/, 'Hip band'], [/^ea_clutch/, 'Smart clutch (upgrade)']];
const PLAIN = [
  [/^(t1_tendon)/, 'Knee tendon'], [/^t3_tendon/, 'Back tendon'], [/^m3_band/, 'Hip band'], [/^crazycreek/, 'Lean-back strap'],
  [/^hamstring_band/, 'Hamstring band'], [/^calf_band/, 'Calf band'], [/^running_band/, 'Running band'], [/^(harness|sternum_strap|panelstrap)/, 'Shoulder harness'],
  [/^cupstrap/, 'Seat cup strap'], [/^m4_cable/, 'Ankle cable (upgrade)'], [/^m5_lever/, 'Shoulder support (upgrade)'],
  [/liner/, 'Soft liner'], [/^thigh_shell/, 'Thigh shell'], [/^thigh_cuff/, 'Back-of-thigh cuff'], [/(strap|buckle)/, 'Strap'],
  [/^(thigh|shin)_arm/, 'Knee hinge arm'], [/^(knee_manifold|mode_lever)/, 'Knee lock'], [/^tendon_fairlead/, 'Knee tendon guide'],
  [/^sit_leaf/, 'Knee spring'], [/^ea_clutch/, 'Smart clutch (upgrade)'], [/^seat_cup/, 'Seat cup'], [/^strut/, 'Seat pole'],
  [/^dring_cc/, 'Lean-back strap ring'], [/^dring/, 'Band ring'], [/^(knee_hub|condyle|knee_yoke)/, 'Knee hinge'],
  [/^knee_arc/, 'Knee arc (artificial kneecap)'], [/^knee_guide/, 'Band guide'], [/^ptb_shell/, 'Below-knee pad'], [/^calf_cuff/, 'Calf pad'],
  [/^shin_anchor/, 'Knee tendon anchor'], [/^runband_clip/, 'Running band clip'], [/^m4_/, 'Ankle spring (upgrade)'], [/^shoe/, 'Shoe'],
  [/^(hip_belt|belt_)/, 'Hip belt'], [/^lumbar_plate/, 'Lower-back plate (hub)'], [/^(lumbar_standoff|panel_guide)/, 'Back tendon guide'],
  [/^glute_guide/, 'Back tendon hip pulley'], [/^m3_standoff/, 'Hip band mount'], [/^back_panel/, 'Back panel'], [/^port_/, 'Cable port (hub)'],
  [/^m2_leaf/, 'Back tendon spring'], [/^whiffletree/, 'Back tendon balancer (even left/right pull)'], [/^p1_battery/, 'Battery (motor upgrade)'],
  [/^(p1_|bowden)/, 'Motor (optional upgrade)'], [/^m5_/, 'Shoulder support (upgrade)'],
];
const plainName = n => { for (const [re, t] of PLAIN) if (re.test(n)) return t; return null; };
const shortName = n => { for (const [re, t] of SHORT) if (re.test(n)) return t; return null; };
function drawLabels() {
  labelLayer.innerHTML = ''; svg.innerHTML = '';
  if (!state.labels || !ready) return;
  const compact = ROOT.classList.contains('compact');
  const W = innerWidth, H = innerHeight;
  const items = [];
  const KEY = /^(thigh_shell|seat_cup_[lr]$|strut_tube0|knee_arc|knee_manifold|sit_leaf_[lr]$|hip_belt|back_panel$|m2_leaf$|whiffletree|knee_hub_lat|ptb_shell|thigh_cuff_[lr]$|p1_motor|m5_cassette|m4_heelclip|ea_clutch)/;
  const KEYC = /^(t1_tendon|t3_tendon|m3_band|crazycreek|hamstring_band|running_band|harness_l|bowden_l)/;
  for (const [name, p] of Object.entries(parts)) {
    if (!p.obj.visible || !p.meta.label || !KEY.test(name)) continue;
    if (p.meta.module === 'upgrade' && state.upgrade === 'off') continue;
    const label = shortName(name); if (!label) continue;   // major parts only; hover/tap gives the full name
    const wp = p.centerLocal.clone().applyMatrix4(p.obj.matrix).applyMatrix4(partRoot.matrix);
    items.push({ label, wp, name, dist: wp.distanceTo(camera.position) });
  }
  const c = cables[state.pose];
  if (c && c.visible) c.traverse(o => {
    if (!o.isMesh || !o.visible) return;
    const ud = Object.keys(o.userData || {}).length ? o.userData : (o.parent && o.parent.userData) || {};
    if (!ud.label || !KEYC.test(o.name)) return;
    const label = shortName(o.name); if (!label) return;
    o.geometry.computeBoundingBox();
    const wp = o.geometry.boundingBox.getCenter(new THREE.Vector3()).applyMatrix4(o.matrixWorld);
    items.push({ label, wp, name: o.name, dist: wp.distanceTo(camera.position) });
  });
  // one label per text, nearest instance wins
  const best = {};
  for (const it of items) if (!best[it.label] || it.dist < best[it.label].dist) best[it.label] = it;
  const f = freeRect();
  const list = [];
  for (const it of Object.values(best)) {
    const p = it.wp.clone().project(camera);
    if (p.z > 1 || Math.abs(p.x) > 1.0 || Math.abs(p.y) > 1.0) continue;
    const x = (p.x + 1) / 2 * W, y = (1 - p.y) / 2 * H;
    if (y < f.t || y > f.b) continue;
    list.push({ ...it, x, y });
  }
  // split by the model's own centre line so leaders run outward, not across the body
  const tc = controls.target.clone().project(camera); const cx = (tc.x + 1) / 2 * W;
  const mb = { l: W, r: 0 }; const bb = bodyBox();
  for (let i = 0; i < 8; i++) {
    const v = new THREE.Vector3(i & 1 ? bb.max.x : bb.min.x, i & 2 ? bb.max.y : bb.min.y, i & 4 ? bb.max.z : bb.min.z).project(camera);
    const x = (v.x + 1) / 2 * W; mb.l = Math.min(mb.l, x); mb.r = Math.max(mb.r, x);
  }
  const left = list.filter(i => i.x < cx).sort((a, b) => a.y - b.y);
  const right = list.filter(i => i.x >= cx).sort((a, b) => a.y - b.y);
  const lh = compact ? 24 : 22, top = f.t + 12, bot = f.b - 10;
  const place = (arr, side) => {
    let y = top;
    for (const it of arr) { it.ly = Math.max(y, it.y); y = it.ly + lh; }
    const over = y - lh - bot;
    if (over > 0) { const k = (bot - top) / Math.max(1, (y - lh - top)); for (const it of arr) it.ly = top + (it.ly - top) * k; }
    const els = arr.map(it => { const el = document.createElement('div'); el.className = 'lbl ' + side; el.textContent = it.label; labelLayer.appendChild(el); return el; });
    const mw = Math.max(0, ...els.map(e => e.offsetWidth));
    // hug the model: columns sit just outside its silhouette when there is room, else at the screen edge
    const edge = side === 'l' ? Math.max(f.l + 8, mb.l - 18 - mw) : Math.min(f.r - 8, mb.r + 18 + mw);
    arr.forEach((it, i) => {
      const el = els[i];
      const lx = side === 'l' ? edge : edge - el.offsetWidth;
      el.style.left = lx + 'px'; el.style.top = (it.ly - 10) + 'px';
      const ex = side === 'l' ? lx + el.offsetWidth : lx;
      const ln = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      ln.setAttribute('d', `M${ex},${it.ly} L${ex + (side === 'l' ? 8 : -8)},${it.ly} L${it.x},${it.y}`);
      svg.appendChild(ln);
      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', it.x); dot.setAttribute('cy', it.y); dot.setAttribute('r', 2.6);
      svg.appendChild(dot);
    });
  };
  place(left, 'l'); place(right, 'r');
}

// ---------- hover (mouse) and tap-a-part (touch) ----------
const ray = new THREE.Raycaster(); const mouse = new THREE.Vector2(); const tip = $('tip');
let tipTimer = 0;
function pick(cx, cy) {
  const r = renderer.domElement.getBoundingClientRect();
  mouse.set((cx - r.left) / r.width * 2 - 1, -(cy - r.top) / r.height * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const objs = [partRoot, anim.on ? animRoot : cables[state.pose]].filter(Boolean);
  const hit = ray.intersectObjects(objs, true).find(h => isVis(h.object));
  if (!hit) return null;
  let o = hit.object; let ud = o.userData || {}; let name = ud.name || o.name;
  while (o && !parts[o.name] && o.parent && o.parent !== partRoot) o = o.parent;
  if (parts[o.name]) { name = o.name; ud = parts[o.name].meta; }
  if (ud.module === 'body' || /^(body|human)/i.test(name)) return null;
  const tech = ud.label || ud.group || name;
  return { lbl: plainName(name) || tech, sub: `${tech}${ud.state ? ' · ' + ud.state : ''}` };
}
function showTip(h, x, y, touch) {
  if (!h) { tip.style.display = 'none'; return; }
  tip.innerHTML = `<b></b><span></span>`; tip.firstChild.textContent = h.lbl; tip.lastChild.textContent = h.sub;
  tip.style.display = 'block';
  const w = tip.offsetWidth, hh = tip.offsetHeight;
  let lx = touch ? x - w / 2 : x + 14, ly = touch ? y - hh - 28 : y + 10;
  lx = Math.max(8, Math.min(innerWidth - w - 8, lx)); ly = Math.max(8, Math.min(innerHeight - hh - 8, ly));
  tip.style.left = lx + 'px'; tip.style.top = ly + 'px';
}
renderer.domElement.addEventListener('pointermove', e => {
  if (e.pointerType !== 'mouse' || e.buttons) return;
  showTip(pick(e.clientX, e.clientY), e.clientX, e.clientY, false);
});
renderer.domElement.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') tip.style.display = 'none'; });
let down = null;
renderer.domElement.addEventListener('pointerdown', e => { down = { x: e.clientX, y: e.clientY, t: performance.now(), type: e.pointerType }; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!down || down.type === 'mouse') return;
  const moved = Math.hypot(e.clientX - down.x, e.clientY - down.y), dt = performance.now() - down.t; down = null;
  if (moved > 10 || dt > 400) return;
  const h = pick(e.clientX, e.clientY);
  showTip(h, e.clientX, e.clientY, true);
  clearTimeout(tipTimer); if (h) tipTimer = setTimeout(() => tip.style.display = 'none', 3200);
  // tapping the model also tucks any open bottom sheet away on phones
  if (ROOT.classList.contains('compact') && !ROOT.classList.contains('land') && (ui.open.ctl || ui.open.info)) { ui.open.ctl = ui.open.info = false; syncSheets(); }
});
function isVis(o) { while (o) { if (!o.visible) return false; o = o.parent; } return true; }

// ---------- UI ----------
function btn(parent, text, on, cls = 'pill') { const b = document.createElement('button'); b.textContent = text; b.className = cls; b.onclick = on; parent.appendChild(b); return b; }
const POSE_NAME = { stand: 'Standing', walk: 'Walking', run: 'Running', chair: 'Leaning back', stoop: 'Bending to lift' };
const POSE_PLAIN = {
  stand: 'Standing. Nothing is locked, so the frame moves freely with you.',
  walk: 'Walking. No motor: elastic hip bands help swing each leg forward.',
  run: 'Running. Every lock is open; a band between the shins and the hip bands do the work.',
  chair: 'Leaning back. A light pole under each hip carries 69% of your weight, the knee lock holds with no power, and two straps hold your back like a camp chair.',
  stoop: 'Bending to lift. The back tendon is loaded and gives the energy back as you stand up.',
};
function buildUI() {
  $('ver').textContent = 'build ' + (BUILD || 'dev');
  const pr = $('poses');
  ui.poses = {};
  for (const p of Object.keys(D.poses.poses)) ui.poses[p] = btn(pr, POSE_NAME[p] || D.poses.poses[p].label, () => { stopProgram(); if (anim.on) stopAnim(); state.pose = p; apply(); });
  const vr = $('views'); ui.views = {};
  for (const [k, t] of [['34', '3/4'], ['front', 'Front'], ['side', 'Side'], ['back', 'Back']]) ui.views[k] = btn(vr, t, () => setView(k));
  const mr = $('mods');
  ui.basic = btn(mr, 'Core kit', () => { state.basic = !state.basic; apply(); });
  ui.coupling = btn(mr, 'Linking bands', () => { state.coupling = !state.coupling; apply(); });
  ui.upgrade = btn(mr, 'Upgrades', () => { state.upgrade = { off: 'ghost', ghost: 'on', on: 'off' }[state.upgrade]; apply(); });
  ui.body = btn(mr, 'Body', () => { state.body = { on: 'ghost', ghost: 'off', off: 'on' }[state.body]; apply(); });
  ui.labels2 = btn(mr, 'Labels', () => toggleLabels());
  const ex = $('explode'); ex.value = state.explode;
  ex.oninput = () => { state.explode = parseFloat(ex.value); $('exVal').textContent = Math.round(state.explode * 100) + '%'; apply(); };
  $('exVal').textContent = Math.round(state.explode * 100) + '%';
  $('bLabels').onclick = () => toggleLabels();
  $('bInfo').onclick = () => toggleSheet('info');
  $('bCtl').onclick = () => toggleSheet('ctl');
  $('ctlHd').onclick = () => toggleSheet('ctl', false);
  $('infoHd').onclick = () => toggleSheet('info', false);
  $('peek').onclick = () => toggleSheet('info');
  for (const id of ['ctl', 'info']) swipeClose($(id).querySelector('.hd'), id);
  if (!matchMedia('(hover: hover)').matches) $('hint').textContent = 'Drag to orbit · pinch to zoom · two fingers to pan · tap a part to name it';
  else $('hint').textContent = 'Drag to orbit · scroll to zoom · right-drag to pan · hover a part to name it';
}
function swipeClose(el, which) {
  let y0 = null;
  el.addEventListener('touchstart', e => { y0 = e.touches[0].clientY; }, { passive: true });
  el.addEventListener('touchend', e => { if (y0 != null && e.changedTouches[0].clientY - y0 > 30) toggleSheet(which, false); y0 = null; });
}
function toggleLabels() { state.labels = !state.labels; updateButtons(); drawLabels(); }
function updateButtons() {
  if (!ui.poses) return;
  for (const [p, b] of Object.entries(ui.poses)) b.classList.toggle('on', !anim.on && p === state.pose);
  for (const [v, b] of Object.entries(ui.views)) b.classList.toggle('on', v === state.view);
  ui.basic.classList.toggle('on', state.basic); ui.coupling.classList.toggle('on', state.coupling);
  ui.upgrade.textContent = 'Upgrades: ' + { off: 'off', ghost: 'preview', on: 'on' }[state.upgrade]; ui.upgrade.classList.toggle('on', state.upgrade !== 'off');
  ui.body.textContent = 'Body: ' + { on: 'on', ghost: 'see-through', off: 'off' }[state.body]; ui.body.classList.toggle('on', state.body !== 'off');
  ui.labels2.classList.toggle('on', state.labels);
  $('bLabels').classList.toggle('on', state.labels); $('bLabels').setAttribute('aria-pressed', state.labels);
  $('lblTxt').textContent = 'Labels: ' + (state.labels ? 'on' : 'off'); ui.labels2.textContent = 'Labels: ' + (state.labels ? 'on' : 'off');
  const k = prog.cur && prog.cur.key;
  for (const [id, key] of [['mWalk', 'walk'], ['mSit', 'sit'], ['mLift', 'lift']]) $(id).classList.toggle('on', k === key);
  $('bCtl').classList.toggle('on', ui.open.ctl);
}
const esc = t => String(t).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
let infoKey = '';
function setInfo(title, html) {
  const k = title + '|' + html; if (k === infoKey) return; infoKey = k;
  $('infoTitle').textContent = title; $('infoBody').innerHTML = html;
}
function techBlock(rows, note) {
  return `<div class="tech"><h5>Technical names (small print)</h5>${note ? `<div>${esc(note)}</div>` : ''}${rows.filter(r => r[1]).map(r => `<div class="row"><span>${esc(r[0])}</span><b>${esc(r[1])}</b></div>`).join('')}</div>`;
}
function updateReadout() {
  const P = D.poses.poses[state.pose];
  const C = D.poses.cables[state.pose] || {};
  const pick = (k) => (C[k + '_l'] || C[k] || {}).state || '';
  const rows = [
    ['Mode', P.mode],
    ['Knee tendon (T1)', pick('t1_tendon')],
    ['Back tendon (T3 / M2 lift leaf)', pick('t3_tendon')],
    ['Hip band (M3)', pick('m3_band')],
    ['Seat pole (strut)', P.mode === 'SIT' ? 'deployed, 4° back, 9° out' : 'stowed along the thigh'],
    ['Lean-back straps (Crazy Creek)', pick('crazycreek')],
    ['Hamstring band (coupling)', state.coupling ? pick('hamstring_band') : 'not docked'],
  ];
  if (C.running_band) rows.push(['Running band', C.running_band.state]);
  setInfo(POSE_NAME[state.pose] || P.label, `<div class="cap">${esc(POSE_PLAIN[state.pose] || P.label)}</div>` + techBlock(rows, P.label));
}

// =====================================================================================
// ANIMATION: walk / run cycles, sit-down, stand-up, stoop-lift (baked frames from Blender:
// cad/viewer/sitka_anim.js) and a viewer-side "kit" sequence where the modules dock one by one.
// =====================================================================================
const SEQS = [['walk', 'Walk'], ['run', 'Run'], ['sitdown', 'Sit down'], ['standup', 'Stand up'], ['stoop', 'Lift'], ['kit', 'Modules dock']];
const SEQ_FPS = { walk: 28, run: 30, sitdown: 14, standup: 14, stoop: 14 };
const anim = { on: false, seq: null, t: 0, playing: false, speed: 1, data: null, body: null, cables: {}, root: null };
const animRoot = new THREE.Group(); animRoot.matrixAutoUpdate = false; animRoot.matrix.copy(ZUP); scene.add(animRoot);
const GLOW = { load: new THREE.Color(0xff7a1a), ret: new THREE.Color(0x27e0c0), lock: new THREE.Color(0xff3344), gate: new THREE.Color(0x46a8ff), band: new THREE.Color(0x3fe0a8), strap: new THREE.Color(0xffc233) };

// one download, shared: a quiet prefetch (during the tour's first step) turns loud if someone is waiting on it
let animP = null, animLoud = false;
function loadAnimData(quiet) {
  if (!quiet) animLoud = true;
  if (!animP) animP = loadScript('cad/viewer/sitka_anim.js', 'Loading animation', 'SITKA_ANIM', () => animLoud);
  if (!quiet && !window.SITKA_ANIM) showLoading('Loading animation', null);
  return animP;
}
function i16(b64) { const b = b64ToU8(b64); return new Int16Array(b.buffer, b.byteOffset, b.byteLength / 2); }
function i8(b64) { const b = b64ToU8(b64); return new Int8Array(b.buffer, b.byteOffset, b.byteLength); }
function b64ToU8(s) { const bin = atob(s); const u = new Uint8Array(bin.length); for (let i = 0; i < bin.length; i++) u[i] = bin.charCodeAt(i); return u; }

let AD = null;
async function ensureAnim() {
  if (AD) return AD;
  const A = await loadAnimData();
  showLoading('Preparing animation', null); await nextFrame();
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
  hideLoading();
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
  anim.st = st; anim.frame = fr < 0.5 ? i0 : i1; anim.n = n;
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
// technical captions: small print in the details sheet only
const HUD_TXT = {
  walk: 'Walking: no motor. Hip bands (M3) stretch in late stance and swing the leg; the stance clutch gates the knee leaf (smart tier); the hamstring band brakes late swing.',
  run: 'Running: every clutch open. The shin-to-shin running band (−6.4%) and the hip bands do the work.',
  sitdown: 'Sit down: the strut swings down and plants; the sit leaf loads 44 J through the 80 mm arc; the cam clutch locks with no power; the Crazy Creek straps take the 10° recline.',
  standup: 'Stand up: the cam clutch opens, the sit leaf gives ~40 J back (28 Nm per knee), the strut retracts and stows along the thigh.',
  stoop: 'Stoop lift: the T3 lift tendon is slack until 35°, then loads the M2 lift leaf through the whiffletree (60 Nm) and gives it back on the lift.',
  kit: 'Kit: Dock → M1 knee/seat → M2 lift → M3 hip → couplings → upgrades (EA clutches, P1 motor, M4 ankle, M5 shoulder).',
};
// plain captions: the details sheet and the caption bar
const HUD_PLAIN = {
  walk: 'Walking with no motor: elastic hip bands swing each leg forward, and a hamstring band slows the knee before your heel lands.',
  run: 'Running: every lock is open; a band linking the shins and the hip bands do the work.',
  sitdown: 'Sitting down: the seat poles swing down and plant, the knee spring stores energy, and the knee lock holds you with no power.',
  standup: 'Standing up: the knee lock opens, the knee spring gives the energy back, and the seat poles fold away.',
  stoop: 'Lifting: the back tendon stays slack until you bend past about 35°, then stores energy and gives it back as you lift, so a 15 kg box feels about 12 kg lighter.',
  kit: 'Every module docks into one hub, starting with the hip belt and back panel.',
};
const CAP_SHORT = {
  walk: 'Walking, no motor: elastic hip bands swing each leg forward.',
  run: 'Running: a band linking the shins and the hip bands do the work.',
  sitdown: 'A pole under each hip takes 69% of your weight; the knee spring stores the energy.',
  standup: 'The knee spring gives the energy back as you stand.',
  stoop: 'The back tendon stores energy as you bend: a 15 kg box feels about 12 kg lighter.',
  kit: 'Every module docks into one hub.',
};
const HUD_ROWS = [['sit_leaf', 'Knee spring storing'], ['sit_return', 'Knee spring giving back'], ['lock', 'Knee lock on'], ['cc', 'Lean-back straps'],
  ['t3_load', 'Back tendon storing'], ['t3_return', 'Back tendon giving back'], ['m3_l', 'Hip band, left'], ['m3_r', 'Hip band, right'],
  ['ea_l', 'Smart clutch, left (upgrade)'], ['ea_r', 'Smart clutch, right (upgrade)'], ['ham_l', 'Hamstring band, left'], ['ham_r', 'Hamstring band, right'], ['runband', 'Running band']];
function hud(seqName, st) {
  const act = HUD_ROWS.filter(([k]) => st[k] > 0.01);
  const rows = act.map(([k, t]) => `<div class="hrow"><span>${t}</span><i><b style="width:${Math.round(10 * Math.min(1, st[k])) * 10}%"></b></i></div>`).join('');
  const ttl = SEQS.find(s => s[0] === seqName)[1];
  setInfo(ttl, `<div class="cap">${esc(HUD_PLAIN[seqName])}</div>${rows}` + techBlock([], HUD_TXT[seqName]));
}
// what is happening right now, read from the same engagement states that drive the glow (so it can't drift)
function phaseOf(seq) {
  const st = anim.st || {}, f = anim.frame || 0, on = k => st[k] > 0.01;
  if (seq === 'sitdown') return on('lock') ? 'Seated: the knee lock holds you, no power' : on('cc') ? 'Settling back: the straps take up' : on('sit_leaf') ? 'Sitting down: the knee spring stores energy' : 'The seat poles swing down';
  if (seq === 'standup') return on('sit_return') ? 'Standing up: the knee spring gives energy back' : on('lock') ? 'Seated, about to stand' : 'Standing: the seat poles fold away';
  if (seq === 'stoop') return on('t3_return') ? 'Lifting: the back tendon gives energy back' : on('t3_load') ? 'Bending: the back tendon stores energy' : f < 10 ? 'Bending: tendon slack until about 35°' : 'Standing tall again';
  if (seq === 'walk') return on('ham_l') || on('ham_r') ? 'Walking: the hamstring band slows the knee' : 'Walking: a hip band swings the leg forward';
  if (seq === 'run') return 'Running: the shin band and hip bands work';
  if (seq === 'kit') return KIT_PLAIN[anim.kitGi || 0];
  return '';
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
const KIT_PLAIN = ['The hub: hip belt + back panel', 'Seat module: knee springs, locks, seat poles', 'Back module: the back tendon', 'Hip module: hip bands',
  'Linking bands (appear when two modules dock)', 'Upgrades: smart clutches, ankles, shoulders, one motor'];
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
  const gi = Math.min(KIT.length - 1, Math.floor(t / KIT_STEP)); caption = KIT[gi][0]; anim.kitGi = gi;
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
  setInfo('Modules dock', `<div class="cap">${esc(HUD_PLAIN.kit)}</div><div class="cap">${gi + 1} / ${KIT.length} · ${esc(KIT_PLAIN[gi])}</div>` + techBlock([], caption));
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
  state.labels = false; drawLabels(); updateButtons(); updateAnimUI();
}
function stopAnim() {
  anim.on = false; anim.playing = false;
  if (anim.body) anim.body.visible = false;
  for (const m of Object.values(anim.cables)) m.visible = false;
  for (const ms of glowMats.values()) for (const m of ms) m.emissiveIntensity = 0;
  for (const p of Object.values(parts)) p.obj.traverse(o => { if (o.isMesh) o.material = o.userData.baseMat; });
  infoKey = ''; apply(); updateAnimUI();
}
function animTick(dt) {
  if (!anim.on) return;
  if (anim.playing) {
    anim.t += dt * anim.speed;
    const L = seqLen(anim.seq);
    if (anim.t > L) { if (anim.seq === 'walk' || anim.seq === 'run') anim.t -= L; else { anim.t = L; anim.playing = false; updateAnimUI(); } }
  }
  renderAnimAt(anim.t);
  const sc = $('scrub'); if (sc && !scrubbing) sc.value = anim.t / seqLen(anim.seq);
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
let scrubbing = false;
const PLAY = '<path d="M4 2.5v11l9.5-5.5z"/>', PAUSE = '<path d="M3.5 2.5h3.2v11H3.5zm5.8 0h3.2v11H9.3z"/>';
function updateAnimUI() {
  if (!ui.seqs) return;
  for (const [k, b] of Object.entries(ui.seqs)) b.classList.toggle('on', anim.on && anim.seq === k);
  ROOT.classList.toggle('anim', anim.on);
  $('playIco').innerHTML = anim.playing ? PAUSE : PLAY;
  $('playTxt').textContent = !anim.on ? 'Play' : anim.playing ? 'Pause' : 'Play';
  $('bPlay').setAttribute('aria-label', $('playTxt').textContent);
  if (anim.on) $('seqName').textContent = SEQS.find(s => s[0] === anim.seq)[1];
  $('bSpeed').textContent = anim.speed === 1 ? '1×' : anim.speed === 0.5 ? '½×' : '¼×';
  updateButtons();
  syncSheets();
}
function buildAnimUI() {
  const r = $('anims'); ui.seqs = {};
  for (const [k, t] of SEQS) ui.seqs[k] = btn(r, t, () => { stopProgram(); startSeq(k); if (ROOT.classList.contains('compact') && !ROOT.classList.contains('land')) toggleSheet('ctl', false); });
  $('bPlay').onclick = () => { if (!anim.on) { stopProgram(); startSeq('walk'); } else { if (!anim.playing && anim.t >= seqLen(anim.seq)) anim.t = 0; anim.playing = !anim.playing; updateAnimUI(); } };
  $('bSpeed').onclick = () => { anim.speed = anim.speed === 1 ? 0.5 : anim.speed === 0.5 ? 0.25 : 1; updateAnimUI(); };
  $('bStop').onclick = () => { stopProgram(); stopAnim(); };
  const sc = $('scrub');
  const seek = () => { if (!anim.on) return; stopProgram(); anim.playing = false; anim.t = parseFloat(sc.value) * seqLen(anim.seq); updateAnimUI(); };
  sc.oninput = seek;
  sc.addEventListener('pointerdown', () => { scrubbing = true; }); addEventListener('pointerup', () => { scrubbing = false; });
  sc.addEventListener('touchstart', () => { scrubbing = true; }, { passive: true }); addEventListener('touchend', () => { scrubbing = false; });
  // the simple main screen: four big buttons
  const main = (id, key) => $(id).onclick = () => {
    if (prog.cur && prog.cur.key === key && anim.on) { anim.playing = !anim.playing; if (anim.playing && anim.t >= seqLen(anim.seq)) anim.t = 0; updateAnimUI(); return; }
    runProgram(MAIN[key]);
  };
  main('mWalk', 'walk'); main('mSit', 'sit'); main('mLift', 'lift');
  $('mTour').onclick = () => tourStart(0);
}

// =====================================================================================
// PROGRAMS: a looping playlist of sequences / poses with one plain caption (main buttons and tour steps)
// =====================================================================================
const MAIN = {
  walk: { key: 'walk', cap: 'Walking with no motor: elastic bands link hips and knees like your own hamstrings.', items: [{ seq: 'walk', speed: 0.6 }] },
  sit: { key: 'sit', cap: 'A pole under each hip takes 69% of your weight; the knee spring gives the energy back when you stand.', items: [{ seq: 'sitdown', speed: 0.7, hold: 1.4 }, { seq: 'standup', speed: 0.7, hold: 1 }] },
  lift: { key: 'lift', cap: 'The back tendon stores energy as you bend: a 15 kg box feels about 12 kg lighter, with no motor.', items: [{ seq: 'stoop', speed: 0.7, hold: 1.2 }] },
};
const prog = { cur: null, i: 0, t: 0, wait: 0, token: 0, busy: false };
function runProgram(p) {
  prog.cur = p; prog.i = 0; prog.token++;
  if (!tour.on) { framePoses = p.frame || null; }
  updateButtons();
  return startItem(prog.token);
}
function stopProgram() { prog.cur = null; prog.token++; prog.busy = false; updateButtons(); }
async function startItem(tok) {
  const it = prog.cur.items[prog.i]; prog.t = 0; prog.wait = 0; prog.busy = true;
  try {
    if (it.pose) { if (anim.on) stopAnim(); state.pose = it.pose; apply(); }
    else { await startSeq(it.seq); if (tok !== prog.token) return; anim.speed = it.speed || 1; updateAnimUI(); }
  } finally { if (tok === prog.token) prog.busy = false; }
}
function progTick(dt) {
  const p = prog.cur; if (!p || prog.busy) return;
  const it = p.items[prog.i]; if (!it || it.pose || !anim.on) return;
  const L = seqLen(anim.seq), finished = !anim.playing && anim.t >= L - 1e-6;
  if (!anim.playing && !finished) return;              // paused by the visitor
  prog.t += dt;
  if (it.dur ? prog.t * (it.speed || 1) >= it.dur * (it.speed || 1) : finished) {
    prog.wait += dt;
    if (it.dur || prog.wait >= (it.hold || 0.8)) { prog.i = (prog.i + 1) % p.items.length; startItem(prog.token); }
  }
}

// ---------- focus: glow the parts that matter, dim everything else (tour) ----------
let focus = null;   // (name) => bool
const dimMat = new THREE.MeshStandardMaterial({ color: 0x8d949c, transparent: true, opacity: 0.30, roughness: 0.8, depthWrite: false });
const dimBody = new THREE.MeshStandardMaterial({ color: 0xd8d2ca, transparent: true, opacity: 0.30, roughness: 0.85, depthWrite: false });
const focusMats = new Map();
const FOCUS_GLOW = new THREE.Color(0xff6a10);
function focusMatFor(m) {
  let f = focusMats.get(m);
  if (!f) { f = m.clone(); f.emissive = FOCUS_GLOW.clone(); f.emissiveIntensity = 0.8; if (!f.transparent) f.depthWrite = true; focusMats.set(m, f); }
  return f;
}
function applyFocus(time) {
  if (!focus) return;
  const pulse = 0.65 + 0.35 * Math.sin(time * 0.004);
  for (const m of focusMats.values()) m.emissiveIntensity = pulse;
  const kit = anim.on && anim.seq === 'kit';
  for (const [name, p] of Object.entries(parts)) {
    if (!p.obj.visible) continue;
    const on = focus(name), body = p.meta.module === 'body';
    p.obj.traverse(o => {
      if (!o.isMesh) return;
      const base = isGhost(p.meta.module, p.meta.requires) ? ghostMat : o.userData.baseMat;
      o.material = on ? focusMatFor(base) : body ? dimBody : kit ? base : dimMat;
      o.castShadow = on || (kit && !body);
    });
  }
  for (const [name, m] of Object.entries(anim.cables)) if (m.visible) {
    const base = isGhost(m.userData.module, m.userData.requires) ? ghostMat : m.userData.baseMat;
    m.material = focus(name) ? focusMatFor(base) : dimMat;
  }
  const c = cables[state.pose] || (kit && cables.stand);
  for (const cc of [cables[state.pose], cables.stand]) if (cc && cc.visible) cc.traverse(o => {
    if (!o.isMesh || !o.visible) return;
    const base = o.material === ghostMat || isGhost((o.userData || {}).module, (o.userData || {}).requires) ? ghostMat : o.userData.baseMat;
    o.material = focus(o.name) ? focusMatFor(base) : kit ? base : dimMat;
  });
  if (anim.body && anim.body.visible) anim.body.material = dimBody;
  for (const b of Object.values(bodies)) if (b.visible) b.traverse(o => { if (o.isMesh) { o.material = dimBody; o.castShadow = false; } });
}
function clearFocus() {
  focus = null;
  for (const p of Object.values(parts)) p.obj.traverse(o => { if (o.isMesh) { o.material = isGhost(p.meta.module, p.meta.requires) ? ghostMat : o.userData.baseMat; o.castShadow = true; } });
  for (const m of Object.values(anim.cables)) m.material = m.userData.baseMat;
  if (anim.body) anim.body.material = anim.body.userData.baseMat;
  for (const b of Object.values(bodies)) b.traverse(o => { if (o.isMesh) { o.material = o.userData.baseMat; o.castShadow = true; } });
  if (!anim.on) apply();
}

// =====================================================================================
// GUIDED TOUR: six steps, one plain sentence each, the right parts glowing
// =====================================================================================
const TOUR = [
  { title: 'Meet Sitka', view: '34', spin: true, chip: 'Glowing: the springs, clutches and tendons',
    cap: 'This is Sitka. Your bones carry the weight; springs, clutches and cable tendons do what your muscles do.',
    items: [{ pose: 'stand' }], focus: /^(sit_leaf|knee_manifold|mode_lever|m2_leaf|whiffletree|t1_tendon|t3_tendon|m3_band|knee_arc)/ },
  { title: 'Sit anywhere', view: '34',
    cap: 'Sit down anywhere: a light pole under each hip takes most of your weight (69%), and the knee spring stores energy and gives it back when you stand.',
    items: [{ seq: 'sitdown', speed: 0.6, hold: 1.6 }, { seq: 'standup', speed: 0.6, hold: 1.2 }], focus: /^(strut_|seat_cup|sit_leaf|knee_manifold|mode_lever|t1_tendon|knee_arc)/ },
  { title: 'Lean back', view: 'side', frame: ['chair'], chip: 'Glowing: the two lean-back straps',
    cap: 'Lean back: two straps hold you, like a camp chair you wear.',
    items: [{ pose: 'chair' }], focus: /^(crazycreek|dring_cc)/ },
  { title: 'Lift', view: 'side', frame: ['stand', 'stoop'],
    cap: 'Lift: the back tendon stores energy as you bend, so a 15 kg box feels about 12 kg lighter, with no motor.',
    items: [{ seq: 'stoop', speed: 0.6, hold: 1.4 }], focus: /^(m2_leaf|whiffletree|t3_tendon|glute_guide|lumbar_standoff|panel_guide|thigh_cuff_[lr]$)/ },
  { title: 'Walk and run', view: 'side', frame: ['walk', 'run'],
    cap: 'Walk and run: elastic bands link your hips, knees and ankles, the way your hamstrings and calves do.',
    items: [{ seq: 'walk', speed: 0.45, dur: 6 }, { seq: 'run', speed: 0.45, dur: 5 }], focus: /^(m3_band|hamstring_band|running_band|calf_band|m3_standoff|knee_guide|dring_ham|dring_m3|runband_clip)/ },
  { title: 'Start small, add more', view: '34', kit: true,
    cap: 'Start with Seat + Back (about $1,300, under 10 lb), then add hips, ankles, shoulders and one optional motor, all docking into one hub.',
    items: [{ seq: 'kit', speed: 0.8, hold: 2.5 }], focus: null },
];
const tour = { on: false, i: 0 };
function kitFocus(name) {
  const g = KIT[anim.kitGi || 0]; if (!g) return false;
  return g[1](name) || g[2].some(c => name === c || name.startsWith(c + '_') || name.startsWith(c + '.'));
}
function tourStart(i = 0) {
  tour.on = true; ROOT.classList.add('touring');
  ui.open.ctl = ui.open.info = false; state.labels = false; tip.style.display = 'none';
  if (state.explode) { state.explode = 0; $('explode').value = 0; $('exVal').textContent = '0%'; }
  state.basic = state.coupling = true; state.upgrade = 'ghost'; state.body = 'on';
  const dots = $('tDots'); dots.innerHTML = TOUR.map(() => '<i></i>').join('');
  loadAnimData(true).catch(() => {});      // fetch the animation quietly while step 1 is read
  tourGo(i);
}
function tourGo(i) {
  tour.i = Math.max(0, Math.min(TOUR.length - 1, i));
  const S = TOUR[tour.i], last = tour.i === TOUR.length - 1;
  $('tCount').textContent = `${tour.i + 1} of ${TOUR.length}`;
  [...$('tDots').children].forEach((d, k) => { d.className = k === tour.i ? 'on' : k < tour.i ? 'done' : ''; });
  $('tTitle').textContent = S.title; $('tCap').textContent = S.cap; $('tPhase').textContent = S.chip || '';
  $('tBack').disabled = tour.i === 0;
  $('tNext').textContent = last ? 'Explore on your own' : 'Next';
  $('tSkip').style.visibility = last ? 'hidden' : 'visible';
  try { localStorage.setItem('sitka_tour_seen', '1'); } catch (e) {}
  clearFocus();
  focus = S.kit ? kitFocus : (n => S.focus.test(n));
  framePoses = S.frame || ['stand'];
  syncSheets();
  controls.autoRotate = !!S.spin; controls.autoRotateSpeed = 0.7;
  runProgram({ key: 'tour', items: S.items }).then(() => { if (tour.on && TOUR[tour.i] === S) setView(S.view); });
  setView(S.view);
}
function tourEnd() {
  tour.on = false; ROOT.classList.remove('touring');
  try { localStorage.setItem('sitka_tour_seen', '1'); } catch (e) {}
  controls.autoRotate = false; stopProgram(); if (anim.on) stopAnim();
  clearFocus(); framePoses = null; state.pose = 'stand'; apply(); syncSheets(); setView('34');
}
$('tNext').onclick = () => { if (tour.i >= TOUR.length - 1) tourEnd(); else tourGo(tour.i + 1); };
$('tBack').onclick = () => tourGo(tour.i - 1);
$('tSkip').onclick = () => tourEnd();
addEventListener('keydown', e => {
  if (!tour.on) return;
  if (e.key === 'ArrowRight') $('tNext').click(); else if (e.key === 'ArrowLeft' && tour.i) tourGo(tour.i - 1); else if (e.key === 'Escape') tourEnd();
});
function tourTick() {
  if (!tour.on) return;
  const S = TOUR[tour.i]; if (S.chip) return;
  const ph = anim.on ? phaseOf(anim.seq) : '';
  if ($('tPhase').textContent !== ph) $('tPhase').textContent = ph;
}
// the caption bar on the main screen
function captionTick() {
  if (tour.on) return;
  let ph = '', txt;
  if (anim.on) { ph = phaseOf(anim.seq); txt = prog.cur && prog.cur.cap ? prog.cur.cap : CAP_SHORT[anim.seq]; if (ROOT.classList.contains('compact')) txt = ph + '. ' + txt; }
  else txt = state.pose === 'stand' ? 'Tap Walk, Sit or Lift to watch how it works.' : POSE_PLAIN[state.pose];
  if ($('peekTxt').textContent !== txt) { $('peekTxt').textContent = txt; ROOT.style.setProperty('--dockh', $('dock').offsetHeight + 'px'); }
  if ($('peekPh').textContent !== ph) $('peekPh').textContent = ph;
}
window.SITKA_ANIM_API = { startSeq, stopAnim, anim, seek: (f) => { anim.playing = false; anim.t = f * seqLen(anim.seq); } };
window.SITKA_TOUR = { start: tourStart, go: tourGo, end: tourEnd, tour, prog };

// ---------- loop ----------
function resize() {
  const w = innerWidth, h = innerHeight;
  renderer.setSize(w, h, false); renderer.domElement.style.width = w + 'px'; renderer.domElement.style.height = h + 'px';
  camera.aspect = w / h; camera.updateProjectionMatrix();
  svg.setAttribute('width', w); svg.setAttribute('height', h);
  layout();
}
let rsT = 0, lastW = 0, lastH = 0;
function onResize() {
  const w0 = innerWidth, h0 = innerHeight; resize();
  // re-frame on a real size change (rotation, window resize), not on the iOS toolbar wobble
  clearTimeout(rsT); rsT = setTimeout(() => { if (ready && (Math.abs(innerWidth - lastW) > 40 || Math.abs(innerHeight - lastH) > 120)) { setView(state.view); } lastW = innerWidth; lastH = innerHeight; }, 180);
}
window.addEventListener('resize', onResize); window.addEventListener('orientationchange', onResize); resize();
lastW = innerWidth; lastH = innerHeight;
document.addEventListener('gesturestart', e => e.preventDefault());
if (window.visualViewport) visualViewport.addEventListener('resize', () => layout());
document.addEventListener('dblclick', e => e.preventDefault());
let lastLbl = 0, lastT = 0;
function loop(t) {
  requestAnimationFrame(loop);
  const dt = Math.min(0.1, (t - lastT) / 1000 || 0); lastT = t;
  progTick(dt);
  animTick(dt);
  tweenTick(dt);
  applyFocus(t);
  tourTick(); captionTick();
  controls.update();
  renderer.render(scene, camera);
  if (t - lastLbl > 120) { drawLabels(); lastLbl = t; }
}
init().then(async () => {
  applyCamParam(); requestAnimationFrame(loop);
  const sq = Q.get('anim');
  let seen = false; try { seen = !!localStorage.getItem('sitka_tour_seen'); } catch (e) {}
  const tq = Q.get('tour');
  if (tq && tq !== '0') { tourStart(Math.max(0, (parseInt(Q.get('step') || '1', 10) || 1) - 1)); return; }
  if (!sq && !seen && tq !== '0' && !Q.get('pose') && !Q.get('cam')) { tourStart(0); return; }
  if (sq) { window.__ready = false; await startSeq(sq); if (Q.get('at')) { anim.playing = false; anim.t = parseFloat(Q.get('at')) * seqLen(sq); } window.__ready = true; }
}).catch(e => {
  showLoading('Load error', 0); $('ldSub').textContent = String(e); window.__errs = [String(e)]; console.error(e);
});
window.SITKA = { state, apply, setView };
