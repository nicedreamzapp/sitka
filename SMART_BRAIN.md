# Sitka smart brain: a tiny on-board model that knows what you're doing (2026-10-30)

Builds on [KINETICS.md](KINETICS.md) (the tendon map, the Modes table, fail-open rules) and the smart tier
in the README. Anything marked EST or VERIFY is not yet measured on Sitka. **Everything below that runs
today runs on simulated sensors** made from open motion capture, not on a real wearer.

## VERDICT

- **The smart tier gets a small brain in the hub.** It reads **2 IMUs per leg** (thigh + shin), the **hub's own IMU** on the back panel, and **pressure insoles**, and calls the mode **50 times a second**.
- **The model suggests, plain code decides.** A short list of safety rules has the final say over every clutch and the motor. On any doubt, every walking clutch opens.
- **The first model is tiny:** a 1D CNN with **6,189 weights** (about **6 KB** at 8 bits), a **1 s** window, about **0.12 M multiply-adds** per call. It fits any $5-10 microcontroller with room to grow 10-50x.
- **Trained before any hardware exists:** sensors are synthesized from CMU motion capture with the same code the 3D viewer runs.
  - Held-out clips (never trained on): **85.6%** of 20 ms steps called right; walk **98%**, run **93-96%**, stoop lift **97%**.
  - Weakest spot: perching on a high seat reads as standing. Stairs and slopes have no training data yet.
- **It learns you.** The first week logs your gait, the phone or Mac retrains a personal version overnight and flashes it back, the same pattern as the personal adapters in our RealTime AI Cam.
- **Watch it live:** [sitka_viewer.html](sitka_viewer.html) shows a "Smart brain" card while Walk, Run, Sit or Lift plays: mode, confidence, each knee clutch, the motor, the seat lock, and a red VETO when a safety rule overrides.

## 1. What it does

| Job | How | When |
|---|---|---|
| Call the mode | model on a 1 s window of sensor data | every 20 ms |
| Time the stance clutch (T1b, electroadhesive) | **close at heel strike, open by 35% of the stride**, before swing | every step, WALK and DESCEND |
| Tell the one motor when to help | stairs up, hills, the lift phase, stand-up | CLIMB, LIFT, SIT stand-up |
| Turn regen on | knee braking downhill | DESCEND |
| Allow the sit cam to hold | only when seated and still | SIT |
| Report | battery, energy stored and returned, mode log | to the phone and Moonstone |

## 2. Sensors

| Sensor | Where | What it gives | Part class (EST cost) |
|---|---|---|---|
| IMU, 6-axis | thigh shell, each leg | thigh angle and swing rate | Bosch BMI270, ST LSM6DSO/LSM6DSV, TDK ICM-42688 class (**$2-6** each) |
| IMU, 6-axis | shin shell (below-kneecap pad), each leg | shin angle and rate, impact | same |
| IMU, 6-axis | the hub on the back panel | trunk bend (lift), body bounce (load) | same, often on the controller board |
| Pressure insole | each shoe, 3-4 force sensors (heel, ball, toe) | weight on each foot, heel strike | FSR (Interlink 402 class) or a home-made velostat insole (**$5-30** a pair, EST) |
| Tendon load cells | already in the S tier | spring force, a check on the clutch | KINETICS §5 |

- **Knee angle comes free:** thigh angle minus shin angle.
- **No skin electrodes.** IMU plus insoles is what the Open Source Leg and the exosuits use (KINETICS §6).

## 3. Modes, and what each clutch and the motor do

Mode names follow the KINETICS Modes table; STAND (idle) is new. Base kits keep the mechanical lever; the
smart tier sets the same states automatically.

| Mode | Trained yet? | T1b stance clutch | Sit cam (T1) | Lift tendon (T3) | Motor (P1) |
|---|---|---|---|---|---|
| **STAND** | yes | open | open | live (slack < 35°) | off |
| **WALK** | yes | **locked from heel strike to 35% of the stride**, else open | open | live | off |
| **RUN** | yes | open (all clutches open) | open | slack | off |
| **SIT** (sitting down / seated / standing up) | yes | open | **holds only when seated**, with no power | OFF | **assist on stand-up** |
| **LIFT** | yes | open | open (sit leaf on, squat lifts) | ON | **assist while the trunk rises** |
| **CLIMB** (stairs up, uphill) | not yet | motor drives the stance leg | open | live | assist in stance |
| **DESCEND** (stairs down, downhill) | not yet | damper or regen branch, same timing as WALK | open | slack | regen |

- **SIT sub-phase** comes from the thigh IMUs: flexing = sitting down, extending = standing up, still and past ~40° = seated.
- **Heel strike** = the insole rising through 20% of body weight while the thigh IMU says that leg is in front.

## 4. The safety layer (plain code, final say)

The model never touches a clutch directly. It proposes a mode; these rules turn that into clutch and motor commands.
The same rules run in the viewer (`brain/sitka_brain.js`, `RULES`).

| Rule | What it does |
|---|---|
| **Hardware first** | Walking clutches are electroadhesive: **no power = open**. Only the mechanical sit cam may hold with power off. Every walking branch keeps its **330 N breakaway limiter** (KINETICS §4). |
| **Agree before switching** | A new mode must win **6 steps in a row (120 ms)** with the model at least **60%** sure. |
| **Unsure = safe** | Model under **60%**: every walking clutch opens, the motor stops. |
| **No load, no lock** | A stance clutch never locks while that insole reads under **10%** of body weight. |
| **Swing = open** | Knee flexing faster than **3 rad/s** means swing has started: that clutch opens. |
| **A gait needs steps** | WALK or RUN is refused unless a thigh swung faster than **0.8 rad/s** in the last second. Standing still in a walking pose is STAND. |
| **Motor needs 80%** | The motor only helps when the model is at least **80%** sure. |
| **Motor needs ground** | No assist with both insoles unloaded. |
| **Lift means hips extending** | Lift assist is refused while the thighs are flexing (that is a sit-down, not a lift). |
| **Seat lock only when seated** | The cam may bite only in SIT, seated, thighs past ~40°, not moving. |
| **Voice is a hint** | "Sit mode" or "stairs" from Moonstone raises that mode's chance for a few seconds; it never skips a rule above. |

- In the viewer these fire for real: the stand-up shows "motor: model under 80%" as the model hesitates between SIT and STAND at the top of the rise.
- The mode-error drill (KINETICS §8, test 6) tests the layer on a harnessed treadmill before anyone walks outside.

## 5. The model

| | First version (in the repo) | Budget on the chip (EST) |
|---|---|---|
| **Inputs** | 15 channels at 50 Hz: per leg thigh angle, shin angle, knee angle, thigh rate, shin rate, insole load; trunk angle and rate; hub vertical acceleration | up to ~40 channels (raw gyro/accel, 4 insole cells per foot) |
| **Window** | **1.0 s** (50 steps), a new answer every 20 ms | 1-2 s |
| **Architecture** | 1D CNN: conv 16 (k5) → conv 24 (k5, stride 2) → conv 24 (k5, stride 2) → average → 5 classes | same family, or a small GRU |
| **Size** | **6,189 weights**: about **6 KB** int8, 24 KB float32 | up to **~300 KB** |
| **Compute** | about **0.12 M** multiply-adds per call, **6 M/s** at 50 Hz | under 2 ms per call |
| **Latency** | 120 ms to switch modes (the 6-step agreement); clutch timing itself is rule-based and runs every step | clutch release under 30 ms (Diller [16] in KINETICS) |

**Chip classes** (any of these runs it; plain C kernels, no vendor ML runtime needed):

| Chip | Core | Fits because (EST) |
|---|---|---|
| nRF52840 | Cortex-M4F, 64 MHz, 256 KB RAM, Bluetooth LE | ~2-4 ms per call with 8-bit kernels; BLE to the phone built in |
| ESP32-S3 | dual Xtensa LX7, 240 MHz, 512 KB RAM, Wi-Fi + BLE, vector instructions | under 1 ms per call |
| STM32 (F4 / G4 / H7 class) | Cortex-M4F / M7 | well under 2 ms |
| Teensy 4.x (already in the S tier for OpenExo) | Cortex-M7, 600 MHz | the brain can share the existing board |

- **Streaming trick:** the window slides by one step, so the first layer only needs the newest column each call (about 10x less work, EST).
- The JavaScript in `brain/sitka_brain.js` is the reference: the C port must match it number for number on replayed data.

## 6. Personalization: it learns your walk

1. **Week one, log:** the hub records IMUs and insoles (about **23 MB per hour** raw at 100 Hz, EST) whenever the wearer moves, plus every voice command and lever change as a label.
2. **Labels without effort:** confident moments from the base model, plus every correction ("sit mode" said while it called STAND).
3. **Overnight, retrain:** the phone or the Mac fine-tunes a personal copy of the model. No cloud: the same idea as RealTime AI Cam's personal adapters.
4. **Gate before flashing:** the personal model must pass the same checks as the base one (held-out day of your own data, the viewer sequences, the mode-error replays) and never be worse on any mode.
5. **Flash over Bluetooth**, keep the previous model on the chip for a one-tap rollback.

## 7. Moonstone tie-in

- **Dashboard:** battery, energy stored and given back (sit leaf ~40 J per stand-up, lift tendon ~14 J per side per lift, motor Wh used and regen Wh back), steps per mode, and how often the safety layer stepped in.
- **Voice:** "sit mode", "stairs", "lift mode", "all free" send a hint to the hub. "All free" opens every walking clutch at once.
- **Path:** hub → Bluetooth LE → phone → Moonstone. The hub never needs the phone to be safe; the phone only adds the dashboard, voice and the overnight retrain.

## 8. Bootstrap from motion capture (what runs today)

- **Source:** CMU motion capture, the same clips the viewer plays (35_01 walk, 35_17 run, 86_09 walk/sit/stand, 115_01 stoop lift) plus more trials of the same subjects fetched by `brain/fetch_mocap.sh`.
  - **Train:** 35_01, 35_02, 35_17, 35_18, 86_09, 115_01, 115_02, each at 0.85x, 1x and 1.18x speed, plus 1.5 s "still holds" of random frames.
  - **Held out:** 35_03, 35_19, 35_20, 86_10, 115_03.
- **Simulated IMUs:** thigh, shin and trunk angles and rates from the skeleton, filtered like a real IMU's output (causal low-pass at 50 Hz). Shin acceleration and hub vertical acceleration from second differences.
- **Simulated insoles:** a foot carries load when its sole is within ~1-4 cm of the floor; body weight × (1 + hub vertical acceleration / g) is split between the feet, and the seat takes up to 75% when the hips are low and the thighs flexed.
- **Labels:** offline rules that may look at the whole clip (walking speed, flight phase, hip height, trunk bend). The model only ever sees the simulated sensors.
- **One code path:** the training script calls the same `brain/sitka_brain.js` the viewer loads, so training and the live readout cannot drift.

**Results** (per 20 ms step):

| Test | Called right | Notes |
|---|---|---|
| Training clips | 99.5% | |
| **Held-out clips** | **85.6%** of 3,661 steps | 35_03 walk 98.3%, 35_19 run 95.5%, 35_20 run 92.6%, 115_03 lift 96.8%, 86_10 mixed 83.8% |
| 86_10, what went wrong | | a perch on a high seat (hips only ~15% lower, trunk forward) called STAND, 270 steps; rising off the seat straight into a jog called WALK/RUN where the labels say LIFT, 137 steps |

**Viewer sequences** (whole brain: model + safety layer; truth = the label rules on the source clip at the same moment):

| Sequence | Called | Truth | Agrees | Notes |
|---|---|---|---|---|
| Walk | WALK 100% | WALK 100% | 100% | stance clutch locked 36% of each stride per side, no vetoes |
| Run | RUN 100% | RUN 100% | 100% | all clutches open |
| Sit down | SIT 73%, LIFT 27% | SIT 100% | 73% | the first 0.64 s, trunk folding forward over still-straight legs, reads as a lift; no clutch or motor acts in that time. (Before the 10/30 leg retarget fix the start pose was a 43° crouch, which read as SIT 85%.) |
| Stand up | SIT 75%, STAND 25% | SIT 65%, STAND 31%, WALK 4% | 90% | motor assists 30% of the clip; one short motor veto (0.14 s) as the model hesitates at the top |
| Lift (stoop) | LIFT 63%, STAND 37% | LIFT 62%, STAND 38% | 90% | the 120 ms agreement delay; motor assists while the trunk rises |

**Honest limits:** the viewer plays the same source clips the model trained on (retargeted onto the Sitka wearer, so not a fair test); the held-out clips are the same three CMU subjects; the insole model is a geometric guess; nobody has worn sensors yet.

## 9. What we depend on, and how we replace it

| Outside thing | Why we use it | How we replace it |
|---|---|---|
| IMU chips (Bosch, ST, TDK) | cheap, tiny, accurate | many interchangeable makers; the firmware reads any 6-axis IMU through one small driver |
| Insole force sensors | weight per foot | home-made velostat or printed insoles; the model only needs heel / ball / toe load |
| Microcontroller (Nordic, Espressif, ST, PJRC) | runs the brain | plain C kernels we write ourselves, so any of the chip classes above works |
| CMU motion capture | data before hardware | our own logged gait from week one, then our own wearers |
| Stairs and slope data | CLIMB / DESCEND have none yet | log our own stairs and ramps on the sensor rig; open lab datasets with thigh/shank IMUs on stairs and ramps exist (Camargo et al. 2021, Georgia Tech, VERIFY licence; ENABL3S, Hu et al. 2018, VERIFY) |
| numpy and node | training and the shared sensor code | open source, run on our own machines; no cloud, no paid API |

## 10. Next: a hip camera that sees stairs before your foot does (future)

- A small camera on the hub, pointed ahead and down, can spot stairs and curbs a step or two early and pre-arm CLIMB or DESCEND. The insole and IMU rules still decide.
- Published exo work on this exists: Laschowski et al., ExoNet (a large image set of walking environments for exo terrain recognition, 2021) and StairNet (VERIFY both citations before quoting numbers).
- It must stay optional: the brain is complete without it.

## 11. Next steps: bench test plan

1. **Sensor rig, no clutches:** 2 IMUs per leg, hub IMU and 2 insoles logging at 100 Hz on a Teensy or ESP32. Walk, run, sit, stairs, ramps, lifts, with a phone video for labels. Compare the real signals to the simulated ones with the same code; retrain on the mix.
2. **Port and replay:** C version of the model and the rules on the chip; replay logged data and check every output matches the JavaScript reference; measure time per call.
3. **Clutch on the bench:** the EA clutch at 375 N (KINETICS test 5) driven by the rules from replayed walking. Check close at heel strike and release before swing, under 30 ms.
4. **Fault drills:** pull an insole cable, freeze an IMU, drop the battery. Every walking clutch must open; only the sit cam may hold.
5. **Mode-error drill:** harnessed treadmill, force a stance lock in swing (KINETICS test 6). The breakaway limiter must cap it at 15° of knee bend.
6. **Personalization dry run:** a week of logs from one wearer, overnight retrain, gate, flash, rollback.

## Files

- `brain/sitka_brain.js`: simulated sensors, the model, the safety layer (used by the viewer and by training)
- `brain/train_mode_model.py`: labels, training (numpy, fixed seed, reproducible), held-out and viewer checks
- `brain/mode_model.json` / `.js`: the trained weights; `brain/viewer_check.json`: the viewer results above
- `brain/brain_cli.mjs`: `node brain/brain_cli.mjs viewer` reruns the viewer check
- `brain/brain_hud.js`: the live card in the viewer; `brain/fetch_mocap.sh`: the extra CMU clips
- Motion capture credit: "The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." ([cad/mocap/CREDITS.md](cad/mocap/CREDITS.md))
