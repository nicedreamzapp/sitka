// Sitka smart-tier brain: simulated sensors, the mode model, and the plain-code safety layer.
// One file, used three ways: the 3D viewer (<script>, window.SitkaBrain), the training script
// (node brain/brain_cli.mjs features) and the offline check (node brain/brain_cli.mjs viewer).
// The sensor and feature code lives only here, so training and the viewer can never drift apart.
//
// Everything this file reads is SIMULATED from motion capture: joint tracks in, synthetic IMU
// (thigh, shin, hub) and pressure-insole load out. See SMART_BRAIN.md.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.SitkaBrain = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';
  const HZ = 50;                 // brain loop rate (Hz)
  const WIN = 50;                // model window: 50 steps = 1.0 s
  const CLASSES = ['STAND', 'WALK', 'RUN', 'SIT', 'LIFT'];         // trained on mocap
  const PLANNED = ['CLIMB', 'DESCEND'];                             // in the design, no training data yet
  const FEATURES = ['thighL', 'shinL', 'kneeL', 'thighRateL', 'shinRateL', 'insoleL',
    'thighR', 'shinR', 'kneeR', 'thighRateR', 'shinRateR', 'insoleR', 'trunk', 'trunkRate', 'hubAz'];
  const MIRROR = [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 12, 13, 14];
  const TRACKS = ['hipL', 'hipR', 'kneeL', 'kneeR', 'ankleL', 'ankleR', 'toeL', 'toeR', 'pelvis', 'trunk'];
  const G = 9.81;

  // ---------------------------------------------------------------- small math
  const clamp = (x, a, b) => Math.max(a, Math.min(b, x));
  const smooth01 = (x, a, b) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
  const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
  const dot = (a, b) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
  const norm = a => Math.hypot(a[0], a[1], a[2]);
  function pct(arr, p) { const s = Array.from(arr).sort((x, y) => x - y); return s[Math.min(s.length - 1, Math.max(0, Math.round(p * (s.length - 1))))]; }

  // ---------------------------------------------------------------- track resampling
  // tracks: { fps, loop, n, hipL: [x,y,z, x,y,z, ...], ... }  (metres, +X left, -Y forward, +Z up)
  // Catmull-Rom between frames, so 15-30 fps viewer keyframes give smooth rates and accelerations.
  function samplePoint(arr, n, loop, x) {
    let i1 = Math.floor(x); const f = x - i1;
    const idx = k => loop ? ((k % n) + n) % n : clamp(k, 0, n - 1);
    const i0 = idx(i1 - 1), j1 = idx(i1), i2 = idx(i1 + 1), i3 = idx(i1 + 2);
    const out = [0, 0, 0];
    const f2 = f * f, f3 = f2 * f;
    for (let a = 0; a < 3; a++) {
      const p0 = arr[i0 * 3 + a], p1 = arr[j1 * 3 + a], p2 = arr[i2 * 3 + a], p3 = arr[i3 * 3 + a];
      out[a] = 0.5 * ((2 * p1) + (-p0 + p2) * f + (2 * p0 - 5 * p1 + 4 * p2 - p3) * f2 + (-p0 + 3 * p1 - 3 * p2 + p3) * f3);
    }
    return out;
  }
  function seqLength(tr) { return tr.loop ? tr.n / tr.fps : (tr.n - 1) / tr.fps; }

  // ---------------------------------------------------------------- sensor synthesis
  // Returns a 50 Hz stream. opts.cycles (loops: how many times round), opts.pad (non-loops: seconds of the
  // first frame held still before t = 0, so the 1 s model window has history). stream.t0 = index of seq time 0.
  function synth(tr, opts = {}) {
    const L = seqLength(tr);
    let times = [], t0 = 0;
    if (tr.loop) {
      const cyc = opts.cycles || 3; const N = Math.round(cyc * L * HZ);
      for (let k = 0; k < N; k++) times.push((k / HZ) % L);
      t0 = Math.round((cyc - 1) * L * HZ);
    } else {
      const pad = opts.pad == null ? 1.0 : opts.pad; const N = Math.round((pad + L) * HZ) + 1;
      for (let k = 0; k < N; k++) times.push(Math.max(0, k / HZ - pad));
      t0 = Math.round(pad * HZ);
    }
    const T = times.length;
    const P = {};
    for (const k of TRACKS) P[k] = times.map(t => samplePoint(tr[k], tr.n, tr.loop, t * tr.fps));
    // floor calibration (on the device: a still-standing calibration at power-up)
    const ankZ = [], toeZ = [];
    for (let i = 0; i < T; i++) { ankZ.push(P.ankleL[i][2], P.ankleR[i][2]); toeZ.push(P.toeL[i][2], P.toeR[i][2]); }
    const aFloor = pct(ankZ, 0.05), tFloor = pct(toeZ, 0.05);
    let thighLen = 0, shinLen = 0;
    for (let i = 0; i < T; i++) for (const s of ['L', 'R']) { thighLen += norm(sub(P['knee' + s][i], P['hip' + s][i])); shinLen += norm(sub(P['ankle' + s][i], P['knee' + s][i])); }
    thighLen /= 2 * T; shinLen /= 2 * T;
    const standH = thighLen + shinLen + (aFloor - tFloor);

    const lp = (prev, x, a) => prev == null ? x : prev + a * (x - prev);
    const A_ANG = 0.55, A_RATE = 0.45, A_ACC = 0.25;   // causal one-pole filters at 50 Hz (~10, ~7, ~3 Hz)
    const S = { T, t0, hz: HZ, L, loop: !!tr.loop, steps: [], X: [] };
    let prev = null;
    for (let i = 0; i < T; i++) {
      const hipL = P.hipL[i], hipR = P.hipR[i];
      const lr = sub(hipL, hipR); const h = Math.hypot(lr[0], lr[1]) || 1;
      const fwd = [lr[1] / h, -lr[0] / h, 0];              // pelvis forward (heading-free, like a real IMU)
      const sag = (d, up) => Math.atan2(dot(d, fwd), up ? d[2] : -d[2]);
      const st = { i, side: {} };
      for (const s of ['L', 'R']) {
        const hip = P['hip' + s][i], knee = P['knee' + s][i], ank = P['ankle' + s][i], toe = P['toe' + s][i];
        const th = sag(sub(knee, hip)), sh = sag(sub(ank, knee));
        const sole = Math.min(ank[2] - aFloor, toe[2] - tFloor);
        const pv = prev && prev.side[s];
        const thF = lp(pv && pv.thigh, th, A_ANG), shF = lp(pv && pv.shin, sh, A_ANG);
        const rT = lp(pv && pv.thighRate, pv ? (thF - pv.thigh) * HZ : 0, A_RATE);
        const rS = lp(pv && pv.shinRate, pv ? (shF - pv.shin) * HZ : 0, A_RATE);
        const mid = [(knee[0] + ank[0]) / 2, (knee[1] + ank[1]) / 2, (knee[2] + ank[2]) / 2];
        st.side[s] = { thigh: thF, shin: shF, knee: thF - shF, thighRate: rT, shinRate: rS, sole, contact: smooth01(-sole, -0.04, -0.012), mid,
          horiz: Math.hypot(ank[0] - (hipL[0] + hipR[0]) / 2, ank[1] - (hipL[1] + hipR[1]) / 2) };
      }
      const tv = P.trunk[i]; const trunk = Math.atan2(dot(tv, fwd), tv[2]);
      st.trunk = lp(prev && prev.trunk, trunk, A_ANG);
      st.trunkRate = lp(prev && prev.trunkRate, prev ? (st.trunk - prev.trunk) * HZ : 0, A_RATE);
      // hub IMU vertical acceleration (pelvis), second difference, low-passed
      const pz = P.pelvis[i][2], pz1 = i > 0 ? P.pelvis[i - 1][2] : pz, pz2 = i > 1 ? P.pelvis[i - 2][2] : pz1;
      st.hubAz = lp(prev && prev.hubAz, (pz - 2 * pz1 + pz2) * HZ * HZ, A_ACC);
      // simulated shin IMU: gyro (sagittal, deg/s) and specific force magnitude (g)
      for (const s of ['L', 'R']) {
        const m = st.side[s].mid, m1 = i > 0 ? prev.side[s].mid : m, m2 = i > 1 ? prev.side[s].mid1 || m1 : m1;
        const acc = [(m[0] - 2 * m1[0] + m2[0]) * HZ * HZ, (m[1] - 2 * m1[1] + m2[1]) * HZ * HZ, (m[2] - 2 * m1[2] + m2[2]) * HZ * HZ + G];
        st.side[s].mid1 = m1;
        st.side[s].gyroShin = st.side[s].shinRate * 180 / Math.PI;
        st.side[s].gyroThigh = st.side[s].thighRate * 180 / Math.PI;
        st.side[s].accShin = lp(prev && prev.side[s].accShin, norm(acc) / G, A_ACC);
      }
      // simulated insoles: fraction of body weight on each foot
      const hipMidZ = (hipL[2] + hipR[2]) / 2;
      const hRel = (hipMidZ - tFloor) / standH;
      const thighMean = (st.side.L.thigh + st.side.R.thigh) / 2;
      const seat = 0.75 * smooth01(-hRel, -0.97, -0.90) * smooth01(thighMean, 0.44, 0.79);   // seat/strut takes weight
      const F = clamp(1 + st.hubAz / G, 0, 3);
      const wL = st.side.L.contact / (0.08 + st.side.L.horiz), wR = st.side.R.contact / (0.08 + st.side.R.horiz);
      const sw = wL + wR;
      st.side.L.insole = sw > 1e-6 ? F * (1 - seat) * wL / sw : 0;
      st.side.R.insole = sw > 1e-6 ? F * (1 - seat) * wR / sw : 0;
      st.hRel = hRel; st.seat = seat;
      S.steps.push(st);
      const L_ = st.side.L, R_ = st.side.R;
      S.X.push([L_.thigh, L_.shin, L_.knee, L_.thighRate, L_.shinRate, L_.insole,
        R_.thigh, R_.shin, R_.knee, R_.thighRate, R_.shinRate, R_.insole, st.trunk, st.trunkRate, st.hubAz / G]);
      prev = st;
    }
    return S;
  }

  // ---------------------------------------------------------------- the model (tiny 1D CNN)
  // M = { mean[C], std[C], layers: [{W:[out][in][k], b:[out], stride}], dense: {W:[K][H], b:[K]}, classes }
  function conv(x, Ly) {           // x: [C][T] -> relu(conv valid)
    const W = Ly.W, b = Ly.b, s = Ly.stride || 1, O = W.length, C = W[0].length, K = W[0][0].length;
    const T = x[0].length, To = Math.floor((T - K) / s) + 1;
    const y = [];
    for (let o = 0; o < O; o++) {
      const row = new Float32Array(To);
      for (let t = 0; t < To; t++) {
        let acc = b[o];
        for (let c = 0; c < C; c++) { const w = W[o][c], xc = x[c], off = t * s; for (let k = 0; k < K; k++) acc += w[k] * xc[off + k]; }
        row[t] = acc > 0 ? acc : 0;
      }
      y.push(row);
    }
    return y;
  }
  function predictWindow(M, rows) {   // rows: WIN x C (time-major raw features)
    const C = rows[0].length, x = [];
    for (let c = 0; c < C; c++) { const r = new Float32Array(rows.length); for (let t = 0; t < rows.length; t++) r[t] = (rows[t][c] - M.mean[c]) / M.std[c]; x.push(r); }
    let h = x;
    for (const Ly of M.layers) h = conv(h, Ly);
    const g = h.map(r => { let s = 0; for (const v of r) s += v; return s / r.length; });
    const z = M.dense.W.map((w, k) => w.reduce((a, wi, i) => a + wi * g[i], M.dense.b[k]));
    const mx = Math.max(...z); const e = z.map(v => Math.exp(v - mx)); const se = e.reduce((a, v) => a + v, 0);
    return e.map(v => v / se);
  }
  function predictStream(M, S) {
    const out = [];
    for (let i = 0; i < S.T; i++) {
      const rows = [];
      for (let k = i - WIN + 1; k <= i; k++) rows.push(S.X[Math.max(0, k)]);
      out.push(predictWindow(M, rows));
    }
    return out;
  }
  function modelSize(M) {
    let n = M.dense.W.length * M.dense.W[0].length + M.dense.b.length;
    for (const L of M.layers) n += L.W.length * L.W[0].length * L.W[0][0].length + L.b.length;
    return n;
  }

  // ---------------------------------------------------------------- the safety layer (plain code, final say)
  // The model suggests a mode. These rules decide what every clutch and the motor actually do.
  const RULES = {
    CONF_MODE: 0.6,          // below this the model is "unsure": all walking clutches open, motor off
    CONF_MOTOR: 0.8,         // the motor needs the model this sure
    DEBOUNCE: 6,             // a new mode must win 6 steps in a row (120 ms) before the hub switches
    LOAD_MIN: 0.10,          // a stance clutch never locks with less than 10% body weight on that insole
    HEEL_STRIKE: 0.20,       // insole rising through 20% BW = heel strike
    SWING_RATE: 3.0,         // knee flexing faster than 3 rad/s = swing has started: clutch must be open
    LOCK_SHARE: 0.35,        // stance clutch holds for the first 35% of the stride (weight acceptance)
    TRUNK_LIFT: 0.61,        // 35 degrees: the lift tendon starts to load
    SEAT_THIGH: 0.70,        // ~40 degrees thigh flexion before the sit cam may hold
    STEP_RATE: 0.8,          // a gait mode needs steps: some thigh swinging faster than 0.8 rad/s in the last second
  };
  function makeController() {
    return { mode: 'STAND', cand: null, candN: 0, motion: 0, side: { L: { hs: -1, prevHs: -1, period: 1.1, prevIns: 0, lock: false }, R: { hs: -1, prevHs: -1, period: 1.1, prevIns: 0, lock: false } }, vetoT: -99, vetoWhy: '' };
  }
  function decide(ctl, st, probs, i) {
    // 1. mode, debounced
    let k = 0; for (let j = 1; j < probs.length; j++) if (probs[j] > probs[k]) k = j;
    const raw = CLASSES[k], conf = probs[k];
    const vetoes = [];
    // a gait mode needs steps: the fastest thigh swing in the last second (decaying peak hold)
    ctl.motion = Math.max(ctl.motion * Math.exp(-1 / HZ), Math.abs(st.side.L.thighRate), Math.abs(st.side.R.thighRate));
    let want = raw;
    if ((raw === 'WALK' || raw === 'RUN') && ctl.motion < RULES.STEP_RATE) { want = 'STAND'; vetoes.push('no steps: not ' + raw.toLowerCase()); }
    if (want !== ctl.mode && conf >= RULES.CONF_MODE) {
      if (ctl.cand === want) ctl.candN++; else { ctl.cand = want; ctl.candN = 1; }
      if (ctl.candN >= RULES.DEBOUNCE) { ctl.mode = want; ctl.cand = null; ctl.candN = 0; }
    } else { ctl.cand = null; ctl.candN = 0; }
    const mode = ctl.mode, unsure = conf < RULES.CONF_MODE;
    // 2. stance clutch per side (T1b, electroadhesive, fails open)
    const clutch = {};
    for (const s of ['L', 'R']) {
      const sd = st.side[s], c = ctl.side[s];
      if (c.prevIns < RULES.HEEL_STRIKE && sd.insole >= RULES.HEEL_STRIKE && sd.thigh > 0.1) {   // insole + thigh IMU agree: heel strike, leg in front
        if (c.hs >= 0) c.period = clamp((i - c.hs) / HZ, 0.5, 1.6);
        c.prevHs = c.hs; c.hs = i;
      }
      c.prevIns = sd.insole;
      const sinceHs = c.hs >= 0 ? (i - c.hs) / HZ : 99;
      const want = (mode === 'WALK' || mode === 'DESCEND') && sinceHs < RULES.LOCK_SHARE * c.period;
      let lock = want, why = '';
      if (want && sd.insole < RULES.LOAD_MIN) { lock = false; why = s + ' insole unloaded'; }
      else if (want && sd.thighRate - sd.shinRate > RULES.SWING_RATE) { lock = false; why = s + ' knee swinging'; }
      else if (want && unsure) { lock = false; why = 'model unsure'; }
      if (why) vetoes.push(why);
      clutch[s] = lock ? 'LOCKED' : 'OPEN';
    }
    // 3. sit cam (mechanical, the only lock allowed to hold with power off) and the SIT sub-phase
    const thighMean = (st.side.L.thigh + st.side.R.thigh) / 2, thighRate = (st.side.L.thighRate + st.side.R.thighRate) / 2;
    let phase = '';
    if (mode === 'SIT') phase = thighRate > 0.25 ? 'sitting down' : thighRate < -0.25 ? 'standing up' : thighMean > RULES.SEAT_THIGH ? 'seated' : 'settling';
    else if (mode === 'LIFT') phase = st.trunkRate < -0.2 ? 'lifting' : st.trunkRate > 0.2 ? 'bending' : st.trunk > RULES.TRUNK_LIFT ? 'bent over' : 'upright';
    else if (mode === 'WALK' || mode === 'RUN') phase = (st.side.L.insole > 0.1 ? 'L' : '') + (st.side.R.insole > 0.1 ? (st.side.L.insole > 0.1 ? '+R' : 'R') : '') || 'flight';
    const cam = mode === 'SIT' && phase === 'seated' ? 'HOLDS' : 'free';
    // 4. the one motor (P1)
    let motorWant = 'off';
    const liftRising = mode === 'LIFT' && st.trunk > RULES.TRUNK_LIFT * 0.6 && st.trunkRate < -0.2;
    if (liftRising) motorWant = 'assist';
    else if (mode === 'SIT' && phase === 'standing up') motorWant = 'assist';
    else if (mode === 'CLIMB') motorWant = 'assist';
    else if (mode === 'DESCEND') motorWant = 'regen';
    let motor = motorWant;
    if (motorWant !== 'off' && conf < RULES.CONF_MOTOR) { motor = 'off'; vetoes.push('motor: model under 80%'); }
    else if (liftRising && thighRate > 0.1) { motor = 'off'; vetoes.push('motor: thighs flexing, not a lift'); }
    else if (motorWant === 'assist' && st.side.L.insole < RULES.LOAD_MIN && st.side.R.insole < RULES.LOAD_MIN) { motor = 'off'; vetoes.push('motor: both feet unloaded'); }
    if (vetoes.length) { ctl.vetoT = i; ctl.vetoWhy = vetoes[0]; }
    return { raw, conf, mode, unsure, phase, clutch, cam, motor, vetoes, veto: vetoes.length > 0 };
  }

  // ---------------------------------------------------------------- whole stream
  function run(M, tr, opts = {}) {
    const S = synth(tr, opts);
    const probs = predictStream(M, S);
    const ctl = makeController();
    const D = [];
    for (let i = 0; i < S.T; i++) D.push(decide(ctl, S.steps[i], probs[i], i));
    return { S, probs, D };
  }
  // per-mode share of the sequence's own time span (last loop for walk/run)
  function summarize(R) {
    const { S, D } = R; const n0 = S.t0, n1 = S.loop ? S.T : S.T;
    const cnt = {}, rawCnt = {}; let veto = 0, lockL = 0, lockR = 0, motor = 0, N = 0;
    for (let i = n0; i < n1; i++) {
      const d = D[i]; N++;
      cnt[d.mode] = (cnt[d.mode] || 0) + 1; rawCnt[d.raw] = (rawCnt[d.raw] || 0) + 1;
      if (d.veto) veto++; if (d.clutch.L === 'LOCKED') lockL++; if (d.clutch.R === 'LOCKED') lockR++; if (d.motor !== 'off') motor++;
    }
    const pctOf = o => Object.fromEntries(Object.entries(o).map(([k, v]) => [k, Math.round(1000 * v / N) / 10]));
    return { steps: N, mode: pctOf(cnt), raw: pctOf(rawCnt), vetoPct: Math.round(1000 * veto / N) / 10,
      lockPctL: Math.round(1000 * lockL / N) / 10, lockPctR: Math.round(1000 * lockR / N) / 10, motorPct: Math.round(1000 * motor / N) / 10 };
  }

  // ---------------------------------------------------------------- viewer data -> joint tracks
  // The viewer's baked animation (cad/viewer/sitka_anim.js) stores a 3x4 matrix per part per frame.
  // The shells sit on the joints: thigh_shell = hip, ptb_shell = knee, shoe = ankle; back_panel gives the trunk.
  const TOE_LOCAL = [0, 0.13, 0.07];            // ball of the foot in the shoe frame (+y forward, +z down)
  function tracksFromViewer(A, seqName) {
    const S = A.seqs[seqName]; const idx = {}; A.parts.forEach((p, k) => { idx[p] = k; });
    const need = ['thigh_shell_l', 'thigh_shell_r', 'ptb_shell_l', 'ptb_shell_r', 'shoe_l', 'shoe_r', 'hip_belt', 'back_panel'];
    for (const p of need) if (!(p in idx)) throw new Error('viewer data has no part ' + p);
    const tr = { fps: S.fps || 15, loop: !!S.loop, n: S.n };
    for (const k of TRACKS) tr[k] = new Float64Array(S.n * 3);
    const put = (k, f, v) => { tr[k][f * 3] = v[0]; tr[k][f * 3 + 1] = v[1]; tr[k][f * 3 + 2] = v[2]; };
    for (let f = 0; f < S.n; f++) {
      const F = S.parts[f]; const m = p => F[idx[p]];
      const pos = a => [a[3], a[7], a[11]];
      const mul = (a, v) => [a[0] * v[0] + a[1] * v[1] + a[2] * v[2] + a[3], a[4] * v[0] + a[5] * v[1] + a[6] * v[2] + a[7], a[8] * v[0] + a[9] * v[1] + a[10] * v[2] + a[11]];
      put('hipL', f, pos(m('thigh_shell_l'))); put('hipR', f, pos(m('thigh_shell_r')));
      put('kneeL', f, pos(m('ptb_shell_l'))); put('kneeR', f, pos(m('ptb_shell_r')));
      put('ankleL', f, pos(m('shoe_l'))); put('ankleR', f, pos(m('shoe_r')));
      put('toeL', f, mul(m('shoe_l'), TOE_LOCAL)); put('toeR', f, mul(m('shoe_r'), TOE_LOCAL));
      put('pelvis', f, pos(m('hip_belt')));
      const bp = m('back_panel'); const up = [bp[2], bp[6], bp[10]]; const u = norm(up) || 1;   // panel local +Z
      put('trunk', f, [up[0] / u, up[1] / u, up[2] / u]);
    }
    return tr;
  }

  return { HZ, WIN, CLASSES, PLANNED, FEATURES, MIRROR, TRACKS, RULES, synth, predictWindow, predictStream, modelSize, makeController, decide, run, summarize, tracksFromViewer, seqLength };
});
