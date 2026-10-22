// Run + Sit Exo — shared inputs. EVERY number here carries its source or is
// flagged EST (our estimate, to be replaced by a measurement). The models import
// from this one file so there is never a second copy of a number to drift.
//
// Tags:  [SRC n]  = sourced, see RESEARCH_REPORT_2026-10-21.md, source n
//        [CALC]   = computed from sourced numbers (math shown where it is used)
//        [EST]    = our estimate. Treat as a guess until a bench measures it.

export const g = 9.81; // m/s^2

// ---------- WHO WE DESIGN FOR ----------
export const PERSON = {
  // NHANES 2015-2018, US men 20+, Table 5: 95th pct weight 130.3 kg [SRC 1]
  mass95: 130.3,
  // NHANES 2015-2018, US men 20+, Table 5: median weight 87.4 kg [SRC 1]
  massMedian: 87.4,
  // NHANES 2015-2018, US men 20+, Table 11: 95th pct stature 187.4 cm [SRC 1]
  stature95: 1.874,
  // ANSUR II male 95th pct buttock-knee length 669 mm (computed from public CSV) [SRC 2]
  buttockKnee95: 0.669,
  // ANSUR II male 95th pct knee height sitting 602 mm [SRC 2]
  kneeHeightSit95: 0.602,
  // Segment length fractions of stature, Winter: thigh 0.245 H, shank 0.246 H [SRC 3]
  // (book value not re-read; matches an independent worksheet at 0.245 — see report)
  thighFrac: 0.245, shankFrac: 0.246,
  // de Leva 1996 male mass fractions [SRC 4]
  shankMassFrac: 0.0433, footMassFrac: 0.0137, thighMassFrac: 0.1416,
};
// NOTE: the 95th pct weight and 95th pct stature are separate marginals [SRC 1];
// pairing them is deliberately conservative (long lever AND heavy body).

// ---------- SEAT GEOMETRY (v2: TRIPOD — heel, toes, rear leg) ----------
// v1 balanced the seat over the heel (the REAR EDGE of the foot) — ~3 cm of backward
// margin. v2 adds a rear leg ("kickstand") hinged at the proximal thigh rail, so each
// leg stands on three points and the seat closes its loads inside the leg unit.
export const SEAT = {
  // Pad centre of pressure, from the knee along the thigh, as a fraction of thigh
  // length. v2 moves the pad PROXIMAL, under the gluteal fold. 0.75 is EST (design choice).
  padCoPFrac: 0.75,
  // Rear-leg hinge on the thigh rail, fraction of thigh length from the knee (rail top). EST
  rearHingeFrac: 0.85,
  // Rear foot target behind the heel edge, m. Plan range 0.40–0.45; the model trims it
  // per mode so the friction the rear foot needs stays at or below rearMuDesign. EST
  rearBackMax: 0.42,
  // Friction the rear foot may NEED (= tan of the leg angle; a pinned strut's ground force runs along it).
  // Sourced rubber friction [SRC 17]: dry concrete 0.6–0.85, wet concrete 0.45–0.75 (Engineering ToolBox;
  // Autodesk lists wet concrete as low as 0.30); wet-rated interior tile must test ≥ 0.42 wet DCOF (ANSI A326.3).
  // Design: need ≤ 0.30, i.e. ≥ 2x margin on dry concrete (0.6) and at the low end of wet concrete. Wood and
  // dry tile not found in a source (EST: similar to dry concrete for rubber).
  rearMuDesign: 0.30,
  frictionTable: [
    ['rubber, dry concrete', 0.6, 0.85, 'SRC 17 (Engineering ToolBox)'],
    ['rubber, wet concrete', 0.45, 0.75, 'SRC 17 (Engineering ToolBox)'],
    ['rubber, wet concrete (low source)', 0.30, 0.30, 'SRC 17 (Autodesk Robot help)'],
    ['wet interior tile, rated', 0.42, 0.42, 'SRC 17 (ANSI A326.3 minimum wet DCOF)'],
    ['wet tile below rating, wet polished stone, ice', 0, 0.3, 'EST, unrated: no promise'],
  ],
  // Rear leg v3: UNIFORM-WALL 3-section telescoping carbon tube, 24/20/16 mm OD x 1.5 mm wall (IDs 21/17/13,
  // 0.5 mm radial clearance per joint for a bushing), each section ~0.32 m, 65 mm overlaps. Replaces the tapering
  // trekking pole (16/14/12 mm [SRC 15]) which buckles at ~0.9 kN at 0.83 m. Tube stock: 3K roll-wrapped metric
  // carbon tube, e.g. 20 x 17 mm listed ~US$10 per 500 mm [SRC 18]. E 70 GPa (EST, roll-wrapped 3K).
  rearTube: { E: 70e9, stowedLen: 0.35, maxLen: 0.85, designAxialN: 1000, rhoCarbon: 1550,
    sections: [{ od: 0.024, wall: 0.0015 }, { od: 0.020, wall: 0.0015 }, { od: 0.016, wall: 0.0015 }],
    old: [{ od: 0.016, wall: 0.0015 }, { od: 0.014, wall: 0.0012 }, { od: 0.012, wall: 0.0010 }] },
  // Rear foot: pivoting rubber cane tip (Blue Jay 360°, $18.95) + flip-down steel ice/trail spike tip
  // (HealthSmart retractable ice tip, $20.59) [SRC 19]. Carbide spike = option, not found sourced.

  // Lateral stance (front view). EST: shoe centres 0.30 m apart (about hip width), shoe 0.10 m wide.
  // Rear feet 0.34 m apart (plan value, set by the thigh-rail spacing + a small splay).
  stance: { shoeCentreSep: 0.30, shoeWidth: 0.10, rearFootSep: 0.34 },
  // Foot contact geometry relative to the ankle axis (m), 95th-pct shoe. EST
  heelX: -0.055, metX: 0.15, toeX: 0.21,
  // Head-arms-trunk centre of mass above the hip along the trunk axis. EST (~mid-trunk).
  hatCoMAboveHip: 0.30,
  // Load factor for dropping into the seat instead of lowering into it. EST.
  sitImpactFactor: 1.5,
  // Lock safety factor on top of the worst case. EST (typical machine-design 1.5–2).
  lockSF: 1.5,
  // Comfortable LOADED ankle dorsiflexion is ~20° (the exo ankle pivot is free, so the
  // wearer's own ankle sets the shank lean). EST — the v1 value of 35° was too much.
  maxShankLeanDeg: 20,
  // knee = flexion, phi = shank lean (≤ 20°), trunk = forward trunk lean (EST, visual + CoM),
  // rear = uses the rear leg. Perch is the no-rear-leg fallback mode.
  modes: [
    { key: 'perch',   name: 'Perch',      knee: 25,  phi: 10, trunk: 4,  rear: false },
    { key: 'halfsit', name: 'Half-sit',   knee: 60,  phi: 15, trunk: 10, rear: true },
    { key: 'chair',   name: 'Chair',      knee: 90,  phi: 15, trunk: 18, rear: true },
    { key: 'squat',   name: 'Deep squat', knee: 120, phi: 20, trunk: 32, rear: true },
  ],
  // v1 chair pose for the honesty check: shank lean 32.9° put the pad CoP over the heel.
  v1Chair: { key: 'v1chair', name: 'v1 chair (heel balance)', knee: 90, phi: 32.9, trunk: 18, rear: false, padFrac: 0.65 },
};

// ---------- ONE-WAY RATCHET (the seat lock, v2) ----------
// Blocks FLEXION, extension always free: you can always stand up, power or no power.
export const RATCHET = {
  v1: { r: 0.035, teeth: 36, width: 0.008, teethEngaged: 1 },   // v1 pawl: one tooth at r = 35 mm
  v2: { r: 0.050, teeth: 40, width: 0.012, teethEngaged: 3, effectiveTeeth: 2 }, // 3-tooth pawl; assume only 2 share load (tolerance) — EST
  pawls: 2,               // dual pawl, offset half a pitch → the knee can sag at most pitch/2 onto a tooth
  catchMaxDegS: 60,       // emergency drop catch allowed only below this knee speed. EST (from the re-audit)
  // Sector bolted to the AK10-9 output flange: 8 x M4. Bolt circle radius 36 mm is EST — read it off the
  // CubeMars drawing. M4 tensile stress area 8.78 mm² (ISO 898-1); class 12.9 UTS 1220 MPa (ISO 898-1); shear 0.6 x UTS EST.
  bolts: { n: 8, rCircle: 0.036, As: 8.78e-6, uts: 1220e6 },
  solenoidN: 4,           // Intertec ITS-LX-2218 start force 4 N [SRC 16]; a sprung detent must out-hold it
  toothThickFrac: 0.6, toothHeightFrac: 0.4,  // tooth base thickness and height as fractions of pitch — EST
};

// ---------- GAIT BIOMECHANICS ----------
export const GAIT = {
  // Schache et al. 2011 MSSE, 3.5 m/s running [SRC 5]:
  runSpeed: 3.5,
  runKneeExtMomentPk: 3.12,   // Nm/kg, midstance
  runKneeFlexMomentPk: 0.53,  // Nm/kg, terminal swing
  runKneeAbsorbPk: -15.7,     // W/kg, initial stance
  runKneeGenPk: 7.7,          // W/kg, terminal stance
  runTermSwingAbsorbPk: -4.6, // W/kg
  runKneeNegWorkStride: 0.74 + 0.19 + 0.41, // J/kg per stride per leg (stance+init swing+term swing) [CALC from SRC 5]
  runKneePosWorkStride: 0.41, // J/kg per stride per leg, terminal stance [SRC 5]
  // Stride frequency at 3.5 m/s: not found in a source. 1.4 strides/s (168 steps/min) EST.
  runStrideHz: 1.4,
  // Ground contact time at 3.5 m/s: not found. 0.25 s EST.
  runStanceS: 0.25,
  // Stairs (Riener 2002 via review) peak knee extension moment, Nm/kg [SRC 6]
  stairAscentMomentPk: 1.06, stairDescentMomentPk: 0.92,
  // Level walking peak knee extension moment ~0.5 Nm/kg — memory of Winter, UNVERIFIED [EST]
  walkMomentPk: 0.5,
  // Hiking: Tobler's function gives ~5 km/h flat, ~6 km/h peak on ~5% descent [SRC 7]
  hikeSpeedFlat: 5 / 3.6,
  // Hiking grade we model. EST (a moderate trail).
  hikeGrade: 0.10,
  // Hike stride frequency, not found. 0.9 strides/s EST.
  hikeStrideHz: 0.9,
  // Hike stance duration, EST (~60% of a 1.1 s stride).
  hikeStanceS: 0.65,
  // Knee extension during uphill stance: ~0.6 rad over stance (EST, ~35° → ~0°)
  hikeKneeExcursionRad: 0.6,
};

// ---------- ACTUATOR: CubeMars AK10-9 V2.0 KV100 [SRC 10, cubemars.com 2026-10-21] ----------
export const AK10_9 = {
  name: 'CubeMars AK10-9 V2.0 KV100',
  ratedNm: 18, peakNm: 48, ratedA: 16.2, peakA: 41.2,
  ktMotor: 0.114,           // Nm/A at the rotor
  gear: 9,
  rPhasePhase: 0.0655,      // ohm
  ratedRpm24: 205, noLoadRpm: 533,
  massKg: 0.96, rotorInertia_gcm2: 1002, backdriveNm: 0.8,
  priceUSD: 698.90,
};
// Output torque constant implied by the vendor's own rated point: 18 Nm / 16.2 A [CALC]
AK10_9.ktOut = AK10_9.ratedNm / AK10_9.ratedA;
// FOC copper loss: P = 1.5 * Iq^2 * R_phase, R_phase = R_pp / 2  =>  0.75 * I^2 * R_pp [CALC]
AK10_9.copperW = (tauNm) => 0.75 * (tauNm / AK10_9.ktOut) ** 2 * AK10_9.rPhasePhase;

// The high-ratio alternative we REJECT for the knee (kept for comparison) [SRC 10]
export const AK80_64 = { name: 'CubeMars AK80-64 KV80', ratedNm: 48, peakNm: 120, ratedRpm24: 23, gear: 64, massKg: 0.85, priceUSD: 889.90 };

// ---------- DRIVETRAIN EFFICIENCIES (all EST until the bench measures them) ----------
export const EFF = {
  driveOut: 0.85,   // battery → shaft beyond copper loss (inverter + gear + iron). EST
  regenIn: 0.85,    // shaft → battery beyond copper loss. EST
  idleW: 5.0,       // whole system electronics idle, both legs + belt. EST
};

// ---------- BATTERY ----------
// Two swappable 6S1P packs of Molicel P45B 21700 (4.5 Ah) [SRC 11].
// 6 x 3.6 V x 4.5 Ah = 97.2 Wh each — under the FAA 100 Wh carry-on line [SRC 12].
export const BATT = {
  packs: 2, cellsPerPack: 6, cellAh: 4.5, cellV: 3.6,
  cellMassKg: 0.070,   // P45B mass not verified; 21700 cells weigh ~70 g (Samsung 50S is 72 g [SRC 11]). EST
  packOverheadKg: 0.10, // BMS, nickel strip, case per pack. EST
  usable: 0.85,        // usable fraction (BMS cut-offs, cold, ageing). EST
  cellPriceUSD: 8.75,  // Battery Junction 2026-10-21 [SRC 11]
};
BATT.packWh = BATT.cellsPerPack * BATT.cellV * BATT.cellAh;
BATT.totalWh = BATT.packWh * BATT.packs;
BATT.massKg = BATT.packs * (BATT.cellsPerPack * BATT.cellMassKg + BATT.packOverheadKg);

// ---------- MATERIALS for the seat lock (handbook values — verify against the mill cert) ----------
export const MAT = {
  // 17-4 PH stainless, H900 condition: UTS ~1310 MPa (ASM handbook value, from memory — VERIFY)
  steel174_H900_UTS: 1310e6,
  // Shear strength taken as 0.6 x UTS (common design rule) [EST]
  shearFrac: 0.6,
  // 17-4 PH H900 yield ~1170 MPa (ASM handbook value, from memory — VERIFY)
  steel174_H900_yield: 1170e6,
  // 7075-T6 aluminium UTS ~572 MPa (handbook value, from memory — VERIFY)
  al7075_UTS: 572e6,
  // 7075-T6 yield ~503 MPa, density 2810 kg/m^3 (handbook values, from memory — VERIFY)
  al7075_yield: 503e6, al7075_rho: 2810,
};

export const line = (s = '') => console.log(s);
export const fmt = (x, d = 1) => Number(x).toFixed(d);
