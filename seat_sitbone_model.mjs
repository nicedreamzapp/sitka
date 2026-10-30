// SEAT v3: THE STRUT HINGE STRAIGHT UNDER THE SIT BONE. Physics check run BEFORE the CAD change (2026-10-30).
//
// What changes (per leg):
//   * the strut hinge moves from the seat cup's outer edge (render two, 10/22) to straight under the ischial
//     tuberosity (sit bone), so the strut pushes up into the bone the body already sits on;
//   * the seat cup is laced to the thigh shell (laced bridge to the posterior cuff + a webbing tab to the shell);
//   * a short rigid spine link (ball-jointed both ends) joins the back panel to the hip belt, replacing the straps;
//   * the strut becomes 5 shorter sections so it stows above the calf's reach (see section 4).
// Geometry comes from the CAD chair pose (cad/build/manifest.json, measured, numbers below). Statics reuse tripod()
// from seat_torque_model.mjs with the hinge at the measured point and the foot planted 4 deg back (TENDON_CONCEPT).
// Everything marked EST is an estimate; tissue limits are from memory (VERIFY), as in TENDON_CONCEPT.md.
import { tripod, buckleStepped } from './seat_torque_model.mjs';
import { SEAT, line, fmt } from './params.mjs';

const R = Math.PI / 180;
const ARC_R = 0.080;            // tendon moment arm on the 80 mm arc
const THIGH_LEVER = 0.25;       // thigh-shell couple lever (TENDON_CONCEPT section 1)
const SPLAY = 9;                // strut leans out 9 deg
const TILT = 4;                 // and back 4 deg

// Measured in the CAD chair pose (left leg; the right mirrors it). x lateral from the midline, fwd from the hip joint.
//   hinge: from the hip joint, forward / up (m); off the sit bone: lateral (+out) and how far below its skin point
//   cup: seated contact footprint (projected), its width, length, centroid x / fwd; sit bone skin point x / fwd
const CAD = {
  old: { name: 'old: hinge on the cup outer edge', hinge: [0.020, -0.136], latOff: 0.110, below: 0.031, pinX: 0.173, pinY: -0.010,
         cup: { A: 0.0301, w: 0.176, L: 0.216, cx: 0.110, cy: -0.019 }, footX: 0.244 },
  new: { name: 'new: hinge under the sit bone', hinge: [-0.003, -0.159], latOff: 0.000, below: 0.053, pinX: 0.063, pinY: 0.013,
         cup: { A: 0.0242, w: 0.158, L: 0.191, cx: 0.124, cy: -0.012 }, footX: 0.134 },
};
const SIT = { x: 0.063, y: 0.013 };

const MODES = [
  ['Chair, upright', { ...SEAT.modes[2] }],
  ['Chair, 10 deg recline', { ...SEAT.modes[2], trunk: -10 }],
  ['Half-sit, recline', { ...SEAT.modes[1], trunk: -10 }],
  ['Deep squat, recline', { ...SEAT.modes[3], trunk: -10 }],
];

function sag(geo, mode) {
  const r = tripod(mode, { hingeAt: geo.hinge, tiltDeg: TILT });
  return { r, MK: r.MK, T: r.MK / ARC_R, N: r.rear.N, share: r.shareRear, back: r.marginBack, tipDeg: r.tipBackDeg, mu: r.rear.mu, len: r.rear.len };
}

// rigid cup on an even (linear) tissue bed, one axis: peak pressure for a load F at offset e from the centroid
function peak(F, A, w, e) {
  e = Math.abs(e);
  if (e <= w / 6) return (F / A) * (1 + (6 * e) / w);
  const L = A / w, c = 3 * (w / 2 - e);          // contact width left after lift-off
  return (2 * F) / (c * L);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  line('=== SEAT v3: STRUT HINGE UNDER THE SIT BONE (per leg, 130.3 kg / 1.874 m wearer) ===');
  line('Hinge from the hip joint (CAD chair pose): old ' + CAD.old.hinge.map((v) => fmt(v * 100, 1)).join(' / ') +
       ' cm fwd/up, new ' + CAD.new.hinge.map((v) => fmt(v * 100, 1)).join(' / ') + ' cm. Foot planted 4 deg back, 9 deg out.');
  line('');
  line('1. SAGITTAL (tripod statics)');
  line('Mode                    hinge  knee Nm  tendon N  strut N  share  room behind  tip-back  grip needed  strut m');
  const rows = {};
  for (const [nm, md] of MODES) for (const k of ['old', 'new']) {
    const s = sag(CAD[k], md); rows[nm + k] = s;
    line(`${nm.padEnd(22)}  ${k.padEnd(4)} ${fmt(s.MK, 0).padStart(7)} ${fmt(s.T, 0).padStart(9)} ${fmt(s.N, 0).padStart(8)} ${fmt(s.share * 100, 0).padStart(5)}%` +
         `  ${fmt(s.back * 100, 0).padStart(6)} cm  ${fmt(s.tipDeg, 0).padStart(6)} deg  ${fmt(s.mu, 2).padStart(9)}  ${fmt(s.len, 2).padStart(6)}`);
  }
  line('The hinge barely moves front-to-back (2 cm), so the sagittal numbers stay where TENDON_CONCEPT put them');
  line('(its 34 Nm / 472 N / 69% used a hinge AT the hip joint; the real hinge is 15.9 cm below it).');

  line('');
  line('2. FRONTAL (chair, 10 deg recline): where the strut push lands, and what holds the cup');
  const cr = 'Chair, 10 deg recline';
  for (const k of ['old', 'new']) {
    const G = CAD[k], s = rows[cr + k];
    const Fv = s.N * Math.cos(TILT * R), Flat = Fv * Math.tan(SPLAY * R);
    const eLine = G.latOff - G.below * Math.tan(SPLAY * R);      // strut line off the sit bone at skin height
    const Msb = Fv * Math.abs(eLine);                             // moment of the strut push about the sit bone
    const Fcup = Fv + s.MK / THIGH_LEVER;                         // strut + thigh-shell couple on the cup
    const ex = (Fv * (G.pinX - G.cup.cx)) / Fcup, ey = (Fv * (G.pinY - G.cup.cy)) / Fcup;
    const pAvg = Fcup / G.cup.A, pX = peak(Fcup, G.cup.A, G.cup.w, ex), pY = peak(Fcup, G.cup.A, G.cup.L, ey);
    line(`${G.name}`);
    line(`  strut push ${fmt(Fv, 0)} N up, ${fmt(Flat, 0)} N inward; its line passes ${fmt(Math.abs(eLine) * 1000, 0)} mm ${eLine > 0 ? 'outside' : 'inside'} the sit bone`);
    line(`  moment about the sit bone (rolls the cup off the bone): ${fmt(Msb, 1)} Nm`);
    line(`  cup load ${fmt(Fcup, 0)} N on ${fmt(G.cup.A * 1e4, 0)} cm2 seated footprint: average ${fmt(pAvg / 1000, 0)} kPa;` +
         ` even-tissue peak ${fmt(pX / 1000, 0)} kPa across, ${fmt(pY / 1000, 0)} kPa along (EST, rigid-cup model)`);
    if (k === 'new') line(`  NOT FIXED BY THE MOVE: on an even tissue bed the peak gets worse, not better (${fmt(pX / 1000, 0)} kPa), because the` +
      ` sit bone is 6.3 cm off the midline and the cup's inner edge can only reach 2.2 cm past it before the two cups touch` +
      ` (they come within 10 mm of each other in the sit-down motion). Average ${fmt(pAvg / 1000, 0)} kPa, not the 15 kPa of` +
      ` KINETICS (that used 400 cm2 of curved surface; the seated footprint is ${fmt(G.cup.A * 1e4, 0)} cm2). Geometry cannot fix this:` +
      ` an air-cell insert under the sit bone (immersion pulls the peak toward the average) has to be proven on a pressure map;` +
      ` until then plan 10-20 min sits (EST).`);
    line(`  peak sits ${k === 'old' ? 'on the OUTER edge (over the hip bone\'s trochanter, no sitting surface)' : 'on the INNER edge, under the sit bone (the body\'s own sitting surface)'}`);
    if (k === 'old') line(`  held only by one strap to the belt (lever ~60 mm): ${fmt(Msb / 0.06, 0)} N of strap tension to keep the cup square. Not credible; it floated.`);
    else {
      const tab = Msb / 0.127, drag = 0.4 * Fcup;
      line(`  laced bridge + webbing tab: tab ${fmt(tab, 0)} N to hold the residual moment (127 mm lever);`);
      line(`  stand-up drag (friction 0.4 x ${fmt(Fcup, 0)} N, EST) ${fmt(drag, 0)} N over 6 cord runs = ${fmt(drag / 6, 0)} N per run, ${fmt(2 * drag / 6, 0)} N per grommet.`);
      line(`  3 mm polyester cord (~1.5 kN, EST) and 9 mm grommets: > 10x margin.`);
    }
    line(`  inward push: ${fmt(Flat, 0)} N per side squeezes the pelvis between the two cups (no crossbar needed),` +
         (G.latOff > 0 ? ` applied ${fmt(G.latOff * 100, 0)} cm outside the sit bone.` : ' applied at the sit bone.'));
  }

  line('');
  line('3. SIDEWAYS TIPPING (chair, recline): the strut feet move in with the hinges');
  {
    const s = rows[cr + 'new'].r, st = SEAT.stance, shoeOut = st.shoeCentreSep / 2 + st.shoeWidth / 2;
    for (const [nm, half] of [['plan (TENDON_CONCEPT)', st.rearFootSep / 2], ['old CAD', CAD.old.footX], ['new CAD, 9 deg splay', CAD.new.footX],
                              ['new, 12 deg splay', CAD.new.footX + (Math.tan(12 * R) - Math.tan(9 * R)) * 0.45]]) {
      const t = (SEAT.heelX - s.cgX) / (SEAT.heelX - s.rear.Rf[0]);
      const h = s.cgX >= SEAT.heelX ? shoeOut : shoeOut + (half - shoeOut) * t;
      line(`  ${nm.padEnd(24)} feet ${fmt(2 * half * 100, 0)} cm apart: polygon half-width ${fmt(h * 100, 1)} cm at the CoM, tips at ${fmt(Math.atan2(h, s.cgY) / R, 0)} deg`);
    }
    line('  The CoM sits over the shoes, not over the strut feet, so pulling the feet in costs little side margin. Splay stays 9 deg.');
  }

  line('');
  line('4. STRUT: stowed length vs the running calf, and buckling');
  {
    const mk = (ods, w, L) => ods.map((od) => ({ od, wall: w, L: L / ods.length }));
    const three = [0.024, 0.020, 0.016], five = [0.024, 0.021, 0.018, 0.015, 0.012];
    line('  Stowed from a hinge under the sit bone, a straight tube runs down the back of the thigh. In the running swing the');
    line('  calf folds up against the back of the thigh from ~0.30 m below the hip (CAD run pose), so the stowed strut must end');
    line('  above that: 3 x 0.32 m sections stow to 0.39 m (foot in the calf, 56 mm deep); 5 x 0.20 m stow to 0.28 m (clear).');
    for (const L of [0.46, 0.65, 0.86]) {
      const p3 = buckleStepped(mk(three, 0.0015, L), SEAT.rearTube.E), p5 = buckleStepped(mk(five, 0.0012, L), SEAT.rearTube.E);
      line(`  ${fmt(L, 2)} m: 3 x 24/20/16 x 1.5 ${fmt(p3, 0)} N, 5 x 24/21/18/15/12 x 1.2 ${fmt(p5, 0)} N` +
           ` (${fmt(p5 / 472, 1)}x the 472 N chair load, SF ${fmt(p5 / SEAT.rearTube.designAxialN, 1)} on the 1 kN design load)`);
    }
    line('  Reach: 0.874 m pin to foot (40 mm overlaps). Tubes 98 g vs 130 g; two more twist locks (+~40 g, EST).');
  }

  line('');
  line('5. SPINE LINK (stoop): two 25 mm rigid links, ball-jointed, panel lower edge to the belt');
  {
    for (const [nm, T] of [['upright / walking (panel + P1 hub weight only)', 0], ['90 deg stoop, passive M2 (300 N per side)', 300], ['90 deg stoop, P1 peak (770 N per side)', 770]]) {
      const C = T > 0 ? T : 1.6 * 9.81 / 2;
      line(`  ${nm.padEnd(48)} ${fmt(C, 0).padStart(4)} N compression per link`);
    }
    line('  The lift tendon pulls the panel down toward its belt standoffs. With straps only, that 600-1540 N went into the');
    line('  shoulder harness and down the spine. The links carry it panel to belt; the shoulders only locate the panel.');
    line('  Links: 11 mm carbon tube between M6 ball joints (VERIFY rating, typically several kN): far above 770 N.');
    line('  The links keep a fixed length, so in a deep stoop the panel slides ~10 cm up the back instead of lifting off');
    line('  (back skin lengthens several cm in full flexion, Schober test, VERIFY). Solved per frame in the CAD (panel_fit).');
  }
}
