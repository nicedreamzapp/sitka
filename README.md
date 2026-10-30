# Sitka: an open-source exoskeleton that works with your body


**▶ A new 90-second video is being remade with the corrected parts-list numbers.** · **[Open the animated 3D CAD](https://nicedreamzapp.github.io/sitka/sitka_viewer.html)** (any browser or phone, no install; starts with a 6-step guided tour)

Most exoskeletons fight your body with motors and metal. Sitka works with it. Your bones already carry the weight; Sitka adds what your muscles do, using springs, clutches and cables that work like tendons. A motor shows up only where your body truly needs extra energy.

Named after the Sitka spruce: strong, light, and it bends without breaking.

## What it does

| | How | Numbers (design targets, not yet measured on a prototype) |
|---|---|---|
| **Sit anywhere** | A light carbon pole under each hip carries most of your weight. A carbon sit spring at each knee catches you and gives the energy back when you stand. A mechanical clutch holds you with the power off. | Pole carries **70%** of seated weight; spring stores **44 J** per knee and returns about **40 J** |
| **Lean back** | Two straps hold you, like a camp chair you wear. | About **94 N** per strap at 10° recline |
| **Lift** | A passive tendon along your back stores energy as you bend. | A **15 kg** box feels about **12 kg** lighter, with no motor |
| **Walk and run** | Elastic bands link hips, knees and ankles the way your hamstrings and calves do. | Published passive devices: **−6 to −8%** effort |
| **Smart tier** | Electroadhesive clutches (26 g, fail open) switch the springs on at the right moment. | About **+0.45 kg** with sensors and battery |
| **Power tier** | One small motor on the back, through cables, only for stairs, hills and heavy lifts. | Box feels **22 to 31 kg** lighter |

## Fully modular

Every module works alone and gets smarter when combined. Cross-joint "tendons" (hamstring, calf and lift bands) appear only when the two modules they link are docked. Everything docks into one hub.

**[PARTS_LIST.md](PARTS_LIST.md)** has every part (print, metal or buy), with mass, price, supplier links, print time and the build story; the same rows are in [parts.csv](parts.csv).

| Kit | Mass | Parts cost, prototype one | Per set, batch of 10 (EST) |
|---|---|---|---|
| **Start here: Seat + Back** (Dock, knee seat, back lift), no motors | 6.7 kg | $2,850 | $2,071 |
| + hips and running band | 6.9 kg | $2,909 | $2,131 |
| + smart clutches | 7.3 kg | $3,476 | $2,697 |
| + one motor | 9.3 kg | $4,750 | $3,906 |
| Full body (+ ankles, shoulders, couplings) | 10.6 kg | $5,227 | $4,283 |

These are counted part by part from the CAD, and much of the cost is still estimate (one-off machining). The earlier "about $1,300 and 4.4 kg" was a top-down target for the hips-included kit; PARTS_LIST.md explains the gap and the path back toward about 4.8 kg.

## The science

- **[KINETICS.md](KINETICS.md):** the full-body modular plan, where the energy goes in every activity, what's passive vs powered, the sources (Collins 2015, Simpson 2019 exotendons, Harvard soft exosuits, Lamers/Zelik back exosuit, Diller/Collins electroadhesive clutches, the Open Source Leg)
- **[TENDON_CONCEPT.md](TENDON_CONCEPT.md):** the seat physics: tendon tension, pad pressures, why the pole sits under the hip
- **[kinetics_sketch.html](kinetics_sketch.html)** and **[tendon_sketch.html](tendon_sketch.html):** side-view force diagrams
- **[BUILD_RIGHT_FIRST_TIME.md](BUILD_RIGHT_FIRST_TIME.md):** the measurement and test gates every part passes before it's made
- **[SMART_BRAIN.md](SMART_BRAIN.md):** the smart tier's tiny on-board model (IMUs + insoles call the mode 50 times a second, plain safety rules have the final say), trained on simulated sensors from motion capture; the viewer shows its live mode readout while Walk, Run, Sit or Lift plays

## The CAD

- **[sitka_viewer.html](sitka_viewer.html):** animated 3D viewer built for phones and desktop: a 6-step guided tour, one-tap Walk / Sit / Lift, plain-English part names, labels on demand, plus an Advanced menu with every pose, module toggle and the explode view
- `cad/`: build123d source, STEP per part (in the release download), STL for printed parts (`cad/stl/`), GLB per pose (`cad/glb/`), renders (`cad/renders/`). The full standing assembly STEP (270 MB) is attached to the [latest release](https://github.com/nicedreamzapp/sitka/releases) as a .gz.
- The wearer is a CC0 MakeHuman/MPFB body.
- Every build (`cad/build_all.sh`) runs two gates on every baked frame and every static pose: the anatomy gate (the motion stands like a human) and the connection gate (`cad/assemble/connection_gate.py`: every part touches the part it hangs on, every cable ends on its anchor, nothing sinks into the wearer, the struts plant on the floor and stow in their clips).

## Status, honestly

This is a design, not a product. Every number above is computed from the open math or taken from published research, and it still needs bench tests and a prototype. Known gaps: the walking-spring timing (a spring engaged mid-swing could trip you, so every walking clutch must fail open), long-sit comfort beyond 30 minutes, seat pressure under the sit bone (25 kPa average on the cup, and a peak an air-cell insert still has to bring down on a pressure map, see TENDON_CONCEPT.md section 6), and a few CAD limits (the skinned body mesh folds through itself in a deep stoop, placeholder shoes). The older parts list (`legacy/PARTS_LIST_BOM.md`) and the model output (`MODEL_OUTPUT.txt`, `*.mjs`) describe the earlier rigid design and are kept as the physics baseline the new one was checked against.

## How the video was made

[docs/VIDEO_PRODUCTION.md](docs/VIDEO_PRODUCTION.md): every shot rendered from the real CAD in Blender, diagrams in Manim, narration timed to the word, original instrumental music.

## License and credits

Open hardware and open source; see [LICENSE](LICENSE) and [CREDITS.md](CREDITS.md). Come build one with us.

The viewer's walk, run, sit, stand and lift are real motion capture: "The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." Details in [cad/mocap/CREDITS.md](cad/mocap/CREDITS.md).
