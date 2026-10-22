// BILL OF MATERIALS — the ONE source of truth. PARTS_LIST_BOM.md is generated from
// this file (`node bom.mjs --md > PARTS_LIST_BOM.md`), the mass budget and the
// project cost import it, so prices and masses can never disagree between files.
//
// src: a URL + date for a real quote, or 'EST' with a reason. loc: where the mass
// rides on the body (drives the metabolic-cost weighting in mass_budget.mjs).
// Prices seen 2026-10-21 unless noted. USD.
import { BATT, AK10_9 } from './params.mjs';

export const BOM = [
  // ---------------- A. KNEE ACTUATION + SEAT LOCK (per exo, both legs) ----------------
  { id: 'A1', grp: 'A', name: 'Knee actuator — CubeMars AK10-9 V2.0 KV100', spec: '9:1 QDD, 18 Nm rated / 48 Nm peak, CAN, dual encoder, 0.8 Nm backdrive', qty: 2, usd: AK10_9.priceUSD, kg: AK10_9.massKg, loc: 'knee', src: 'https://www.cubemars.com/goods-1148-AK10-9+V20.html' },
  { id: 'A2', grp: 'A', name: 'Seat lock — toothed ring + pawl, 17-4PH H900', spec: 'r = 35 mm, 4 detents (25/60/90/120°) + fine teeth between; 507 Nm design hold', qty: 2, usd: 180, kg: 0.20, loc: 'knee', src: 'EST — custom CNC part, needs a quote (SendCutSend/PCBWay CNC)' },
  { id: 'A3', grp: 'A', name: 'Pawl actuator — bistable latching solenoid', spec: 'stays put with power off: a locked seat stays locked, a free knee stays free', qty: 2, usd: 25, kg: 0.03, loc: 'knee', src: 'EST — generic 12–24 V latching solenoid' },
  { id: 'A4', grp: 'A', name: 'Pawl-engaged hall sensor + magnet', spec: 'confirms the pawl is fully seated before the motor lets go', qty: 2, usd: 3, kg: 0.005, loc: 'knee', src: 'EST' },

  // ---------------- B. STRUCTURE ----------------
  { id: 'B1', grp: 'B', name: 'Donor hinged knee brace — DonJoy (aluminium hinge)', spec: 'gives cuffs, straps and the MEDIAL passive hinge; lateral hinge replaced by A1', qty: 2, usd: 189.99, kg: 0.50, loc: 'knee', src: 'https://arrowheadmedstore.com/product/donjoy-drytex-economy-hinged-knee-w-popout (kg EST)' },
  { id: 'B2', grp: 'B', name: '7075-T651 bar 3/4" x 1-1/2" x 36" (Speedy Metals)', spec: 'machined to 8 x 28 mm lateral uprights: 2 thigh + 2 shank per bar pair', qty: 2, usd: 91.60, kg: 0, loc: 'none', src: 'https://speedymetals.com/p-2694-34-x-1-12-7075-t651-aluminum-cold-finish.aspx' },
  { id: 'B2m', grp: 'B', name: 'Lateral uprights (finished, from B2)', spec: 'thigh + shank, 8 x 28 mm 7075, Z ≥ 1008 mm³ (seat_torque_model.mjs)', qty: 4, usd: 0, kg: 0.28, loc: 'knee', src: 'CALC — 0.45 m x 8 x 28 mm x 2810 kg/m³' },
  { id: 'B3', grp: 'B', name: 'Heel stirrup + shoe clip', spec: 'carries the seat load from the shank upright into the ground under the heel', qty: 2, usd: 60, kg: 0.25, loc: 'foot', src: 'EST — 7075 strip + clip, modelled on the Chairless Chair heel path' },
  { id: 'B4', grp: 'B', name: 'Fold-down seat pad', spec: 'aluminium pan + 20 mm closed-cell foam + hinge + over-centre detent', qty: 2, usd: 35, kg: 0.18, loc: 'thigh', src: 'EST' },
  { id: 'B5', grp: 'B', name: 'Fasteners, bushings, thread-locker', spec: '', qty: 1, usd: 60, kg: 0.10, loc: 'knee', src: 'EST' },
  { id: 'B6', grp: 'B', name: 'CNC machining of uprights, stirrups, lock rings', spec: 'outsourced; the biggest unknown in the parts list', qty: 1, usd: 600, kg: 0, loc: 'none', src: 'EST — get 3 quotes before M1' },

  // ---------------- C. SENSING + CONTROL ----------------
  { id: 'C1', grp: 'C', name: 'Teensy 4.1 (SparkFun DEV-16771)', spec: '600 MHz, native CAN — same MCU family as NAU OpenExo', qty: 1, usd: 31.50, kg: 0.01, loc: 'waist', src: 'https://www.sparkfun.com/teensy-4-1.html' },
  { id: 'C2', grp: 'C', name: 'CAN transceiver — Waveshare SN65HVD230', spec: '3.3 V', qty: 1, usd: 4.99, kg: 0.005, loc: 'waist', src: 'https://www.waveshare.com/product/iot-communication/wired-comm-converter/rs232-rs485-can-dali2/sn65hvd230-can-board.htm' },
  { id: 'C3', grp: 'C', name: 'IMU — Adafruit BNO085 (#4754)', spec: 'pelvis + each shank; gait phase, stillness, stumble detection', qty: 3, usd: 29.50, kg: 0.005, loc: 'knee', src: 'https://www.adafruit.com/product/4754' },
  { id: 'C4', grp: 'C', name: 'FSR — Interlink 402', spec: '4 per foot: heel, 1st + 5th metatarsal, toe', qty: 8, usd: 2.99, kg: 0.002, loc: 'foot', src: 'https://www.interlinkelectronics.com/products/fsr-model-402' },
  { id: 'C5', grp: 'C', name: 'Insole carrier + foot harness', spec: '', qty: 2, usd: 10, kg: 0.03, loc: 'foot', src: 'EST' },
  { id: 'C6', grp: 'C', name: 'BLE / phone link — Adafruit ESP32-S3 Feather (#5477)', spec: 'seat offer, place memory, app', qty: 1, usd: 17.50, kg: 0.01, loc: 'waist', src: 'https://www.adafruit.com/product/5477' },
  { id: 'C7', grp: 'C', name: 'Haptic disc — Adafruit #1201', spec: 'the "seat offer" buzz, one per thigh', qty: 2, usd: 1.95, kg: 0.002, loc: 'thigh', src: 'https://www.adafruit.com/product/1201' },
  { id: 'C8', grp: 'C', name: 'Belt tap button + big red E-STOP', spec: 'E-stop cuts motor power; the latching pawls hold their state', qty: 1, usd: 20, kg: 0.05, loc: 'waist', src: 'EST' },
  { id: 'C9', grp: 'C', name: 'Harness: CAN + power cable, XT30 / JST-GH, fuse, 5 V DC-DC', spec: '', qty: 1, usd: 75, kg: 0.25, loc: 'knee', src: 'EST' },
  { id: 'C10', grp: 'C', name: 'Controller enclosure (printed)', spec: '', qty: 1, usd: 10, kg: 0.10, loc: 'waist', src: 'EST' },

  // ---------------- D. POWER ----------------
  { id: 'D1', grp: 'D', name: 'Cell — Molicel P45B 21700 4.5 Ah', spec: '2 packs x 6S1P = 2 x 97.2 Wh (each under FAA 100 Wh)', qty: BATT.packs * BATT.cellsPerPack, usd: BATT.cellPriceUSD, kg: BATT.cellMassKg, loc: 'waist', src: 'https://www.batteryjunction.com/molicel-inr21700-p45b (kg EST ~70 g)' },
  { id: 'D2', grp: 'D', name: '6S BMS + nickel + pack case', spec: 'quick-swap belt packs', qty: BATT.packs, usd: 21, kg: BATT.packOverheadKg, loc: 'waist', src: 'EST — generic BMS $3–6 seen for 10S; case/strip EST' },
  { id: 'D3', grp: 'D', name: '6S balance charger', spec: '', qty: 1, usd: 45, kg: 0, loc: 'none', src: 'EST' },
  { id: 'D4', grp: 'D', name: 'Hip belt — Peak Design outdoor hip belt', spec: 'carries packs + controller', qty: 1, usd: 44.95, kg: 0.20, loc: 'waist', src: 'https://www.peakdesign.com/products/outdoor-hip-belt (kg EST)' },
];

export const GROUPS = { A: 'KNEE ACTUATION + SEAT LOCK', B: 'STRUCTURE', C: 'SENSING + CONTROL', D: 'POWER + BELT' };
export const total = (rows = BOM) => rows.reduce((a, r) => a + r.qty * r.usd, 0);
export const mass = (rows = BOM) => rows.reduce((a, r) => a + r.qty * r.kg, 0);
const $ = (n) => '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes('--md')) {
    console.log('# Run + Sit Exo — Bill of Materials (prototype one)');
    console.log('**Generated by `node bom.mjs --md` on ' + new Date().toISOString().slice(0, 10) + '.** Do not hand-edit; edit `bom.mjs`.\n');
    console.log('Prices are USD, seen 2026-10-21 at the linked retailer. **EST** means our estimate, not a quote. Masses marked EST have not been weighed.\n');
    for (const [k, title] of Object.entries(GROUPS)) {
      const rows = BOM.filter((r) => r.grp === k);
      console.log(`## ${k}. ${title}`);
      console.log('| # | Part | Spec | Qty | Mass ea | Cost ea | Line | Source |');
      console.log('|---|---|---|---|---|---|---|---|');
      for (const r of rows) {
        const src = r.src.startsWith('http') ? `[link](${r.src.split(' ')[0]})${r.src.includes(' ') ? ' ' + r.src.split(' ').slice(1).join(' ') : ''}` : r.src;
        console.log(`| ${r.id} | ${r.name} | ${r.spec} | ${r.qty} | ${r.kg ? r.kg + ' kg' : '—'} | ${r.usd ? $(r.usd) : '—'} | ${$(r.qty * r.usd)} | ${src} |`);
      }
      console.log(`| | **Subtotal** | | | **${mass(rows).toFixed(2)} kg** | | **${$(total(rows))}** | |\n`);
    }
    console.log('## Roll-up');
    console.log('| | Mass | Cost |\n|---|---|---|');
    for (const [k, title] of Object.entries(GROUPS)) { const rows = BOM.filter((r) => r.grp === k); console.log(`| ${k} ${title} | ${mass(rows).toFixed(2)} kg | ${$(total(rows))} |`); }
    console.log(`| **TOTAL — parts for one exo** | **${mass().toFixed(2)} kg** | **${$(total())}** |`);
    const est = BOM.filter((r) => r.src.startsWith('EST')).reduce((a, r) => a + r.qty * r.usd, 0);
    console.log(`\n**${$(est)} of the ${$(total())} (${((est / total()) * 100).toFixed(0)}%) is estimate, not quote** — mostly machining (B6) and the custom lock (A2). See \`project_cost.mjs\` for what a parts list leaves out, and \`mass_budget.mjs\` for where the mass rides.`);
    console.log('\n## Rejected parts (and why)');
    console.log('| Part | Why not |\n|---|---|');
    console.log('| CubeMars AK80-64 ($889.90, 48/120 Nm) | 64:1 → 23 rpm rated at 24 V = 28% of running swing speed; a 64:1 reducer is hard to backdrive (vendor gives no backdrive figure); still only 120 Nm peak vs 142 Nm chair hold. |');
    console.log('| MyActuator RMD-X12-P20 (85/320 Nm, 2.4 kg) | Could hold the seat on torque, but 2.4 kg per knee and holding burns heat continuously. A 0.2 kg pawl does it for 0 W. |');
    console.log('| Spring-applied e-brake on the motor shaft | Needs ~507/9 = 56 Nm at the rotor through a 9:1 gear. The largest small 24 V brakes found hold 5.65–10 Nm (Warner, Precima FDB 10), so it does not fit at the knee. |');
    console.log('| Carbon tube uprights (25x22 mm) | ~826 MPa at the design moment; only workable bilateral or much larger. Kept as a v2 weight-loss option. |');
  } else {
    for (const [k, title] of Object.entries(GROUPS)) {
      const rows = BOM.filter((r) => r.grp === k);
      console.log(`${k} ${title.padEnd(28)} ${mass(rows).toFixed(2).padStart(6)} kg  ${$(total(rows)).padStart(10)}`);
    }
    console.log(`TOTAL parts, one exo          ${mass().toFixed(2).padStart(6)} kg  ${$(total()).padStart(10)}`);
  }
}
