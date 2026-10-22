// SEAT MODE v2 — TRIPOD STATICS. Does the seat actually stand up, and what does
// each part carry, for a 95th-percentile adult at each lock angle?
//
// THE MECHANISM (side view, one leg; both legs identical, each carries half):
//   * Heel stirrup + shoe sit on the ground; the exo's ANKLE PIVOT is free (+35° dorsi / −45° plantar),
//     so the shin rail is pinned at the ankle and the wearer's own ankle muscles relax.
//   * Thigh rail + locked knee + shin rail = one rigid frame B ("the leg unit").
//   * REAR LEG: a telescoping carbon pole hinged at the top of the thigh rail, foot on
//     the ground behind the heel. Pinned at both ends → a two-force member: it can only
//     push along its own axis (compression), never pull.
//   * Gravity on B: half the head-arms-trunk (HAT) weight — whose resultant passes through
//     the HAT centre of mass however it is shared between pad and hip joint — plus one
//     thigh, one shank, and the exo's own mass.
//
//   Moment balance of B about the ankle pivot gives the rear-leg force N:
//       sum(W_i * x_i) + N * [(Hr - A) x u] = 0          (x = forward of the ankle)
//   N must be ≥ 0 (a strut cannot pull): the load line has to fall BEHIND the ankle.
//   The knee lock carries the moment of everything above the knee about the knee.
//   Tipping: the WHOLE-system centre of mass must lie inside the support polygon
//   (rear feet … toes). Margin < 0.10 m is flagged.
//
// Coordinates: metres, x forward of the ankle axis, y up from the floor.
import { PERSON, SEAT, RATCHET, MAT, AK10_9, AK80_64, g, line, fmt } from './params.mjs';
import { budget } from './mass_budget.mjs';

const R = Math.PI / 180;
const add = (a, b) => [a[0] + b[0], a[1] + b[1]], sub = (a, b) => [a[0] - b[0], a[1] - b[1]];
const mul = (a, k) => [a[0] * k, a[1] * k], cross = (a, b) => a[0] * b[1] - a[1] * b[0];
const norm = (a) => Math.hypot(a[0], a[1]);

const EXO = budget();          // exo masses from bom.mjs (per leg and belt)
const ANKLE_H = 0.08;          // ankle axis above the floor in a shoe, EST (same as the CAD)
// Per-leg exo mass split by where it rides (bom.mjs loc tags). The knee items (actuator,
// ratchet, hinge) sit on the axis, so half goes to each side of the knee.
const perLeg = (k) => (EXO.byLoc[k] || 0) / 2;
const EXO_THIGH = perLeg('thigh') + perLeg('knee') / 2;
const EXO_SHANK = perLeg('shank') + perLeg('ankle') + perLeg('knee') / 2;
const EXO_FOOT = perLeg('foot');

export function tripod(mode, { rearLeg = mode.rear, massKg = PERSON.mass95, stature = PERSON.stature95 } = {}) {
  const Lt = PERSON.thighFrac * stature, Ls = PERSON.shankFrac * stature;
  const th = mode.knee * R, phi = mode.phi * R, tr = mode.trunk * R;
  const A = [0, ANKLE_H];
  const K = [Ls * Math.sin(phi), ANKLE_H + Ls * Math.cos(phi)];
  const tdir = [-Math.sin(th - phi), Math.cos(th - phi)];          // knee → hip
  const Hip = add(K, mul(tdir, Lt));
  const padFrac = mode.padFrac ?? SEAT.padCoPFrac;
  const Pad = add(K, mul(tdir, padFrac * Lt));
  const Hr = add(K, mul(tdir, SEAT.rearHingeFrac * Lt));
  const hat = add(Hip, [SEAT.hatCoMAboveHip * Math.sin(tr), SEAT.hatCoMAboveHip * Math.cos(tr)]);
  const thighC = add(K, mul(tdir, (1 - 0.4095) * Lt));            // de Leva COM 0.4095 from the hip
  const shankC = add(K, mul(sub(A, K), 0.4395));                   // de Leva COM 0.4395 from the knee
  const footC = [0.06, 0.04];                                       // EST
  const m = massKg, mf = PERSON;
  // per-leg masses (kg): half of HAT and of the belt, one of each leg segment, one exo leg
  const mHat = (m * (1 - 2 * (mf.thighMassFrac + mf.shankMassFrac + mf.footMassFrac))) / 2;
  const legExo = EXO.perLeg, beltHalf = EXO.waistKg / 2;
  const loadsAboveKnee = [
    { n: 'HAT/2 + belt/2', kg: mHat + beltHalf, at: hat },
    { n: 'thigh', kg: m * mf.thighMassFrac, at: thighC },
    { n: 'exo thigh side', kg: EXO_THIGH, at: add(K, mul(tdir, 0.5 * Lt)) },
  ];
  const loadsBelowKnee = [
    { n: 'shank', kg: m * mf.shankMassFrac, at: shankC },
    { n: 'exo shank side', kg: EXO_SHANK, at: add(K, mul(sub(A, K), 0.5)) },
  ];
  const footLoads = [{ n: 'foot + stirrup', kg: m * mf.footMassFrac + EXO_FOOT, at: footC }];
  const B = [...loadsAboveKnee, ...loadsBelowKnee];
  const WB = B.reduce((s, l) => s + l.kg * g, 0);
  const MgA = B.reduce((s, l) => s + (l.at[0] - A[0]) * (-l.kg * g), 0);   // z-moment of gravity about the ankle

  // rear foot placement: as far back as allowed (rearBackMax), trimmed so mu_req ≤ rearMuDesign
  const heelX = SEAT.heelX, toeX = SEAT.toeX;
  let rear = null;
  if (rearLeg) {
    let back = SEAT.rearBackMax, Rf, u, mu;
    for (; back > 0.05; back -= 0.005) {
      Rf = [heelX - back, 0]; u = mul(sub(Hr, Rf), 1 / norm(sub(Hr, Rf))); mu = Math.abs(u[0] / u[1]);
      if (mu <= SEAT.rearMuDesign) break;
    }
    const len = norm(sub(Hr, Rf));
    const N = -MgA / cross(sub(Hr, A), u);              // axial compression, N
    rear = { back, Rf, u, mu, len, N, angleDeg: Math.atan2(Math.abs(u[0]), u[1]) / R };
  }
  const Nvec = rear ? mul(rear.u, rear.N) : [0, 0];
  const RA = [-Nvec[0], WB - Nvec[1]];                    // ankle-pivot reaction on B
  // knee lock: moment of everything above the knee about K, plus the rear-leg push at Hr
  const MK = loadsAboveKnee.reduce((s, l) => s + (l.at[0] - K[0]) * (-l.kg * g), 0) + (rear ? cross(sub(Hr, K), Nvec) : 0);
  // ankle muscle moment the WEARER must supply if there is no rear leg (like standing)
  const ankleMuscleNm = rear ? 0 : -MgA;
  // foot: ankle load + foot weight split between heel and metatarsal heads (relaxed ankle)
  const Wf = footLoads[0].kg * g, Fa = [-RA[0], -RA[1]];  // force from B on the foot
  const heel = [heelX, 0], met = [SEAT.metX, 0];
  let Tm = -(cross(sub(A, heel), Fa) + (footC[0] - heelX) * (-Wf) + (rear ? 0 : ankleMuscleNm)) / (met[0] - heel[0]);
  let Th = -Fa[1] + Wf - Tm;
  // whole-system centre of mass (both legs identical → per-leg is enough)
  const all = [...B, ...footLoads];
  const mTot = all.reduce((s, l) => s + l.kg, 0);
  const cgX = all.reduce((s, l) => s + l.kg * l.at[0], 0) / mTot;
  const cgY = all.reduce((s, l) => s + l.kg * l.at[1], 0) / mTot;
  const backEdge = rear ? rear.Rf[0] : heelX;
  const marginBack = cgX - backEdge, marginFront = toeX - cgX;
  const tooAnkle = !rear && Math.abs(ankleMuscleNm) > 0 && (cgX < heelX || cgX > toeX);
  return {
    mode, Lt, Ls, A, K, Hip, Pad, Hr, hat, rear, WB, MgA, RA, MK, ankleMuscleNm, Th, Tm, cgX, marginBack, marginFront,
    shareRear: rear ? (rear.N * rear.u[1]) / (WB + Wf) : 0,
    shareHeelToe: (Th + Tm) / (WB + Wf),
    ok: (rear ? rear.N >= 0 && rear.len <= SEAT.rearTube.maxLen && rear.len >= SEAT.rearTube.stowedLen : true) && marginBack >= 0.10 && marginFront >= 0.10,
    stable: marginBack > 0 && marginFront > 0,
    hipH: Hip[1], tooAnkle, cgY,
    tipBackDeg: Math.atan2(marginBack, cgY) / R, tipFwdDeg: Math.atan2(marginFront, cgY) / R,
    lateral: lateral(cgX, cgY, rear ? rear.Rf[0] : null),
  };
}

// LATERAL (front view): support polygon = both shoes + both rear feet. CoM is on the midline,
// so the side margin is the half-width of the polygon edge at the CoM's fore-aft station.
export function lateral(cgX, cgY, rearX) {
  const st = SEAT.stance, shoeOut = st.shoeCentreSep / 2 + st.shoeWidth / 2, rearOut = st.rearFootSep / 2;
  let half;
  if (rearX === null || cgX >= SEAT.heelX) half = shoeOut;                       // over the shoes
  else { const t = (SEAT.heelX - cgX) / (SEAT.heelX - rearX); half = shoeOut + (rearOut - shoeOut) * t; } // heel corner → rear foot
  return { half, tipDeg: Math.atan2(half, cgY) / R };
}

// Stepped pinned-pinned column: EI(x) y'' + P y = 0, finite differences + inverse iteration.
export function buckleStepped(segs, E) {
  const N = 600, Lt = segs.reduce((a, x) => a + x.L, 0), h = Lt / N, EI = [];
  for (let i = 1; i < N; i++) { let acc = 0, sg; for (sg of segs) { acc += sg.L; if (i * h <= acc + 1e-12) break; } EI.push(E * (Math.PI / 64) * (sg.od ** 4 - (sg.od - 2 * sg.wall) ** 4)); }
  const n = N - 1, a = -1 / h / h, b = 2 / h / h; let y = new Array(n).fill(1), lam = 0;
  for (let it = 0; it < 200; it++) {
    const d = y.map((v, k) => v / EI[k]), cp = [a / b], dp = [d[0] / b];
    for (let k = 1; k < n; k++) { const m = b - a * cp[k - 1]; cp[k] = a / m; dp[k] = (d[k] - a * dp[k - 1]) / m; }
    const z = new Array(n); z[n - 1] = dp[n - 1]; for (let k = n - 2; k >= 0; k--) z[k] = dp[k] - cp[k] * z[k + 1];
    const nz = Math.max(...z.map(Math.abs)); lam = Math.max(...y.map(Math.abs)) / nz; y = z.map((v) => v / nz);
  }
  return lam;
}

// ratchet tooth bending (Lewis-style cantilever: sigma = 6 F h / (b t^2))
export function toothStress(cfg, Mdesign) {
  const pitch = (2 * Math.PI * cfg.r) / cfg.teeth;
  const t = RATCHET.toothThickFrac * pitch, h = RATCHET.toothHeightFrac * pitch;
  const F = Mdesign / cfg.r / (cfg.effectiveTeeth ?? cfg.teethEngaged);
  return { pitch, F, sigma: (6 * F * h) / (cfg.width * t * t), stepDeg: 360 / cfg.teeth };
}

// v1 worst case kept as the FALLBACK structural load (rear leg slips, one leg takes it all)
export function fallbackDesignMoment() {
  const Lt = PERSON.thighFrac * PERSON.stature95, s = 0.65 * Lt;
  const mAbove = PERSON.mass95 * (1 - 2 * (PERSON.shankMassFrac + PERSON.footMassFrac));
  const F = (mAbove * g) / 2;
  return F * s * 2 * SEAT.lockSF;   // full lever (thigh horizontal), all weight on one leg, x SF
}

if (import.meta.url === `file://${process.argv[1]}`) {
  line('=== SEAT v2 — TRIPOD STATICS, 95th-pct US man (130.3 kg, 1.874 m, NHANES) ===');
  line(`Exo worn: ${fmt(EXO.perLeg, 2)} kg per leg + ${fmt(EXO.waistKg, 2)} kg belt (bom.mjs). Ankle pivot FREE; shank lean capped at ${SEAT.maxShankLeanDeg}° (loaded dorsiflexion).`);
  line(`Pad CoP at ${SEAT.padCoPFrac} x thigh from the knee (proximal). Rear-leg hinge at ${SEAT.rearHingeFrac} x thigh (rail top).`);
  line('');
  line('Mode         knee lean  hip ht  rear foot  leg len  angle  mu req  N axial  %rear  %heel+toe  KNEE LOCK  CoM vs heel  margin back/front   verdict');
  const rows = SEAT.modes.map((md) => tripod(md));
  for (const r of rows) {
    const re = r.rear;
    line(`${r.mode.name.padEnd(12)} ${String(r.mode.knee).padStart(4)}° ${String(r.mode.phi).padStart(3)}°  ${fmt(r.hipH, 2)} m  ` +
      (re ? `${fmt(re.back, 3)} m   ${fmt(re.len, 2)} m  ${fmt(re.angleDeg, 0).padStart(3)}°   ${fmt(re.mu, 2)}   ${fmt(re.N, 0).padStart(4)} N  ${fmt(r.shareRear * 100, 0).padStart(3)}%` : '   (stowed — no rear leg)                     0%') +
      `    ${fmt(r.shareHeelToe * 100, 0).padStart(3)}%    ${fmt(r.MK, 0).padStart(4)} Nm    ${fmt((r.cgX - SEAT.heelX) * 100, 1).padStart(5)} cm   ${fmt(r.marginBack, 2)} / ${fmt(r.marginFront, 2)} m   ${r.ok ? 'OK' : r.stable ? 'THIN MARGIN' : 'TIPS'}`);
  }
  line('\nTipping angles (CoM height, then how far the whole system must tilt before it goes over):');
  for (const r of rows) line(`  ${r.mode.name.padEnd(11)} CoM ${fmt(r.cgY, 2)} m high → back ${fmt(r.tipBackDeg, 0)}°, forward ${fmt(r.tipFwdDeg, 0)}°, sideways ${fmt(r.lateral.tipDeg, 0)}° (polygon half-width ${fmt(r.lateral.half, 2)} m at the CoM)`);
  line(`  Side check: shoes ${SEAT.stance.shoeCentreSep} m apart (EST), rear feet ${SEAT.stance.rearFootSep} m apart. A cross-slope of θ eats θ of the side margin.`);
  for (const md of SEAT.modes) if (md.phi > SEAT.maxShankLeanDeg) line(`  !! ${md.name}: shank lean ${md.phi}° exceeds the ${SEAT.maxShankLeanDeg}° ankle cap`);
  const perch = rows[0];
  line(`\nPERCH IS A LEAN-ASSIST, NOT HANDS-FREE SITTING (firmware, app and manual must never call it hands-free): the knee lock takes the bend, but your own calves keep you balanced,`);
  line(`exactly as when standing. Backward margin ${fmt(perch.marginBack * 100, 0)} cm (${fmt(perch.tipBackDeg, 0)}° tilt). Lean on a wall or pole, or deploy the rear legs and use Half-sit.`);
  line(`Perch has no rear leg: the wearer balances at the ankle exactly as when standing, ${fmt(Math.abs(perch.ankleMuscleNm), 0)} Nm per ankle (calf), CoM ${fmt(perch.cgX * 100, 1)} cm ${perch.cgX >= 0 ? 'ahead of' : 'behind'} the ankle.`);

  line('\n=== WITHOUT THE REAR LEG (stowed, broken, or soft ground) ===');
  for (const md of SEAT.modes) {
    const r = tripod(md, { rearLeg: false });
    line(`${md.name.padEnd(11)} knee lock ${fmt(r.MK, 0).padStart(4)} Nm, ankle muscle ${fmt(Math.abs(r.ankleMuscleNm), 0).padStart(3)} Nm, CoM ${fmt((r.cgX - SEAT.heelX) * 100, 1).padStart(6)} cm from the heel edge → ${r.cgX < SEAT.heelX ? 'BEHIND the heel: tips backward. NOT ALLOWED.' : r.marginBack < 0.1 ? 'inside the foot but thin: needs calf balance' : 'inside the foot (standing-style balance)'}`);
  }
  line('Firmware rule: with no rear leg detected on the ground (foot switch), ONLY Perch may lock.');

  line('\n=== WHY v1 HAD TO GO ===');
  const v1 = tripod(SEAT.v1Chair, { rearLeg: false });
  line(`v1 chair: shank lean 32.9° (past the ~20° comfortable dorsiflexion), pad CoP placed over the heel.`);
  line(`Whole-body CoM ${fmt((v1.cgX - SEAT.heelX) * 100, 1)} cm from the heel edge (the BACK edge of the support polygon) → backward margin ~${fmt(Math.abs(v1.cgX - SEAT.heelX) * 100, 0)} cm, a ${fmt(v1.tipBackDeg, 0)}° backward tilt to go over.`);
  line('A 3–4 cm lean back, a pack shift or a slope and you go over backward. "The feet take the rest" meant muscles,');
  line('which contradicted the 100% load share it assumed. The rear leg moves the back edge ~0.4 m further back.');

  line('\n=== CAN THE MOTOR HOLD IT? ===');
  const ch = rows[2];
  line(`Chair with rear leg: ${fmt(ch.MK, 0)} Nm per knee. AK10-9 peak ${AK10_9.peakNm} Nm → ${fmt(ch.MK / AK10_9.peakNm, 1)}x its peak, and ${fmt(AK10_9.copperW(48), 0)} W of heat at 48 Nm. Still a mechanical lock.`);
  const v1k = tripod(SEAT.v1Chair, { rearLeg: false });
  line(`v1 errors, for the record: v1 chair needed ${fmt(v1k.MK, 0)} Nm per knee in this model (v1 report: 142 Nm); the 48 Nm motor could never`);
  line('unload a pawl carrying that to let it lift, and a small solenoid cannot pull a loaded pawl out (~2 kN tooth friction).');
  line('v2 never asks either: the ratchet lets the knee EXTEND, which unloads the pawl by itself.');
  line(`(AK80-64: ${AK80_64.peakNm} Nm peak, but ${AK80_64.ratedRpm24} rpm cannot follow a running knee — rejected, see gait_assist_model.mjs.)`);

  const Mfb = fallbackDesignMoment();
  line(`\n=== ONE-WAY RATCHET (blocks flexion; extension always free) ===`);
  line(`Fallback design load (rear leg slips, thigh horizontal, all weight on ONE leg, x${SEAT.lockSF}): ${fmt(Mfb, 0)} Nm — the lock and rails are still sized for this.`);
  for (const [k, cfg] of [['v1 pawl', RATCHET.v1], ['v2 ratchet', RATCHET.v2]]) {
    const t = toothStress(cfg, Mfb);
    line(`${k.padEnd(10)}: ${cfg.teeth}T at r = ${cfg.r * 1000} mm, ${cfg.width * 1000} mm wide, ${cfg.effectiveTeeth ?? cfg.teethEngaged} tooth/teeth loaded → ${fmt(t.F / 1000, 1)} kN each, bending ${fmt(t.sigma / 1e6, 0)} MPa vs 17-4PH H900 yield ~${MAT.steel174_H900_yield / 1e6} MPa (VERIFY) → ${t.sigma > MAT.steel174_H900_yield ? 'FAILS' : 'SF ' + fmt(MAT.steel174_H900_yield / t.sigma, 1)}; step ${fmt(t.stepDeg, 0)}°`);
  }
  {
    const cfg = RATCHET.v2, t = toothStress(cfg, Mfb), h = RATCHET.toothHeightFrac * t.pitch;
    const pMatched = t.F / (cfg.width * h), single = toothStress({ ...cfg, effectiveTeeth: 1 }, Mfb);
    line(`Single tooth (one of the two misses): ${fmt(single.F / 1000, 1)} kN, bending ${fmt(single.sigma / 1e6, 0)} MPa → SF ${fmt(MAT.steel174_H900_yield / single.sigma, 1)}. Thin: PROOF TEST to 507 Nm is required.`);
    line(`Flank contact, MATCHED flank angles (flat-on-flat, crown relief at the edges): ${fmt(pMatched / 1e6, 0)} MPa with 2 teeth, ${fmt((2 * pMatched) / 1e6, 0)} MPa on one tooth.`);
    line('Line contact (mismatched angles) would be far higher: the drawing must specify matched flank angles + crown relief.');
    const Lt = PERSON.thighFrac * PERSON.stature95, sag = (t.stepDeg / RATCHET.pawls) * R;
    line(`DUAL PAWL offset half a pitch (${fmt(t.stepDeg / 2, 1)}°): worst sag onto a tooth = ${fmt(sag * SEAT.padCoPFrac * Lt * 100, 1)} cm at the pad, ${fmt(sag * Lt * 100, 1)} cm at the hip (single pawl: ${fmt(2 * sag * Lt * 100, 1)} cm).`);
    const B = RATCHET.bolts, Fb = Mfb / (B.n * B.rCircle), cap = 0.6 * B.uts * B.As;
    line(`MOUNTING: sector on the AK10-9 output flange, ${B.n} x M4 on a ${fmt(B.rCircle * 2000, 0)} mm circle (EST): ${fmt(Fb / 1000, 2)} kN shear each at ${fmt(Mfb, 0)} Nm`);
    line(`  vs ~${fmt(cap / 1000, 1)} kN for a 12.9 M4 (0.6 x 1220 MPa x 8.78 mm²) → SF ${fmt(cap / Fb, 1)}. Pawl housing on the actuator case's outboard face.`);
  }
  line('Pawl-load sensor (strain gauge) and hall sensor on each pawl.');
  line('');
  line('SEQUENCE (re-audited). The motor CANNOT hold any seat target: 78–94 Nm per knee with the rear leg, 145–190 without, vs 48 Nm peak.');
  line('  1 DROP: your QUADS hold you, the motor adds braking. Pawls held UP (solenoid + detent).');
  line('  2 SEAT: at the target the pawls are released; you LOWER UNTIL SEATED — hall says engaged AND load sensor carries load —');
  line('    and only then does the motor let go. Sag onto the next tooth is the half-pitch figure above.');
  line(`  3 EMERGENCY CATCH: if the knee flexes unexpectedly, the pawls drop ONLY below ${RATCHET.catchMaxDegS}°/s (threshold from the re-audit, EST: above it the`);
  line('    impact on a tooth is not tested, so the catch is not attempted). The DESCENT IS UNPROTECTED except by this catch. Say it plainly in the manual.');
  line('  4 STAND: extension is always free. The pawls CLICK over the teeth on the way up: that is correct, not a fault.');
  line('    Below 20° and extending, the solenoid lifts the pawls for walking.');
  line(`  5 DETENT: a sprung mechanical detent holds each pawl up/down; the bistable solenoid's ${RATCHET.solenoidN} N alone must never be able to drop a pawl mid-stride.`);
  line('  6 DEPTH CHANGE: the rear pole is locked in compression and cannot shorten, so you change depth only by STANDING (knee < 20°)');
  line('    and sitting again. Never re-seat deeper in place.');
  line('  (A small solenoid cannot drag a pawl out under ~2 kN of tooth friction, so the sequence never asks it to.)');

  line('\n=== REAR LEG STRENGTH (stepped column, pinned both ends, solved numerically) ===');
  const T = SEAT.rearTube;
  const maxN = Math.max(...rows.filter((r) => r.rear).map((r) => r.rear.N));
  const stepped = (secs, L) => buckleStepped(secs.map((x) => ({ ...x, L: L / secs.length })), T.E);
  for (const r of rows.filter((x) => x.rear)) {
    const Pcr = stepped(T.sections, r.rear.len), Pold = stepped(T.old, r.rear.len);
    line(`${r.mode.name.padEnd(11)} length ${fmt(r.rear.len, 2)} m → 24/20/16 x 1.5 tube ${fmt(Pcr, 0)} N (SF ${fmt(Pcr / T.designAxialN, 1)} on 1 kN design, ${fmt(Pcr / r.rear.N, 0)}x nominal ${fmt(r.rear.N, 0)} N); old trekking pole 16/14/12 would be ${fmt(Pold, 0)} N`);
  }
  const tubeKg = T.sections.reduce((a, x) => a + (Math.PI / 4) * (x.od ** 2 - (x.od - 2 * x.wall) ** 2) * 0.32 * T.rhoCarbon, 0);
  line(`Tube mass: ${fmt(tubeKg * 1000, 0)} g for three 0.32 m sections at ${T.rhoCarbon} kg/m³ (EST density); + locks, hinge boss, spring, pivoting foot ≈ 0.30 kg per leg in bom.mjs.`);
  line(`Self-check: one uniform Ø16 x 1.5 section at 0.83 m solves to ${fmt(buckleStepped([{ od: 0.016, wall: 0.0015, L: 0.83 }], T.E), 0)} N; Euler formula gives ${fmt((Math.PI ** 3 * T.E * (0.016 ** 4 - 0.013 ** 4)) / 64 / 0.83 ** 2, 0)} N.`);
  line(`Nominal max ${fmt(maxN, 0)} N; one-way lock (extends freely, locks in compression). E is EST: proof-test each pole to 1 kN at M1.`);

  line('\n=== REAR FOOT SLIP (friction NEEDED = tan of the leg angle) ===');
  const need = Math.max(...rows.filter((r) => r.rear).map((r) => r.rear.mu));
  line(`Worst mode needs mu = ${fmt(need, 2)} (design cap ${SEAT.rearMuDesign}). Pivoting rubber foot keeps full rubber contact at any leg angle.`);
  for (const [n, lo, hi, src] of SEAT.frictionTable) {
    const v = hi < need ? 'SLIPS: use the spike or Perch' : lo >= need ? `holds, ${fmt(lo / need, 1)}x margin at the low end` : 'holds only at the upper end: not promised';
    line(`  ${n.padEnd(46)} ${fmt(lo, 2)}–${fmt(hi, 2)}  → ${v}   [${src}]`);
  }
  line('Wet-floor limit, plainly: rated wet tile (≥0.42) and wet concrete hold; wet polished stone, unrated wet tile, mud and ice do NOT.');
  line('There, flip down the spike tip (outdoors) or use Perch. The FSR + load check flags a rear foot that unloads or skids.');

  line('\n=== THIGH UPRIGHT (sized for the fallback load) ===');
  const Zreq = (Mfb / MAT.al7075_yield) * 1e9, h = Math.ceil(Math.sqrt((6 * Zreq) / 8));
  line(`Fallback ${fmt(Mfb, 0)} Nm at 7075-T6 yield ${MAT.al7075_yield / 1e6} MPa (VERIFY) → Z ≥ ${fmt(Zreq, 0)} mm³ → lateral bar 8 x ${h} mm (kept at 8 x 28).`);
  line('With the rear leg working, normal sitting puts only the KNEE LOCK column above on the rails.');
}
