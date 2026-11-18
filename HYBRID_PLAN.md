# Sitka Seat: the hybrid build plan (November 2026)

**[Open the phone-friendly plan with every part and price](https://nicedreamzapp.github.io/sitka/plan.html)**

This plan comes from a full audit of this repo plus a second pass that re-derived every number from the CAD (`cad/parts/build_parts.py`, the STLs in `cad/stl/`, `parts.csv`, and the `.mjs` models). Nothing in the CAD has been changed yet. This is the direction for the next design round.

## The verdict

The sitting physics is sound. With the strut hinge under the sit bone, a chair pose at 10° of recline puts 33 Nm on the knee and 413 N in the tendon. The struts carry 70% of body weight, and there's 9° of margin before tipping back.

The parts as drawn now are not ready to wear:

| Part | Problem (our numbers) | Fix |
|---|---|---|
| Sit leaf spring (34 g E-glass) | It stores 6 to 17 J against the 44 J needed, and its tip moves only 30 to 60 mm of the 126 mm stroke | 16 mm latex speargun band, 22 to 30 g per knee at 3x stretch |
| 80 mm knee arc + 12 x 6 mm yoke | In the 3.6 kN strut-loss catch, the yoke section sees 1,650 to 3,900 MPa | Laser-cut 7075 side plates (about 115 MPa), or drop the rigid catch entirely (below) |
| CSK20 sprag in `knee_manifold` | A 47 mm OD bearing will not fit a 44.7 mm housing. The take-up spring is missing from the BOM | Repackage it, or replace the sprag lock (below) |
| 5-section twist-lock strut | Friction locks slip under a steady load, and one row of the BOM specifies two different lock types | Crutch lower tube with a push-button pin |
| 3.5 mm PAHT-CF seat cup | The fork footprint puts 63 to 80 MPa locally into the cup, which will creep | Bicycle saddle shell on rails, or 6 mm ribbed with an aluminium doubler |
| Glute guides and hip standoffs | They sit on soft belt fabric and take 300 to 800 N | A 2 mm HDPE framesheet in the belt |
| Ankle module | The frame isn't in the CAD yet | Design the frame before building M4 |

Starter as listed: **$2,850 and 6.66 kg**. About half of that is one-off CNC metal.

## The hybrid: the simplest proven part for each job

The rule for this round is tension before structure, and bought before invented.

- **Knee lock: a rigid-locking gas spring across the knee** (the office-chair / hospital-bed Bloc-O-Lift type), released by a cable lever on the belt. It locks at any angle. If something slips, the wearer sinks instead of dropping, which removes the arc, yoke, sprag and 3.6 kN catch chain. The loads are 320 N at a 90° chair, 490 N at a 60° half-sit, and 1.8 kN with a strut lost. The Noonee Chairless Chair uses the same idea with a hydraulic damper. As a backup on the same bench, try a BMX freewheel ratchet on a 14 mm spool.
- **Spring: latex speargun band**, run in parallel for stand-up help.
- **Strut: aluminium crutch lower tube**, with a push-button pin at 3 set lengths and the crutch's rubber tip. It's rated for 300 lb users.
- **Leg frame: a post-op ROM hinged knee brace.** It gives us the thigh cuff, shin cuff, hinge and straps.
- **Seat: a wide bicycle saddle shell per side.** The rails become the strut hinge, so no printed part sits in the load path.
- **Sit-bone cushion: a two-cell air insert**, ROHO style. The cup also extends back under the thigh so soft tissue carries more of the load. Wheelchair data has air cushions holding ischial peaks at about 11 to 46 kPa, and gel and foam did worst. Today's model peak is about 86 kPa. The target is under 45 kPa for a 20 minute sit, measured with a pressure map.
- **Belt: a pack hip belt with an HDPE framesheet. Backrest: Crazy Creek straps**, unchanged.

Hybrid sit-only unit: **about $420 to $560 in parts and 3.2 to 3.8 kg.**

## Step 0: the bench rig (about $500)

This is a sandbag dummy leg with no person in it. It tests four things:

1. The gas spring holds 50 Nm and sinks under control at 1.8 kN.
2. The latex band returns about 35 J.
3. The crutch strut takes 1 kN.
4. The air insert keeps the sit-bone peak under 45 kPa.

The shopping list with prices and links is in [plan.html](https://nicedreamzapp.github.io/sitka/plan.html). Print the jigs in PETG (dummy thigh and shin, gas-spring brackets, the saddle-rail hinge block, and a sit-bone test pelvis). Reprint the knee brackets in carbon nylon once the geometry is proven.

## Printing

A Bambu P2S-class printer handles brackets, jigs, TPU pads and the dummy. Send the large shells to MJF PA12, which runs about $0.28/g at JLC3DP: roughly $26 per seat cup and $81 per thigh shell. MJF nylon is close to equally strong in every direction, which matters for anything you sit on.

## First product: Sitka Seat

The first product is passive and sit-only: two legs and a belt, with no electronics. The target is **$599 retail and $499 early bird**, on a parts cost of $150 to $200 at 100 units. Here's the path:

1. Bench rig.
2. Wearable prototype on video.
3. Kickstarter, which needs a working prototype and bans photoreal renders.

Every unit gets a 120 kg user limit, a fall warning and a proof-test record. It's sold as a non-medical consumer product, with the ASTM F48 standards as the checklist: F3358, F3795, F3474, F3517 and F3444.

The original modules (lift, walking bands, smart clutch, one motor) stay on the roadmap as upgrades.

## Next actions

1. Order and build the step-0 rig.
2. Bench the locking gas spring. If it passes, retire the sprag, arc and yoke rows.
3. Pressure-map the cup with and without the air insert.
4. Swap the leaf rows for latex in `parts_list.py`.
5. Crutch-tube struts, proofed to 1 kN.
6. Add an HDPE framesheet and fix the pelvis standoff offsets in `build_parts.py`.
7. Try the saddle shell as the cup.
8. Get MJF quotes for the shells.
9. Rewrite the starter BOM around the hybrid.
10. Film the first wearable prototype.
