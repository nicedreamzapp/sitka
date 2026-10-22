// PROJECT COST — the parts list is not the project. Same honesty rule as Sky Tribe:
// show what a BOM quietly leaves out, and the cheapest step that answers the
// biggest question first.
import { BOM, total } from './bom.mjs';
import { AK10_9 } from './params.mjs';

const f = (n) => '$' + Math.round(n).toLocaleString('en-US');
const parts = total();
const usd = (id) => BOM.find((r) => r.id === id).usd;  // one unit, from bom.mjs

console.log('=== 1. ONE EXO, PARTS ONLY (bom.mjs) ===');
console.log(`Prototype one (P1), both legs:   ${f(parts)}`);

console.log('\n=== 2. WHAT THE PARTS LIST DOES NOT INCLUDE (all EST) ===');
const missing = [
  ['Knee test stand: aluminium dummy leg, load cell + HX711, clamps', 400],
  ['Bench power supply 30 V / 10 A (actuator bring-up)', 120],
  ['Spare actuator (one will get cooked in tuning)', AK10_9.priceUSD],
  ['Spare lock ring + pawl set', 180],
  ['Overhead safety harness + rope + anchor for first sit tests', 250],
  ['Filament, foam, straps, Velcro, test fixtures', 120],
  ['Shipping, duties, sales tax (~10% of parts)', parts * 0.10],
  ['Breakage allowance (M2–M4 exist to find failures)', 500],
];
let m = 0;
for (const [n, c] of missing) { m += c; console.log(`  ${n.padEnd(62)} ${f(c).padStart(7)}`); }
console.log(`  ${'SUBTOTAL'.padEnd(62)} ${f(m).padStart(7)}`);
console.log(`\nP1 WORN AND TESTED, ALL IN:     ${f(parts + m)}   (labour $0 — assumes you build it)`);

console.log('\n=== 3. YOU DO NOT BUILD THE WHOLE EXO FIRST ===');
const steps = [
  ['M1  one knee on a dummy-leg stand: actuator + lock + controller + stand',
    AK10_9.priceUSD + usd('A2') + usd('A3') + usd('A4') + usd('A5') + 31.5 + 4.99 + 120 + 400 + 150],
  ['M2  one leg, worn, walking/stairs only, no seat', 189.99 + 91.6 + 60 + 40 + 20 + 25 + 300 + 29.5 * 2 + 2.99 * 4 + 80 + 60],
  ['M3  both legs + belt + packs, running and hiking assist', parts / 2],
  ['M4  rear legs + seat modes, under an overhead harness first', 250 + 40 * 2 + 60 * 2 + 15 * 2 + 10 * 2 + 180],
];
let s = 0;
for (const [n, c] of steps) { s += c; console.log(`  ${n.padEnd(76)} ${f(c).padStart(7)}`); }
console.log('  (Steps overlap with the parts list; they show when the money moves, not extra money.)');
console.log(`\n  The cheapest useful thing: M1, ~${f(steps[0][1])}. It answers the two questions that`);
console.log('  decide the project — does the 3-tooth ratchet hold 507 Nm and drop in cleanly at every tooth,');
console.log('  and does the motor stay cool through a simulated hour of hiking — before anything is worn.');
console.log('  M1 also buckle-tests the real rear-leg pole (1 kN design) and measures rubber-foot friction.');
