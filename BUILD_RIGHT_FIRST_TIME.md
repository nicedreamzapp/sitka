# Build it right the first time

Our last hardware project, a heat-and-clean oven made with a factory overseas, cost us rounds of reprints because the measurements were wrong before anything was cut. Sitka is set up so those same mistakes can't happen again. This page lists what went wrong there, the rule that stops it here, and why Sitka is ready to build.

## What went wrong last time, and the rule that prevents it

| Last time | The Sitka rule |
|---|---|
| The factory sent screenshots, and nobody can measure a screenshot. | **Nothing is measured from a picture.** Every bought part's dimensions come from the maker's dimensioned drawing or STEP file, then get confirmed with calipers on the real part when it arrives. |
| A "12 mm too short" finding was really a bounding box that included the drawing's title text. The parameter file was edited from it and later had to be reverted. | **One parameter file, every value tagged.** `params.mjs` is the single source for every dimension. Each value is marked `[SRC]` (sourced, with the citation) or `[EST]` (our estimate). Right now there are 29 sourced values and 35 estimates, and the estimates are the to-measure list. |
| Our own older CAD files didn't have features the newer design had, and both versions were in circulation. | **One current version.** The CAD, models, BOM and viewer all read the same parameters, and git holds the history. Older versions are never sent to anyone. |
| A key dimension (the ceramic core height) was never asked for, so parts were printed around a guess. | **Measure before you cut.** Before any part is printed or machined, every `[EST]` value that part depends on must be turned into a measurement, either from a datasheet or on the bench. |
| Problems were found after parts were made. | **Physics before parts.** Balance, load paths and every connection get checked before CAD (we learned that on Sitka's own first draft, which tipped over backward on paper). Then whole-body simulation (MuJoCo) and part-by-part stress tests (FEA) run at real weights. A part that fails on screen never gets made. |

## The build gates, in order

1. **Datasheet gate.** Pull the drawings for the CubeMars AK10-9 (flange bolt circle, case face), the brace hinges, the carbon tube and the battery cells. Replace each matching `[EST]`.
2. **Simulation gate.** `sim/SIMULATION.md` passes for a 130 kg wearer: every sit mode, shoves, lean-back, wet-floor slip, drop-catch, stand-up, running impact and uneven ground.
3. **Stress gate.** FEA on every printed and metal part at the simulation's peak loads, with a stated safety factor and a pass or fail for each.
4. **Fit-check prints.** Print cheap test pieces of every interface first: the bolt patterns, the tube sockets, the cuff clamps and the ratchet housing. Check them against the real bought parts before printing full parts.
5. **First-article inspection.** Every first part gets measured against the drawing and logged in `inspection/` before it's assembled.
6. **Proof tests before anyone sits.** Rear legs, ratchet and seat get loaded to 1.5x the 130 kg case on a bench rig, with sandbags, not a person.

## Why it's ready to build now

- **The physics closes.** Balance, load path, ratchet logic, rear-leg buckling and slip were all independently checked, and every failed item was fixed and re-checked (see the README's honest-status section).
- **Almost everything is off the shelf.** The motors, cells, controller, sensors, carbon tube and brace hinges can all be ordered today. See `PARTS_LIST_BOM.md`, with prices and links.
- **The control code isn't starting from zero.** It builds on NAU's open-source OpenExo firmware (Teensy plus the same motor family).
- **Most of the frame can be printed** (see the printable edition), so changes cost hours instead of tooling.
- **Every remaining unknown is written down,** with the test that settles it, so nothing is a surprise at the bench.
