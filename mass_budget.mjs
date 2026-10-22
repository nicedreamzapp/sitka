// MASS BUDGET — per leg and on the belt, and what it costs the wearer to carry it.
// Mass on the legs is NOT the same as mass on the waist: the further down the leg,
// the more it costs to swing. Weights below are relative to the same mass at the waist.
import { BOM, mass } from './bom.mjs';
import { PERSON, line, fmt } from './params.mjs';

// Cost multipliers vs. waist-carried mass.
//  knee/thigh: Schertzer & Riemer 2014 measured knee/back cost ratios 1.015–1.103 [SRC 14] → 1.06 mid
//  shank:      Schertzer & Riemer ankle/knee 0.99–1.049 → ~1.08 vs back (CALC from the two ratios)
//  foot:       Browning 2007 via Mooney & Herr 2016: foot mass costs >4x waist mass in walking [SRC 13] → 4
const W = { waist: 1.0, thigh: 1.06, knee: 1.06, shank: 1.08, foot: 4.0, none: 0 };

export function budget() {
  const worn = BOM.filter((r) => r.loc !== 'none' && r.kg > 0);
  const byLoc = {};
  for (const r of worn) byLoc[r.loc] = (byLoc[r.loc] || 0) + r.qty * r.kg;
  const legKg = (byLoc.knee || 0) + (byLoc.thigh || 0) + (byLoc.shank || 0) + (byLoc.foot || 0);
  const waistKg = byLoc.waist || 0;
  const equiv = Object.entries(byLoc).reduce((a, [k, v]) => a + v * W[k], 0);
  return { worn, byLoc, perLeg: legKg / 2, waistKg, total: legKg + waistKg, equiv };
}

if (import.meta.url === `file://${process.argv[1]}`) {
  const b = budget();
  line('=== MASS BUDGET (from bom.mjs) ===');
  line('Part                                                   where    each      line');
  for (const r of b.worn) line(`${r.name.slice(0, 54).padEnd(54)} ${r.loc.padEnd(6)} ${fmt(r.kg, 3).padStart(6)} x${r.qty}  ${fmt(r.kg * r.qty, 2).padStart(5)} kg`);
  line('');
  line(`PER LEG: ${fmt(b.perLeg, 2)} kg   BELT: ${fmt(b.waistKg, 2)} kg   TOTAL WORN: ${fmt(b.total, 2)} kg`);
  line('');
  line('Compare (vendor / press numbers, see RESEARCH_REPORT):');
  line('  Dnsys Z1 knee unit      ~0.68 kg per leg  (powered, no seat)');
  line('  Hypershell X Ultra      1.8 kg total w/o battery (hip, no seat)');
  line('  Noonee Chairless Chair  2.95 kg total     (seat, no motor)');
  line(`  Run + Sit Exo P1        ${fmt(b.perLeg, 2)} kg per leg, ${fmt(b.total, 1)} kg total  (both)`);
  line('');
  line(`Waist-equivalent load (distal mass weighted up): ${fmt(b.equiv, 1)} kg — the foot stirrups alone count as ${fmt((b.byLoc.foot || 0) * W.foot, 1)} kg.`);
  for (const m of [PERSON.massMedian, PERSON.mass95])
    line(`  vs a ${m} kg wearer: ~${fmt((b.equiv / m) * 100, 1)}% extra load if walking cost scales with load (EST, first-order).`);
  line('Sobering cross-check: Donelan 2008\'s 1.6 kg knee harvester raised walking cost 19.2% just by being worn.');
  line('Assist must beat the mass penalty before the exo helps at all. Cut the foot mass first: it is the expensive kilogram.');
}
