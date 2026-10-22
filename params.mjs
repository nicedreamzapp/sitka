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

// ---------- SEAT GEOMETRY ----------
export const SEAT = {
  // Thigh pad centre of pressure, measured from the knee axis along the thigh, as a
  // fraction of thigh length. Chairless Chair puts the seat under the proximal
  // thigh / buttock [SRC 8]. 0.65 is EST — the pad position is a design choice.
  padCoPFrac: 0.65,
  // Share of body weight the device carries when seated. Luger 2019 measured the
  // Chairless Chair carrying UP TO 64% of body mass [SRC 9]. We design to 100% of
  // everything above the shanks (worst case: feet unloaded) — EST, conservative.
  designLoadShare: 1.0,
  // Load factor for dropping into the seat instead of lowering into it. EST.
  sitImpactFactor: 1.5,
  // Lock safety factor on top of the worst case. EST (typical machine-design 1.5–2).
  lockSF: 1.5,
  modes: [
    { key: 'perch',   name: 'Perch',      knee: 25 },
    { key: 'halfsit', name: 'Half-sit',   knee: 60 },
    { key: 'chair',   name: 'Chair',      knee: 90 },
    { key: 'squat',   name: 'Deep squat', knee: 120 },
  ],
  // Max comfortable loaded ankle dorsiflexion used to bound shank lean. EST.
  maxShankLeanDeg: 35,
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
  // 7075-T6 aluminium UTS ~572 MPa (handbook value, from memory — VERIFY)
  al7075_UTS: 572e6,
  // 7075-T6 yield ~503 MPa, density 2810 kg/m^3 (handbook values, from memory — VERIFY)
  al7075_yield: 503e6, al7075_rho: 2810,
};

export const line = (s = '') => console.log(s);
export const fmt = (x, d = 1) => Number(x).toFixed(d);
