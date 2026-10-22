// ENERGY — battery runtime for walking, hiking (up and down), running and sitting,
// plus what regenerative braking actually puts back.
//
// Per leg, per stride, the battery pays:
//     E = copper loss + positive mechanical work / eta_out  -  negative work * eta_in
// Copper loss for a half-sine torque pulse of peak T over duration t:
//     integral (0.75 R (T sin / kt)^2) = 0.75 R (T/kt)^2 * t/2        [CALC]
// System power = 2 legs * E * stride frequency + idle electronics.
import { PERSON, GAIT, AK10_9, EFF, BATT, g, line, fmt } from './params.mjs';

const halfSineCopperJ = (Tpk, t) => AK10_9.copperW(Tpk) * (t / 2);

// RUNNING: exo torque = alpha x biological knee moment, capped at actuator peak.
export function running(mass, alphaTarget = 0.2) {
  const bioPk = GAIT.runKneeExtMomentPk * mass;
  const Tpk = Math.min(alphaTarget * bioPk, AK10_9.peakNm);
  const alpha = Tpk / bioPk;
  const swingT = Math.min(alpha * GAIT.runKneeFlexMomentPk * mass, AK10_9.peakNm);
  const swingDur = 0.15; // terminal-swing pulse duration, EST
  const cu = halfSineCopperJ(Tpk, GAIT.runStanceS) + halfSineCopperJ(swingT, swingDur);
  const pos = alpha * GAIT.runKneePosWorkStride * mass;
  const neg = alpha * GAIT.runKneeNegWorkStride * mass;
  const perStride = cu + pos / EFF.driveOut - neg * EFF.regenIn;
  const legW = perStride * GAIT.runStrideHz;
  const P = Math.max(2 * legW, 0) + EFF.idleW;
  const regenOnly = 2 * neg * EFF.regenIn * GAIT.runStrideHz;
  return { Tpk, alpha, cu, pos, neg, perStride, P, regenOnly, noRegenP: 2 * (cu + pos / EFF.driveOut) * GAIT.runStrideHz + EFF.idleW };
}

// HIKING on a grade. Assist torque pulse during stance; work = mean torque x knee excursion.
export function hiking(mass, Tpk, dir /* +1 up, -1 down */) {
  const t = GAIT.hikeStanceS;
  const W = Tpk * (2 / Math.PI) * GAIT.hikeKneeExcursionRad; // J per stride per leg, mean of half-sine
  const cu = halfSineCopperJ(Tpk, t);
  const perStride = dir > 0 ? cu + W / EFF.driveOut : cu - W * EFF.regenIn;
  const P = 2 * perStride * GAIT.hikeStrideHz + EFF.idleW;
  const mechW = 2 * W * GAIT.hikeStrideHz;
  // cross-check against the potential-energy rate of the whole body
  const vz = GAIT.hikeSpeedFlat * GAIT.hikeGrade / Math.sqrt(1 + GAIT.hikeGrade ** 2);
  const PE = mass * g * vz;
  return { Tpk, W, cu, P, mechW, PE, vz, shareOfPE: mechW / PE };
}

// PUSH-ONLY running: torque only during the terminal-stance push (positive work),
// motor transparent the rest of the stride. No regen credit at all.
export function runningPushOnly(mass, Tpk = AK10_9.peakNm, pushS = 0.12 /* EST */) {
  const bioPk = GAIT.runKneeExtMomentPk * mass;
  const alpha = Math.min(Tpk, AK10_9.peakNm) / bioPk;
  const cu = halfSineCopperJ(Tpk, pushS);
  const pos = alpha * GAIT.runKneePosWorkStride * mass;
  const perStride = cu + pos / EFF.driveOut;
  return { alpha, cu, pos, perStride, P: 2 * perStride * GAIT.runStrideHz + EFF.idleW };
}

// Best downhill braking torque for NET charge: harvest grows with T, copper with T^2.
export function bestRegen() {
  let best = { T: 0, net: -1e9 };
  for (let T = 1; T <= AK10_9.peakNm; T += 0.5) {
    const W = T * (2 / Math.PI) * GAIT.hikeKneeExcursionRad;
    const net = 2 * (W * EFF.regenIn - halfSineCopperJ(T, GAIT.hikeStanceS)) * GAIT.hikeStrideHz;
    if (net > best.net) best = { T, net };
  }
  return best;
}

const usableWh = BATT.totalWh * BATT.usable;
const hrs = (P) => usableWh / P;

if (import.meta.url === `file://${process.argv[1]}`) {
  const m = PERSON.massMedian;
  line(`=== BATTERY: ${BATT.packs} x 6S1P Molicel P45B = ${BATT.packs} x ${fmt(BATT.packWh, 1)} Wh = ${fmt(BATT.totalWh, 0)} Wh; ${fmt(usableWh, 0)} Wh usable (85% EST); ~${fmt(BATT.massKg, 2)} kg ===`);
  line(`Each pack is under the FAA 100 Wh carry-on line. Runner/hiker: median US man, ${m} kg.\n`);

  const r = running(m);
  line('--- RUNNING, 3.5 m/s ---');
  line(`Assist: ${fmt(r.Tpk, 0)} Nm peak per knee = ${fmt(r.alpha * 100, 1)}% of the biological midstance moment (capped by actuator peak)`);
  line(`Per stride per leg: copper ${fmt(r.cu, 1)} J + positive ${fmt(r.pos, 1)} J/${EFF.driveOut} − regen ${fmt(r.neg, 1)} J x ${EFF.regenIn} = ${fmt(r.perStride, 1)} J`);
  const po = runningPushOnly(m);
  line(`Strategy A — MIRROR (exo torque follows the whole knee moment, brakes AND pushes):`);
  line(`  no regen credit: ${fmt(r.noRegenP, 0)} W → ${fmt(hrs(r.noRegenP), 1)} h (${fmt(hrs(r.noRegenP) * GAIT.runSpeed * 3.6, 0)} km)   ← HEADLINE (conservative)`);
  line(`  with regen:      ${fmt(r.P, 0)} W → ${fmt(hrs(r.P), 1)} h. The knee is a net ABSORBER in running (−1.34 vs +0.41 J/kg per stride, Schache),`);
  line(`                   so on paper braking recovers ~${fmt(r.regenOnly, 0)} W. NOT CLAIMED until a bench shows it — eta_in is a guess.`);
  line(`Strategy B — PUSH-ONLY (torque only in the ${0.12} s terminal-stance push, EST): ${fmt(po.P, 0)} W → ${fmt(hrs(po.P), 1)} h (${fmt(hrs(po.P) * GAIT.runSpeed * 3.6, 0)} km)`);
  line(`Whether ANY knee assist lowers a runner's metabolic cost is UNPROVEN (Elliott/Herr clutch-spring exo did not).`);

  line('\n--- HIKING, 10% grade, ~5 km/h (Tobler flat speed; uphill is slower — runtime is per hour of assist) ---');
  for (const Tpk of [15, 25, 35]) {
    const u = hiking(m, Tpk, +1), d = hiking(m, Tpk, -1);
    line(`assist ${String(Tpk).padStart(2)} Nm pk: UP ${fmt(u.P, 0).padStart(3)} W → ${fmt(hrs(u.P), 1).padStart(4)} h | exo lifts ${fmt(u.mechW, 0)} W of ${fmt(u.PE, 0)} W climbing power (${fmt(u.shareOfPE * 100, 0)}%) | DOWN ${fmt(d.P, 1).padStart(5)} W (${d.P < EFF.idleW ? 'regen covers part of idle' : 'regen < copper'}) → ${fmt(hrs(Math.max(d.P, 0.1)), 1)} h`);
  }
  const d25 = hiking(m, 25, -1);
  line(`\nDownhill regen at 25 Nm: ${fmt(2 * d25.W * EFF.regenIn * GAIT.hikeStrideHz, 1)} W harvested before copper loss; net to battery ${fmt(2 * (d25.W * EFF.regenIn - d25.cu) * GAIT.hikeStrideHz, 1)} W.`);
  line(`Cross-check: Donelan 2008 knee harvester measured 4.8 ± 0.8 W walking at 1.5 m/s; Wu 2022 reports ~6.5 W downhill per leg (UNVERIFIED convention).`);
  const br = bestRegen();
  line(`Best NET regen: brake at ${fmt(br.T, 1)} Nm peak → ${fmt(br.net, 1)} W to the battery. Harder braking turns the extra into heat (copper ∝ T²).`);
  line(`One hour of descent at that setting banks ~${fmt(br.net, 1)} Wh of ${fmt(usableWh, 0)} Wh usable (${fmt((br.net / usableWh) * 100, 1)}%).`);
  line('FINDING: a low-ratio QDD knee motor is a POOR generator at hiking speeds — copper loss eats most of the');
  line('harvest. Donelan\'s 4.8 W came from a purpose-built high-ratio generator. Downhill mode is worth having');
  line('because it takes braking load off the quads, NOT because it charges the battery. Say so in the README.');

  line('\n--- SITTING (pawl locked) ---');
  line(`Lock holds mechanically; motors off. Draw = idle ${EFF.idleW} W → ${fmt(hrs(EFF.idleW), 0)} h. Sitting costs almost nothing.`);
  line(`(Holding the chair on motors instead would need >142 Nm per knee — impossible on this actuator; see seat_torque_model.mjs.)`);

  line('\n--- A DAY HIKE: 3 h up at 25 Nm, 2 h down at 25 Nm, 4 x 15 min seat breaks ---');
  const up = hiking(m, 25, +1), dn = hiking(m, 25, -1);
  const day = up.P * 3 + dn.P * 2 + EFF.idleW * 1;
  line(`Energy: ${fmt(up.P * 3, 0)} + ${fmt(dn.P * 2, 0)} + ${fmt(EFF.idleW, 0)} = ${fmt(day, 0)} Wh vs ${fmt(usableWh, 0)} Wh usable → ${day <= usableWh ? 'FITS' : 'DOES NOT FIT'} (${fmt((day / usableWh) * 100, 0)}% of the packs).`);
  line('\nAll efficiencies, stride rates and the assist profile are EST. The bench (M1) replaces them.');
}
