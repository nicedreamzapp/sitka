# Sitka kinetics-first design: a modular full-body system (2026-10-22)

Builds on `TENDON_CONCEPT.md` (strut under each sit bone, 80 mm artificial-kneecap arc, one-way clutch,
Crazy Creek straps). Wearer **130.3 kg / 1.874 m**. Numbers are **per leg / per side** unless noted.
Gait joint work is textbook per-kg values scaled to 130 kg (**EST**, VERIFY against our own mocap).
Anything marked EST or VERIFY is not yet measured on Sitka.

## VERDICT

- **Most of the body runs on springs, clutches and cables. A motor is only worth it for climbing, stairs up and heavy lifts.**
- **Base model = zero motors:** about **4.4 kg**, about **$1,300** (Dock + Knee/Seat + Back/Lift + Hip + running band).
- **One motor, not two:** a single AK10-9 on the hub serves both legs in turn, since stance alternates. That makes about **6.7 kg** with the smart clutches (old tendon concept with 2 motors: **7.0 kg**; v2: **9.2 kg**).
- **A second motor is not worth it for lifting:** the pad under the lift tendon caps the useful hip torque at about **160 Nm**, and one motor already gets to about **154 Nm**.
- **Lift, stoop (130 kg wearer + 15 kg box, L5/S1 moment ~265 Nm EST):**
  - Passive: **60 Nm** at the hips, so the box feels about **12 kg lighter** (23% of the back moment).
  - One motor: **110 Nm rated / 154 Nm peak**, so the box feels **22 / 31 kg lighter** (42% / 58%).
  - Squat lifts add the knee sit-springs: **+28 Nm per knee**, passive.
- **Walking:** the knee absorbs net energy in level walking. **No motor at the knee for flat ground.** The useful passive gains are at the hip (bands, ~7% in published devices) and the ankle (clutch-spring, ~7%).
- **Downhill and stairs down:** the knee brakes. That runs on a passive damper (base) or **motor regen** (one-motor tier), which puts roughly **20 Wh back per 500 m descended** (EST).
- **Sitting:** a constant-force **sit leaf spring (350 N, 28 Nm)** stores **44 J per knee** on the way down and gives about **40 J back** on stand-up. The mechanical cam still holds you with the power off.
- **Smartest single upgrade:** **electroadhesive clutches** (Diller/Collins: **26 g** element, **0.6 mW**) instead of solenoid ratchets. They gate the walking springs, are light and silent, and **fail open** (power off = no assist, never a lock).
- **Padding target: ≤ 15 kPa average** on every long-hold contact (down from 20–24 kPa) by enlarging the seat cup and the pad below the kneecap. Use a silicone gel liner, a spacer-mesh cover and a graded TPU lattice.
- **Top risk:** a **mode error**, where a walking spring is engaged during swing. It would block knee bend and trip the wearer. Every walking clutch must fail open and carry a breakaway limiter.

## 0. What the research says (one line each)

| Result | Number | Source |
|---|---|---|
| Unpowered clutch-spring ankle exo (Collins, Wiggin, Sawicki, Nature 2015) | **−7.2 ± 2.6%** walking metabolic cost, ~0.4–0.5 kg, no battery | [1] |
| Exotendon for running (Simpson et al. 2019). **Correction to the brief:** this is a latex band **shoe to shoe**, length 25% of leg length, not hip to knee | **−6.4 ± 2.8%** running at 2.7 m/s | [2] |
| Unpowered hip exo, springs (2021) | **−7.2%** walking, **−6.8%** running | [4] |
| Hip-coupling spring between the two thighs (Nasiri 2018) | **−8%** running at 2.5 m/s | [5] |
| Powered hip exosuit (Harvard), tuned | **−17.4 ± 3.2%** walking (Ding 2018); portable: −9.3% walk / −4.0% run (Kim 2019) | [6] |
| Quasi-passive knee: a spring engaged only in stance (Shamaei/Dollar, Yale) | the knee acts like a spring in weight acceptance; clutch it in stance, free in swing. Metabolic benefit not clearly shown (VERIFY) | [3] |
| Knee generative braking (Donelan 2008) | ~5 W of electricity for **1/8** the metabolic cost of continuous harvesting | [7] |
| Stairs and slopes: who absorbs the energy | **knee = 61%** of absorption in stair descent, **45%** of production in ascent; ~1.6 J/kg per stair (VERIFY) | [8] |
| Passive back exosuit (Lamers/Zelik, HeroWear Apex prototype) | erector spinae activity **−14 to −16%** lifting, −23 to −43% leaning | [9] |
| Laevo (rigid passive back) | **−21 to −31%** static / pick-and-place (Bosch 2016); ~5–10% dynamic; one null result | [10] |
| Paexo Back | small-sample theses + one conference paper, mixed results | [11] |
| Active back exosuit (Harvard, LBP patients) | peak back moment **−9%**, muscle **−16%** lifting | [12] |
| Active lumbar/hip exo, 15 kg lifts | back-muscle moment **−15 to −29%**; ~40 Nm per hip devices | [13] |
| Passive trunk-knee exo (EPFL 2022): hip and knee coupled by a **double-pulley wire** to **one gas spring** | sit-to-stand and stand-to-sit, 11 users | [14] |
| Knee exo harvesting on sit-down | **9.4 J** harvested sitting, **6.8 J** returned standing (72%) | [15] |
| Electroadhesive clutch (Diller, Majidi, Collins, ICRA 2016) | **1.5 g** electrode pair holds **100 N**, < 30 ms, element **26 g**, **0.6 mW** | [16] |
| Open Source Leg (U-Michigan) | open powered knee/ankle prosthesis, **$10–30k**, Dephy actuators, belt drive 49:1 | [17] |
| Össur Rheo Knee | MR-fluid damper switches stance/swing resistance. MR torque density judged short of orthotic needs (patent note) | [18] |
| Carbon running blades (Össur Cheetah) | "up to 90–95%" energy return (**retailer claim**, not peer-reviewed); stiffness categories chosen by body weight | [19] |
| Passive shoulder exos (Paexo Shoulder, Exo4Work) | deltoid activity down in abducted postures; up to **−16%** activity, **−41%** fatigue overhead | [20] |
| Exotendons crossing several joints (van den Bogert 2003) | simulation concept for biarticular passive tendons (VERIFY) | [21] |

## 1. Where the energy goes (130 kg, EST from per-kg norms)

| Activity | Hip | Knee | Ankle | So |
|---|---|---|---|---|
| Level walk, 1.3 m/s (per stride, per leg) | **+26 J net** (positive) | **−26 J net** (absorbs) | **+26 J net**, peak ~195 Nm | Knee = brake/spring, never motor. Hip and ankle = where springs pay |
| Uphill 10%, 1.0 m/s | positive | positive | positive | Body needs **128 W** of lift: real net work, the motor's job |
| Downhill 10%, 1.2 m/s | small | absorbs ~**92 W** (both knees, ~60%) | absorbs | Damper or regen |
| Stairs up (17 cm step) | ~25% | **~98 J/step** | ~30% | Motor-worthy |
| Stairs down | small | **~132 J/step** absorbed | absorbs | Damper or regen |
| Run, 2.7 m/s | springy | springy | springy | All passive (bands) |
| Sit-down (CoM drop ~0.4 m) | absorbs | absorbs, **~510 J** total body | small | Store it in the sit spring |
| Stand-up | ext. moment | peak ~**90–117 Nm per knee** (EST) | small | Spring gives it back |
| Stoop lift + 15 kg | **~265 Nm** at L5/S1 | ~0 | small | Hip/back tendon |

## 2. The modules

Every module works **alone** in a passive base version and **docks** onto the shared Dock.
Cross-joint tendons exist **only when both modules are docked**.

### The Dock (shared hub, required)

- Back panel + hip belt + the two seat-cup frames + the Crazy Creek straps.
- **2026-10-30:** the panel hangs on **two short rigid spine links** (ball-jointed, 25 mm) to the belt instead of straps:
  they carry the lift tendon's 300 N per side (770 N at the P1 peak) panel to belt, not through the shoulders. Each seat
  cup is **laced to its thigh cuff** and tabbed to the thigh shell, and its strut hinge sits **under the sit bone**
  (TENDON_CONCEPT.md section 6).
- **Mechanical:** the belt and panel carry tendon reactions down into the seat cups and struts (sitting) or the pelvis (walking).
- **Cable couplers:** quick-release cable terminals (ball-end into keyhole, ≥ 3.6 kN) at 6 standard ports: L/R knee, L/R hip-back, L/R shoulder.
- **Power/data (optional):** one 5-pin magnetic connector per port (12 V + CAN). Passive modules leave it empty.
- **Target:** **0.7 kg, ~$150** (EST).

### M1 Knee/Seat (basic): the existing tendon concept plus a sit spring

- **Alone:** strut under the sit bone, seat cup, 80 mm arc, **mechanical cam clutch (power-off lock)**, backup strap.
- **New: sit leaf spring** in a parallel branch: a prestressed glass/carbon leaf ("bow"), near-constant **350 N** over **126 mm** of cable (0 → 90° knee at r = 80 mm).
  - **28 Nm per knee** from bending to standing; **44 J stored** per knee on sit-down; ~**40 J back** on stand-up (90% leaf, EST).
  - Set below the 426 N hold so you **sink into** the seat and the cam locks; the cam carries only the last ~76 N.
  - Preload knob **250–400 N** for wearer weight.
- **Mode lever** on the thigh manifold: WALK / SIT-LIFT / FREE.
- **Target:** **2.9 kg pair, ~$900** (EST). **Benefit:** sit anywhere (69% of weight on the struts), **−28 Nm per knee** at stand-up and in squat lifts (~25–30% of the stand-up peak).

### M2 Back/Lift (basic)

- **Alone:** two posterior **lift tendons** from the back-panel top, through a **whiffletree** (floating pulley: equal left/right share in an asymmetric lift), down over a lumbar standoff and a glute standoff (**r = 100 mm** at the hip), to a posterior thigh cuff.
- **Element:** tapered glass/carbon leaf at the panel, **3.1 N/mm**, slack until **35°** of trunk/hip flexion (walking never feels it, like the HeroWear Apex).
- **At 90° stoop:** **300 N → 30 Nm per side, 60 Nm total**, **14 J** stored per side on the way down and returned on the lift.
- **ON/OFF switch** (Apex-style): **OFF when sitting**, or it would push the trunk back against the Crazy Creek straps.
- **Target:** **0.35 kg, ~$150. Benefit: 60 Nm, the box feels ~12 kg lighter.** Expected muscle drop ~15–25% (in line with [9][10][12]).

### M3 Hip (basic)

- **Alone:** anterior **hip-flexor bands**, belt front → standoff (**r = 60 mm**) → front of the thigh shell.
- **14 N/mm**, engaged only when the hip extends past 0°: **18 Nm at 20° extension, 3 J stored** in late stance, returned to swing the leg.
- Slack in sitting and stooping (hip flexed).
- **Target:** **0.35 kg, ~$80. Benefit:** published unpowered hip exos **−7.2% walking** [4]; expect **3–7%** for ours (VERIFY).

### Running band (basic, 50 g)

- Simpson exotendon: latex tube **~0.25 m** (25% of a ~0.99 m leg), **shoe to shoe** [2]. Clips to the M4 heel clips, or to the shin-shell bottoms (shorter lever: VERIFY).
- **RUN mode only.** **~$15. Benefit: −6.4% running** (one speed tested).

### M4 Ankle (upgrade, puts mass on the foot)

- **Alone:** Collins-type clutch-spring [1]: heel clip + calf spring + **mechanical clutch** (no power), engaged at foot-flat, releases at push-off.
- **Target:** **~0.9 kg pair, ~$400** (EST). **Benefit: −7% walking** in healthy users. But foot mass costs several times more than waist mass (VERIFY %/kg). Optional.

### M5 Shoulder/Arm (upgrade)

- **Alone:** spring cassettes at the shoulder blades push the upper arms up (Paexo Shoulder style) [20].
- Arm load goes into the back panel, then the belt, then (sitting) the struts.
- **Target:** **~1.6 kg, ~$600** (EST). **Benefit:** deltoid activity **−7 to −16%**, fatigue up to −41% overhead.

### Couplings (only when two modules are docked)

| Coupling | Needs | Route | Moment arms | Element | What it does |
|---|---|---|---|---|---|
| **Hamstring band** | M1 + M3 (or M2) | posterior belt/seat cup → behind thigh → behind knee → calf pad | hip **80 mm**, knee **40 mm** | elastic, **3 N/mm** | Slack in mid-swing (−7 mm), **taut in late swing (+42 mm, 126 N)**: brakes knee extension (**5 Nm**) and returns **10 Nm hip extension** at heel strike, **2.6 J/stride**. **OFF in sit** (it would add knee-flexion load) |
| **Calf band** (gastrocnemius) | M1 + M4 | posterior thigh above knee → heel clip | knee **40 mm**, ankle **50 mm** | leaf + clutch | Stretched by knee extension + dorsiflexion in late stance, returned at push-off. Torque **15–25 Nm** (VERIFY vs [1]) |
| **Squat differential** | M1 + M2 | knee sit leaf and hip lift leaf joined by a floating pulley (EPFL idea [14]) | 80 / 100 mm | one shared leaf | One spring charges from the hip **or** the knee: stoop, squat and stand-up all use it. **v2 mass saver**, not in the base |
| **Shoulder-back** | M5 + M2 | arm-support reaction → panel → whiffletree | — | — | Carrying in front: arm springs and lift tendons share the same ground path, so the belt sees one load instead of two |
| **Running band** | two legs | shoe ↔ shoe | — | latex | Interleg spring, RUN only |

## 3. Joint × activity: passive, coupled, or motor

| | Hip | Knee | Ankle | Back |
|---|---|---|---|---|
| **Walk** | **Passive** M3 band, 18 Nm, 3 J. **Coupled:** hamstring band 10 Nm | **Quasi-passive** stance leaf (smart tier): **26 Nm at 15°**, 3.4 J, EA clutch. **No motor** | **Passive** M4 clutch-spring (optional) | Lift tendon slack (< 35°) |
| **Hike up** | Passive band | **Motor** (P1): **15–30 Nm** in stance, ~25–35 W per stance leg | M4 spring | slack |
| **Hike down** | — | **Damper** on the stance branch (base, **c ≈ 3,100 N·s/m**, ~30 Nm) or **regen** (P1, **~20 W** harvested at 10% grade) | M4 | slack |
| **Run** | **Passive** hip-coupling spring / band (−8% [5]) | **FREE** (all clutches open) | running band (−6.4%) | slack |
| **Sit-down** | lift tendon **OFF** | **sit leaf** charges **44 J**, cam locks | — | Crazy Creek straps take up |
| **Sitting** | Crazy Creek **94 N** at 10° recline | cam **426 N**, power-off lock, strut **472 N** | — | panel **2–3 kPa** |
| **Stand-up** | lift tendon can be switched ON to help hip extension | sit leaf returns **~40 J, 28 Nm**; P1 adds up to **30 Nm** | — | — |
| **Stairs up** | band | **Motor** (P1): ~**35 J/step** of the **98 J** | M4 | — |
| **Stairs down** | — | damper / regen: ~**30–40%** of the **132 J/step** | M4 | — |
| **Stoop lift** | **Passive** lift tendon **60 Nm**; P1 adds **+50 rated / +94 peak** | — | — | same tendon (it spans the lumbar spine) |
| **Squat lift** | lift tendon | **Passive** sit leaf **28 Nm/knee** (SIT-LIFT mode, cam open) | — | — |

## 4. Tendon / cable map

| # | Tendon | From → to | Crosses | Moment arm | Element / stiffness | Clutch, and when it engages |
|---|---|---|---|---|---|---|
| T1 | **Knee seat tendon** | thigh manifold → 80 mm arc → below-kneecap shin anchor | knee | **80 mm** (constant on the arc) | Vectran/SK99 line, ~stiff | **Mechanical cam** (sprag): free in extension, bites in SIT, **locks with power off**. Proof **3.6 kN** |
| T1a | Sit leaf branch | manifold → T1 | knee | 80 mm | **350 N constant**, 126 mm stroke | mode lever: SIT-LIFT |
| T1b | Stance branch | manifold → T1 | knee | 80 mm | leaf **15.6 N/mm**, 21 mm stroke, **330 N** stop; or damper c ≈ 3,100 N·s/m (DESCEND) | **Electroadhesive**: closes at heel strike (FSR + IMU), opens at mid-stance when unloaded. **Fails open** |
| T2 | Hip-flexor band | belt front → standoff → front thigh shell | hip | **60 mm** | **14 N/mm** | none (slack in flexion) |
| T3 | Lift tendon | panel top → whiffletree → lumbar + glute standoffs → posterior thigh cuff | spine + hip | **100 mm** at hip | leaf **3.1 N/mm**, slack to 35° | ON/OFF switch (OFF in SIT); P1 hub can pull it directly |
| T4 | Hamstring band | seat-cup back → behind knee → calf pad | hip + knee | **80 / 40 mm** | **3 N/mm** | OFF in SIT (mode lever) |
| T5 | Calf band | posterior thigh → heel clip | knee + ankle | **40 / 50 mm** | leaf | mechanical (Collins) or EA, stance only |
| T6 | Running band | shoe ↔ shoe | both legs | — | latex, 0.25 m | RUN only |
| T7 | Crazy Creek strap | panel top → thigh shell 36 cm ahead of hip | hip | ~210 mm | webbing, stiff | fixed length (adjustable buckle) |
| T8 | Strut | seat cup → floor | — | compression | carbon 24/20/16, buckles at **5.2 kN** | one-way telescoping lock |
| P | Bowden (P1) | hub drum → T1 manifold | — | spool 25 mm | η **0.68–0.79** | **2 dog clutches** at the hub pick L, R or both |

**Rules that keep it safe:**
- Only the **sit cam** may lock with power off. Every walking clutch (T1b, T5-EA) **fails open**.
- Every walking branch has a **breakaway limiter** (330 N stop) so a mis-timed engage costs ≤ 15° of knee bend, not a lock.
- With no strut foot on the ground, **only Perch may lock** (kept from v2).

**Modes** (mechanical lever in the base, automatic from IMU + insoles in the smart tier):

| Mode | T1 cam | T1a sit leaf | T1b stance | T2 | T3 | T4 | Motor |
|---|---|---|---|---|---|---|---|
| WALK | open | off | leaf, gated | live | live (slack < 35°) | live | off |
| CLIMB | open | off | motor through Bowden | live | live | live | assist |
| DESCEND | open | off | damper or regen | live | slack | live | regen |
| RUN | open | off | off | live | slack | off | off |
| SIT | **locked** | **on** | off | slack | **OFF** | **OFF** | off |
| LIFT | open | **on** | off | slack | **ON** | on | assist (P1) |

## 5. Do the motors shrink or disappear?

- **Base model (no motor):** sit, stand-up help, stoop/squat lift, walking bands, running band, descent damper. **Disappear.**
- **The motor only earns its weight where net positive work is needed:** stairs up, uphill, heavy lifts beyond stored energy, stand-up from very deep.
- **One AK10-9, not two:** a hub drum with **two solenoid dog clutches** pulls the **stance leg** in gait (legs alternate) or **both** in a lift (through the T3 whiffletree).
  - Rated **18 Nm** → **720 N** at a 25 mm spool → ~**500 N** after the Bowden → **40 Nm** at the knee (one leg) or **25 Nm per side** at the hip (both).
  - It also acts as a **series-elastic actuator**: the leaf springs in series give force sensing from their deflection.
- **Battery (EST):**
  - Assisting a **500 m climb**: ~**26 Wh**.
  - Descending **500 m** with regen: ~**+20 Wh** back.
  - **One 97 Wh pack** (0.52 kg, under the FAA 100 Wh line) covers ~**1,600 m** of assisted climbing without regen.

| Tier | Contents | Mass | Cost (EST) |
|---|---|---|---|
| **B: Basic passive** | Dock + M1 + M2 + M3 + running band | **~4.4 kg** | **~$1,300** |
| **S: Smart** | + EA clutches (T1b), HV driver, Teensy, 2 shank IMUs, insoles, tendon load cells, 10 Wh pack | **~4.7 kg** | **~$1,900** |
| **P1: One motor** | + 1 AK10-9, hub drum + 2 dog clutches, Bowden, 1 × 97 Wh pack | **~6.7 kg** | **~$3,000** |
| Full body | + M4 ankle + M5 shoulder + couplings | **~9.4 kg** | **~$4,100** |
| P2: Second motor | + AK10-9 + pack | +1.2 kg | +$800: **not recommended** (pad cap, see lift) |

- **Bottom-up check (2026-10-22):** these tier masses and costs are top-down targets. Counting every CAD part, prototype one comes out heavier and pricier (Basic about 6.5 kg and $2,700). See [PARTS_LIST.md](PARTS_LIST.md) for the list and the reasons.
- Saves vs the tendon concept: **−1 motor (0.96 kg, $699), −1 pack (0.52 kg)**, and the knee holds with no power.

### Lift assist: passive vs motor (the owner's priority)

- Stoop, 130 kg wearer + 15 kg box: back moment **~265 Nm** (EST; trunk 78 kg × 0.25 m + box × 0.5 m).
- "Felt kg" = assist torque / (9.81 × 0.5 m hand lever).

| Version | Hip torque (both) | Share of the back moment | Box feels lighter by |
|---|---|---|---|
| **Passive M2** | **60 Nm** | 23% | **~12 kg** |
| **+ P1, rated** | **110 Nm** | 42% | **~22 kg** |
| **+ P1, peak (2–3 s)** | **154 Nm** | 58% | **~31 kg** |
| + P2 (two motors) | capped at **~160 Nm** | 60% | ~33 kg |

- **Why the cap:** the posterior thigh cuff tolerates ~**40 kPa** briefly over **200 cm²** = **800 N = 80 Nm per side**. Skin, not motors, sets the ceiling.
- **What the motor adds beyond the springs:** it scales with the load (insoles sense the box), it **does not resist** bending to pick up nothing, and it adds net energy (passive returns only the **~28 J** stored on the way down, vs **~300 J** of lift work).
- **Squat lift:** add **2 × 28 Nm** at the knees, passive (~**25–37%** of a ~107 Nm-per-knee deep-squat moment, EST).

## 6. Advanced vs cheap: what wins (owner: "use the most advanced systems where they beat the cheap one")

| Job | Advanced option | Cheap option | Pick | Why |
|---|---|---|---|---|
| Hold the seat | EA clutch | mechanical cam/sprag | **Cam (cheap)** | Must hold **with power off**. EA lets go when power is lost |
| Gate walking springs | **Electroadhesive** (26 g, 0.6 mW, 30 ms) [16] | solenoid ratchet (35 g + pawls, 0.28 kg sector) | **EA**, ~$200/pair | Lighter, silent, fails open. Needs ~**8 electrode pairs** for 375 N at SF 2 (~12 g of electrodes) |
| Springs | **Glass/carbon tapered leaf** (prosthetic-blade tech [19]) | gas spring, latex, webbing | **Leaf** for M1/M2; latex for small bands | Gas springs drift with temperature and have friction; a tapered glass leaf stores 50 J in ~**0.1 kg** (EST) |
| Knee braking | MR damper (Rheo) [18] | fixed hydraulic damper | **Fixed damper** in B; **motor regen** in P1 | MR needs power, adds ~0.3 kg, short on torque density for orthotics; regen also harvests |
| Actuator | Open Source Leg / Dephy stack [17] | AK10-9 QDD at the hub | **AK10-9** + the **OSL software ideas** | OSL is joint-mounted ($10–30k per leg); ours sits on the back |
| Gait phase | EMG | **IMU + pressure insoles** | **IMU + insoles** | No skin electrodes; what OSL and the exosuits use |
| Pad pressure | smart-textile pressure liner | Tekscan-type map (test only) | **Tekscan for tests** | Textile liners not proven yet (VERIFY) |
| Philosophy | — | DIY dog carts / prosthetics | keep **simple, replaceable, field-fixable** | Fewest parts that can fail |

## 7. Padding (owner: "padding will be crucial")

- **Target: ≤ 15 kPa average** on long holds (Reswick–Rogers style curves allow far less time at 20–27 kPa than at ~13 kPa, VERIFY).
- **Honest:** even 15 kPa (≈ 110 mmHg) is well above wheelchair-cushion targets and capillary pressure (~32 mmHg ≈ 4.3 kPa, Landis 1930, VERIFY). 60 min needs **shifting every 15–20 min** (lean, stand, recline).
- **Stack, skin outward:**
  1. **Liner:** 3 mm **silicone gel liner** with a fabric face (prosthetic-socket tech) on shear-loaded pads; **3D spacer mesh (3–4 mm)** elsewhere for airflow. Washable, swappable covers.
  2. **Comfort layer:** 6–10 mm **viscoelastic (memory) foam, perforated**, only on small pads (it traps heat).
  3. **Load layer:** 10–15 mm **3D-printed TPU lattice** (gyroid), **graded** 85A soft at the skin to 95A firm at the shell. Open cells breathe; tuned to sit at **30–50% strain** at working pressure, never bottoming out.
  4. **Shell:** thermoformed or carbon, contoured from a 3D scan.
  - Cheap fallback: 8–10 mm closed-cell **EVA** + spacer mesh.

| Contact | Load | Old area → new | Pressure old → **new** | Stack |
|---|---|---|---|---|
| **Seat cup** (sit bone) | 614 N | 250 → **400 cm²** of curved surface, but only **242 cm²** seated footprint (CAD, 2026-10-30) | 24 → **25 kPa** average, ~86 kPa even-tissue peak under the sit bone (EST) | silicone + 15 mm lattice + **air-cell insert under the sit bone** (needed, not optional: TENDON_CONCEPT.md section 6) |
| **Below-kneecap pad** (PTB) | 140 N | 70 → **100 cm²** | 20 → **14 kPa** | silicone + 12 mm lattice |
| Calf pad | 144 N | 96 → **120 cm²** | 15 → **12 kPa** | spacer + 10 mm lattice |
| Thigh front pad | 140 N | 100 → **120 cm²** | 14 → **12 kPa** | spacer + 10 mm lattice |
| Back panel | ~134 N + straps | **600 cm²** | **2–3 kPa** | spacer mesh + 6 mm foam |
| Shoulder harness (lift peak) | 2 × 300 N | **175 cm²** each (7 cm wide) | **17 kPa** (seconds) | spacer + 8 mm lattice |
| Posterior thigh cuff (lift) | 300–800 N | **200 cm²** | **15–40 kPa** (seconds) | silicone + 12 mm lattice |
| Hip belt | band reactions | **300 cm²** | < 10 kPa | spacer + 8 mm EVA |
| Arm cuffs (M5) | ~40 N | 60 cm² | ~7 kPa | spacer + 6 mm foam |

- Mass of the padding upgrade: ~**+0.15 kg** total (included in the tiers).

## 8. Honest limits and what needs a prototype

- **Gait energies are scaled textbook values**, not our wearer. Mocap one 130 kg walker first.
- **Published savings do not add up.** Hip −7% + ankle −7% + running band −6% were each measured alone on lighter people. Expect less combined, and the base mass (4.4 kg) costs some of it back.
- **EA clutches at 375 N, next to skin, in sweat:** untested at this load. HV insulation, humidity and fatigue need a bench test.
- **Mode errors = trip risk.** Test the breakaway limiter and the fail-open logic before any outdoor walking.
- **Sit leaf at 350 N constant-force:** prove the curve shape and fatigue (**10⁵ cycles**) on the bench.
- **Lift tendon cap** comes from a skin-pressure guess (40 kPa transient). Pressure-map it.
- **Hamstring band** could fight the knee seat tendon if left ON while sitting. The mode lever must interlock.
- **Regen numbers** (20 Wh per 500 m) assume ~50% round trip through the Bowden. Measure the Bowden efficiency.
- **Prosthetics are not exos:** sockets load a residual limb, while our shells load an intact leg with skin that slides.

**Prototype tests, in build order:**
1. Seat-cup and PTB-pad **pressure map** at 400 / 100 cm², 60 min sit, with shifts.
2. **Sit leaf** bench: force curve, energy return, 10⁵ cycles.
3. **M2 lift tendon** on 5 people: stoop/squat with 15 kg, EMG optional, felt-kg rating, pad map.
4. **M3 hip bands** + running band: treadmill, metabolic cart if available.
5. **EA clutch** on the bench at 375 N, wet and dry.
6. **Mode-error drill:** force a stance engage in swing on a harnessed treadmill.
7. **P1 hub:** dog-clutch switching at 1 Hz, Bowden η, regen on a 10% treadmill decline.

## Sources

1. Collins, Wiggin, Sawicki, Nature 2015: [PMC4481882](https://pmc.ncbi.nlm.nih.gov/articles/PMC4481882), [NCSU release](https://news.ncsu.edu/2015/04/device-helps-walking-efficiency)
2. Simpson et al. 2019, exotendon: [bioRxiv preprint](https://www.biorxiv.org/content/10.1101/474650v2.full.pdf), [PMC8404320](https://pmc.ncbi.nlm.nih.gov/articles/PMC8404320)
3. Shamaei & Dollar, quasi-passive knee: [TBME 2014](https://www.eng.yale.edu/grablab/pubs/Shamaei_TBME2014.pdf), [ICRA 2015](https://www.eng.yale.edu/grablab/pubs/Shamaei_ICRA2015.pdf)
4. Unpowered hip exoskeleton, walking and running, 2021: [PMC8182901](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC8182901/)
5. Nasiri et al. 2018, hip-coupling spring for running: [RehabPub summary](https://rehabpub.com/industry-news/research/metabolic-rate-reducing-exoskeleton-developed-lab/)
6. Harvard hip exosuit: [Ding 2018](https://biodesign.seas.harvard.edu/publications/human-loop-multi-dimensional-bayesian-optimization-hip-extension), [Kim 2019 summary](https://spectrum.ieee.org/soft-exosuit-makes-walking-and-running-easier-than-ever)
7. Donelan 2008 knee harvester: [Technology Review](https://www.technologyreview.com/s/409508/knee-power); harvesting cost: [PMC4454656](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4454656/)
8. Stairs and slopes joint work: [PMC10653464](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10653464/), [ENSAM 2023 (VERIFY)](https://sam.ensam.eu/handle/10985/26424)
9. Back exosuit (Lamers/Zelik/HeroWear): [PMC8453127](https://pmc.ncbi.nlm.nih.gov/articles/PMC8453127), [Vanderbilt 2024](https://engineering.vanderbilt.edu/2024/12/17/peer-reviewed-study-validates-performance-enhancement-and-injury-risk-reduction-from-back-assist-exosuits/)
10. Laevo: [NIOSH caregiver study](https://stacks.cdc.gov/view/cdc/208709/cdc_208709_DS1.pdf), [TU Delft null result](https://repository.tudelft.nl/file/File_0c75122f-8993-407a-bc94-d35db847bf4a)
11. Paexo Back: [Scoccia 2024](https://iris.univpm.it/handle/11566/341312)
12. Harvard active back exosuit: [biodesign pdf (VERIFY)](https://biodesign.seas.harvard.edu/resource/pdf-288)
13. Active lumbar/hip exos: [PMC11729479](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11729479/), [IEEE 2018, ~40 Nm per hip](https://ieeexplore.ieee.org/document/8360955)
14. EPFL trunk-knee passive exo, double pulley + gas spring: [arXiv 2201.03374](https://arxiv.org/abs/2201.03374v1)
15. Sit-stand energy harvesting: [Frontiers 2025](https://www.frontiersin.org/journals/robotics-and-ai/articles/10.3389/frobt.2025.1597271/epub), [JSI-KneExo](https://arxiv.org/pdf/2306.16000)
16. Diller, Majidi, Collins, electroadhesive clutch, ICRA 2016: [pdf](https://www.andrew.cmu.edu/user/shc17/Diller_2016_ICRA.pdf)
17. Open Source Leg: [U-Michigan](https://neurobionics.robotics.umich.edu/research/wearable-robotics/open-source-leg/), [cost](https://engaged.umich.edu/news/open-source-bionic-leg-first-of-its-kind-platform-aims-to-rapidly-advance-prosthetics/)
18. Össur Rheo Knee MR: [O&P News](https://progress.oandp.com/ShowcaseProducts/NEWS_2016-05-01_15/NEWS_2016-05-01_15); orthotic torque-density note: [patent 9730824 (VERIFY)](https://patents.justia.com/patent/9730824)
19. Cheetah blades: [retailer listing (claim)](https://www.cascade-usa.com/Cheetah-Xcel/CXL0021), [stiffness study](https://www.frontiersin.org/journals/rehabilitation-sciences/articles/10.3389/fresc.2024.1290092/full)
20. Shoulder exos: [Paexo Shoulder 2025](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12441637/), [Exo4Work (VERIFY)](https://researchportal.be/en/node/9534562)
21. van den Bogert 2003, "Exotendons for assistance of human locomotion", Biomed Eng Online 2:17 (from memory, VERIFY)
- Reswick & Rogers 1976; Landis 1930; Browning 2007 load-on-feet cost: from memory, VERIFY.

## Files

- `kinetics_sketch.html`: full-body side views, walking and sitting, with the basic modules highlighted.
