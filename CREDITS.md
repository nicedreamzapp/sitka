# 🙏 Credits

None of this starts from scratch. Here's whose work this is built on.

| Project | What it does here | By | License |
|---|---|---|---|
| 🦿 [OpenExo](https://theopenexo.nau.edu/) ([GitHub](https://github.com/naubiomech/OpenExo), [wiki](https://wiki.theopenexo.org)) | Electronics and firmware starting point: Teensy + AK-series motors over CAN, FSR gait sensing | Northern Arizona University (naubiomech) | CERN-OHL-P-2.0 / LGPL-3.0 |
| 🪑 [ChairlessChair-IoT](https://github.com/Madeeha-Fayyaz8621/ChairlessChair-IoT) | Open wearable-chair firmware; FSR posture detection | GitHub user Madeeha-Fayyaz8621 | MIT |
| 🦵 [eliotk/OpenExo](https://github.com/eliotk/OpenExo) | Early Arduino exo with FSR + brake | GitHub user eliotk | MIT |
| 🧊 [three.js](https://threejs.org/) | Renders the 3D viewer | three.js authors | MIT |
| 📐 [OpenSCAD](https://openscad.org/) | Parametric CAD and the PNG renders | OpenSCAD contributors | GPL-2.0 |
| 🏃 [CMU Graphics Lab Motion Capture Database](http://mocap.cs.cmu.edu/) | Real human motion for the 3D viewer's walk, run, sit, stand and lift (subjects 35, 86, 115; see [cad/mocap/CREDITS.md](cad/mocap/CREDITS.md)). "The data used in this project was obtained from mocap.cs.cmu.edu. The database was created with funding from NSF EIA-0196217." | Carnegie Mellon University | free for any use, credit requested |

Inspiration only (no license on the repos, so no files are reused; we will ask):
[srisura1010 — IMU-gait knee exo](https://github.com/srisura1010/Motor-Actuated-Knee-Exoskeleton-Using-IMU-Based-Gait-Detection) ·
[MaGabRam — QDD knee actuator](https://github.com/MaGabRam/qdd-knee-exoskeleton)

The research this design leans on hardest: Schache et al. 2011 (running knee kinetics),
Donelan et al. 2008 (knee energy harvesting), Luger et al. 2019 (Chairless Chair),
NHANES 2015–2018 and ANSUR II (body size). Full list in `RESEARCH_REPORT_2026-10-21.md`.


## Render two CAD (cad/, sitka_viewer.html)

- Reference wearer: the **MakeHuman base mesh and targets (CC0)**, generated headless through the
  MPFB Blender extension (GPL-3.0, used as a tool only; none of its code is in this repo).
- Parts: **build123d** / OpenCascade (Apache-2.0 / LGPL), trimesh (MIT).
- Viewer: **three.js r170** (MIT), bundled into `cad/viewer/sitka_viewer.bundle.js`.
- Viewer motion: real human motion capture from the **CMU Graphics Lab Motion Capture Database** (mocap.cs.cmu.edu; the database was created with funding from NSF EIA-0196217), retargeted onto the wearer in `cad/mocap/` (clips and credits: [cad/mocap/CREDITS.md](cad/mocap/CREDITS.md)).

---

If your work is listed here and you'd like the wording changed, or if something's
missing, open an issue and I'll fix it.
