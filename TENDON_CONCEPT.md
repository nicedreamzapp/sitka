# Sitka tendon concept: physics check (2026-10-22)

Wearer: **130.3 kg / 1.874 m** (NHANES 95th pct, `params.mjs`). Statics reuse `tripod()` from `seat_torque_model.mjs`
(free ankle, old exo masses, so slightly conservative). Numbers are **per leg** unless noted.
Pressures and limits are first-order estimates; anything marked EST or VERIFY is not yet sourced or measured.

## VERDICT

- **It closes, but only with the strut moved.** With the old tripod strut geometry it does not close.
- The fix: strut hinged at a **seat cup under the sit bone**, tilted back only **4°**, and the wearer leans back **10°** on the back panel.
- Knee load drops from **79 Nm** (old tripod, chair) to **34 Nm** (chair, 10° recline).
- Chosen moment arm: **80 mm**, on a grooved arc centred on the knee hinge (an "artificial kneecap").
- Tendon tension at that point: **426 N** (about 43 kg).
- Worst shell pressure: **~20 kPa** average on the pad below the kneecap (~28 kPa peak, linear model). The thigh sees **14 kPa**, the seat cup **24 kPa**.
- That sits at the low end of the **20–40 kPa** sustained band: **OK for 10–30 min, 60 min marginal** (the shin limits it).
- A pure soft exosuit (no knee hinge) **does not close**: 426 N of skin shear is over the ~200–300 N anchor range, and the bend at the knee would press **602 N** into the kneecap.
- So the minimum rigid set is: **strut, seat cup, a knee hinge carrying the arc, a clutch, a thin back panel.** Everything else is cable, webbing and contoured shells.
- Mass: about **7.0 kg** powered (old **9.2 kg**), about **3.3 kg** seat-only, and **nothing on the foot**.
- The previous `tendon_sketch.html` claimed **19 Nm** and **70%** on the strut. The model does not reproduce that. A dead-vertical strut gets near it only by eating the tipping margin (see section 2). The sketch has been replaced.

## 1. SEAT: knee tendon tension and anchor pressure

### Knee moment the tendon must hold (from `tripod()`)

| Mode | Old tripod strut (0.85 thigh, 17°) | No strut | **New: sit-bone strut, 4°**, own trunk lean | **New + 10° recline** |
|---|---|---|---|---|
| Perch (25°) | 52 Nm (no strut) | 52 Nm | 52 Nm (no strut) | n/a |
| Half-sit (60°) | 78 Nm | 145 Nm | 52 Nm | **38 Nm** |
| Chair (90°) | 79 Nm | 190 Nm | 48 Nm | **34 Nm** |
| Deep squat (120°) | 94 Nm | 168 Nm | 72 Nm (trunk 32° forward) | **39 Nm** |

- Strut share of body weight, new geometry: **46%** chair upright, **69%** chair at 10° recline (old tripod: **27–40%**).
- The ~40–60% share in the brief only happens with the new geometry. The old strut at 0.85 thigh and 17° never takes more than **40%** in the model's poses.

### Tendon tension T = M / r

| Knee moment | r = 40 mm | 60 mm | **80 mm** | 100 mm |
|---|---|---|---|---|
| 34 Nm (chair, recline) | 851 N | 567 N | **426 N** | 340 N |
| 48 Nm (chair, upright) | 1195 N | 797 N | **598 N** | 478 N |
| 52 Nm (perch) | 1312 N | 874 N | **656 N** | 525 N |
| 79 Nm (old tripod) | 1975 N | 1317 N | **988 N** | 790 N |
| 190 Nm (strut lost, chair) | 4750 N | 3167 N | **2375 N** | 1900 N |

### Why 80 mm

- At 90° the skin over the kneecap is roughly **55–65 mm** in front of the knee axis (EST). An arc over the front must be **≥ ~75 mm**.
- **40–60 mm** works only as discs at the sides of the knee. The medial disc rubs the other knee, and tension is 1.4–2x higher.
- **100 mm** cuts tension 20% but sticks out ~4 cm past the kneecap. That breaks "contour is everything".
- A cable wrapped on an arc centred on the hinge axis has a **constant moment arm** at every knee angle. The anchors can lie flat on the shells.

### Where the pull goes (key finding)

- The arc's reaction (**√2 × T = 602 N** at 90° of wrap) goes into the **hinge**, then through short arms into the shells. It does not go into the kneecap.
- The hinge arm on each shell cancels the cable's pull along the leg. **The shells see no net shear from the tendon**, only a twisting couple equal to the knee moment.
- So shell pressure depends on the **knee moment and the shell length**, not on r. The moment arm only sets cable, clutch and hinge loads.
- Shell couple: thigh = proximal back of the thigh (the seat cup, pushed up) + distal front pad above the kneecap (pushed down).
- Shin = pad just below the kneecap (patellar-tendon-bearing area, as in prosthetic sockets) + lower-calf pad behind.

### Anchor pressure (two-pad model, F = M / lever)

- Thigh: lever **0.25 m**, front pad **100 cm²**, seat-cup couple area **180 cm²**.
- Shin: lever **0.24 m**, below-kneecap pad **70 cm²**, calf pad **96 cm²**.
- Cross-check with a linear-pressure shell (0.30 m long): peak = 6M / (w L²), w = 0.13 m (thigh) or 0.08 m (shin).

| Case | M | Thigh front pad | Below-kneecap pad | Calf pad | Shin peak (linear) |
|---|---|---|---|---|---|
| **Chair, 10° recline** | 34 Nm | **14 kPa** | **20 kPa** | **15 kPa** | **28 kPa** |
| Chair, upright | 48 Nm | 19 kPa | 28 kPa | 21 kPa | 40 kPa |
| Deep squat, 32° forward | 72 Nm | 29 kPa | 43 kPa | 31 kPa | 60 kPa |
| Old tripod, chair | 79 Nm | 32 kPa | **47 kPa** | 34 kPa | **66 kPa** |
| Strut lost (catch only) | 190 Nm | 76 kPa | 113 kPa | 82 kPa | 158 kPa |

- Seat cup (strut push + thigh couple): **607 N** chair at recline, **24 kPa** over **250 cm²**. That is a 15 × 20 cm cup per side, roughly a bike-saddle half (EST comparison).
- Comfort band used: **20–40 kPa** sustained (from the brief). Pressure-time curves (Reswick & Rogers 1976, VERIFY) drop with time, so 60 min wants the low end.
- Shear lowers the tolerable pressure (Bennett 1979 reported about half, VERIFY). This is why the hinge cancelling the tendon shear matters.
- **Comfortable for 10–60 min:** the 10° recline modes (34–39 Nm), r = 80 mm, a thigh shell ≥ **0.30 m** long, and a shin shell ≥ **0.30 m** with a **≥ 70 cm²** pad below the kneecap.
- **Short sits only (≤ 10 min):** upright chair (48 Nm) and perch (52 Nm).
- **Not a resting pose:** a forward-leaning deep squat (72 Nm). Squat only with the recline.
- **Does not close:** the old tripod geometry (47 kPa on the shin) and any pure-soft version (shear 426–988 N vs ~200–300 N).

## 2. BALANCE: rear strut without rails

- The strut hinges on a **contoured seat cup under the sit bone**. Its push goes straight up into the ischium, which is the body's own sitting surface. No rail is needed.
- **Not a pelvis belt:** a belt pushed upward by 400–500 N rides up over the hip bones. Belts only work in tension.
- **Not the side of the thigh shell:** an offset push would roll the shell around the thigh.
- Strut force, chair: **316 N** upright, **472 N** at 10° recline, **500 N** at 15°.
- Grip needed at the strut foot drops from **0.30 to 0.07** (tan 4°). Wet tile and wet concrete become comfortable margins.
- Strut length: chair **0.65 m**, half-sit **0.86 m**. The half-sit length is 1 cm over the old 0.85 m tube: lengthen the top section ~3 cm.
- Buckling: the old 24/20/16 carbon tube holds **5.2 kN** at 0.65 m. That is **11x** the 472 N load.
- Splay: sit bones are ~13 cm apart and the feet stay 34 cm apart, so each strut leans out ~9°. That pushes each cup **~75 N inward**. The two cups squeeze the pelvis between them, so no crossbar is needed.

### The trade the old sketch skipped: knee load vs. tip-back room (chair, 10° recline)

| Strut tilt | Knee moment | Strut force | Room behind your weight |
|---|---|---|---|
| 0° (vertical) | 13 Nm | 529 N | **8 cm** (under the 10 cm rule) |
| 2° | 24 Nm | 499 N | 10 cm |
| **4° (chosen)** | **34 Nm** | **472 N** | **12 cm** (9° of tilt) |
| 8° | 51 Nm | 429 N | 17 cm |
| old tripod (0.85, 17°) | 81 Nm | 422 N | 20 cm |

- The knee moment and the tip-back room are the same lever. You cannot cut one without the other.
- Keep the tendon **always loaded (≥ ~30 Nm)**. Strut + thigh + shin + floor is a four-bar linkage: if the knee load goes negative, the linkage folds toward standing and the wearer has to catch it with their muscles. A dead-vertical strut at recline gets close to that.
- Recline cap: **10°**. At 15°, half-sit and squat fall to **9 cm** of room.

## 3. BACKREST: Crazy Creek straps

- The trunk wants to fall back about the hip: per side, **385 N** (half the head, arms and trunk) × 0.30 m × sin(recline).
- Hip moment: **0 Nm** at 0°, **20 Nm** at 10°, **30 Nm** at 15°.
- Strap from the panel top (0.45 m up the back) to the strut anchor at the seat cup: lever only **~43 mm**, giving **466 N at 10°** and **732 N at 15°**. **Rejected.**
- Strap to the **thigh shell 0.36 m in front of the hip** (near the knee, true Crazy Creek geometry: the femur is the seat board in compression).

| Recline | Strap tension (to thigh, 36 cm) | (to thigh, 20 cm) |
|---|---|---|
| 0° | **0 N** (posture only) | 0 N |
| 10° | **94 N** | 139 N |
| 15° | **150 N** | 221 N |

- The strap pulls between trunk and thigh, which are both above the knee. It does **not** add knee load. The recline lowers knee load because it moves your weight back over the strut.
- The strap's upward pull on the distal thigh shell partly cancels the tendon's downward front-pad load (small help, not counted).

## 4. GAIT: hub motors through Bowden into the same tendon

- AK10-9s sit on the back hub. A Bowden cable runs to the clutch on each thigh shell, and the same tendon runs over the 80 mm arc.

| Knee assist | Tendon at knee | Motor-side (η 0.68 / 0.79) | Motor torque, 25 mm spool | Copper heat |
|---|---|---|---|---|
| 15 Nm | **188 N** | 276 / 237 N | **6.9 Nm** | 1.9 W |
| 22 Nm | 275 N | 404 / 348 N | 10.1 Nm | 4.1 W |
| 30 Nm | **375 N** | 551 / 475 N | **13.8 Nm** (rated 18) | 7.6 W |

- Shell pressure in gait: thigh **8–15 kPa** and shin **13–25 kPa** peak, held only during stance. Fine.
- Without the hinge, 188–375 N would be the skin shear. That is the Harvard range only at the low end, which is one more reason to keep the hinge.
- Sheath reaction closes at the hub: the hub feels **no net force**, and only sheath friction loads the body along the route.
- Speed: hiking stance ~1–3 rad/s at the knee means 0.08–0.24 m/s of cable and ≤ 10 rad/s at the spool. That is OK (rated ~21 rad/s).
- Swing: the knee flexes at ~6–8 rad/s, which would need 20–26 rad/s at the spool, right at the motor's limit. So **let the cable go slack in swing** (as the Harvard exosuits do) and pull only in stance.
- Running: midstance would need **~600 N** at the knee and **~22 Nm** at the motor through the Bowden. That is over rated torque. **Running assist is not promised in the tendon version.**
- **One tendon can do both jobs:** hub motor → Bowden → one-way clutch → tendon → arc → shin anchor, all in series.
  - The clutch's free direction (taking up cable) is the knee-extension direction, which is the same way the motor pulls. So assist passes straight through.
  - In gait the clutch cam is **held open** (latch or solenoid), so the knee can flex.
  - In sit mode the cam bites and holds with **power off**.
  - Standing up is always free: the knee extends, and a small take-up spring on the hub side keeps the line snug without power.

## 5. What stays rigid, mass, risks

### Minimum rigid parts (lightest form)

- **Rear strut**: the existing carbon telescoping tube (0.30 kg).
- **Seat cup**: thermoformed or carbon, foam-lined, ~15 × 20 cm.
- **Knee hinge pair + 80 mm grooved arc** on a thin yoke over the kneecap. It carries **602 N** at the sit point, and must survive **~3.4 kN** if the strut is lost (2375 N × √2).
- **One-way clutch**: a needle/sprag clutch spool (e.g. ~12 mm spool radius holds 426–600 N with 5–7 Nm; HF/CSK series, VERIFY ratings) or a sailing cam cleat (VERIFY the safe working load with the chosen line).
- **Thin back panel** (also carries the hub and battery).
- Shells are **semi-rigid contoured** (thermoplastic or carbon, foam-lined, laced). They spread pressure and do not carry the column.

### Mass (EST until weighed)

| Item | Old v2 | Tendon |
|---|---|---|
| Per leg (shells, hinge + arc, clutch, tendon + backup, strut, cup, Bowden, sensors) | 3.85 kg | **~1.45 kg** |
| Waist / back (2 × AK10-9, spools, panel + straps, battery, electronics, belt) | 1.52 kg | **~4.1 kg** |
| **Total powered** | **9.21 kg** | **~7.0 kg** |
| Seat-only (no motors, battery or Bowden) | n/a | **~3.3 kg** (Noonee Chairless Chair 2.95 kg) |

- The motors move from the knee to the back, and the heel stirrups, ankle pivots and uprights are gone. Distal mass drops from **3.85 to ~1.45 kg per leg**, with **nothing on the foot**. That is the expensive kilogram in walking.

### Honest risks

- **Shell migration**: the hinge cancels tendon shear, but sitting down and standing up still drag the shells. Use lacing plus a strap from the seat cup to the thigh shell, and a silicone liner (EST). The thigh shell's front pad must not slide down onto the kneecap.
- **Cable creep**: Dyneema creeps under constant load. 0.2% (EST) on 0.5 m is **1 mm, about 0.7° of knee sag** per sit. Use Vectran or a low-creep SK99, or 7x19 stainless (arc diameter / wire = 160/2.4 = 67, fine for fatigue). Every stand-up re-takes the slack.
- **Clutch failure → drop**: the strut stays under you. A **backup strap** with its own cleat, set **≤ 3 mm slacker (2°, 1.6 cm drop at the hip)**, catches.
  - With stretchy nylon or polyester webbing the catch peak is **~2.8x static (~1.2 kN)**. A stiff Dyneema backup would be **~5x**. At a 10° slack (7.9 cm) it is **4–10x**: too much.
- **Strut slips or is stowed**: the knee jumps to **145–190 Nm**, the tendon to **1.8–2.4 kN**, and the shin to **>100 kPa**. That is a catch, not a seat.
  - Firmware rule kept from v2: with no strut foot on the ground, **only Perch may lock**.
  - Size the cable, clutch and hinge for **190 Nm × 1.5 ≈ 3.6 kN of tendon load** and proof-test them.
- **Hinge alignment**: a single-axis hinge on a rolling-gliding knee moves the arc a few mm. The tendon stays tangent, so the moment arm changes little, but shell pistoning adds to the migration risk. Bench-check it.
- **Forward lean**: leaning forward at the table moves your weight forward and **raises** knee load (34 → 48+ Nm). The app should coach the recline. Haptics can warn when the tendon load sensor passes ~500 N.
- **All tissue limits here are EST or from memory.** Measure with a pressure-mapping liner (e.g. a Tekscan-type sensor) before sits longer than 10 min.

## Files

- `tendon_sketch.html`: side view at the design point (chair, 10° recline, 4° strut).
- The statics come from `tripod()`. The variant runs were scratch scripts (strut hinge at 1.0 × thigh, foot placed at the stated tilt). They have not been added to the repo yet.
