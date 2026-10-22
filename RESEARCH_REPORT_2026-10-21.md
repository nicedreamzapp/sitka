# Run + Sit Exo: Research Report
**Date:** October 21, 2026 · **Method:** three parallel research passes (prior art, purchasable parts, biomechanics), each required to cite a URL or DOI for every number and to write "not found" rather than guess. One extra direct fetch for the actuator constants. Every number the models use is tagged in `params.mjs` as `[SRC n]` (below), `[CALC]` or `[EST]`.

## Bottom line

1. **Nobody sells this yet.** As of October 2026 we found powered exos with no seat (Hypershell, Dnsys, Ascentiz, Arc'teryx MO/GO) and wearable seats with no motor (Noonee Chairless Chair, Archelis). We found no product that combines powered running or hiking assist with a lockable seat. That conclusion rests on targeted searches, not an exhaustive catalogue.
2. **The motor cannot hold the seat.** Chair mode needs about 142 Nm per knee to hold a 130 kg man (balanced, static). The best backdrivable actuator for running gives 48 Nm peak. The seat therefore has to be a mechanical lock. That is the central design decision, and it is cheap: a 17-4PH pawl and toothed ring.
3. **A good running actuator and a good holding actuator are different machines.** A 9:1 quasi-direct drive keeps up with a running knee (about 8.7 rad/s in swing). A 64:1 actuator holds more torque but runs at 28% of that speed. Hence a 9:1 motor plus a pawl.
4. **Regenerative braking on descents is worth a few watts, not a charger.** Copper loss in a low-ratio motor at hiking speeds eats most of the harvest. The downhill mode is still worth having, because it takes braking work off the quads.
5. **Mass is the live risk.** At 2.9 kg per leg, P1 weighs about four times as much per leg as the Dnsys Z1. A 1.6 kg knee harvester raised walking cost 19% just by being worn (Donelan 2008).

## Sources the models use (`[SRC n]` in `params.mjs`)

| # | Source | What we take from it |
|---|---|---|
| 1 | Fryar et al., *Anthropometric Reference Data for Children and Adults: United States, 2015–2018*, Vital Health Stat 3(46), 2021. [PDF](https://www.cdc.gov/nchs/data/series/sr_03/sr03-046-508.pdf) | US men 20+: 95th-pct weight **130.3 kg** (Table 5), median 87.4 kg; 95th-pct stature **187.4 cm** (Table 11). These are separate marginals; we pair them on purpose as a worst case. |
| 2 | ANSUR II male public dataset (US Army, 2012), n = 4,082. [CSV](https://tools.openlab.psu.edu/publicData/ANSUR_II_MALE_Public.csv) | 95th pct (computed from the CSV): weight 110.7 kg, stature 1870 mm, buttock-knee **669 mm**, knee height sitting 602 mm. Military, not civilian, so NHANES is the design case. |
| 3 | Winter, *Biomechanics and Motor Control of Human Movement* | Thigh 0.245 H, shank 0.246 H. **We did not re-read the book**; a second worksheet independently lists 0.245 for the thigh. Flagged. |
| 4 | de Leva 1996, J Biomech 29(9):1223, [doi:10.1016/0021-9290(95)00178-6](https://doi.org/10.1016/0021-9290(95)00178-6), via the [Duarte BMC table](https://nbviewer.jupyter.org/github/demotu/BMC/blob/master/notebooks/BodySegmentParameters.ipynb) | Male mass fractions: thigh 0.1416, shank 0.0433, foot 0.0137; shank radius of gyration 0.251, COM 0.4395. |
| 5 | Schache et al. 2011, *Effect of running speed on lower limb joint kinetics*, MSSE 43(7):1260. [full text](https://paulogentil.com/pdf/Effect%20of%20Running%20Speed%20on%20Lower%20Limb%20Joint%20Kinetics.pdf) | At 3.5 m/s: knee extension moment **3.12 Nm/kg**; terminal-swing flexion 0.53 Nm/kg; absorption −15.7 W/kg (stance), −4.6 W/kg (terminal swing); generation +7.7 W/kg; negative work 0.74 + 0.19 + 0.41 J/kg per stride, positive 0.41 J/kg. |
| 6 | Riener et al. 2002 (stairs), as tabulated in [PMC7160724](https://pmc.ncbi.nlm.nih.gov/articles/PMC7160724/) | Peak knee extension moment 1.06 Nm/kg ascent, 0.92 descent. **Secondhand**; original not retrieved. |
| 7 | Tobler's hiking function, via [arXiv 2303.16065](https://arxiv.org/pdf/2303.16065) | About 5 km/h on flat ground, peaking near 6 km/h on a ~5% descent. |
| 8 | Noonee Chairless Chair 2.0: [Noonee shop](https://shop.noonee.com/en/products/chairless-chair-2-0), [RobotShop](https://www.robotshop.com/products/noonee-chairless-chair-20-large), [New Atlas](https://newatlas.com/wearables/chairless-chair-2-wearable/) | Passive, weight through the heel, 2.95 kg, €2,190 / $2,890. Our heel-stirrup load path copies this. |
| 9 | Luger et al. 2019, Appl Ergon 80:152, [doi:10.1016/j.apergo.2019.05.018](https://doi.org/10.1016/j.apergo.2019.05.018) | The Chairless Chair carried **up to 64% of body mass**. Vastus activity rose 95–135% sitting vs standing. 125° (high) and 90° (low) sitting, secondhand via [arXiv 2205.09910](https://arxiv.org/pdf/2205.09910). |
| 10 | CubeMars AK10-9 V2.0 KV100 [product page](https://www.cubemars.com/goods-1148-AK10-9+V20.html), fetched 2026-10-21 | 18 / 48 Nm, 16.2 / 41.2 A, Kt 0.114 Nm/A (rotor), 65.5 mΩ phase-phase, 9:1, 960 g, rotor 1002 g·cm², 0.8 Nm backdrive, 205 rpm rated at 24 V, **$698.90**. AK80-64 [page](https://www.cubemars.com/product/ak80-64-kv80-robotic-actuator.html): 48 / 120 Nm, 23 rpm, 850 g, $889.90. |
| 11 | Cells: [Battery Junction P45B](https://www.batteryjunction.com/molicel-inr21700-p45b) ($8.75, 4.5 Ah); [nkon Samsung 50S](https://www.nkon.nl/en/rechargeable/samsung-inr21700-50s-5000mah-35a.html) (72 g) | P45B mass not verified; we use 70 g (EST). |
| 12 | FAA PackSafe, [batteries](https://faa.gov/hazmat/packsafe/airline-passengers-and-batteries) | ≤100 Wh carry-on freely; 101–160 Wh with airline approval; >160 Wh banned. Hence 2 × 97 Wh packs. |
| 13 | Browning et al. 2007, MSSE 39:515, [doi:10.1249/mss.0b013e31802b3562](https://doi.org/10.1249/mss.0b013e31802b3562); Mooney & Herr 2016, [JNER](https://jneuroengrehab.biomedcentral.com/track/pdf/10.1186/s12984-016-0111-3) | Distal leg mass costs more; foot mass costs >4× the same mass at the waist (walking). Exact %/kg not retrieved. |
| 14 | Schertzer & Riemer 2014, Appl Ergon 45:1422, [doi:10.1016/j.apergo.2014.04.009](https://doi.org/10.1016/j.apergo.2014.04.009) | Knee-mass vs back-mass cost ratio 1.015–1.103; ankle vs knee 0.99–1.049 (walking, ≤2 kg per leg). |

### Cross-check and context sources
| Source | Used for |
|---|---|
| Donelan et al. 2008, Science 319:807; methods via [PMC2709631](https://pmc.ncbi.nlm.nih.gov/articles/PMC2709631/) | Knee harvester: **4.8 ± 0.8 W** at 1.5 m/s with generative braking; ~1.6 kg device; wearing it raised walking metabolic power 19.2%. |
| Wu et al. 2022, IEEE/ASME T-Mech 27(6), [abstract](https://scholar.hit.edu.cn/en/publications/generating-electricity-during-locomotion-modes-dominated-by-negat/) | ~5.4 W level, 6.5 W downhill, 8.2 W stair descent (per leg; convention unverified). |
| Elliott, Marecki, Herr, J Mech Des, [doi:10.1115/1.4027841](https://doi.org/10.1115/1.4027841) | Clutch-spring running knee exo: 190 Nm clutch, 710 g; per Mooney & Herr it did **not** reduce running metabolic cost. |
| Zhu et al., ICRA 2017, [doi:10.1109/ICRA.2017.7989063](https://doi.org/10.1109/ICRA.2017.7989063) | Knee-ankle orthosis at 30 Nm continuous / 60 Nm peak per joint: the torque class we are in. |
| Mooney, Rouse, Herr 2014, [PMC4236484](https://pmc.ncbi.nlm.nih.gov/articles/PMC4236484/) | Ankle exo, 3.6 kg, cut walking cost 10 ± 3%: proof that a well-placed powered exo can beat its own mass. |
| Kuster 1995, [doi:10.1007/BF01552646](https://doi.org/10.1007/BF01552646) | Downhill tibiofemoral load ~8 × body weight vs 3.9 × level: why the downhill braking mode matters to knees. |

## Prior art: open source (licences checked 2026-10-21 via `gh api`)

| Repo | ★ | Licence | What it is | Can we build on it? |
|---|---|---|---|---|
| [naubiomech/OpenExo](https://github.com/naubiomech/OpenExo) · [site](https://theopenexo.nau.edu/) · [wiki](https://wiki.theopenexo.org) | 385 | Custom LICENSE.md: hardware **CERN-OHL-P v2**, software "LGPL v3" | NAU's modular untethered exo (hip, ankle, elbow); Science Robotics, June 2025. Teensy + AK-series CAN motors, FSR and torque-sensor code; knee controllers exist in firmware but there is no knee build in the wiki. ~$1,000 materials per joint (press). | **Yes.** CERN-OHL-P can flow into OHL-S; LGPL code can be used in GPL-3.0. The LGPL label points at the GPL text, so we will ask NAU to confirm. **Our firmware target (Teensy + AK CAN) is chosen to match OpenExo.** |
| [srisura1010/Motor-Actuated-Knee-Exoskeleton-Using-IMU-Based-Gait-Detection](https://github.com/srisura1010/Motor-Actuated-Knee-Exoskeleton-Using-IMU-Based-Gait-Detection) | 1 | **None** | High-school BLDC knee exo, Moteus FOC over CAN, 3 IMUs, IMU gait detection. | **Inspiration only** (no licence = all rights reserved). We will ask the author. |
| [MaGabRam/qdd-knee-exoskeleton](https://github.com/MaGabRam/qdd-knee-exoskeleton) | 1 | **None** | Pediatric QDD knee actuator: CAD, FEA, thermal and control sims; not built. | **Inspiration only.** |
| [eliotk/OpenExo](https://github.com/eliotk/OpenExo) | 15 | MIT | 2011–12 Arduino lower-limb exo with servo, FSR and a brake pin. | Yes (MIT); low value. |
| [Madeeha-Fayyaz8621/ChairlessChair-IoT](https://github.com/Madeeha-Fayyaz8621/ChairlessChair-IoT) | 2 | MIT | Wearable-chair firmware: Arduino Uno R4, FSR posture detection, dual linear actuators, web UI. | Yes (MIT); closest open "seat" code. |
| [MarcelHansmann/Re-Move-Exoskeleton](https://github.com/MarcelHansmann/Re-Move-Exoskeleton) | 1 | CC BY-NC-SA 4.0 | Passive printed squat-assist knee exo. | **No**: non-commercial clause conflicts with our licences. |
| [vish8426/kneeExoskeleton](https://github.com/vish8426/kneeExoskeleton) | 1 | MIT | Hinged brace for children with CP (sit/stand/walk). | Yes; not reviewed in depth. |

No open-source repo combines a powered knee with a wearable seat.

## Prior art: commercial (vendor and press claims, not tests)

| Product | Joint / type | Mass | Battery / range | Torque or power | Price | Seat? |
|---|---|---|---|---|---|---|
| [Hypershell X Ultra](https://hypershell.tech/products/hypershell-x-ultra) (now X Ultra S) | hip, powered | 1.8 kg w/o battery | 2 × 72 Wh, 30 km/battery | 1000 W, 22 Nm | $1,599 sale / $1,999 list | no |
| Hypershell X Pro | hip, powered | ~2.0 kg w/o battery | 2 × 72 Wh, 17.5 km | 800 W, 18 Nm | $899 sale / $1,199 | no |
| [Dnsys X1](https://gearjunkie.com/outdoor/hiking/dnsys-x1-exoskeleton-review) | **hip** (the brief called it a knee unit) | 3.53 lb | 15 mi | 900 W; torque claims conflict (40–50 Nm) | — | no |
| [Dnsys Z1](https://ko.ifixit.com/Device/Dnsys_Z1_Exoskeleton_Pro_Death_Stranding_2_Edition) | **knee**, powered | ~0.68 kg per leg | 4–5 h claimed | 450–900 W (sources conflict) | $699–$1,398 pre-order | no |
| [Ascentiz H1 Pro / K module](https://www.wellbots.com/products/ascentiz-h-ultra-exoskeleton) | hip + swappable knee | H Ultra 5.5 lb | 20 km / 10 h claims | 36–44 Nm, 900–1000 W (conflicting) | $1,049 | no |
| Noonee Chairless Chair 2.0 [SRC 8] | knee, **passive seat** | 2.95 kg | none | none | €2,190 / $2,890 | **yes** |
| [Archelis / ArchelisFX](https://exoskeletonreport.com/product/archelis/) | knee, **passive seat** | 2.3–2.7 kg | none | none | ~$5,000 (2021, unconfirmed) | **yes** (lock as stool) |
| Arc'teryx MO/GO (Skip) | hip + knee pants | ~3 kg | ~3 h | — | $5,000 | no |

Roam Robotics, WIRobotics WIM, Keeogo and Ottobock C-Brace returned nothing current enough to use.

## Parts we did NOT find (open questions for a vendor)
- A CubeMars or MyActuator actuator with a built-in fail-safe brake.
- A holding torque in Nm for any orthotic drop-lock or stance-control knee joint (they are rated by patient weight).
- A belt-sized 100–160 Wh pack off the shelf (so P1 builds its own 6S1P packs).
- Running cadence and contact time at 3.5 m/s, level-walking knee moment, and downhill knee work per stride from a primary source. The models carry these as **EST** and say so.

## Refuted or corrected during research
- "Dnsys X1 is a knee exo": it is a hip exo. Dnsys's knee product is the Z1.
- A retailer lists the AK10-9 KV100 at 15 / 38 Nm; CubeMars lists 18 / 48 Nm. We use the manufacturer's numbers.
