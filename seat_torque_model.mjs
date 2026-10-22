// SEAT MODE — how much knee torque does it take to hold a 95th-percentile adult
// sitting on the exo, at each of the four lock angles? And what has to hold it?
//
// Free body (side view, one leg):
//   pad force F pushes DOWN on the thigh link at distance s from the knee axis.
//   The thigh link is held by the knee joint, so the knee must resist
//       M_knee = F * s * sin(theta - phi)
//   where theta = knee flexion (0 = straight), phi = forward lean of the shank from
//   vertical, and (theta - phi) = thigh angle from vertical. sin(theta-phi)*s is
//   simply the horizontal lever arm from the knee to the pad.
//   The device stands on the heel stirrup under the ankle. If the pad's centre of
//   pressure sits directly over the heel the wearer is balanced:
//       Ls*sin(phi) = s*sin(theta - phi)   =>   tan(phi) = s*sin(theta) / (Ls + s*cos(theta))
//   Real people shift around, so we also take the WORST lean between upright shank
//   and the balanced lean, then add load factors on top.
import { PERSON, SEAT, AK10_9, AK80_64, MAT, g, line, fmt } from './params.mjs';

const deg = (r) => (r * 180) / Math.PI, rad = (d) => (d * Math.PI) / 180;

export function seatCase(massKg = PERSON.mass95, stature = PERSON.stature95) {
  const Lt = PERSON.thighFrac * stature;             // thigh length [CALC]
  const Ls = PERSON.shankFrac * stature;             // shank length [CALC]
  const s = SEAT.padCoPFrac * Lt;                    // pad CoP lever from knee [EST frac]
  // mass above the shanks: whole body minus two shanks and two feet (de Leva) [CALC]
  const mAbove = massKg * (1 - 2 * (PERSON.shankMassFrac + PERSON.footMassFrac));
  const Fleg = (SEAT.designLoadShare * mAbove * g) / 2; // N per leg, both legs sharing
  const ankleH = 0.08; // ankle axis height above floor in a shoe, EST

  return SEAT.modes.map((m) => {
    const th = rad(m.knee);
    let phiBal = Math.atan2(s * Math.sin(th), Ls + s * Math.cos(th));
    const clamped = deg(phiBal) > SEAT.maxShankLeanDeg;
    if (clamped) phiBal = rad(SEAT.maxShankLeanDeg);
    const Mbal = Fleg * s * Math.sin(th - phiBal);
    // worst lean in [0, phiBal]: maximise sin(th - phi)
    let Mworst = 0, phiWorst = 0;
    for (let p = 0; p <= phiBal + 1e-9; p += rad(0.5)) {
      const M = Fleg * s * Math.sin(th - p);
      if (M > Mworst) { Mworst = M; phiWorst = p; }
    }
    const Mimpact = Mworst * SEAT.sitImpactFactor;   // dropping into the seat
    const MoneLeg = Mworst * 2;                      // all weight shifted onto one leg
    const Mdesign = Math.max(Mimpact, MoneLeg) * SEAT.lockSF;
    const hipH = ankleH + Ls * Math.cos(phiBal) + Lt * Math.cos(th - phiBal);
    return { ...m, Lt, Ls, s, Fleg, phiBalDeg: deg(phiBal), clamped, Mbal, Mworst,
             phiWorstDeg: deg(phiWorst), Mimpact, MoneLeg, Mdesign, hipH };
  });
}

// Pawl / tooth lock sizing for the worst mode
export function lockSizing(Mdesign, radius = 0.035) {
  const Ft = Mdesign / radius;                                   // tooth force, N
  const tauAllow = MAT.shearFrac * MAT.steel174_H900_UTS;        // Pa (SF already in Mdesign)
  const areaMM2 = (Ft / tauAllow) * 1e6;
  return { radius, Ft, areaMM2 };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const rows = seatCase();
  const r0 = rows[0];
  line('=== SEAT MODE — knee torque to hold a 95th-percentile US man ===');
  line(`Person: ${PERSON.mass95} kg (NHANES 95th), ${PERSON.stature95} m (NHANES 95th) — both marginals, paired on purpose`);
  line(`Thigh ${fmt(r0.Lt, 3)} m, shank ${fmt(r0.Ls, 3)} m (Winter fractions), pad CoP ${fmt(r0.s, 3)} m from knee (EST 65% of thigh)`);
  line(`Load per leg, both legs sharing, 100% of mass above the shanks: ${fmt(r0.Fleg, 0)} N`);
  line('');
  line('Mode        knee  bal.shank  hip ht   M balanced  M worst   x1.5 drop  x2 one-leg  LOCK DESIGN (xSF1.5)');
  for (const r of rows) {
    line(`${r.name.padEnd(11)} ${String(r.knee).padStart(4)}°  ${fmt(r.phiBalDeg, 1).padStart(6)}°${r.clamped ? '*' : ' '}  ${fmt(r.hipH, 2)} m  ${fmt(r.Mbal, 0).padStart(6)} Nm  ${fmt(r.Mworst, 0).padStart(5)} Nm  ${fmt(r.Mimpact, 0).padStart(6)} Nm  ${fmt(r.MoneLeg, 0).padStart(7)} Nm   ${fmt(r.Mdesign, 0).padStart(5)} Nm`);
  }
  line('  * shank lean capped at the EST ankle limit — the pad sits behind the heel, feet must take the rest');
  const worst = rows.reduce((a, b) => (b.Mdesign > a.Mdesign ? b : a));
  line('');
  line('=== CAN THE MOTOR HOLD IT? ===');
  line(`Chair, balanced, static: ${fmt(rows[2].Mbal, 0)} Nm per knee.`);
  line(`${AK10_9.name}: ${AK10_9.ratedNm} Nm rated / ${AK10_9.peakNm} Nm peak → ${fmt(rows[2].Mbal / AK10_9.peakNm, 1)}x its PEAK. No.`);
  line(`${AK80_64.name}: ${AK80_64.ratedNm} Nm rated / ${AK80_64.peakNm} Nm peak → ${fmt(rows[2].Mbal / AK80_64.ratedNm, 1)}x its RATED. No — and at ${AK80_64.ratedRpm24} rpm it cannot follow a running knee anyway.`);
  line(`Holding 48 Nm on the AK10-9 alone burns ${fmt(AK10_9.copperW(48), 0)} W per knee as heat — minutes, not hours.`);
  line('VERDICT: the seat is held by a MECHANICAL lock. The motor only positions the knee so the lock can drop in.');
  line('');
  const L = lockSizing(worst.Mdesign);
  line(`=== LOCK SIZING (worst mode: ${worst.name}, ${fmt(worst.Mdesign, 0)} Nm design) ===`);
  line(`Pawl on a toothed ring at r = ${L.radius * 1000} mm → tooth force ${fmt(L.Ft / 1000, 1)} kN`);
  line(`17-4PH H900, shear = 0.6 x ${MAT.steel174_H900_UTS / 1e6} MPa (handbook, VERIFY) → shear area ≥ ${fmt(L.areaMM2, 0)} mm²`);
  line(`SHEAR ONLY. Contact (Hertz) and tooth-bending checks are NOT done yet; plan on 3x this area until they are.`);
  line(`So: e.g. two pawl teeth, each 10 mm wide x ${fmt(Math.ceil((3 * L.areaMM2) / 20), 0)} mm engaged. The lock itself is small.`);
  line('');
  // Thigh upright bending: the full design moment passes through the thigh rail at the knee.
  const sigma = MAT.al7075_yield;
  const Zreq = (worst.Mdesign / sigma) * 1e9; // mm^3
  const b = 8, h = Math.ceil(Math.sqrt((6 * Zreq) / b));
  const railMass = 0.45 * (b * h * 1e-6) * MAT.al7075_rho;
  line(`=== THIGH UPRIGHT (the part that IS hard) ===`);
  line(`Design moment ${fmt(worst.Mdesign, 0)} Nm at yield ${sigma / 1e6} MPa (7075-T6, VERIFY) → section modulus ≥ ${fmt(Zreq, 0)} mm³`);
  line(`One lateral 7075 bar ${b} mm thick needs to be ${h} mm deep → ${fmt(railMass, 2)} kg per 450 mm thigh upright.`);
  line('A single 25x22 mm roll-wrapped carbon tube (Z ≈ 614 mm³) would see ' + fmt(worst.Mdesign * 1e3 / 614, 0) + ' MPa — beyond what we can count on from a roll-wrapped tube. Carbon tubes must go bilateral or much bigger.');
}
