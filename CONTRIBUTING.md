# Contributing to Sitka

Thank you for helping build an open exoskeleton. This project belongs to everyone who improves it.

## Ground rules
1. **Safety first, always.** No change may encourage anyone to sit in or run in the exo before the seat lock is proof-loaded on a stand and the README's safety ladder is passed. Test data and safety analysis are as welcome as design changes.
2. **Keep it open.** By contributing you agree your work is licensed under the project licenses (CERN-OHL-S-2.0 for hardware/CAD, GPL-3.0-or-later for code, CC-BY-SA-4.0 for docs). Nothing here becomes proprietary.
3. **Show your math.** Torque, mass, energy and cost claims should cite a source or a calculation. Put new inputs in `params.mjs` tagged `[SRC n]`, `[CALC]` or `[EST]`, and the source in the research report. Vendor spec sheets are a starting point, not proof; real numbers come off a test stand.
4. **No weapons work.** This is a peaceful freedom-of-movement project. Contributions to weaponize it will be declined.

## Where help is most valuable right now
- **The mass war:** 2.91 kg per leg against ~0.68 kg for a Dnsys Z1. Lighter uprights, a lighter heel stirrup, a lighter lock.
- **The seat lock:** contact-stress and tooth-bending analysis, then a proof-load and cycle rig (M1).
- **Controllers:** gait-phase assist and the standstill detector, ported from NAU OpenExo.
- **Measurements:** knee moment while hiking downhill, running cadence and contact time, real regen efficiency of an AK10-9 at hiking speed.

## How to propose a change
- Edit the parametric `run_sit_exo.scad` (not the renders) and run `bash render_all.sh`.
- Change parts and prices only in `parts_list.py`, then run `python3 parts_list.py` (it rewrites `PARTS_LIST.md` and `parts.csv`). The retired v2 list lives in `legacy/`.
- Describe *why* in plain language, with the numbers that back it.
- Small, well-explained changes are easier to accept than large opaque ones.
