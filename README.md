# Run + Sit Exo: Open Powered Knee Exoskeleton with a Seat Built In
*Motorized knees that help you walk, hike and run, then lock at the angle you pick so you can sit anywhere. Designed in America, given away to everyone.*

![Run + Sit Exo P1, chair mode](renders/mode_chair_quarter.png)

### ▶ [Open the live 3D viewer](https://nicedreamzapp.github.io/run-sit-exo/run_sit_exo_viewer.html) · [watch it assemble](https://nicedreamzapp.github.io/run-sit-exo/run_sit_exo_viewer.html?anim=assembly) · [watch it walk, hike, run and sit](https://nicedreamzapp.github.io/run-sit-exo/run_sit_exo_viewer.html?anim=body)
*Runs in any browser, no install. Click any part for its price, mass and why it's there.*

> **Mission:** This project is about freedom of movement. Go farther on your own legs, and rest wherever you are: on a trail with no bench, at a shop bench all day, in a line that never ends. The machine works for the person wearing it, quietly, and never against anyone. We build it to give people more say in how far they can go and when they can stop.

| | |
|---|---|
| ![front](renders/stand_front.png) | ![back](renders/stand_back.png) |

## What this is
A fully open-source design for a **powered lower-limb exoskeleton** that does two jobs no single product does today:

1. **Assist.** A quasi-direct-drive robot-joint motor at each knee adds torque while you walk, climb, run and come back down.
2. **Seat.** Stop, tap once, and the motors bend your knees to one of four angles. A steel pawl drops into a toothed ring at each knee, pads fold down under your thighs, and your weight goes through the frame into your heels.

**As of October 2026 no product combines powered running or hiking assist with a lockable seat.** Hypershell, Dnsys, Ascentiz and Arc'teryx MO/GO assist but cannot seat you. Noonee's Chairless Chair and Archelis seat you but have no motor. See `RESEARCH_REPORT_2026-10-21.md`.

Everything is open: the CAD, the 3D viewer, the physics, the parts list with prices, and the research behind every decision. Where someone already gave their work away (NAU's OpenExo above all), we build on it and give ours away too.

**Every number below is one we can defend, including the ones that hurt.** Each input is tagged in `params.mjs` as sourced, computed, or our estimate.

## The four seat angles
Torque is what each knee's lock must carry for a **130 kg, 1.87 m man** (US 95th percentile for both, NHANES), with the seat balanced over the heel. `node seat_torque_model.mjs`

| | **Perch** | **Half-sit** | **Chair** | **Deep squat** |
|---|---|---|---|---|
| Knee angle | 25° | 60° | 90° | 120° |
| | ![](renders/mode_perch_side.png) | ![](renders/mode_halfsit_side.png) | ![](renders/mode_chair_side.png) | ![](renders/mode_squat_side.png) |
| Seat height (hip) | 0.98 m | 0.87 m | 0.72 m | 0.50 m |
| Hold per knee, balanced | 44 Nm | 102 Nm | **142 Nm** | 168 Nm |
| Lock design load | 214 Nm | 439 Nm | **507 Nm** | 507 Nm |
| Use | long lines | bar stool | full seat | work near the ground |

"Lock design load" is the worst lean, all weight on **one** leg, times a 1.5 safety factor.

| Running stride | Exo only | Exploded |
|---|---|---|
| ![run](renders/mode_run_quarter.png) | ![exo only](renders/exo_only_quarter.png) | ![exploded](renders/exploded_quarter.png) |

## Current design (prototype one, P1)
- **Knee actuators:** CubeMars **AK10-9 V2.0** at each knee: 9:1 quasi-direct drive, 18 Nm rated, 48 Nm peak, 0.8 Nm backdrive, CAN, $698.90. It keeps up with a running knee (rated 205 rpm = 21.5 rad/s at 24 V, more than twice the ~8.7 rad/s a running knee reaches in swing), and it adds only ~2% to the inertia your shank already swings.
- **Seat lock:** a **17-4PH toothed ring and a pawl** on a bistable latching solenoid. With power off it stays locked or stays free, whichever it was. A hall sensor confirms the pawl is seated before the motor lets go. The motor never holds the seat.
- **Why not a stronger motor?** A 64:1 AK80-64 has 120 Nm peak, which is still short of the 142 Nm chair hold, and at 23 rpm it runs at 28% of running swing speed, so it would fight a runner. A motor holding even 48 Nm burns about 92 W per knee as heat. The pawl holds 507 Nm for 0 W.
- **Frame:** 7075-T6 lateral uprights, 8 × 28 mm, sized for the 507 Nm design moment. A single 25 mm carbon tube would see ~826 MPa there. Cuffs, straps and the medial hinge come from a donor hinged knee brace. **Heel stirrups** carry the seat load into the ground under your heels, the Chairless Chair load path.
- **Brain:** Teensy 4.1 + CAN, the same MCU family and motor bus as NAU's OpenExo, so their firmware is our starting point. BNO085 IMUs at the pelvis and both shanks. Four FSRs per foot. An ESP32-S3 links to the phone.
- **Power:** two quick-swap **6S1P Molicel P45B packs, 97 Wh each** (194 Wh total). Each is under the FAA's 100 Wh carry-on line, so it flies with you.
- **Features:**
  - **Seat offer:** it detects that you've stopped, buzzes your thighs, and one tap sits you down.
  - **Downhill braking:** the motors brake your knees on descents and stairs.
  - **Fall catch:** on a stumble, both knees go to peak torque and heavy damping.
  - **Place memory:** it suggests the angle you picked last time at this spot.

### Seat lock safety rule
The pawl may drop **only** when all of these are true: both feet loaded on the FSRs, shank IMUs quiet for about a second, knee velocity near zero, and the motor already holding the target angle. It is never dropped at a walk or a run. Throwing a pawl into a moving ring is how teeth break and knees get hurt.

## Honest status: what does not close yet
- **Mass is the live risk.** P1 is **2.91 kg per leg and 7.2 kg worn**. That is about four times the Dnsys Z1's ~0.68 kg per leg and more than double a Chairless Chair. Weighting by where it rides (foot mass costs >4× waist mass), it is a 9.3 kg waist-equivalent load. Donelan's 1.6 kg knee harvester raised walking cost 19% just by being worn. **The assist has to beat its own mass before this helps anyone at all, and nothing here proves it does yet.** The heel stirrups are the most expensive kilograms; cut those first. `node mass_budget.mjs`
- **Running assist is real but modest.** 48 Nm peak is ~18% of a median runner's midstance knee moment and ~12% for a 130 kg runner. No knee exo we found has shown a metabolic saving in running. MIT's clutch-spring knee exo did not.
- **Runtime depends on a strategy we haven't tested.** Conservative running is **~2.8 h (~36 km) at 58 W**. Push-only assist is ~4 h. Hiking uphill at 25 Nm assist is **~4.2 h**. A day hike (3 h up, 2 h down, four seat breaks) uses 81% of the packs. Sitting costs 5 W, so a pack lasts ~33 h seated. On paper, braking assist while running could stretch runtime to 17 h. We do not claim that until a bench shows it, because the regen efficiency is a guess. `node energy_model.mjs`
- **Regen is a few watts, not a charger.** The best net downhill regen is **~3.7 W** (at 12.5 Nm braking). An hour of descent banks about 2% of the battery. A low-ratio motor is a poor generator at hiking speed because copper loss eats the harvest. Donelan's 4.8 W came from a purpose-built high-ratio generator. Downhill mode earns its place by taking load off your quads.
- **Fall catch buys time; it does not catch you.** A hard single-leg catch is ~270–410 Nm of knee moment. Two motors at 48 Nm give 12–18% of that.
- **The lock is only checked for shear.** At 14.5 kN tooth force it needs only ~18 mm² of 17-4PH in shear. Contact stress and tooth bending are **not** checked, so plan on 3× until they are. The frame (uprights, stirrups, cuff interfaces) is the harder structural problem.
- **Inputs flagged EST in `params.mjs`:**
  - pad position (65% of thigh length)
  - running cadence and contact time
  - drive efficiencies
  - idle draw
  - level-walking knee moment
  - 39% of the parts cost (mostly machining and the custom lock)

  The bench replaces all of these.

## What it costs, honestly
The parts list is not the project. Both numbers matter. `node project_cost.mjs`

| | |
|---|---|
| **P1, one exo, parts only** | **$3,759** (`bom.mjs`; $1,478 of it is estimate, not quote) |
| P1 worn and tested, all in | **~$6,400** |

The gap is what a parts list quietly omits:
- a knee test stand with a load cell
- a bench supply
- a spare actuator (one will get cooked in tuning)
- a spare lock set
- an overhead safety harness for the first sit tests
- shipping and tax
- a $500 breakage allowance

Labour is $0; it assumes you build it yourself.

### You do not build the whole exo first
| | | |
|---|---|---|
| **M1** | one knee + lock on a dummy-leg stand | **~$1,613** |
| **M2** | one leg, worn: walking and stairs, no seat | ~$853 |
| **M3** | both legs + belt: running and hiking assist | ~$1,880 |
| **M4** | seat modes, under an overhead harness first | ~$500 |

**M1 answers the two questions that decide the project** before anything is strapped to a person: does the pawl drop in cleanly at every angle under load, and does the motor stay cool through a simulated hour of hiking?

## Safety comes before anyone wears it
**No person sits in it until the lock has held its design load on the bench, thousands of times.** The ladder is not optional:
1. **M0:** close the mass and torque budgets on paper (this repo).
2. **M1:** one knee on a stand. Proof-load the pawl to 507 Nm at every detent; cycle it 10,000×. Thermal test the motor. **Vendor numbers die on the stand.**
3. **M2:** one leg worn, walking and stairs only, with motor torque capped low. E-stop in reach.
4. **M3:** both legs: hiking, then running, on a treadmill with a fall harness.
5. **M4:** seat modes under an overhead harness, then free.

Hard rules in firmware and hardware:
- The pawl locks only at a confirmed standstill.
- The E-stop cuts motor power, but the latching pawls keep their state.
- Motor torque is software-limited per stage.
- Nothing ships with a seat mode until M4 passes.

This is experimental assistive hardware, not a medical device. Anyone with a knee condition should talk to a clinician before wearing anything like it.

## Built on (and credited)
- **[NAU OpenExo](https://theopenexo.nau.edu/)** ([naubiomech/OpenExo](https://github.com/naubiomech/OpenExo), CERN-OHL-P-2.0 hardware / LGPL-3.0 software). Our electronics and firmware starting point: Teensy plus AK-series motors over CAN.
- **[Madeeha-Fayyaz8621/ChairlessChair-IoT](https://github.com/Madeeha-Fayyaz8621/ChairlessChair-IoT)** (MIT). Open wearable-chair firmware with FSR posture detection.
- **[eliotk/OpenExo](https://github.com/eliotk/OpenExo)** (MIT). An early Arduino exo with an FSR and a brake.
- **Inspiration only** (no licence, so we cannot reuse their files):
  - [srisura1010's IMU-gait knee exo](https://github.com/srisura1010/Motor-Actuated-Knee-Exoskeleton-Using-IMU-Based-Gait-Detection)
  - [MaGabRam's QDD knee actuator](https://github.com/MaGabRam/qdd-knee-exoskeleton)
- **Noonee Chairless Chair** and **Archelis** proved a wearable seat works. **Hypershell** and **Dnsys** proved people will wear powered legs on a trail. See `CREDITS.md`.

## Repository map
| File | What it is |
|------|-----------|
| `index.html` | Redirects the GitHub Pages site to the viewer |
| `run_sit_exo_viewer.html` | **The live CAD** ([open it](https://nicedreamzapp.github.io/run-sit-exo/run_sit_exo_viewer.html)). Orbit, switch modes, explode, click any part for price and spec. **▶ Assembly** builds it in 7 steps; **▶ On body** walks, hikes, runs, stops, offers a seat, sits in all four angles and stands up, with motor, lock, pad and foot-sensor state live |
| `run_sit_exo_assembly.html` / `run_sit_exo_onbody.html` | Open the viewer straight into either animation |
| `run_sit_exo.scad` | Parametric OpenSCAD model; `mode` = stand / perch / halfsit / chair / squat / run |
| `render_all.sh` → `renders/*.png` | Renders every view and mode with the OpenSCAD CLI |
| `params.mjs` | Every input, each tagged `[SRC n]`, `[CALC]` or `[EST]` |
| `seat_torque_model.mjs` | Seat torque per angle, lock sizing, upright sizing |
| `gait_assist_model.mjs` | Assist share per activity, speed check, inertia, fall catch |
| `energy_model.mjs` | Runtime for walk, hike, run and sit; regen; a day-hike budget |
| `mass_budget.mjs` | Mass per leg and belt, and its metabolic weighting |
| `bom.mjs` → `PARTS_LIST_BOM.md` | Bill of materials with prices, links and sources (one source of truth) |
| `project_cost.mjs` | All-in cost and the M1–M4 money ladder |
| `run_all.mjs` → `MODEL_OUTPUT.txt` | Every model's output in one file |
| `concept.html` | One-page concept sketch, drawn from the same geometry |
| `RESEARCH_REPORT_2026-10-21.md` | Sources, prior art, licences, what we could not find |

**Run the numbers:** `node run_all.mjs` (Node 18+, no dependencies).
**View the CAD:** [live viewer](https://nicedreamzapp.github.io/run-sit-exo/run_sit_exo_viewer.html), or open `run_sit_exo_viewer.html` locally in any browser; no install, no account. Options: `?anim=assembly|body` · `?mode=chair` · `?view=side` · `?labels=1` · `?shot=1` (download a PNG).
**Re-render:** `bash render_all.sh` (OpenSCAD 2021.01+).

## How to contribute
Anyone may use, study, modify and share this design. Improvements that keep it open are welcome, especially:
- **Mass:** lighter uprights, a lighter stirrup, a lighter lock.
- **The lock:** contact and bending analysis, then a test rig.
- **Controllers:** gait-phase control ported from OpenExo.
- **Real data:** metabolic test data of any kind.

**Test data is as valuable as design changes.** No weapons work. See `CONTRIBUTING.md`.

## License
Open hardware and open source, chosen so it can **never be locked up**:
- **Hardware / CAD:** [CERN-OHL-S-2.0](https://ohwr.org/cern_ohl_s_v2.txt) (strongly reciprocal; derivatives stay open)
- **Software:** [GPL-3.0](https://www.gnu.org/licenses/gpl-3.0.txt)
- **Documentation / research:** [CC-BY-SA-4.0](https://creativecommons.org/licenses/by-sa/4.0/)

You are free to build one. You are not free to take it private.
