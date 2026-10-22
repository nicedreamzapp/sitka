// BILL OF MATERIALS — the ONE source of truth. PARTS_LIST_BOM.md is generated from
// this file (`node bom.mjs --md > PARTS_LIST_BOM.md`), the mass budget and the
// project cost import it, so prices and masses can never disagree between files.
//
// src: a URL + date for a real quote, or 'EST' with a reason. loc: where the mass
// rides on the body (drives the metabolic-cost weighting in mass_budget.mjs).
// Prices seen 2026-10-21 unless noted. USD.
import { BATT, AK10_9 } from '../params.mjs';

export const BOM = [
  // ---------------- A. KNEE ACTUATION + SEAT LOCK (per exo, both legs) ----------------
  { id: 'A1', grp: 'A', name: 'Knee actuator — CubeMars AK10-9 V2.0 KV100', spec: '9:1 QDD, 18 Nm rated / 48 Nm peak, CAN, dual encoder, 0.8 Nm backdrive', qty: 2, usd: AK10_9.priceUSD, kg: AK10_9.massKg, loc: 'knee', src: 'https://www.cubemars.com/goods-1148-AK10-9+V20.html' },
  { id: 'A2', grp: 'A', name: 'One-way ratchet — 140° toothed sector + DUAL 3-tooth pawls (offset half a pitch), 17-4PH H900', spec: '40T at r = 50 mm, 12 mm wide, MATCHED flank angles + crown relief; blocks FLEXION, extension always free; worst sag onto a tooth 4.5° (2.7 cm at the pad); 507 Nm fallback: 359 MPa bending on 2 teeth, 717 MPa on 1 (SF 1.6, proof test required); flank contact 134 / 269 MPa (seat_torque_model.mjs)', qty: 2, usd: 220, kg: 0.28, loc: 'knee', src: 'EST — custom CNC + wire-EDM teeth, needs a quote' },
  { id: 'A3', grp: 'A', name: 'Pawl lift — bistable latching solenoid (lifts both pawls via a yoke) + sprung mechanical detent', spec: 'lifts the pawls only when unloaded (knee < 20° and extending, or load sensors ≈ 0); the detent out-holds the solenoid’s 4 N so it can never drop a pawl mid-stride; always-live 12 V rail', qty: 2, usd: 59, kg: 0.035, loc: 'knee', src: 'https://rapidonline.com/intertec-its-lx-2218-12vdc-10mm-4n-de-energised-20n-bi-directional-solenoid-50-2909 (Intertec ITS-LX-2218, £40.32 ≈ $54, 4/20 N bistable) + $5 detent spring/ball EST; kg EST' },
  { id: 'A4', grp: 'A', name: 'Pawl-engaged hall sensor + magnet (one per pawl)', spec: 'confirms each pawl is fully seated; the motor lets go only when hall = engaged AND the load sensor carries load', qty: 4, usd: 3, kg: 0.005, loc: 'knee', src: 'EST' },
  { id: 'A5', grp: 'A', name: 'Pawl load sensor — strain gauge (one per pawl) + HX711', spec: 'reads tooth load; a pawl may only lift when it reads ~0', qty: 4, usd: 10, kg: 0.01, loc: 'knee', src: 'EST' },
  { id: 'A6', grp: 'A', name: 'Sector mounting — 8 x M4 class 12.9 socket cap screws per knee to the AK10-9 output flange', spec: '1.76 kN shear each at 507 Nm on a 72 mm bolt circle (EST — confirm on the CubeMars drawing); 12.9 M4 ≈ 6.4 kN shear → SF 3.7', qty: 16, usd: 0.6, kg: 0.002, loc: 'knee', src: 'EST — commodity 12.9 M4 cap screws' },
  { id: 'A7', grp: 'A', name: 'Pawl housing on the actuator case outboard face (7075, pawl pivots + detent + sensor mounts)', spec: 'bolts to the AK10-9 case mounting holes; carries the pawl reaction back into the thigh rail', qty: 2, usd: 45, kg: 0.06, loc: 'knee', src: 'EST — CNC part, quote with B6' },

  // ---------------- B. STRUCTURE ----------------
  { id: 'B1', grp: 'B', name: 'Donor hinged knee brace — DonJoy (aluminium hinge)', spec: 'donor for straps and rigid shell cuffs (silicone-lined; shin cuff on the tibial crest); its polycentric hinges are discarded', qty: 2, usd: 189.99, kg: 0.50, loc: 'knee', src: 'https://arrowheadmedstore.com/product/donjoy-drytex-economy-hinged-knee-w-popout (kg EST)' },
  { id: 'B2', grp: 'B', name: '7075-T651 bar 3/4" x 1-1/2" x 36" (Speedy Metals)', spec: 'machined to 8 x 28 mm lateral uprights: 2 thigh + 2 shank per bar pair', qty: 2, usd: 91.60, kg: 0, loc: 'none', src: 'https://speedymetals.com/p-2694-34-x-1-12-7075-t651-aluminum-cold-finish.aspx' },
  { id: 'B2t', grp: 'B', name: 'Lateral thigh upright (from B2)', spec: '8 x 28 mm 7075, Z ≥ 1008 mm³; slotted ±10 mm knee-axis mount at the lateral epicondyle; length-adjust', qty: 2, usd: 0, kg: 0.28, loc: 'thigh', src: 'CALC — 0.45 m x 8 x 28 mm x 2810 kg/m³' },
  { id: 'B2s', grp: 'B', name: 'Lateral shank upright (from B2)', spec: '8 x 28 mm 7075, bolted to the actuator output flange, runs to the ankle pivot', qty: 2, usd: 0, kg: 0.28, loc: 'shank', src: 'CALC — 0.45 m x 8 x 28 mm x 2810 kg/m³' },
  { id: 'B3', grp: 'B', name: 'Heel stirrup + heel pad + shoe-heel-counter strap', spec: 'hangs from the ankle pivot (B9); heel pad directly below the pivot', qty: 2, usd: 60, kg: 0.25, loc: 'foot', src: 'EST — 7075 strip + strap, after the Chairless Chair heel path' },
  { id: 'B4', grp: 'B', name: 'Fold-down seat pad, 200 x 180 mm', spec: 'aluminium pan + 20 mm closed-cell foam; hinged on the lateral rail, proximal (75% of thigh from the knee)', qty: 2, usd: 40, kg: 0.22, loc: 'thigh', src: 'EST' },
  { id: 'B7', grp: 'B', name: 'Rear leg — 3-section uniform-wall carbon tube 24/20/16 x 1.5 mm + pivoting foot', spec: 'roll-wrapped 3K tube, 3 x 0.32 m, 65 mm overlaps, bushings; one-way lock (extends freely, locks in compression), torsion-spring retract, hinge boss at the thigh-rail top. 0.35 m stowed → 0.46 / 0.65 / 0.84 m; buckling 3.16 kN at 0.84 m (stepped-column solve). Foot: 360° pivoting rubber cane tip ($18.95) + flip-down ice/trail spike tip ($20.59); carbide option not sourced', qty: 2, usd: 85, kg: 0.30, loc: 'thigh', src: 'EST total — tubes ~$10 per 500 mm (https://www.ebay.de/itm/155584394259, 20 x 17 mm, unverified seller) x3 + feet $39.54 (https://fashionablecanes.com/products/ingrid-ice-gripper-cane-tip and retail listings, 2026-10-21) + ~$15 lock/boss/spring EST; tubes 130 g CALC + 0.17 kg hardware EST' },
  { id: 'B8', grp: 'B', name: 'Medial bars + single-axis medial hinge + 2 bridges', spec: '6 x 20 mm 7075, 0.36 m thigh + 0.10 m shank, hinge coaxial with the actuator; anterior thigh bridge above the patella, posterior shank bridge', qty: 2, usd: 40, kg: 0.24, loc: 'thigh', src: 'CALC bars 0.46 m x 6 x 20 mm x 2810 kg/m³ = 0.16 kg + bridges 0.08 EST' },
  { id: 'B9', grp: 'B', name: 'Ankle pivot (free, +35° dorsi / −45° plantar hard stops) at the lateral malleolus', spec: 'joins the shin rail to the stirrup; plain bearing + hard stops', qty: 2, usd: 20, kg: 0.05, loc: 'ankle', src: 'EST' },
  { id: 'B10', grp: 'B', name: 'Suspension yoke + 2 straps per side', spec: 'belt rear, over the glute, to a yoke at the thigh-rail top: stops the leg units migrating down. NO rigid hip joint', qty: 1, usd: 25, kg: 0.12, loc: 'thigh', src: 'EST — webbing, ladder-locks, 2 printed yokes (one set per exo)' },
  { id: 'B11', grp: 'B', name: 'Pad medial support arm', spec: 'carries the medial edge of the pad pan to the medial bar', qty: 2, usd: 15, kg: 0.04, loc: 'thigh', src: 'EST' },
  { id: 'B5', grp: 'B', name: 'Fasteners, bushings, thread-locker', spec: '', qty: 1, usd: 60, kg: 0.10, loc: 'knee', src: 'EST' },
  { id: 'B6', grp: 'B', name: 'CNC machining of uprights, stirrups, lock rings', spec: 'outsourced; the biggest unknown in the parts list', qty: 1, usd: 600, kg: 0, loc: 'none', src: 'EST — get 3 quotes before M1' },

  // ---------------- C. SENSING + CONTROL ----------------
  { id: 'C1', grp: 'C', name: 'Teensy 4.1 (SparkFun DEV-16771)', spec: '600 MHz, native CAN — same MCU family as NAU OpenExo', qty: 1, usd: 31.50, kg: 0.01, loc: 'waist', src: 'https://www.sparkfun.com/teensy-4-1.html' },
  { id: 'C2', grp: 'C', name: 'CAN transceiver — Waveshare SN65HVD230', spec: '3.3 V', qty: 1, usd: 4.99, kg: 0.005, loc: 'waist', src: 'https://www.waveshare.com/product/iot-communication/wired-comm-converter/rs232-rs485-can-dali2/sn65hvd230-can-board.htm' },
  { id: 'C3', grp: 'C', name: 'IMU — Adafruit BNO085 (#4754), shank', spec: 'gait phase, stillness, stumble detection', qty: 2, usd: 29.50, kg: 0.005, loc: 'shank', src: 'https://www.adafruit.com/product/4754' },
  { id: 'C3p', grp: 'C', name: 'IMU — Adafruit BNO085 (#4754), pelvis', spec: 'in the controller box', qty: 1, usd: 29.50, kg: 0.005, loc: 'waist', src: 'https://www.adafruit.com/product/4754' },
  { id: 'C4', grp: 'C', name: 'FSR — Interlink 402', spec: '4 per foot: heel, 1st + 5th metatarsal, toe', qty: 8, usd: 2.99, kg: 0.002, loc: 'foot', src: 'https://www.interlinkelectronics.com/products/fsr-model-402' },
  { id: 'C5', grp: 'C', name: 'Insole carrier + foot harness', spec: '', qty: 2, usd: 10, kg: 0.03, loc: 'foot', src: 'EST' },
  { id: 'C6', grp: 'C', name: 'BLE / phone link — Adafruit ESP32-S3 Feather (#5477)', spec: 'seat offer, place memory, app', qty: 1, usd: 17.50, kg: 0.01, loc: 'waist', src: 'https://www.adafruit.com/product/5477' },
  { id: 'C7', grp: 'C', name: 'Haptic disc — Adafruit #1201', spec: 'the "seat offer" buzz, one per thigh', qty: 2, usd: 1.95, kg: 0.002, loc: 'thigh', src: 'https://www.adafruit.com/product/1201' },
  { id: 'C8', grp: 'C', name: 'Belt tap button + big red E-STOP', spec: 'E-stop cuts motor power; the latching pawls hold their state', qty: 1, usd: 20, kg: 0.05, loc: 'waist', src: 'EST' },
  { id: 'C9', grp: 'C', name: 'Harness: 24 V + CAN per side in a braided sleeve, XT30 / JST-GH, fuse, 5 V DC-DC', spec: 'belt → service loop at the rail top (120° hip flexion) → lateral rail → actuator gland; branch at the knee to the shank IMU and down the shin rail to the insole', qty: 1, usd: 75, kg: 0.30, loc: 'thigh', src: 'EST' },
  { id: 'C11', grp: 'C', name: '12 V always-live rail for the pawl solenoids', spec: 'separate DC-DC; the E-stop cuts MOTORS only, so the ratchet keeps working', qty: 1, usd: 8, kg: 0.02, loc: 'waist', src: 'EST' },
  { id: 'C10', grp: 'C', name: 'Controller enclosure (printed)', spec: '', qty: 1, usd: 10, kg: 0.10, loc: 'waist', src: 'EST' },

  // ---------------- D. POWER ----------------
  { id: 'D1', grp: 'D', name: 'Cell — Molicel P45B 21700 4.5 Ah', spec: '2 packs x 6S1P = 2 x 97.2 Wh (each under FAA 100 Wh)', qty: BATT.packs * BATT.cellsPerPack, usd: BATT.cellPriceUSD, kg: BATT.cellMassKg, loc: 'waist', src: 'https://www.batteryjunction.com/molicel-inr21700-p45b (kg EST ~70 g)' },
  { id: 'D2', grp: 'D', name: '6S BMS + nickel + pack case', spec: 'quick-swap belt packs', qty: BATT.packs, usd: 21, kg: BATT.packOverheadKg, loc: 'waist', src: 'EST — generic BMS $3–6 seen for 10S; case/strip EST' },
  { id: 'D3', grp: 'D', name: '6S balance charger', spec: '', qty: 1, usd: 45, kg: 0, loc: 'none', src: 'EST' },
  { id: 'D4', grp: 'D', name: 'Hip belt — Peak Design outdoor hip belt', spec: 'carries packs + controller + the suspension-strap anchors', qty: 1, usd: 44.95, kg: 0.28, loc: 'waist', src: 'https://www.peakdesign.com/products/outdoor-hip-belt (kg EST)' },
];

export const GROUPS = { A: 'KNEE ACTUATION + SEAT LOCK', B: 'STRUCTURE', C: 'SENSING + CONTROL', D: 'POWER + BELT' };
export const total = (rows = BOM) => rows.reduce((a, r) => a + r.qty * r.usd, 0);
export const mass = (rows = BOM) => rows.reduce((a, r) => a + r.qty * r.kg, 0);
const $ = (n) => '$' + n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

if (import.meta.url === `file://${process.argv[1]}`) {
  if (process.argv.includes('--md')) {
    console.log('# Sitka — Bill of Materials (prototype one)');
    console.log('> **Legacy:** this is the retired rigid v2 design (knee motors, ratchets, metal uprights); the current parts list is [PARTS_LIST.md](../PARTS_LIST.md).\n');
    console.log('**Generated by `node legacy/bom.mjs --md > legacy/PARTS_LIST_BOM.md` on ' + new Date().toISOString().slice(0, 10) + '.** Do not hand-edit; edit `bom.mjs`.\n');
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
    console.log('| CubeMars AK80-64 ($889.90, 48/120 Nm) | 64:1 → 23 rpm rated at 24 V = 28% of running swing speed; a 64:1 reducer is hard to backdrive (vendor gives no backdrive figure); still only 120 Nm peak vs the 507 Nm fallback lock load (and 72 Nm even with the rear leg). |');
    console.log('| MyActuator RMD-X12-P20 (85/320 Nm, 2.4 kg) | Could hold the seat on torque, but 2.4 kg per knee and holding burns heat continuously. A 0.2 kg pawl does it for 0 W. |');
    console.log('| Rigid hip joint between belt and legs (v1 left them unconnected) | A 3-DOF passive hip is the v2 plan only (flexion pivot coaxial with the greater trochanter, ab/ad 50 mm posterior-superior, rotation via a 30 mm slotted prismatic). P1 hangs each leg unit from the belt on straps; seat loads never go through the belt. |');
    console.log('| Monopod / single rear leg, or a stiffened ankle | Monopod puts the support in line with nothing; a locked ankle makes the wearer\'s own ankle carry the tipping moment. Rejected for two rear legs + a free ankle pivot. |');
    console.log('| Spring-applied e-brake on the motor shaft | Needs ~507/9 = 56 Nm at the rotor through a 9:1 gear. The largest small 24 V brakes found hold 5.65–10 Nm (Warner, Precima FDB 10), so it does not fit at the knee. |');
    console.log('| Carbon tube uprights (25x22 mm) | ~826 MPa at the 507 Nm fallback moment; only workable bilateral or much larger. Kept as a v2 weight-loss option. |');
    console.log('| Single-tooth pawl at r = 35 mm (v1) | ~1.98 GPa tooth bending at the fallback load: fails. Replaced by the 3-tooth ratchet at r = 50 mm (359 MPa). |');
  } else {
    for (const [k, title] of Object.entries(GROUPS)) {
      const rows = BOM.filter((r) => r.grp === k);
      console.log(`${k} ${title.padEnd(28)} ${mass(rows).toFixed(2).padStart(6)} kg  ${$(total(rows)).padStart(10)}`);
    }
    console.log(`TOTAL parts, one exo          ${mass().toFixed(2).padStart(6)} kg  ${$(total()).padStart(10)}`);
  }
}
