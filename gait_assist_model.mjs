// GAIT ASSIST + ACTUATOR SIZING — walk, hike, run, stairs, and the stumble.
// Question: what fraction of the biological knee moment can one AK10-9 per knee
// provide, can it keep up with a running knee, and why not a high-ratio actuator?
import { PERSON, GAIT, AK10_9, AK80_64, BATT, line, fmt } from './params.mjs';

const rpmToRad = (rpm) => (rpm * 2 * Math.PI) / 60;

export function assistTable(mass) {
  const acts = [
    ['Level walk (peak, Winter ~0.5 Nm/kg, UNVERIFIED)', GAIT.walkMomentPk],
    ['Stair ascent (Riener 2002 via review)', GAIT.stairAscentMomentPk],
    ['Stair descent (Riener 2002 via review)', GAIT.stairDescentMomentPk],
    ['Run 3.5 m/s, midstance (Schache 2011)', GAIT.runKneeExtMomentPk],
  ];
  return acts.map(([name, nmkg]) => {
    const bio = nmkg * mass;
    return { name, bio, pctPeak: (AK10_9.peakNm / bio) * 100, pctRated: (AK10_9.ratedNm / bio) * 100 };
  });
}

// Knee angular velocity implied by the published power and moment peaks: w = P / M.
// (Peaks of P and M need not coincide in time — this is a lower-bound estimate of
//  the speed the actuator must follow.)
export function speeds() {
  const swing = Math.abs(GAIT.runTermSwingAbsorbPk) / GAIT.runKneeFlexMomentPk; // rad/s
  const stance = Math.abs(GAIT.runKneeAbsorbPk) / GAIT.runKneeExtMomentPk;
  const busV = BATT.cellsPerPack * BATT.cellV;               // 6S nominal 21.6 V
  const noLoad = rpmToRad((100 * busV) / AK10_9.gear);       // KV100 x V / 9 [CALC]
  const rated24 = rpmToRad(AK10_9.ratedRpm24);
  const ak8064 = rpmToRad(AK80_64.ratedRpm24);
  return { swing, stance, busV, noLoad, rated24, ak8064 };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  line('=== HOW MUCH OF THE KNEE CAN ONE AK10-9 CARRY? ===');
  for (const [label, m] of [['median man', PERSON.massMedian], ['95th pct man', PERSON.mass95]]) {
    line(`\n-- ${label}, ${m} kg --`);
    line('Activity                                         bio peak   AK10-9 48 Nm peak   18 Nm rated');
    for (const r of assistTable(m))
      line(`${r.name.padEnd(48)} ${fmt(r.bio, 0).padStart(5)} Nm   ${fmt(Math.min(r.pctPeak, 999), 0).padStart(5)} %            ${fmt(r.pctRated, 0).padStart(4)} %`);
  }
  line('\nReading: walking and stairs can be covered well. Running gets ~13–18% of the');
  line('midstance knee moment from a 48 Nm peak — in the range other running exos target');
  line('(active running exos report 3.9–14.6% metabolic savings, review claim, UNVERIFIED).');

  const sp = speeds();
  line('\n=== CAN IT KEEP UP WITH A RUNNING KNEE? ===');
  line(`Terminal swing:  ${GAIT.runTermSwingAbsorbPk} W/kg / ${GAIT.runKneeFlexMomentPk} Nm/kg → ~${fmt(sp.swing, 1)} rad/s (${fmt(sp.swing * 57.3, 0)}°/s)`);
  line(`Initial stance:  ${GAIT.runKneeAbsorbPk} W/kg / ${GAIT.runKneeExtMomentPk} Nm/kg → ~${fmt(sp.stance, 1)} rad/s`);
  line(`(A student lab report measured ~478°/s at an unstated speed — same ballpark, weak source.)`);
  line(`AK10-9 on a ${fmt(sp.busV, 1)} V 6S bus: no-load ~${fmt(sp.noLoad, 1)} rad/s; vendor rated speed ${AK10_9.ratedRpm24} rpm = ${fmt(sp.rated24, 1)} rad/s at 24 V → ${fmt(sp.rated24 / sp.swing, 1)}x margin. OK.`);
  line(`AK80-64 rated ${AK80_64.ratedRpm24} rpm = ${fmt(sp.ak8064, 1)} rad/s → ${fmt(sp.ak8064 / sp.swing * 100, 0)}% of the swing speed. It would FIGHT the runner. Rejected.`);

  // reflected inertia vs the shank+foot the knee already swings
  const m = PERSON.massMedian, H = 1.754; // NHANES median stature 175.4 cm [SRC 1]
  const Ls = PERSON.shankFrac * H;
  const mS = PERSON.shankMassFrac * m, mF = PERSON.footMassFrac * m;
  const Ishank = mS * Ls * Ls * (0.251 ** 2 + 0.4395 ** 2); // de Leva radii [SRC 4]
  const Ifoot = mF * Ls * Ls;                              // foot as a point at the ankle, EST
  const Irefl = AK10_9.rotorInertia_gcm2 * 1e-7 * AK10_9.gear ** 2;
  line(`\nReflected rotor inertia: ${AK10_9.rotorInertia_gcm2} g·cm² x ${AK10_9.gear}² = ${fmt(Irefl, 4)} kg·m²`);
  line(`Shank+foot about the knee (median man): ~${fmt(Ishank + Ifoot, 3)} kg·m² → actuator adds ${fmt((Irefl / (Ishank + Ifoot)) * 100, 1)}%. Transparent enough.`);
  line(`Backdrive torque ${AK10_9.backdriveNm} Nm (vendor) — the wearer feels this when unpowered.`);

  line('\n=== FALL CATCH — what it can and cannot do ===');
  for (const mm of [PERSON.massMedian, PERSON.mass95]) {
    const need = GAIT.runKneeExtMomentPk * mm; // single-leg dynamic support, running-like
    line(`${mm} kg: a hard single-leg catch is running-class load ~${fmt(need, 0)} Nm; one AK10-9 gives ${AK10_9.peakNm} Nm = ${fmt((AK10_9.peakNm / need) * 100, 0)}%.`);
  }
  line('So "fall catch" = both knees go to peak torque + high damping in a few ms to BUY TIME and');
  line('keep the knee from buckling fast. It does NOT hold a falling adult. The tooth lock must');
  line('never be thrown at speed — dropping a pawl into a moving ring is how teeth break.');
}
