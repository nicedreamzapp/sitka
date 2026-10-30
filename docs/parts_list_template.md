{TABLES}

## 3. Did it reconcile with the README? No, and here is why

The README and KINETICS.md said the starter costs **about $1,300** and weighs **about 4.4 kg**. Counting every part in the CAD gives:

- **Seat + Back starter (Dock + Knee/Seat + Back/Lift): {starter_kg}, {starter_usd}** for prototype one, about **{starter_batch}** per set in a batch of 10 (EST).
- **Full body (every module, one motor): {full_kg}, {full_usd}** for prototype one, about **{full_batch}** in a batch of 10.

Three honest reasons for the gap:

1. **The label was wrong.** The 4.4 kg / $1,300 figure in KINETICS.md is the Basic tier (Dock + Knee/Seat + Back/Lift + Hip + running band), not "Seat + Back". Seat + Back alone was about 3.9 kg / $1,200 in that same plan.
2. **The old numbers were top-down targets, this list is bottom-up.** KINETICS.md budgeted the padding at +0.15 kg and the Dock at 0.7 kg. The CAD's pads alone (graded lattice, gel and spacer mesh on every contact, sized for 15 kPa) come to about 1.2 kg, and a real padded belt, harness and webbing are another 1.1 kg.
3. **Prototype one pays one-off prices.** About {starter_est} of the starter cost is estimate, mostly one-off CNC of the knee metal (hinges, arcs, spool, strut fork). The branded sprag clutches chosen for the power-off seat lock are a real price, about $300 a pair (budget ones are about $20 each, fine for the bench).

{MASS_TABLE}

**Path back down (EST, not designed yet):** carbon layup shells at 1.5 mm instead of 3 mm printed PAHT-CF (about -0.45 kg), lighter lattice or EVA in the short-hold pads (about -0.5 kg), pocketed metal (about -0.3 kg) and a lighter belt and harness (about -0.3 kg) would bring the starter to roughly **4.8 kg**. Batch pricing brings it to roughly **$1,900**. The README now quotes this list, not the old target.

## 4. Print vs metal vs buy

{MAKE_TABLE}

**What must be metal, and the load that decides it.** The rule: anything the knee tendon load passes through, anything a line turns on, and anything that holds a spring root. Those parts see the 426 N sitting tension every sit, and they are sized for the **3.6 kN proof load** (the 190 Nm strut-lost catch times 1.5, from TENDON_CONCEPT.md). PAHT-CF creeps under constant load and a cable groove in plastic wears and cuts.

{METAL_TABLE}

**What prints:** every shell and pad (they spread pressure and do not carry the column), every housing and bracket where a metal pin or bearing takes the actual line load, and the jigs. The glute guide and heel clip are printed for prototype one but flagged: if they creep on the bench they become 7075.

**What you buy:** the carbon strut tubes, the sprag clutches, the line (Dyneema for the bench, Vectran or SK99 for wear, to keep creep under the 0.7 deg of sag per sit in TENDON_CONCEPT.md), the glass for the leaf springs, webbing, buckles, gel sheet, spacer mesh, the motor, cells and electronics.

## 5. Print time and filament (Bambu X1C / P1S class)

{PRINT_TABLE}

- **Seat + Back starter: about {starter_paht} kg of PAHT-CF and {starter_tpu} kg of TPU, about {starter_print_h} printer hours** (about a week on one printer). The whole body is about {all_print_h} hours.
- Hours are EST at about 15 g/h for PAHT-CF on strong settings and 20 g/h for TPU lattice.
- **Print sets** used in the tables:
  - **A (shell):** PAHT-CF (or PA12-CF), 0.4 hardened nozzle, 0.2 mm layers, wall printed solid (6 to 8 perimeters), filament dried 80 C for 8 h.
  - **B (bracket):** PAHT-CF, 0.2 mm, 5 walls, 40% gyroid, layers laid across the load, heat-set inserts.
  - **C (lattice pad):** TPU 95A HF, 0.2 mm, graded gyroid from about 12% at the skin to 25% at the shell, no supports, spacer mesh or gel glued on. KINETICS.md asks for 85A at the skin to 95A at the shell; prototype one grades the density on one material instead (VERIFY on the pressure map).
  - **D (PETG):** 0.2 mm, 3 walls, 20% infill (enclosures and jigs).
- **Too big for a 256 mm bed:** the thigh shells and pads (289 mm) and the back panel and pad (279 mm). Split them with a bolted lap joint, or print them whole on a larger bed (Bambu H2D class).
- STLs for every printed part are in `cad/stl/`. Shells are not exported as STL yet because the CAD marks them carbon; export them from `cad/step/` until the CAD gets a print variant.

## 6. The build story (prototype one)

1. **Scan and fit.** Scan the wearer's legs, hips and back with a phone. Fit the shells in `cad/parts/` to the scan and rebuild, so every pad lands where the physics says.
2. **Order the long-lead parts first:** the metal (send the STEP files from the release to three job shops), the sprag clutches, carbon tubes, line and gel sheet.
3. **Print** the shells, cups, pads and brackets while the metal is out (about {starter_print_h} hours for the starter).
4. **Make the springs.** Laminate the glass leaves, then bench-test the sit leaf's force curve and 10^5 cycles before it goes on a person (gate 2 in KINETICS.md).
5. **Build one knee on the bench:** hinge, arms, arc and yoke, clutch in its housing, then splice the T1 line from the clutch over the arc to the anchor below the kneecap. **Proof-test it to 3.6 kN of line pull.** Then the second knee.
6. **Build the Dock:** belt, panel, harness, seat cups laced to the thigh cuffs, strut forks and rod ends, struts, the spine links and the Crazy Creek straps.
7. **First sits:** pressure-map the seat cup and the pad below the kneecap, then sit 10, 30 and 60 minutes with shifts (gate 1).
8. **Add the back:** lift leaf, whiffletree and the two lift lines to the thigh cuffs; stoop and squat lifts with 15 kg (gate 3).
9. **Then upgrade one module at a time:** hip bands and the running band, then the smart clutches (bench them wet and dry at 375 N first), then the motor, then ankle and shoulder.

Every gate before a part is worn is in [BUILD_RIGHT_FIRST_TIME.md](BUILD_RIGHT_FIRST_TIME.md).

## 7. Every part, by module

{PART_TABLES}
