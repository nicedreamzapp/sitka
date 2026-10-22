#!/usr/bin/env python3
"""Sitka parts list: the ONE source of truth for the current (kinetics-first, render two) design.

Writes PARTS_LIST.md (prose from docs/parts_list_template.md) and parts.csv:   python3 parts_list.py
No dependencies. Masses of CAD parts come from the solid volumes in cad/build/manifest.json
(written by cad/parts/build_parts.py) times a material density and a fill factor, so a CAD change
moves the mass here on the next run. Everything else is a supplier figure or an estimate.

Every row says whether its mass and its price are estimates (EST). Prices are USD, seen 2026-10-22
at the linked seller unless marked EST. The retired rigid v2 list lives in legacy/.
"""
import csv, json, os
from collections import OrderedDict

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = {p["name"]: p for p in json.load(open(os.path.join(HERE, "cad/build/manifest.json")))["parts"]}

# ---------------------------------------------------------------- materials
# density g/cm3; price $/g incl. ~15% waste, supports and failed prints
RHO = dict(PAHT=1.06, TPU=1.22, PETG=1.27, AL=2.81, SS=7.80, GF=1.90, CF=1.55)
FIL = dict(PAHT=94.99 / 1000 * 1.15, TPU=39.00 / 1000 * 1.15, PETG=19.99 / 1000 * 1.15)
FIL_SRC = dict(
    PAHT="https://www.gigaparts.com/bambu-lab-paht-cf-black-carbon-fiber-reinforced-paht-3d-printer-filament-1-75mm-1kg-spool.html",
    TPU="https://3dprintingusa.com/collections/bambu-lab-tpu",
    PETG="EST (Bambu PETG HF, about $20/kg)")
# print speed on an X1C / P1S class printer, grams per hour (EST: strong settings, not speed settings)
GPH = dict(PAHT=15, TPU=20, PETG=25)

SET_SHELL = "PAHT-CF, 0.4 hardened nozzle, 0.2 mm layers, wall printed solid (6 to 8 perimeters), dried 80 C 8 h"
SET_STRONG = "PAHT-CF, 0.4 hardened nozzle, 0.2 mm, 5 walls, 40% gyroid, layers laid across the load, heat-set inserts"
SET_LINER = "TPU 95A HF, 0.2 mm, graded gyroid (about 12% at the skin to 25% at the shell), no supports; spacer mesh or gel glued on"
SET_PETG = "PETG, 0.2 mm, 3 walls, 20% infill"


def vol(name):
    """CAD solid volume, cm3, mean of the L and R copies when both exist"""
    if name in MAN:
        return MAN[name]["volume_cm3"]
    vs = [MAN[n]["volume_cm3"] for n in (name + "_l", name + "_r") if n in MAN]
    if not vs:
        raise KeyError(name)
    return sum(vs) / len(vs)


ROWS = []


def add(module, tier, name, tech, qty, make, material, process, mass_g, unit_usd, source,
        mass_est=True, cost_est=True, cad="", print_mat=None):
    ROWS.append(OrderedDict(
        module=module, tier=tier, name=name, technical=tech, qty=qty, make=make, material=material,
        process=process, mass_each_g=round(mass_g, 1), mass_line_g=round(mass_g * qty, 1),
        unit_usd=round(unit_usd, 2), line_usd=round(unit_usd * qty, 2),
        mass_est="EST" if mass_est else "", cost_est="EST" if cost_est else "",
        source=source, cad=cad, print_mat=print_mat or ""))


def printed(module, tier, name, tech, qty, cadname, mat, fill, settings, note="", cad=None):
    """3D-printed part: mass and filament cost from the CAD volume"""
    m = vol(cadname) * RHO[mat] * fill
    matname = {"PAHT": "PAHT-CF (or PA12-CF)", "TPU": "TPU 95A HF", "PETG": "PETG"}[mat]
    add(module, tier, name, tech, qty, "PRINT", matname, settings + (("; " + note) if note else ""),
        m, m * FIL[mat], "filament: " + FIL_SRC[mat], mass_est=True, cost_est=False,
        cad=cad or cadname, print_mat=mat)


def metal(module, tier, name, tech, qty, cadname, mat, fill, process, usd, note="", cad=None, mass_g=None):
    m = mass_g if mass_g is not None else vol(cadname) * RHO[mat] * fill
    matname = {"AL": "7075-T6 aluminium", "SS": "17-4PH H900 stainless"}[mat]
    add(module, tier, name, tech, qty, "METAL", matname, process + (("; " + note) if note else ""),
        m, usd, "EST: one-off job-shop price, get 3 quotes", cost_est=True, cad=cad or cadname or "")


def buy(module, tier, name, tech, qty, material, process, mass_g, usd, source, mass_est=True, cost_est=None, cad=""):
    if cost_est is None:
        cost_est = not source.startswith("http")
    add(module, tier, name, tech, qty, "BUY", material, process, mass_g, usd, source,
        mass_est=mass_est, cost_est=cost_est, cad=cad)


B, S, P, F = "Basic", "Smart", "Power (P1)", "Full body"

# ================================================================ DOCK (hub)
D = "Dock (hub)"
printed(D, B, "Back panel (carries the straps, ports and later the motor)", "back_panel, 600 cm2 contoured plate", 1,
        "back_panel", "PAHT", 1.0, SET_SHELL, "279 x 277 mm: print as two halves with a bolted lap joint on a 256 mm bed, one piece on an H2D")
printed(D, B, "Back panel pad", "back_panel_liner, spacer mesh + 6 mm lattice", 1, "back_panel_liner", "TPU", 0.15, SET_LINER,
        "split like the panel")
printed(D, B, "Lumbar plate (stiffens the belt at the spine)", "lumbar_plate", 1, "lumbar_plate", "PAHT", 1.0, SET_SHELL)
printed(D, B, "Seat cup under each sit bone (400 cm2)", "seat_cup_l/r, 18 x 24 cm cup, takes 607 N", 2, "seat_cup", "PAHT", 1.0,
        SET_SHELL, "bench-proof at 1.5 x 607 N before wearing; v2 = carbon layup using the print as the plug")
printed(D, B, "Seat cup cushion (gel + lattice, 15 kPa target)", "seat_cup_liner_l/r, 15 mm graded lattice under a 3 mm gel sheet", 2,
        "seat_cup_liner", "TPU", 0.20, SET_LINER)
printed(D, B, "Belt side clips", "belt_sideclip_l/r", 2, "belt_sideclip", "PAHT", 0.7, SET_STRONG)
metal(D, B, "Cable ports, ball-end into keyhole (6 per Dock)", "port_knee/hip/shoulder_l/r, quick-release terminal, 3.6 kN proof", 6,
      "port_knee", "SS", 1.0, "waterjet or wire-EDM keyhole plate, then pocket", 18,
      "must be metal: carries the full tendon proof load of 3.6 kN")
buy(D, B, "Hip belt, padded (backpack replacement belt)", "hip_belt, 300 cm2 contact, < 10 kPa", 1, "nylon + EVA foam",
    "off the shelf, e.g. a Granite Gear or Osprey replacement hip belt; add the side clips", 300, 60,
    "EST: backpack replacement belts sell for about $40 to $80")
buy(D, B, "Belt buckle, aluminium cobra type", "belt_buckle, 38 mm", 1, "aluminium", "off the shelf (AustriAlpin Cobra style)", 55, 30,
    "EST: cobra buckles sell for about $25 to $35")
buy(D, B, "Shoulder harness with sternum strap", "harness_l/r + sternum_strap, 7 cm wide, 17 kPa at lift peak", 1, "nylon + spacer mesh",
    "off the shelf backpack harness, sewn to the panel", 250, 40, "EST: replacement backpack harness")
buy(D, B, "Webbing: Crazy Creek straps, panel straps, seat-cup straps", "crazycreek_l/r (94 N at 10 deg), panelstrap_l/r, cupstrap_l/r; 25 to 38 mm polyester, low stretch",
    1, "polyester webbing", "about 5 m, cut, heat-sealed, bar-tacked", 120, 30,
    "EST: polyester webbing about $1.5 to $3 per yard")
buy(D, B, "Cam buckles and ladder locks for the Dock straps", "8 pieces", 8, "aluminium / acetal", "off the shelf", 12, 3.5, "EST")
buy(D, B, "D-rings for the Crazy Creek strap at the thigh", "dring_cc_l/r", 2, "aluminium", "off the shelf, 25 mm", 6, 1.5, "EST")
buy(D, B, "Silicone gel sheet, 3 mm, fabric backed (seat cups)", "skin layer of the seat-cup stack", 1, "silicone gel",
    "Silipos Soft Sheer type sheet, cut to the cup outline", 120, 60,
    "EST (no public price): https://ortoped.ca/Silipos-Soft-Sheer-Sheeting/family-844")
buy(D, B, "3D spacer mesh, 3 to 4 mm (all pad covers)", "breathable skin layer for every pad", 1, "polyester spacer fabric",
    "about 2 yd, sewn into washable covers", 150, 16, "EST: about $5 to $8 per yd (eBay spacer-mesh listings)")
buy(D, B, "Fasteners, heat-set inserts, thread-locker (Dock)", "M4/M5 stainless, brass inserts", 1, "stainless / brass", "kit", 60, 15, "EST")

# ================================================================ M1 KNEE + SEAT (per pair)
K = "Knee + Seat (M1)"
printed(K, B, "Thigh shell, laced", "thigh_shell_l/r, contoured from a 3D scan", 2, "thigh_shell", "PAHT", 1.0, SET_SHELL,
        "289 mm long: split above the knee on a 256 mm bed, one piece on an H2D; v2 = carbon layup on the print as a plug")
printed(K, B, "Thigh pad", "thigh_liner_l/r, spacer mesh + 10 mm lattice", 2, "thigh_liner", "TPU", 0.15, SET_LINER, "split like the shell")
printed(K, B, "Below-kneecap pad shell (PTB, 100 cm2)", "ptb_shell_l/r, patellar-tendon-bearing pad", 2, "ptb_shell", "PAHT", 1.0, SET_SHELL)
printed(K, B, "Calf pad shell (120 cm2)", "calf_cuff_l/r", 2, "calf_cuff", "PAHT", 1.0, SET_SHELL)
printed(K, B, "Shin pad (gel + lattice)", "shin_liner_l/r, 12 mm lattice under 3 mm gel", 2, "shin_liner", "TPU", 0.18, SET_LINER)
printed(K, B, "Calf pad lattice", "calf_liner_l/r", 2, "calf_liner", "TPU", 0.18, SET_LINER)
printed(K, B, "Knee side pads", "condyle_pad_lat/med_l/r", 4, "condyle_pad_lat", "TPU", 0.25, SET_LINER)
metal(K, B, "Hinge arms, thigh side", "thigh_arm_lat/med_l/r, 24 x 4.8 mm strip", 4, "thigh_arm_lat", "AL", 1.2,
      "laser cut flat from 0.190 in 7075-T6 (SendCutSend lists it), the CAD joggle taken up by a printed spacer at the shell", 22,
      "must be metal: carries the knee couple, 34 Nm sitting and up to 190 Nm if the strut is lost (205 MPa, SF 2.5)")
metal(K, B, "Hinge arms, shin side", "shin_arm_lat/med_l/r, 24 x 4.8 mm strip", 4, "shin_arm_lat", "AL", 1.2,
      "laser cut flat from 0.190 in 7075-T6, same as the thigh arms", 26, "must be metal: same couple as the thigh arms")
metal(K, B, "Geared bicentric knee hinge (hub pair per knee)", "knee_hub_lat/med_l/r, two geared plates + cover", 4, "knee_hub_lat", "AL", 0.8,
      "CNC 7075, gear segments milled or wire-EDM", 70,
      "must be metal: carries the arc reaction of 602 N sitting and about 3.4 kN in a strut-lost catch")
metal(K, B, "80 mm grooved arc (artificial kneecap) with its yoke", "knee_arc_l/r + knee_yoke_l/r, r = 80 mm, 93 deg sector", 2, None, "AL", 1.0,
      "CNC 7075 as one piece, groove polished for the line", 160,
      "must be metal: sees sqrt2 x T = 602 N sitting, 3.4 kN catch; a groove in plastic would creep and cut", cad="knee_arc + knee_yoke",
      mass_g=(vol("knee_arc") + vol("knee_yoke")) * RHO["AL"] * 0.9)
printed(K, B, "Cam clutch housing + mode lever mount", "knee_manifold_l/r, WALK / SIT-LIFT / FREE", 2, "knee_manifold", "PAHT", 0.6, SET_STRONG,
        "the housing only positions the clutch; the load path is the metal spool, shaft and pins")
buy(K, B, "One-way sprag clutch (the power-off seat lock)", "CSK20-PP, 20 x 47 x 14 mm, 50 Nm rated", 2, "bearing steel",
    "off the shelf, pressed into a 7075 spool of 14 mm radius: 50 Nm = 3.57 kN line pull, right at the 3.6 kN proof, so proof-test or step up to CSK25",
    110, 150, "https://uk.rs-online.com/web/p/sprag-clutch-bearings/1465256", cost_est=False)
metal(K, B, "Clutch spool, shaft and release dog", "inside knee_manifold: spool r = 14 mm, the mode lever frees or grounds the outer race", 2, None, "AL", 1.0,
      "CNC 7075 spool, 17-4PH shaft and dog", 70, "must be metal: the tendon load passes straight through it", cad="(inside knee_manifold)", mass_g=60)
printed(K, B, "Mode lever", "mode_lever_l/r", 2, "mode_lever", "PAHT", 0.8, SET_STRONG)
metal(K, B, "Tendon fairlead", "tendon_fairlead_l/r, turns T1 onto the arc", 2, "tendon_fairlead", "AL", 0.6,
      "CNC 7075 with a polished radius (or a printed body with a stainless sheave)", 35, "metal preferred: 426 N line turning on it")
add(K, B, "Sit leaf spring (350 N near-constant, 44 J)", "sit_leaf_l/r, tapered glass leaf, 126 mm stroke", 2, "BUY",
    "unidirectional E-glass laminate (bow-limb glass)",
    "laminate 5 to 6 strips of 0.030 in bow glass with epoxy, taper-ground, bench-tested to 10^5 cycles",
    vol("sit_leaf") * RHO["GF"], 15, "glass strips: https://bigjimsbowcompany.com/?p=8861 ($13 to $15 per 72 in strip); leaf price EST",
    mass_est=True, cost_est=True, cad="sit_leaf")
metal(K, B, "Leaf root clamp with preload knob (250 to 400 N)", "sit_leaf_root_l/r", 2, "sit_leaf_root", "AL", 0.7,
      "CNC 7075", 40, "must be metal: the leaf's root bending moment and the preload screw")
buy(K, B, "Telescoping carbon strut, 3 sections, one-way lock, rubber foot", "strut_tube0..2 24/20/16 x 1.5 mm, 0.36 m stowed to 0.86 m; 472 N, buckles at 5.2 kN",
    2, "roll-wrapped 3K carbon tube", "three tubes cut to 0.32 m, bushed, twist-lock collars, pivoting rubber cane tip",
    300, 85, "tubes about $15 to $20 each (https://aws.robu.in/?p=894416 lists 24 x 22 x 1000 mm); cane tip $18.95 (legacy list); lock EST",
    cost_est=True, cad="strut_tube0-2, strut_collar0-1, strut_foot")
metal(K, B, "Strut hinge (ball clevis on the seat cup)", "strut_clevis_l/r, sagittal fold + 9 deg splay", 2, "strut_clevis", "AL", 0.6,
      "CNC 7075 with a bought stainless rod-end ball", 60, "must be metal: the strut's 472 N push goes through it into the cup")
printed(K, B, "Strut stow clip", "strut_clip_l/r", 2, "strut_clip", "PAHT", 0.7, SET_STRONG)
buy(K, B, "Knee seat tendon T1 + backup strap line", "t1_tendon_l/r: 1/8 in (3.2 mm) 12-strand Dyneema; production: Vectran or SK99 (low creep)",
    1, "Dyneema SK75 (bench) / Vectran", "spliced eyes; about 25 ft covers T1, the backup lines and practice splices",
    15, 0.47 * 25, "https://www.fisheriessupply.com/samson-rope-blue-amsteel-blue/872007006030 ($0.47/ft, 1/8 in)",
    cost_est=False, cad="t1_tendon")
buy(K, B, "Backup strap cleat (catches if the clutch slips)", "own cleat, set 3 mm slacker than T1, nylon line for a soft catch", 2,
    "aluminium + composite", "Harken 150 Cam-Matic on 6 mm nylon double braid; VERIFY its working load against the 1.2 kN catch", 30, 44.95,
    "https://defender.com/en_us/harken-150-standard-cam-matic-cleat", cost_est=False)
buy(K, B, "Tendon anchor below the kneecap", "shin_anchor_l/r, 3.6 kN proof", 2, "316 stainless", "off the shelf stainless pad eye, through-bolted with a backing plate",
    12, 12, "EST: small marine pad eyes $8 to $15", cad="shin_anchor")
buy(K, B, "Thigh and shin straps + buckles", "thigh_strap0/1, shin_strap0/1, thigh_buckle0/1 (L and R)", 2, "nylon webbing + aluminium cam buckles",
    "38 mm webbing, cut and bar-tacked; lacing for the shells", 90, 25, "EST")
buy(K, B, "Silicone gel sheet, 3 mm (below-kneecap pads)", "skin layer on the shear-loaded pads", 1, "silicone gel", "cut to the PTB pad outline",
    60, 60, "EST (no public price): https://ortoped.ca/Silipos-Soft-Sheer-Sheeting/family-844")
buy(K, B, "Fasteners, inserts, bushings (knee)", "M4/M5 12.9 and stainless, oilite bushings", 1, "steel / bronze", "kit", 80, 25, "EST")

# ================================================================ M2 BACK / LIFT
L = "Back / Lift (M2)"
add(L, B, "Lift leaf spring (3.1 N/mm, slack below 35 deg)", "m2_leaf, tapered glass leaf at the panel", 1, "BUY",
    "unidirectional E-glass laminate", "laminated like the sit leaf; 300 N per side at a 90 deg stoop",
    vol("m2_leaf") * RHO["GF"], 15, "glass strips: https://bigjimsbowcompany.com/?p=8861; leaf price EST", cad="m2_leaf")
metal(L, B, "Lift leaf root clamp + ON/OFF switch", "m2_leaf_root; OFF when sitting", 1, "m2_leaf_root", "AL", 0.7, "CNC 7075", 45,
      "must be metal: leaf root bending, 600 N total line pull")
buy(L, B, "Whiffletree (floating pulley, equal left/right share)", "whiffletree", 1, "aluminium + stainless", "small sailing block, about 20 mm sheave",
    25, 25, "EST: micro blocks $15 to $35", cad="whiffletree")
printed(L, B, "Lumbar standoff", "lumbar_standoff_l/r", 2, "lumbar_standoff", "PAHT", 0.7, SET_STRONG,
        "line runs over a 6 mm stainless pin pressed in, not over the plastic")
printed(L, B, "Glute guide (100 mm lever)", "glute_guide_l/r, takes the lift tendon wrap", 2, "glute_guide", "PAHT", 0.7, SET_STRONG,
        "stainless pin insert; bench-proof at 1.2 kN (the P1 peak is 800 N per side): VERIFY, CNC 7075 if it creeps")
printed(L, B, "Panel line guides", "panel_guide_l/r", 2, "panel_guide", "PAHT", 0.7, SET_STRONG)
printed(L, B, "Posterior thigh cuff (lift anchor, 200 cm2)", "thigh_cuff_l/r", 2, "thigh_cuff", "PAHT", 1.0, SET_SHELL)
printed(L, B, "Thigh cuff pad", "thigh_cuff_liner_l/r, gel + 12 mm lattice", 2, "thigh_cuff_liner", "TPU", 0.18, SET_LINER)
buy(L, B, "Lift tendon T3 line", "t3_tendon_l/r, 1/8 in Dyneema, about 1 m each", 1, "Dyneema SK75", "spliced eyes", 10, 0.47 * 8,
    "https://www.fisheriessupply.com/samson-rope-blue-amsteel-blue/872007006030", cost_est=False, cad="t3_tendon")
buy(L, B, "Stainless roller pins and D-rings", "6 mm pins for the standoffs, dring_t3_l/r", 1, "316 stainless / aluminium", "off the shelf", 30, 12, "EST")

# ================================================================ M3 HIP
H = "Hip (M3)"
printed(H, B, "Hip-flexor standoff (60 mm lever)", "m3_standoff_l/r", 2, "m3_standoff", "PAHT", 0.7, SET_STRONG, "stainless pin insert")
buy(H, B, "Hip-flexor spring element (14 N/mm, 300 N at 20 deg)", "m3_band_l/r: webbing in series with a steel extension spring", 2,
    "music-wire spring + polyester webbing", "a 14 N/mm, 30 mm-travel extension spring sewn into a 20 mm webbing band; latex is far too soft for this rate",
    60, 15, "EST: industrial extension springs $5 to $12", cad="m3_band")
buy(H, B, "D-rings and slides for the hip bands", "dring_m3_l/r", 1, "aluminium", "off the shelf", 15, 6, "EST")

# ================================================================ COUPLINGS
C = "Couplings (bands)"
buy(C, B, "Running band (shoe to shoe or shin to shin, RUN only)", "running_band, latex tube about 0.25 m, Simpson 2019 exotendon", 1, "latex tubing",
    "cut to length, knotted or crimped to the clips; tune stiffness on the treadmill",
    50, 21, "https://www.walmart.com/ip/20969124 (TheraBand heavy tubing, 25 ft, about $21)", cost_est=False, cad="running_band")
printed(C, B, "Running band clips", "runband_clip_l/r", 2, "runband_clip", "PAHT", 0.8, SET_STRONG)
buy(C, F, "Hamstring band (hip + knee coupling, 3 N/mm)", "hamstring_band_l/r, 126 N at 42 mm, OFF in SIT", 2, "latex (speargun-type rubber) + webbing",
    "cut to length and tuned; a TheraBand strand is about 50 times too soft", 40, 12, "EST: speargun rubber about $3 to $5 per ft",
    cad="hamstring_band")
printed(C, F, "Band guide 40 mm behind the knee axis", "knee_guide_l/r, with a 623 bearing pulley", 2, "knee_guide", "PAHT", 0.8, SET_STRONG)
buy(C, F, "Coupling D-rings", "dring_ham_l/r, dring_ham_calf_l/r", 4, "aluminium", "off the shelf", 3, 1.5, "EST")
buy(C, F, "Calf band line (knee + ankle, needs M4)", "calf_band_l/r", 1, "Dyneema SK75", "spliced", 5, 0.47 * 6,
    "https://www.fisheriessupply.com/samson-rope-blue-amsteel-blue/872007006030", cost_est=False, cad="calf_band")

# ================================================================ SMART CLUTCH UPGRADE
SM = "Smart-clutch upgrade"
buy(SM, S, "Electroadhesive stance clutch (fails open)", "ea_clutch_l/r, about 8 electrode pairs for 375 N at SF 2, 26 g element", 2,
    "PET film electrodes, dielectric film", "built from film to the Diller/Collins ICRA 2016 recipe; bench-test wet and dry at 375 N",
    30, 100, "EST: KINETICS.md target of about $200 a pair", cad="ea_clutch")
buy(SM, S, "Stance leaf (15.6 N/mm, 330 N breakaway stop)", "T1b branch", 2, "glass laminate", "laminated like the sit leaf", 25, 15, "EST")
buy(SM, S, "High-voltage driver for the EA clutches", "about 300 V, mW level", 1, "electronics", "small HV DC-DC module + switching", 30, 90, "EST")
buy(SM, S, "Microcontroller, Teensy 4.1", "600 MHz, native CAN", 1, "electronics", "off the shelf", 10, 31.50,
    "https://www.sparkfun.com/teensy-4-1.html (legacy list price)", mass_est=False)
buy(SM, S, "Shank IMU, Adafruit BNO085", "gait phase", 2, "electronics", "off the shelf", 5, 29.50, "https://www.adafruit.com/product/4754 (legacy list price)",
    mass_est=False)
buy(SM, S, "Insole pressure sensors, Interlink FSR 402", "4 per foot", 8, "electronics", "taped into a thin insole", 2, 2.99,
    "https://www.interlinkelectronics.com/products/fsr-model-402 (legacy list price)", mass_est=False)
buy(SM, S, "Tendon load cell + HX711", "reads T1 tension, coaches the recline (warns at about 500 N)", 2, "electronics", "inline mini load cell", 25, 35, "EST")
buy(SM, S, "Small battery, 1 cell 21700 (16 Wh) + charger board", "Molicel P45B", 1, "Li-ion", "with a protection/charge board", 90, 8.75 + 12,
    "https://www.batteryjunction.com/molicel-inr21700-p45b ($8.75) + board EST", cost_est=True)
buy(SM, S, "Wiring, connectors, haptic buzzers", "JST-GH, braided sleeve, 2 haptic discs", 1, "electronics", "kit", 60, 40, "EST")
add(SM, S, "Controller enclosure", "on the back panel, about 60 g", 1, "PRINT", "PETG", SET_PETG, 60, 60 * FIL["PETG"],
    "filament: " + FIL_SRC["PETG"], mass_est=True, cost_est=True, print_mat="PETG")

# ================================================================ ONE-MOTOR POWER TIER (P1)
PW = "One-motor power (P1)"
buy(PW, P, "Motor, CubeMars AK10-9 V3 (one, on the back)", "p1_motor, 9:1 QDD, 18 Nm rated, CAN", 1, "actuator", "off the shelf",
    960, 698.90, "https://aifitlab.com/collections/cubemars-motor/products/cubemars-ak10-9-v3-0-motor ($698.90, motor; $935 with driver at OpenELAB)",
    mass_est=True, cost_est=False, cad="p1_motor")
metal(PW, P, "Hub drum, 25 mm spool", "p1_drum", 1, "p1_drum", "AL", 0.5, "CNC 7075", 120, "must be metal: 720 N line pull at rated torque")
buy(PW, P, "Dog clutches pick left, right or both (solenoid + steel dogs)", "p1_dogclutch_l/r", 2, "17-4PH dogs + bistable solenoid",
    "CNC dogs (EST $60) + Intertec ITS-LX-2218 latching solenoid (about $54)", 80, 114,
    "solenoid: https://rapidonline.com/intertec-its-lx-2218-12vdc-10mm-4n-de-energised-20n-bi-directional-solenoid-50-2909; dogs EST",
    cad="p1_dogclutch")
buy(PW, P, "Bowden cables, hub to knee manifold", "bowden_l/r, efficiency 0.68 to 0.79, 551 N motor side", 2,
    "PTFE-lined housing + 7x19 stainless inner", "motorcycle-clutch style housing, swaged ends", 80, 30, "EST", cad="bowden")
buy(PW, P, "Battery, 97 Wh (under the FAA 100 Wh line), 6S1P Molicel P45B", "p1_battery", 6, "Li-ion 21700 cell", "spot-welded pack",
    70, 8.75, "https://www.batteryjunction.com/molicel-inr21700-p45b ($8.75 each)", mass_est=False, cost_est=False, cad="p1_battery")
buy(PW, P, "6S BMS, nickel strip, pack case, fuse", "for the 97 Wh pack", 1, "electronics", "kit + printed case", 100, 25, "EST")
buy(PW, P, "6S balance charger", "one-time", 1, "electronics", "off the shelf", 0, 45, "EST (legacy list)")
buy(PW, P, "CAN transceiver + power wiring + E-stop", "SN65HVD230, XT30, big red stop on the belt", 1, "electronics", "kit", 120, 45, "EST")

# ================================================================ M4 ANKLE
A = "Ankle (M4)"
printed(A, F, "Heel clip", "m4_heelclip_l/r", 2, "m4_heelclip", "PAHT", 0.8, SET_STRONG,
        "prototype only; CNC 7075 if the bench shows creep under the 15 to 25 Nm ankle torque")
printed(A, F, "Ankle clutch housing (Collins type, no power)", "m4_clutch_l/r", 2, "m4_clutch", "PAHT", 0.7, SET_STRONG)
metal(A, F, "Ankle clutch ratchet, pawl and spring set", "inside m4_clutch: engages at foot-flat, releases at push-off", 2, None, "SS", 1.0,
      "CNC / wire-EDM 17-4PH", 60, "must be metal: the calf spring load passes through the pawl", cad="(inside m4_clutch)", mass_g=35)
add(A, F, "Calf spring leaf", "m4_spring_l/r", 2, "BUY", "unidirectional E-glass laminate", "laminated like the sit leaf",
    vol("m4_spring") * RHO["GF"], 10, "EST", cad="m4_spring")
buy(A, F, "Ankle frame, shin pad to heel clip (not in the CAD yet)", "carbon strip pair per side, after the Collins 2015 device", 2,
    "carbon strip or 7075 strip", "cut from 3 mm carbon plate, bonded and bolted", 150, 40,
    "EST: the CAD shows only the clip, clutch and leaf; Collins' whole device was about 0.4 to 0.5 kg per leg")
buy(A, F, "Ankle cable", "m4_cable_l/r", 1, "Dyneema SK75", "spliced", 5, 0.47 * 4,
    "https://www.fisheriessupply.com/samson-rope-blue-amsteel-blue/872007006030", cost_est=False, cad="m4_cable")
buy(A, F, "Ankle straps, heel-counter strap, fasteners", "", 2, "nylon webbing", "sewn", 40, 12, "EST")

# ================================================================ M5 SHOULDER
SH = "Shoulder (M5)"
printed(SH, F, "Shoulder spring cassette housing", "m5_cassette_l/r", 2, "m5_cassette", "PAHT", 0.6, SET_STRONG)
buy(SH, F, "Cassette spring set (Paexo-style arm support)", "springs + cam + bearings inside m5_cassette", 2, "spring steel",
    "off-the-shelf compression or torsion springs, tuned per wearer", 150, 45, "EST")
metal(SH, F, "Arm lever", "m5_lever_l/r, 12 x 6 mm", 2, None, "AL", 1.0, "laser-cut 7075 strip with a bearing at the pivot", 30,
      "must be metal: arm support torque at the pivot", cad="m5_lever", mass_g=45)
printed(SH, F, "Arm cuff", "m5_armcuff_l/r", 2, "m5_armcuff", "PAHT", 1.0, SET_SHELL)
printed(SH, F, "Arm cuff pad", "m5_armliner_l/r", 2, "m5_armliner", "TPU", 0.15, SET_LINER)
buy(SH, F, "Arm straps and fasteners", "", 2, "nylon webbing", "sewn", 30, 10, "EST")

# ---------------------------------------------------------------- roll-ups
MODULES = ["Dock (hub)", "Knee + Seat (M1)", "Back / Lift (M2)", "Hip (M3)", "Couplings (bands)",
           "Smart-clutch upgrade", "One-motor power (P1)", "Ankle (M4)", "Shoulder (M5)"]


def tot(rows):
    return sum(r["mass_line_g"] for r in rows), sum(r["line_usd"] for r in rows), \
        sum(r["line_usd"] for r in rows if r["cost_est"])


def batch(rows):
    return sum(r["line_usd"] * (0.45 if r["make"] == "METAL" else 1.0) for r in rows)


def pmass(rows, mat):
    return sum(r["mass_line_g"] for r in rows if r["print_mat"] == mat)


def kg(g):
    return f"{g / 1000:.2f} kg"


def usd(x):
    return f"${x:,.0f}"


bym = {m: [r for r in ROWS if r["module"] == m] for m in MODULES}
starter = bym["Dock (hub)"] + bym["Knee + Seat (M1)"] + bym["Back / Lift (M2)"]
basic = [r for r in ROWS if r["tier"] == B]
smart = basic + [r for r in ROWS if r["tier"] == S]
power = smart + [r for r in ROWS if r["tier"] == P]
full = list(ROWS)
TIERS = [("Seat + Back starter (Dock + M1 + M2)", starter, "Sit anywhere, stand-up help, passive lift", "~3.9 kg, ~$1,200 (Dock 0.7 + M1 2.9 + M2 0.35)"),
         ("B: Basic passive (+ Hip + running band)", basic, "Adds the walking and running bands", "~4.4 kg, ~$1,300"),
         ("S: Smart (+ EA clutches, sensors)", smart, "Springs switch on at the right moment, fail open", "~4.7 kg, ~$1,900"),
         ("P1: One motor", power, "Stairs, hills, heavy lifts", "~6.7 kg, ~$3,000"),
         ("Full body (+ ankle, shoulder, couplings)", full, "Everything", "~9.4 kg, ~$4,100")]

# ---------------------------------------------------------------- CSV
COLS = ["module", "tier", "name", "technical", "qty", "make", "material", "process", "mass_each_g", "mass_line_g",
        "mass_est", "unit_usd", "line_usd", "cost_est", "source", "cad"]
with open(os.path.join(HERE, "parts.csv"), "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
    w.writeheader()
    for r in ROWS:
        w.writerow(r)


# ---------------------------------------------------------------- markdown
SHORT = [(SET_SHELL, "print set A (shell)"), (SET_STRONG, "print set B (bracket)"), (SET_LINER, "print set C (lattice pad)"),
         (SET_PETG, "print set D (PETG)")]


def cell(s):
    s = str(s).replace("|", "/")
    for long_, short in SHORT:
        s = s.replace(long_, short)
    if s.startswith("http"):
        return f"[link]({s.split()[0]})" + (" " + " ".join(s.split()[1:]) if len(s.split()) > 1 else "")
    return s


def src(s):
    import re
    return re.sub(r"(https?://[^\s;,)]+)", lambda m: f"[link]({m.group(1)})", str(s).replace("|", "/"))


out = []
P_ = out.append
P_("# Sitka parts list and cost (current design: kinetics-first, render two)")
P_("")
P_("**Generated by `python3 parts_list.py` on 2026-10-22. Do not hand-edit; edit `parts_list.py`.** "
   "The same rows are in [parts.csv](parts.csv). The retired rigid v2 list is in [legacy/](legacy/PARTS_LIST_BOM.md).")
P_("")
P_("Sources of truth: [KINETICS.md](KINETICS.md) (modules, tiers, loads), [TENDON_CONCEPT.md](TENDON_CONCEPT.md) (seat physics), "
   "and the build123d CAD in `cad/` (part names, and every printed and metal mass is the CAD solid volume times a density).")
P_("")
P_("How to read it:")
P_("")
P_("- **PRINT** = 3D-printed on a Bambu X1C / P1S class printer. **METAL** = cut or machined by a job shop. **BUY** = off the shelf, or made from bought stock (glass leaves, line, webbing).")
P_("- **EST** in a mass or cost column means an estimate, not a weighed part or a quote. Prices are USD, seen 2026-10-22 at the linked seller.")
P_("- Printed masses use 1.06 g/cm3 for PAHT-CF and 1.22 g/cm3 for TPU, with a fill factor per part (solid thin shells, 60 to 80% for chunky brackets, 15 to 25% for lattice pads). Printed cost is filament only, plus 15% for waste. Metal cost is a one-off job-shop guess.")
P_("- Prototype one prints the shells in PAHT-CF. The CAD and renders show carbon; a carbon layup (using the print as the plug) is the v2 weight and stiffness upgrade, not needed to prove the physics.")
P_("- Not included: the printer, tools, shipping, tax, your time, the bench rigs and the pressure-mapping liner (see the old `project_cost.mjs` for those).")
P_("")

# --- tiers
P_("## 1. Totals per tier")
P_("")
P_("| Tier | What you get | Mass | Cost, prototype one | of which EST | Cost, batch of 10 sets (EST) | Earlier top-down target (KINETICS.md) |")
P_("|---|---|---|---|---|---|---|")
for name, rows, what, tgt in TIERS:
    m, c, e = tot(rows)
    P_(f"| **{name}** | {what} | **{kg(m)}** | **{usd(c)}** | {usd(e)} | {usd(batch(rows))} | {tgt} |")
P_("")
P_("Batch of 10 = metal parts at 45% of the one-off price (setup spread over 10 sets, EST); everything else unchanged.")
P_("")
P_("## 2. Totals per module")
P_("")
P_("| Module | Tier | Parts | Mass | Cost | of which EST | Printed PAHT-CF | Printed TPU | Print time (EST) |")
P_("|---|---|---|---|---|---|---|---|---|")
PT = {}
for mname in MODULES:
    rows = bym[mname]
    m, c, e = tot(rows)
    pa, tp, pe = pmass(rows, "PAHT"), pmass(rows, "TPU"), pmass(rows, "PETG")
    hrs = pa / GPH["PAHT"] + tp / GPH["TPU"] + pe / GPH["PETG"]
    PT[mname] = (pa, tp, pe, hrs)
    tiers = sorted({r["tier"] for r in rows}, key=lambda t: [B, S, P, F].index(t))
    P_(f"| {mname} | {', '.join(tiers)} | {sum(r['qty'] for r in rows)} | {kg(m)} | {usd(c)} | {usd(e)} | {pa:.0f} g | {tp:.0f} g | {hrs:.0f} h |")
m, c, e = tot(ROWS)
P_(f"| **All modules** | | {sum(r['qty'] for r in ROWS)} | **{kg(m)}** | **{usd(c)}** | {usd(e)} | {pmass(ROWS, 'PAHT'):.0f} g | {pmass(ROWS, 'TPU'):.0f} g | "
   f"{sum(v[3] for v in PT.values()):.0f} h |")
P_("")

TABLES = "\n".join(out)

# --- part tables per module
rows_md = []
for mname in MODULES:
    rows = bym[mname]
    m, c, e = tot(rows)
    rows_md.append(f"### {mname}: {kg(m)}, {usd(c)}")
    rows_md.append("")
    rows_md.append("| Part (plain name) | Technical / CAD | Qty | Make | Material | Process | Mass ea (g) | Unit | Line | Source |")
    rows_md.append("|---|---|---|---|---|---|---|---|---|---|")
    for r in rows:
        me = " EST" if r["mass_est"] else ""
        ce = " EST" if r["cost_est"] else ""
        rows_md.append(f"| {cell(r['name'])} | {cell(r['technical'])} | {r['qty']} | **{r['make']}** | {cell(r['material'])} | {cell(r['process'])} | "
                       f"{r['mass_each_g']:.0f}{me} | ${r['unit_usd']:,.2f}{ce} | ${r['line_usd']:,.2f} | {src(r['source'])} |")
    rows_md.append(f"| **Subtotal** | | | | | | **{kg(m)}** | | **{usd(c)}** | |")
    rows_md.append("")
PART_TABLES = "\n".join(rows_md)

# print time / filament table
ft = ["| Module | PAHT-CF | TPU 95A HF | PETG | Filament cost | Printer hours (EST) | Parts over 256 mm |", "|---|---|---|---|---|---|---|"]
BIG = {"Dock (hub)": "back panel + pad (split or H2D)", "Knee + Seat (M1)": "thigh shells + pads (split or H2D)"}
for mname in MODULES:
    pa, tp, pe, hrs = PT[mname]
    fc = pa * FIL["PAHT"] + tp * FIL["TPU"] + pe * FIL["PETG"]
    if pa + tp + pe == 0:
        continue
    ft.append(f"| {mname} | {pa:.0f} g | {tp:.0f} g | {pe:.0f} g | ${fc:,.0f} | {hrs:.0f} h | {BIG.get(mname, 'none')} |")
tpa, ttp, tpe = pmass(ROWS, "PAHT"), pmass(ROWS, "TPU"), pmass(ROWS, "PETG")
th = sum(v[3] for v in PT.values())
ft.append(f"| **All** | **{tpa:.0f} g** | **{ttp:.0f} g** | {tpe:.0f} g | **${tpa * FIL['PAHT'] + ttp * FIL['TPU'] + tpe * FIL['PETG']:,.0f}** | **{th:.0f} h** | |")
sp = sum(PT[mn][3] for mn in MODULES[:3])
spa = sum(PT[mn][0] for mn in MODULES[:3]); stp = sum(PT[mn][1] for mn in MODULES[:3])
PRINT_TABLE = "\n".join(ft)

# make-type summary
mk = ["| Make | Parts (pieces) | Mass, full body | Cost, full body |", "|---|---|---|---|"]
for t in ("PRINT", "METAL", "BUY"):
    rr = [r for r in ROWS if r["make"] == t]
    mk.append(f"| **{t}** | {sum(r['qty'] for r in rr)} | {kg(sum(r['mass_line_g'] for r in rr))} | {usd(sum(r['line_usd'] for r in rr))} |")
MAKE_TABLE = "\n".join(mk)
mm = ["| Part | Module | Material | Why it must be metal (the load) |", "|---|---|---|---|"]
for r in ROWS:
    if "must be metal" in r["process"] or "metal preferred" in r["process"]:
        why = r["process"].split("must be metal: ")[-1] if "must be metal" in r["process"] else r["process"].split("; ")[-1]
        mm.append(f"| {r['name']} | {r['module']} | {r['material']} | {why} |")
METAL_TABLE = "\n".join(mm)

def bucket(r):
    n = r["name"].lower()
    if r["print_mat"] == "TPU" or "gel sheet" in n or "spacer mesh" in n:
        return "Pads: TPU lattice, gel sheet, spacer mesh"
    if r["print_mat"] == "PAHT":
        return "Printed shells, cups and brackets (PAHT-CF)"
    if r["make"] == "METAL":
        return "Metal: hinges, arcs, arms, clamps, clevises, ports"
    if "strut" in n:
        return "Struts (carbon tube, lock, foot)"
    if any(k in n for k in ("belt", "harness", "webbing", "buckle", "strap", "d-ring")):
        return "Belt, harness, webbing, buckles"
    return "Clutches, cleats, lines, leaves, fasteners"


bk = OrderedDict()
for r in starter:
    bk[bucket(r)] = bk.get(bucket(r), 0) + r["mass_line_g"]
mt = ["| Where the starter's mass is | Mass |", "|---|---|"]
for k_, v_ in sorted(bk.items(), key=lambda kv: -kv[1]):
    mt.append(f"| {k_} | {kg(v_)} |")
MASS_TABLE = "\n".join(mt)
sm_, sc_, se_ = tot(starter)
bm_, bc_, be_ = tot(basic)
TEMPLATE = open(os.path.join(HERE, "docs", "parts_list_template.md")).read()
md = TEMPLATE.format(TABLES=TABLES, MASS_TABLE=MASS_TABLE, METAL_TABLE=METAL_TABLE, PRINT_TABLE=PRINT_TABLE, MAKE_TABLE=MAKE_TABLE, PART_TABLES=PART_TABLES,
                     starter_kg=kg(sm_), starter_usd=usd(sc_), starter_batch=usd(batch(starter)),
                     full_kg=kg(tot(full)[0]), full_usd=usd(tot(full)[1]), full_batch=usd(batch(full)), starter_est=usd(se_), basic_kg=kg(bm_), basic_usd=usd(bc_),
                     starter_print_h=f"{sp:.0f}", starter_paht=f"{spa / 1000:.1f}", starter_tpu=f"{stp / 1000:.1f}",
                     all_print_h=f"{th:.0f}")
open(os.path.join(HERE, "PARTS_LIST.md"), "w").write(md)

# console summary
for name, rows, _, tgt in TIERS:
    m, c, e = tot(rows)
    print(f"{name:45s} {kg(m):>9s} {usd(c):>8s}  (EST {usd(e)})   target {tgt}")
for mname in MODULES:
    m, c, e = tot(bym[mname])
    print(f"   {mname:28s} {kg(m):>9s} {usd(c):>8s}  print {PT[mname][3]:.0f} h")
