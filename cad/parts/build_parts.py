"""Sitka render two: body-contoured parts of the kinetics-first design (KINETICS.md, TENDON_CONCEPT.md).

Every rigid part is built in the anatomical frame of the body segment it rides on (see common.py),
contoured to the MakeHuman wearer (1.874 m / 130 kg) as the max skin surface over all five poses.
Cables, bands and straps that cross a joint are NOT here: they are anchored here (manifest
`anchors`) and routed per pose by assemble.py.

Run:  cad/.venv/bin/python cad/parts/build_parts.py
Out:  cad/step/<part>.step, cad/stl/<printed part>.stl, cad/glb/parts/<part>.glb, cad/build/manifest.json
Units: build123d works in mm; frames and anchors are in metres.
"""
import os, sys, json, math, time
import numpy as np
import build123d as bd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, POSES, A, seg_len, radial, side_s, FR, to_world
from geom import contour_part, skin_grid, point, MM, safe_fillet

OUT = dict(step=os.path.join(ROOT, "step"), stl=os.path.join(ROOT, "stl"),
           glb=os.path.join(ROOT, "glb", "parts"), build=os.path.join(ROOT, "build"))
for d in OUT.values():
    os.makedirs(d, exist_ok=True)

PARTS, ANCH = [], {}
T0 = time.time()


def add(name, shape, seg, module, mat, label=None, printed=False, group=None, note=None):
    print(f"{time.time() - T0:6.1f}s built {name}", flush=True)
    PARTS.append(dict(name=name, shape=shape, seg=seg, module=module, mat=mat, label=label,
                      printed=printed, group=group or name.rsplit("_", 1)[0], note=note))


def skin(seg, z, th, axis_offset=(0, 0), cap=0.03):
    zs, TH = np.array([z], float), np.array([[th]], float)
    return float(skin_grid(seg, zs, TH, cap=cap, axis_offset=axis_offset)[0, 0])


def anchor(key, seg, z, th, off, axis_offset=(0, 0)):
    """a cable/band attachment point: skin + off at (z, theta) in the segment frame (metres)"""
    r = skin(seg, z, th, axis_offset) + off
    p = [v / MM for v in point(seg, z, th, r, axis_offset)]
    ANCH[key] = dict(seg=seg, p=p)
    return p


def anchor_xyz(key, seg, p):
    ANCH[key] = dict(seg=seg, p=[float(v) for v in p])
    return p


def pod(seg, z0, z1, thc, width_mm, off, height, fillet=None, axis_offset=(0, 0), round_p=2.2, min_frac=0.35):
    """a smooth body-hugging pebble (housing) sitting at skin+off, `height` thick at its crown"""
    r = skin(seg, (z0 + z1) / 2, thc, axis_offset) + off
    half = math.degrees((width_mm / 2 / MM) / r)
    zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
    dome = lambda z: height * max(0.3, (1 - abs((z - zc) / hz) ** 2.4)) ** 0.5
    sol, _ = contour_part(seg, z0, z1, lambda z: thc - half, lambda z: thc + half, off, dome,
                          nz=11, nth=9, round_p=round_p, min_frac=min_frac, axis_offset=axis_offset)
    return sol


def at(shape, seg, z, th, r, axis_offset=(0, 0), spin=0.0):
    """place a shape built around the origin (its +Z = outward normal) on the skin at (z, theta, r)"""
    s = side_s(seg)
    t = math.radians(th)
    n = bd.Vector(s * math.sin(t), math.cos(t), 0)
    o = bd.Vector(*point(seg, z, th, r, axis_offset))
    pl = bd.Plane(origin=o, x_dir=(0, 0, 1), z_dir=n)
    return pl * bd.Rot(0, 0, spin) * shape


def boss(d, h, chamfer=0.6):
    c = bd.Cylinder(d / 2, h, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    try:
        c = bd.fillet(c.edges().group_by(bd.Axis.Z)[-1], min(d / 2, h) * 0.45)
    except Exception:
        pass
    return c


def tube_between(p0, p1, d, d_in=None):
    p0, p1 = bd.Vector(*p0), bd.Vector(*p1)
    L = (p1 - p0).length
    pl = bd.Plane(origin=p0, z_dir=(p1 - p0).normalized())
    c = bd.Cylinder(d / 2, L, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    if d_in:
        c = c - bd.Cylinder(d_in / 2, L, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
    return pl * c


def strip(pts_mm, w, t, xdir):
    """sweep a rounded w x t (mm) profile along a spline; the thin side (t) faces xdir"""
    path = bd.Spline(*[bd.Vector(*p) for p in pts_mm])
    tan = path % 0
    xd = bd.Vector(*xdir)
    xd = (xd - tan * xd.dot(tan)).normalized()
    pl = bd.Plane(origin=path @ 0, x_dir=xd, z_dir=tan)
    with bd.BuildSketch(pl) as sk:
        bd.RectangleRounded(t, w, min(t, w) * 0.45)
    return bd.sweep(sk.sketch, path=path)


def oval_sweep(pts_mm, w, t):
    path = bd.Spline(*[bd.Vector(*p) for p in pts_mm])
    pl = bd.Plane(origin=path @ 0, z_dir=path % 0)
    with bd.BuildSketch(pl) as sk:
        bd.Ellipse(w / 2, t / 2)
    return bd.sweep(sk.sketch, path=path)


_TM = {}


def outer_r(name, seg, z, th, axis_offset=(0, 0)):
    """radius (m) of the OUTER surface of an already built part along the ray at (z, theta) of its segment frame,
    so a boss / eyelet / D-ring sits ON the real (smoothed, filleted) surface, not on skin + a nominal offset"""
    import trimesh
    if name not in _TM:
        sh = next(p["shape"] for p in PARTS if p["name"] == name)
        vv, ff = sh.tessellate(0.2, 0.2)
        _TM[name] = trimesh.Trimesh(np.array([tuple(v) for v in vv]), np.array(ff), process=False)
    s = side_s(seg)
    t = math.radians(th)
    o = np.array(point(seg, z, th, 0.0, axis_offset))
    d = np.array([s * math.sin(t), math.cos(t), 0.0])
    loc, ri, _ = _TM[name].ray.intersects_location([o], [d], multiple_hits=True)
    if len(loc) == 0:
        raise ValueError(f"outer_r: ray misses {name} at z={z} th={th}")
    return float(np.max(np.linalg.norm(loc - o, axis=1))) / MM


def sitbone(sd):
    """the skin under the sit bone (ischial tuberosity) in the seated (chair) pose: the lowest skin point 65 mm off the
    midline (sit bones ~13 cm apart, TENDON_CONCEPT section 2). Returns the thigh-frame z, theta, skin radius and the
    world point. Measured on the wearer mesh, so the hinge follows the body if the body changes."""
    from common import mesh
    V = mesh("chair").vertices
    hl, hr = A("chair", "thigh_l")[:3, 3], A("chair", "thigh_r")[:3, 3]
    mid = (hl + hr) / 2
    s = 1.0 if sd == "l" else -1.0
    sel = ((np.abs(V[:, 0] - (mid[0] + s * 0.065)) < 0.012) & (V[:, 1] > mid[1] - 0.05) & (V[:, 1] < mid[1] + 0.10)
           & (V[:, 2] < mid[2] - 0.04))
    P = V[sel]
    p = P[np.argmin(P[:, 2])]
    q = np.linalg.inv(A("chair", "thigh_" + sd)) @ np.r_[p, 1.0]
    S = side_s("thigh_" + sd)
    return float(q[2]), float(math.degrees(math.atan2(S * q[0], q[1]))), float(math.hypot(q[0], q[1])), p


# =====================================================================================
# LEGS
# =====================================================================================
for sd in ("l", "r"):
    S = side_s("thigh_" + sd)
    TH_, SH_, KN_ = "thigh_" + sd, "shin_" + sd, "knee_" + sd
    LT = seg_len(TH_)                       # hip -> knee axis, ~0.476 m
    # knee axis half-widths (hub planes): max over thigh, shin and knee frames, every pose
    def patch_max(th):
        zs = np.linspace(-0.026, 0.026, 7)
        TH = np.array([[th + d for d in range(-24, 25, 6)] for _ in zs], float)
        return float(skin_grid(KN_, zs, TH).max())
    r_lat = max(skin(TH_, LT - 0.005, 90), skin(SH_, 0.005, 90), patch_max(90))
    r_med = max(skin(TH_, LT - 0.005, -90), skin(SH_, 0.005, -90), patch_max(-90))
    x_lat, x_med = r_lat + 0.009, r_med + 0.009          # 7 mm condyle pad + 2 mm gap
    ANCH["knee_x_" + sd] = dict(lat=x_lat, med=x_med)

    # ---------------- thigh ----------------
    # top edge slants: high on the lateral side, low at the front/inside where the hip folds when seated
    lo_sh = lambda z: float(np.interp(z, [0.11, 0.19, 0.27, 0.385], [30, -45, -100, -108]))
    hi_sh = lambda z: 128 - 6 * (z - 0.11) / 0.275
    shell, _ = contour_part(TH_, 0.11, 0.385, lo_sh, hi_sh, 0.011, 0.003, nz=18, round_p=3.5, min_frac=0.6)
    add("thigh_shell_" + sd, shell, TH_, "basic", "carbon", "Thigh shell (carbon, laced)", group="thigh_shell")
    sleeve, _ = contour_part(TH_, 0.106, 0.389, lambda z: lo_sh(z) - 3, lambda z: hi_sh(z) + 3, 0.0012, 0.0092,
                             nz=18, nth=19, round_p=3.5, min_frac=0.6)
    add("thigh_liner_" + sd, sleeve, TH_, "basic", "foam", "Spacer mesh + TPU lattice liner", printed=True, group="liner")
    cuff, _ = contour_part(TH_, 0.190, 0.335, lambda z: 132, lambda z: 236, 0.011, 0.003, fillet=0.0012, round_p=3, min_frac=0.6)
    add("thigh_cuff_" + sd, cuff, TH_, "basic", "carbon", "Posterior thigh cuff (lift anchor, 200 cm2)", group="thigh_cuff")
    cl, _ = contour_part(TH_, 0.186, 0.339, lambda z: 129, lambda z: 239, 0.0012, 0.0092, round_p=3, min_frac=0.6)
    add("thigh_cuff_liner_" + sd, cl, TH_, "basic", "foam", None, printed=True, group="liner")

    # closure straps (webbing over the liner, across shell + cuff)
    def strap_off(z, t, lo=lo_sh, hi=hi_sh):
        # on a pad: ride over shell/cuff; across a gap: lie on the skin. Smooth 8 deg ramps.
        tt = ((t + 180) % 360) - 180
        pads = [(lo(z), hi(z)), (132, 236), (132 - 360, 236 - 360)]
        dmin = min(max(a - tt, tt - b, 0) for a, b in pads)
        k = min(1.0, dmin / 8.0)
        return 0.0142 * (1 - k) + 0.0025 * k
    for k, zc in enumerate((0.245, 0.315)):
        st, _ = contour_part(TH_, zc - 0.019, zc + 0.019, lambda z: 100, lambda z: 438, strap_off, 0.0018,
                             nz=5, nth=61, round_p=8, min_frac=0.98)
        add(f"thigh_strap{k}_" + sd, st, TH_, "basic", "fabric", "Thigh strap" if k == 0 else None, group="strap")
        buckle = pod(TH_, zc - 0.022, zc + 0.022, 92, 30, 0.0158, 0.005, fillet=0.0018)
        add(f"thigh_buckle{k}_" + sd, buckle, TH_, "basic", "alu", None, printed=False, group="buckle")

    # medial / lateral hinge arms (thigh side): carbon strip from the shell down to the hub
    for nm, th, xh in (("lat", 90, x_lat), ("med", -90, x_med)):
        r0 = skin(TH_, 0.30, th) + 0.0142 + 0.002
        r1 = skin(TH_, 0.385, th) + 0.0142 + 0.002
        xa = xh + 0.002
        pts = [(S * math.copysign(1, th) * r0 * MM, 0, 0.30 * MM),
               (S * math.copysign(1, th) * r1 * MM, 0, 0.385 * MM),
               (S * math.copysign(1, th) * (0.5 * r1 + 0.5 * xa) * MM, 0, (LT - 0.045) * MM),
               (S * math.copysign(1, th) * xa * MM, 0, (LT - 0.012) * MM),
               (S * math.copysign(1, th) * xa * MM, 0, LT * MM)]
        arm = strip(pts, 24, 4, (S * math.copysign(1, th), 0, 0))
        disc = bd.Plane(origin=(S * math.copysign(1, th) * xa * MM, 0, LT * MM), z_dir=(1, 0, 0)) * \
            bd.Cylinder(15, 4, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        add(f"thigh_arm_{nm}_" + sd, arm + disc, TH_, "basic", "carbon",
            "Hinge arm (thigh side)" if nm == "lat" else None, group="hinge_arm")

    # M1 cam clutch manifold (sprag spool + WALK / SIT-LIFT / FREE lever), on the front of the thigh
    man = pod(TH_, 0.200, 0.292, 14, 44, 0.0142, 0.019, fillet=0.0075)
    add("knee_manifold_" + sd, man, TH_, "basic", "carbon_gloss", "M1 cam clutch (locks with power off) + mode lever",
        printed=True, group="manifold")
    sk = lambda z, t: skin(TH_, z, t) + 0.0142
    lev_pts = [point(TH_, 0.212, 34, sk(0.212, 34) + 0.012), point(TH_, 0.220, 26, sk(0.22, 26) + 0.016),
               point(TH_, 0.236, 22, sk(0.236, 22) + 0.020)]
    lever = oval_sweep(lev_pts, 9, 4.5)
    lever += at(boss(11, 6), TH_, 0.212, 34, sk(0.212, 34) + 0.005)
    add("mode_lever_" + sd, lever, TH_, "basic", "accent", "Mode lever WALK / SIT-LIFT / FREE", group="lever")
    anchor("t1_manifold_" + sd, TH_, 0.293, 14, 0.0142 + 0.010)
    fair = pod(TH_, 0.348, 0.376, 6, 18, 0.0142, 0.017, fillet=0.003)
    add("tendon_fairlead_" + sd, fair, TH_, "basic", "alu", None, group="fairlead")
    anchor("t1_fairlead_" + sd, TH_, 0.366, 6, 0.0142 + 0.019)

    # sit leaf spring (T1a): tapered glass/carbon blade on the front-lateral thigh, bowed off the shell
    leaf_off = lambda z: 0.0150 + 0.020 * ((z - 0.150) / 0.125) ** 1.6
    rl = skin(TH_, 0.2, 52)
    wdeg = lambda w: math.degrees(w / rl)
    leaf, _ = contour_part(TH_, 0.150, 0.275, lambda z: 52 - wdeg(0.016 - 0.0055 * (z - 0.15) / 0.125),
                           lambda z: 52 + wdeg(0.016 - 0.0055 * (z - 0.15) / 0.125), leaf_off, 0.0042,
                           nz=12, nth=7, round_p=6, min_frac=0.8, fillet=0.0015)
    add("sit_leaf_" + sd, leaf, TH_, "basic", "leaf", "Sit leaf spring 350 N (stores 44 J)", group="sit_leaf")
    clamp = pod(TH_, 0.140, 0.168, 52, 40, 0.0142, 0.013, fillet=0.0045)
    add("sit_leaf_root_" + sd, clamp, TH_, "basic", "alu", None, group="leaf_clamp")
    # short link cable leaf tip -> manifold spool (static on the thigh)
    tip = point(TH_, 0.270, 52, skin(TH_, 0.27, 52) + leaf_off(0.27) + 0.004)
    spool = point(TH_, 0.262, 26, skin(TH_, 0.262, 26) + 0.0142 + 0.016)
    mid = [(a + b) / 2 for a, b in zip(tip, spool)]
    mid = point(TH_, 0.268, 40, skin(TH_, 0.268, 40) + 0.034)
    add("sit_leaf_link_" + sd, oval_sweep([tip, mid, spool], 2.6, 2.6), TH_, "basic", "cable", None, group="cable_static")

    # electroadhesive stance clutch (smart tier): flat 26 g element on the shell
    ea = pod(TH_, 0.300, 0.342, 30, 30, 0.0142, 0.0065, fillet=0.0025)
    add("ea_clutch_" + sd, ea, TH_, "upgrade", "electronics", "Electroadhesive stance clutch (fails open)", group="ea")

    # seat cup under the sit bone, foam lined (TENDON_CONCEPT section 2, SEAT_SITBONE.md). Centred on the sit bone as far
    # as the midline allows: shifted back along the thigh and in toward the midline, the medial edge kept clear of the
    # other cup (connection gate CLEAR >= 3 mm in every frame)
    # the back (proximal) end lifts off by up to 10 mm: the hip flexes the buttock up into it when walking and stooping
    cup_lo, cup_hi = (lambda z: 140), (lambda z: 216)
    cup_off = lambda z: 0.016 + 0.010 * min(1.0, max(0.0, (-0.012 - z) / 0.038))
    cup, _ = contour_part(TH_, -0.050, 0.140, cup_lo, cup_hi, cup_off, 0.0035, fillet=0.0015, round_p=2.6, min_frac=0.55)
    add("seat_cup_" + sd, cup, TH_, "basic", "carbon", "Seat cup under the sit bone (400 cm2)", group="seat_cup")
    cupl, _ = contour_part(TH_, -0.054, 0.144, lambda z: 137, lambda z: 219, lambda z: cup_off(z) - 0.0148, 0.0140,
                           round_p=2.6, min_frac=0.55)
    add("seat_cup_liner_" + sd, cupl, TH_, "basic", "foam", "Gel + TPU lattice cup liner (15 kPa)", printed=True, group="liner")

    # ---- strut hinge straight under the sit bone (SEAT_SITBONE.md): fork + pin on the cup, rod-end eye on the tube
    # the pin goes straight below the sit bone in the seated pose: from the skin point under the ischial tuberosity, down
    # (world vertical, chair pose) through the cup to its outer surface, then PIN_H further
    z_h, th_h, _, it_w = sitbone(sd)
    Ac = A("chair", TH_)
    it_l = (np.linalg.inv(Ac) @ np.r_[it_w, 1.0])[:3]
    down_l = Ac[:3, :3].T @ np.array([0.0, 0.0, -1.0])
    outer_r("seat_cup_" + sd, TH_, z_h, th_h)                     # (tessellates the cup into _TM)
    hits, _, _ = _TM["seat_cup_" + sd].ray.intersects_location([it_l * MM], [down_l], multiple_hits=True)
    cup_pt = hits[np.argmax((hits - it_l * MM) @ down_l)] / MM      # outer surface of the cup under the sit bone
    PIN_H = 0.014                                           # pin centre below the cup (rod-end eye r 12.4 mm clears it)
    pin_l = cup_pt + down_l * PIN_H
    z_h, th_h = float(cup_pt[2]), float(math.degrees(math.atan2(S * cup_pt[0], cup_pt[1])))
    ANCH["strut_pin_" + sd] = dict(seg=TH_, p=[float(v) for v in pin_l])
    ANCH["sitbone_" + sd] = dict(seg=TH_, p=[float(v) for v in it_l])
    # stowed line: from the pin down the back-outside of the thigh, lifted just enough to clear cup, lacing and cuff
    # down the back of the thigh, toward the outside. A straight tube from a pin under the sit bone cannot hug the outer
    # thigh (the chord would cut through it). The 5-section strut is 0.28 m stowed, so it ends above the calf's reach
    stow_z, stow_th = 0.26, 165.0
    def line_clear(r1):
        p1 = np.array(point(TH_, stow_z, stow_th, r1)) / MM
        worst = 9.0
        Ltot = np.linalg.norm(p1 - pin_l)
        for t in np.linspace(0.06 / Ltot, 1.0, 40):         # from 60 mm down the tube (the eye end is the hinge)
            q = pin_l + (p1 - pin_l) * t
            zq, thq, rq = q[2], math.degrees(math.atan2(S * q[0], q[1])), math.hypot(q[0], q[1])
            top = 0.0225 if zq < 0.13 else (0.024 if zq < 0.19 else 0.0195)   # cup + grommets, lacing, cuff + strap
            worst = min(worst, rq - (skin(TH_, zq, thq) + top + 0.002 + 0.012))
        return worst, p1
    r1 = skin(TH_, stow_z, stow_th) + 0.025
    while line_clear(r1)[0] < 0 and r1 < skin(TH_, stow_z, stow_th) + 0.07:
        r1 += 0.001
    print(f"stow line {sd}: bottom end {1000 * (r1 - skin(TH_, stow_z, stow_th)):.0f} mm off the skin, clearance {1000 * line_clear(r1)[0]:.1f} mm")
    stow_p = line_clear(r1)[1]
    ANCH["strut_stow_" + sd] = dict(seg=TH_, p=[float(v) for v in stow_p])
    d_stow = (stow_p - pin_l) / np.linalg.norm(stow_p - pin_l)
    # deployed (chair) direction in the thigh frame: foot 4 deg back, 9 deg out (assemble.strut_foot)
    Ac = A("chair", TH_)
    pw = Ac[:3, :3] @ pin_l + Ac[:3, 3]
    hh = pw[2] - 0.016 * 1.25
    fw = np.array([pw[0] + S * math.tan(math.radians(9)) * hh, pw[1] + math.tan(math.radians(4)) * hh, 0.016 * 1.25])
    d_dep = Ac[:3, :3].T @ ((fw - pw) / np.linalg.norm(fw - pw))
    pax = np.cross(d_stow, d_dep); pax /= np.linalg.norm(pax)       # pin axis: normal of the fold plane
    ANCH["strut_axis_" + sd] = dict(seg=TH_, axis=[float(v) for v in pax])
    nrm = -down_l - pax * (-down_l @ pax); nrm /= np.linalg.norm(nrm)        # cheeks stand along the seated vertical
    bvec = np.cross(pax, nrm)
    def slab(c, ax, n, b, ln, lb, la):
        pl = bd.Plane(origin=tuple(c * MM), x_dir=tuple(n), z_dir=tuple(ax))
        return pl * bd.Box(ln * MM, lb * MM, la * MM)
    CHEEK_IN, CHEEK_T = 0.010, 0.005                         # rod-end ball +-6 mm, cone spacers 4 mm, cheek 5 mm
    n_lo, n_hi = -0.012, PIN_H + 0.004                      # cheek from 12 mm past the pin (down) to 4 mm into the cup
    fork = pod(TH_, z_h - 0.024, z_h + 0.024, th_h, 46, outer_r("seat_cup_" + sd, TH_, z_h, th_h) - skin(TH_, z_h, th_h) - 0.0008,
               0.005, fillet=0.002)
    for sg in (-1, 1):
        cc = pin_l + pax * sg * (CHEEK_IN + CHEEK_T / 2) + nrm * (n_lo + n_hi) / 2
        fork += slab(cc, pax, nrm, bvec, n_hi - n_lo, 0.026, CHEEK_T)
    add("strut_fork_" + sd, fork, TH_, "basic", "alu", "Strut hinge: fork + pin under the sit bone", group="clevis")
    pinp = bd.Plane(origin=tuple(pin_l * MM), z_dir=tuple(pax)) * bd.Cylinder(4.0, 2 * (CHEEK_IN + CHEEK_T) * MM + 3,
                                                                                align=(bd.Align.CENTER,) * 3)
    for sg in (-1, 1):   # cone spacers: centre the ball, leave the eye room to tilt (high-misalignment rod end)
        pinp += bd.Plane(origin=tuple((pin_l + pax * sg * (0.006 + CHEEK_IN) / 2) * MM), z_dir=tuple(pax)) * \
            bd.Cylinder(6.0, (CHEEK_IN - 0.006) * MM + 1.0, align=(bd.Align.CENTER,) * 3)
    add("strut_hingepin_" + sd, pinp, TH_, "basic", "alu", None, group="clevis")
    # stow clips at both ends of the stowed tube: C-saddles hugging tube0 (r 12 mm), each on a post to the part below
    def stow_clip(s_t, base, ring_r, name, lab):
        """C-saddle around the stowed tube s_t metres down from the pin (ring_r = that section's outer radius), on a post
        down to the part below it"""
        c = pin_l + d_stow * s_t
        zq, thq = c[2], math.degrees(math.atan2(S * c[0], c[1]))
        nq = np.array([S * math.sin(math.radians(thq)), math.cos(math.radians(thq)), 0.0])
        nq = nq - d_stow * (nq @ d_stow); nq /= np.linalg.norm(nq)
        b0 = np.array(point(TH_, zq, thq, outer_r(base, TH_, zq, thq) - 0.0008)) / MM
        ring = bd.Plane(origin=tuple(c * MM), z_dir=tuple(d_stow)) * (
            bd.Cylinder(ring_r * MM + 3.5, 16, align=(bd.Align.CENTER,) * 3) - bd.Cylinder(ring_r * MM, 18, align=(bd.Align.CENTER,) * 3))
        cut = bd.Plane(origin=tuple((c + nq * (ring_r + 0.004)) * MM), x_dir=tuple(nq), z_dir=tuple(d_stow)) * \
            bd.Box(20, ring_r * MM * 1.4, 20)
        post = tube_between(tuple(b0 * MM), tuple((c - nq * (ring_r + 0.0005)) * MM), 10)
        add(name, (ring - cut) + post, TH_, "basic", "alu", lab, group="clip")
    stow_clip(0.075, "seat_cup_" + sd, 0.012, "strut_clip_hi_" + sd, "Strut stow clip (top)" if sd == "l" else None)
    stow_clip(0.252, "thigh_cuff_" + sd, 0.0075, "strut_clip_" + sd, "Strut stow clip (bottom)" if sd == "l" else None)

    # ---- laced bridge: cup lower edge to the posterior thigh cuff (3 + 4 grommets, 3 mm cord, zigzag), and a
    # webbing tab from the cup's outer edge to the thigh shell. The cup is held by the thigh shell, not by a belt strap
    CUP_OUT, CUFF_OUT, SHELL_OUT = "seat_cup_" + sd, "thigh_cuff_" + sd, "thigh_shell_" + sd
    gro = lambda zz, tt, base: at(boss(9, 3.5), TH_, zz, tt, outer_r(base, TH_, zz, tt) - 0.0006)
    top = lambda zz, tt, base: np.array(point(TH_, zz, tt, outer_r(base, TH_, zz, tt) + 0.0024)) / MM
    ey_cup = [(0.118, t) for t in (166, 182, 198)]
    ey_cuff = [(0.205, t) for t in (158, 174, 190, 206)]
    g_cup = gro(0.085, 154, CUP_OUT)
    for zz, tt in ey_cup:
        g_cup += gro(zz, tt, CUP_OUT)
    add("cup_eyelets_" + sd, g_cup, TH_, "basic", "alu", None, group="eyelet")
    g_cuff = None
    for zz, tt in ey_cuff:
        g = gro(zz, tt, CUFF_OUT); g_cuff = g if g_cuff is None else g_cuff + g
    add("cuff_eyelets_" + sd, g_cuff, TH_, "basic", "alu", None, group="eyelet")
    add("shell_eyelets_" + sd, gro(0.190, 117, SHELL_OUT), TH_, "basic", "alu", None, group="eyelet")
    zig = [top(*ey_cuff[0], CUFF_OUT), top(*ey_cup[0], CUP_OUT), top(*ey_cuff[1], CUFF_OUT), top(*ey_cup[1], CUP_OUT),
           top(*ey_cuff[2], CUFF_OUT), top(*ey_cup[2], CUP_OUT), top(*ey_cuff[3], CUFF_OUT)]
    lace = None
    for a_, b_ in zip(zig[:-1], zig[1:]):
        seg_ = tube_between(tuple(a_ * MM), tuple(b_ * MM), 3.0)
        lace = seg_ if lace is None else lace + seg_
    for q in zig:
        lace += bd.Pos(*(q * MM)) * bd.Sphere(1.5)
    add("cup_lacing_" + sd, lace, TH_, "basic", "fabric", "Laced bridge: seat cup to thigh cuff" if sd == "l" else None, group="lacing")
    ta, tb = top(0.085, 154, CUP_OUT), top(0.190, 117, SHELL_OUT)
    tm = np.array(point(TH_, 0.138, 134, max(skin(TH_, 0.138, 134) + 0.017, (math.hypot(*ta[:2]) + math.hypot(*tb[:2])) / 2))) / MM
    nm_ = np.array([S * math.sin(math.radians(134)), math.cos(math.radians(134)), 0.0])
    add("cup_bridge_" + sd, strip([tuple(ta * MM), tuple(tm * MM), tuple(tb * MM)], 18, 2.0, tuple(nm_)), TH_, "basic", "fabric",
        "Webbing tab: seat cup to thigh shell" if sd == "l" else None, group="lacing")

    # cable / band anchors on the thigh
    anchor("t3_cuff_" + sd, TH_, 0.222, 180, 0.0142 + 0.004)        # lift tendon -> posterior cuff top
    anchor("m3_thigh_" + sd, TH_, 0.150, 12, 0.0142 + 0.003)        # hip-flexor band -> shell front top
    anchor_xyz("cc_thigh_" + sd, TH_, np.array(point(TH_, 0.348, 74, outer_r("thigh_shell_" + sd, TH_, 0.348, 74) + 0.003)) / MM)
    anchor_xyz("ham_cup_" + sd, TH_, np.array(point(TH_, 0.090, 160, outer_r("seat_cup_" + sd, TH_, 0.090, 160) + 0.003)) / MM)
    anchor_xyz("calfband_thigh_" + sd, TH_, np.array(point(TH_, 0.272, 145, outer_r("thigh_cuff_" + sd, TH_, 0.272, 145) + 0.003)) / MM)
    bstop = at(boss(11, 13), TH_, 0.214, 22, skin(TH_, 0.214, 22) + 0.0142 - 0.001)
    add("bowden_stop_" + sd, bstop, TH_, "upgrade", "alu", None, group="anchor")
    anchor("bowden_thigh_" + sd, TH_, 0.214, 22, 0.0142 + 0.010)    # Bowden end stop on the clutch manifold
    anchor("bowden_hip_" + sd, TH_, 0.080, 100, 0.012)
    for nm, zz, tt, base in (("dring_cc", 0.348, 74, "thigh_shell_"), ("dring_m3", 0.150, 12, "thigh_shell_"),
                             ("dring_t3", 0.222, 180, "thigh_cuff_")):
        dr = at(boss(12, 5), TH_, zz, tt, outer_r(base + sd, TH_, zz, tt) - 0.0006)
        add(f"{nm}_{sd}", dr, TH_, "basic", "alu", None, group="dring")
    dr = at(boss(12, 5), TH_, 0.090, 160, outer_r("seat_cup_" + sd, TH_, 0.090, 160) - 0.0006)
    add("dring_ham_" + sd, dr, TH_, "coupling", "alu", None, group="dring")
    dr = at(boss(12, 5), TH_, 0.272, 145, outer_r("thigh_cuff_" + sd, TH_, 0.272, 145) - 0.0006)
    add("dring_calf_" + sd, dr, TH_, "coupling", "alu", None, group="dring")

    # ---------------- knee (centre plate turns at half the knee angle) ----------------
    for nm, xh in (("lat", x_lat), ("med", x_med)):
        sx = S * (1 if nm == "lat" else -1)
        thp = 90 if nm == "lat" else -90
        pad, _ = contour_part(KN_, -0.024, 0.024, lambda z, t=thp: t - 20, lambda z, t=thp: t + 20, 0.0008, 0.0062,
                              nz=7, nth=9, round_p=2.2, min_frac=0.4)
        inner = bd.Plane(origin=(sx * (xh - 0.0015) * MM, 0, 0), z_dir=(sx, 0, 0)) * \
            bd.Cylinder(19, 3, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        cap = bd.Plane(origin=(sx * (xh + 0.0105) * MM, 0, 0), z_dir=(sx, 0, 0)) * \
            bd.Cylinder(21, 5, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        cap = safe_fillet(cap, 2.0)
        # the condyle pad's foam fills the gap up to the hub's inner disc, so the hinge holds the pad, not the skin
        bb = pad.bounding_box()
        x_pad = (bb.max.X if sx > 0 else -bb.min.X) / MM - 0.003
        x_hub = xh - 0.0025
        hub = inner + cap
        if x_hub - x_pad > 0.0005:
            pad += bd.Plane(origin=(sx * (x_pad + x_hub) / 2 * MM, 0, 0), z_dir=(sx, 0, 0)) * \
                bd.Cylinder(16, (x_hub - x_pad) * MM, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        add(f"knee_hub_{nm}_" + sd, hub, KN_, "basic", "alu",
            "Geared bicentric knee hinge" if nm == "lat" else None, group="hub")
        add(f"condyle_pad_{nm}_" + sd, pad, KN_, "basic", "foam", None, group="liner")
    # 80 mm grooved arc ("artificial kneecap"), +-55 deg about the bisector, groove bottom at r = 80.7 mm
    with bd.BuildSketch(bd.Plane.XY) as prof:
        with bd.Locations((0, 79.5)):
            bd.RectangleRounded(20, 7.5, 2.5)
        with bd.Locations((0, 83.0)):
            bd.Circle(3.0, mode=bd.Mode.SUBTRACT)
    # asymmetric sector -33..+60 deg about the bisector: the free space in front of the knee (measured
    # on the wearer in every pose) and the wrap the chair pose needs
    arc = bd.revolve(prof.sketch, axis=bd.Axis.X, revolution_arc=93)
    arc = bd.Rot(-33, 0, 0) * arc
    add("knee_arc_" + sd, arc, KN_, "basic", "alu", "80 mm grooved arc (artificial kneecap)", group="arc")
    ANCH["arc_" + sd] = dict(seg=KN_, r=0.0816, lo=-33, hi=60)
    # yoke: carbon horseshoe from both hubs around the front, fused to the arc
    yk = []
    for k in range(0, 21):
        ph = math.radians(-90 + 9 * k)
        ax = x_lat + 0.004 if ph > 0 else x_med + 0.004
        yk.append((S * ax * math.sin(ph) * MM, 0.0745 * math.cos(ph) * MM if abs(ph) > 1e-6 else 74.5, 0))
    yoke = oval_sweep(yk, 12, 6)
    add("knee_yoke_" + sd, yoke, KN_, "basic", "carbon", None, group="yoke")
    # hamstring / calf band guide pulleys, 40 mm behind the axis on the lateral hub
    gd = bd.Plane(origin=(S * (x_lat + 0.012) * MM, -40, 0), z_dir=(S, 0, 0)) * \
        bd.Cylinder(8, 7, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
    gd += strip([(S * (x_lat + 0.012) * MM, -6, 0), (S * (x_lat + 0.012) * MM, -36, 0)], 9, 4, (S, 0, 0))
    add("knee_guide_" + sd, gd, KN_, "coupling", "alu", "Hamstring/calf band guide (40 mm behind the axis)", group="guide")
    anchor_xyz("knee_guide_" + sd, KN_, (S * (x_lat + 0.012), -0.040 - 0.009, 0.0))

    # ---------------- shin ----------------
    ssl, _ = contour_part(SH_, 0.036, 0.169, lambda z: -104, lambda z: 104, 0.0012, 0.0076,
                          round_p=2.8, min_frac=0.55)
    add("shin_liner_" + sd, ssl, SH_, "basic", "foam", None, printed=True, group="liner")
    csl, _ = contour_part(SH_, 0.211, 0.339, lambda z: 96, lambda z: 264, 0.0012, 0.0076, round_p=3, min_frac=0.6)
    add("calf_liner_" + sd, csl, SH_, "basic", "foam", None, printed=True, group="liner")
    # the PTB pad and the calf pad run under the hinge arms (arms at +-97 deg): the arms carry them
    ptb, _ = contour_part(SH_, 0.040, 0.165, lambda z: -101, lambda z: 101, 0.0094, 0.003, fillet=0.0012, round_p=2.8, min_frac=0.55)
    add("ptb_shell_" + sd, ptb, SH_, "basic", "carbon", "Below-kneecap pad (PTB, 100 cm2, 14 kPa)", group="ptb")
    calf, _ = contour_part(SH_, 0.215, 0.335, lambda z: 99, lambda z: 261, 0.0094, 0.003, fillet=0.0012, round_p=3, min_frac=0.6)
    add("calf_cuff_" + sd, calf, SH_, "basic", "carbon", "Calf pad (120 cm2)", group="calf")
    for nm, th, xh in (("lat", 97, x_lat), ("med", -97, x_med)):
        sg = S * math.copysign(1, th)
        xa = xh + 0.006
        pts = [(sg * xa * MM, 0, 0), (sg * xa * MM, 0, 0.012 * MM)]
        for z in (0.06, 0.13, 0.20, 0.275):
            r = skin(SH_, z, th) + 0.0124 + 0.002
            t = math.radians(abs(th))
            pts.append((sg * r * math.sin(t) * MM, r * math.cos(t) * MM, z * MM))
        arm = strip(pts, 24, 4, (sg, 0, 0))
        disc = bd.Plane(origin=(sg * xa * MM, 0, 0), z_dir=(1, 0, 0)) * \
            bd.Cylinder(15, 4, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER))
        add(f"shin_arm_{nm}_" + sd, arm + disc, SH_, "basic", "carbon", None, group="hinge_arm")
    def shin_off(z, t):
        tt = ((t + 180) % 360) - 180
        pads = [(-101, 101), (99, 261), (99 - 360, 261 - 360)] if 0.215 <= z <= 0.335 else [(-101, 101)]
        if not (0.04 <= z <= 0.165):
            pads = [p for p in pads if p != (-101, 101)]
        dmin = min([max(a - tt, tt - b, 0) for a, b in pads] or [99])
        k = min(1.0, dmin / 8.0)
        return 0.0124 * (1 - k) + 0.0025 * k
    for k, (zc, a, b) in enumerate(((0.150, 80, 280), (0.290, -118, 118))):
        st, _ = contour_part(SH_, zc - 0.017, zc + 0.017, (lambda z, a=a: a), (lambda z, b=b: b), shin_off, 0.0018,
                             nz=5, nth=41, round_p=8, min_frac=0.98)
        add(f"shin_strap{k}_" + sd, st, SH_, "basic", "fabric", None, group="strap")
    anc = at(boss(14, 7), SH_, 0.105, 0, skin(SH_, 0.105, 0) + 0.0124)
    add("shin_anchor_" + sd, anc, SH_, "basic", "alu", "Tendon anchor (below kneecap)", group="anchor")
    anchor("t1_shin_" + sd, SH_, 0.105, 0, 0.0124 + 0.008)
    anchor("ham_calf_" + sd, SH_, 0.250, 124, 0.0124 + 0.005)
    rb = at(boss(12, 6), SH_, 0.290, 255, outer_r("calf_cuff_" + sd, SH_, 0.290, 255) - 0.0006)
    add("runband_clip_" + sd, rb, SH_, "basic", "alu", None, group="clip")
    anchor_xyz("runband_" + sd, SH_, np.array(point(SH_, 0.290, 255, outer_r("calf_cuff_" + sd, SH_, 0.290, 255) + 0.004)) / MM)
    for nm, zz, tt in (("dring_ham_calf", 0.250, 124),):
        add(f"{nm}_{sd}", at(boss(11, 5), SH_, zz, tt, skin(SH_, zz, tt) + 0.0124), SH_, "coupling", "alu", None, group="dring")

    # ---------------- M4 ankle clutch-spring (upgrade) ----------------
    m4c = pod(SH_, 0.300, 0.350, 180, 34, 0.0124, 0.012, fillet=0.004)
    add("m4_clutch_" + sd, m4c, SH_, "upgrade", "carbon_gloss", "M4 ankle clutch (Collins type, no power)", group="m4")
    m4l, _ = contour_part(SH_, 0.345, 0.405, lambda z: 180 - 10, lambda z: 180 + 10,
                          lambda z: 0.014 + 0.012 * (z - 0.345) / 0.06, 0.0035, nz=7, nth=5, round_p=6, min_frac=0.8,
                          fillet=0.0012)
    add("m4_spring_" + sd, m4l, SH_, "upgrade", "leaf", "M4 calf spring leaf", group="m4")
    anchor("m4_spring_" + sd, SH_, 0.404, 180, 0.014 + 0.012 + 0.004)

    # ---------------- shoe (reference footwear, not part of Sitka) + M4 heel clip ----------------
    import trimesh
    d = np.load(os.path.join(ROOT, "body", "stand_weights.npz"))
    V, dom = d["V"], d["dom"]
    fb = [f"foot_{sd}", f"ball_{sd}"] + [n for n in set(dom) if n.endswith("_" + sd) and n.startswith(("toe", "big"))]
    sel = np.isin(dom, fb)
    ank = np.array(FR["stand"]["bones"][f"foot_{sd}"]["head"])
    P = V[sel]
    P = P[P[:, 2] < ank[2] - 0.010]
    c = P.mean(0)
    hull0 = trimesh.convex.convex_hull(P)
    # grow 5 mm, add a flat 22 mm sole to the floor
    Pn = P + 0.005 * (P - np.array([c[0], c[1], P[:, 2].min()])) / np.linalg.norm(
        P - np.array([c[0], c[1], P[:, 2].min()]), axis=1)[:, None]
    low = P[P[:, 2] < P[:, 2].min() + 0.03].copy()
    low_out = low + 0.006 * np.c_[np.sign(low[:, 0] - c[0]), np.sign(low[:, 1] - c[1]), 0 * low[:, 0]]
    sole = low_out.copy(); sole[:, 2] = 0.0
    hull = trimesh.convex.convex_hull(np.vstack([Pn, sole, low_out]))
    hull = hull.subdivide().subdivide()
    Aw = A("stand", "foot_" + sd)
    Ai = np.linalg.inv(Aw)
    hull.apply_transform(Ai)
    hy = hull.copy()
    hy.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1.0]]))  # glTF is y-up
    hy.export(os.path.join(OUT["glb"], f"shoe_{sd}.glb"))
    PARTS.append(dict(name="shoe_" + sd, shape=None, seg="foot_" + sd, module="body", mat="shoe", label=None,
                      printed=False, group="shoe", note="reference shoe"))
    # heel clip: a band around the heel counter, 30-62 mm above the floor
    Hw = hull.copy(); Hw.apply_transform(Aw)
    ring = []
    yb = Hw.vertices[:, 1].max()
    for zz in (0.046,):
        sec = Hw.section(plane_origin=(0, 0, zz), plane_normal=(0, 0, 1))
        pts2 = np.array(sec.discrete[0]) if sec is not None else None
    back = pts2[pts2[:, 1] > yb - 0.075]
    cx = np.mean(back[:, 0])
    ang = np.degrees(np.arctan2(back[:, 0] - cx, back[:, 1] - (yb - 0.075)))
    order = np.argsort(ang)
    back = back[order]
    sel_idx = np.linspace(0, len(back) - 1, 9).astype(int)
    hp = []
    for q in back[sel_idx]:
        v = np.array([q[0] - cx, q[1] - (yb - 0.075), 0]); v /= np.linalg.norm(v)
        hp.append(q + v * 0.004)
    hp_l = (np.array(hp) @ Ai[:3, :3].T + Ai[:3, 3]) * MM
    rad0 = np.array(hp[0]) - np.array([cx, yb - 0.075, hp[0][2]])
    rad0 = rad0 @ Ai[:3, :3].T
    hc = strip([tuple(p) for p in hp_l], 26, 3.2, tuple(rad0))
    hpc = np.array(hp)[len(hp) // 2]
    v = hpc - np.array([cx, yb - 0.075, hpc[2]]); v /= np.linalg.norm(v)
    spur_w = hpc + v * 0.010 + np.array([0, 0, 0.012])
    spur_l = (spur_w @ Ai[:3, :3].T + Ai[:3, 3])
    spur = bd.Pos(*(spur_l * MM)) * bd.Sphere(6.5)
    add("m4_heelclip_" + sd, hc + spur, "foot_" + sd, "upgrade", "alu", "M4 heel clip", group="m4")
    ANCH["heel_" + sd] = dict(seg="foot_" + sd, p=[float(x) for x in spur_l + np.array([0, 0, 0])])

# =====================================================================================
# TRUNK: the Dock (back panel + hip belt), M2 lift, M3 hip bands, upgrades
# =====================================================================================
PO = (0, 0.045)       # pelvis sampling axis: 45 mm forward of the pelvis bone, near the trunk centre
CO = (0, 0.080)       # chest sampling axis
# the belt is cut higher at the front-sides (35-110 deg each side), where the thigh folds up into it when seated:
# a full-height back section and two raised front sections, fused
belt, _ = contour_part("pelvis", 0.060, 0.150, lambda z: 104, lambda z: 256, 0.0015, 0.010,
                       nz=9, nth=41, round_p=8, min_frac=0.96, axis_offset=PO, cap=0.075)
def belt_front_off(z, t):
    # the front sections stand off the belly (it bulges over the belt when stooping and running), most at the lower edge
    tt = abs(((t + 180) % 360) - 180)
    w = min(1.0, max(0.0, (tt - 4) / 6)) * min(1.0, max(0.0, (75 - tt) / 15))
    return 0.0015 + w * (0.008 + 0.004 * min(1.0, max(0.0, (0.138 - z) / 0.020)))
for a0, a1 in ((9, 110), (250, 351)):
    fr, _ = contour_part("pelvis", 0.116, 0.150, lambda z, a=a0: a, lambda z, b=a1: b, belt_front_off, 0.010,
                         nz=7, nth=31, round_p=8, min_frac=0.96, axis_offset=PO, cap=0.075)
    belt = belt + fr
belt = safe_fillet(belt, 3.0)
add("hip_belt", belt, "pelvis", "basic", "fabric", "Hip belt (Dock)", group="belt")
buckle = pod("pelvis", 0.075, 0.135, 0, 64, 0.0115, 0.008, fillet=0.003, axis_offset=PO)
add("belt_buckle", buckle, "pelvis", "basic", "alu", None, group="buckle")
lplate, _ = contour_part("pelvis", 0.070, 0.153, lambda z: 146, lambda z: 214, 0.0115, 0.003,
                         axis_offset=PO, fillet=0.0012, round_p=3, min_frac=0.6)
add("lumbar_plate", lplate, "pelvis", "basic", "carbon", "Lumbar plate (Dock)", group="belt")
for sd in ("l", "r"):
    S = 1 if sd == "l" else -1
    # lumbar standoffs (M2), glute guides (M2), hip-flexor standoffs (M3), belt side clip (Crazy Creek)
    ls = pod("pelvis", 0.100, 0.135, 180 - S * 30, 22, 0.0145, 0.016, fillet=0.005, axis_offset=PO)
    add("lumbar_standoff_" + sd, ls, "pelvis", "basic", "alu", "Lumbar standoff (lift tendon)" if sd == "l" else None, group="standoff")
    anchor("t3_lumbar_" + sd, "pelvis", 0.117, 180 - S * 30, 0.0145 + 0.020, PO)
    gg = pod("pelvis", 0.040, 0.078, 180 - S * 52, 26, 0.0115, 0.014, fillet=0.005, axis_offset=PO)
    add("glute_guide_" + sd, gg, "pelvis", "basic", "alu", "Glute guide (100 mm lever)" if sd == "l" else None, group="standoff")
    anchor("t3_glute_" + sd, "pelvis", 0.050, 180 - S * 52, 0.0115 + 0.018, PO)
    hs = pod("pelvis", 0.113, 0.146, S * 52, 26, 0.0115, 0.016, fillet=0.005, axis_offset=PO)
    add("m3_standoff_" + sd, hs, "pelvis", "basic", "alu", "M3 hip-flexor standoff" if sd == "l" else None, group="standoff")
    anchor("m3_belt_" + sd, "pelvis", 0.125, S * 52, 0.0115 + 0.013, PO)
    sc = pod("pelvis", 0.085, 0.125, S * 96, 20, 0.0115, 0.008, fillet=0.003, axis_offset=PO)
    add("belt_sideclip_" + sd, sc, "pelvis", "basic", "alu", None, group="clip")
    anchor("cc_belt_" + sd, "pelvis", 0.105, S * 96, 0.0115 + 0.009, PO)
    anchor_xyz("harness_belt_" + sd, "pelvis", np.array(point("pelvis", 0.140, S * 34, outer_r("hip_belt", "pelvis", 0.140, S * 34, PO) - 0.002, PO)) / MM)
    # spine link, belt end: pivot pin on the lumbar plate's top edge
    pv = pod("pelvis", 0.137, 0.155, 180 - S * 20, 22, 0.0145 - 0.001, 0.006, fillet=0.002, axis_offset=PO)
    pc = np.array(point("pelvis", 0.146, 180 - S * 20, skin("pelvis", 0.146, 180 - S * 20, PO) + 0.0145 + 0.011, PO))
    pv += bd.Pos(*pc) * bd.Rot(0, 90, 0) * bd.Cylinder(6, 18, align=(bd.Align.CENTER,) * 3)
    add("spine_pivot_belt_" + sd, pv, "pelvis", "basic", "alu", "Spine link pivot (belt)" if sd == "l" else None, group="spine")
    ANCH["spine_belt_" + sd] = dict(seg="pelvis", p=[float(v) / MM for v in pc])
    anchor("bowden_belt_" + sd, "pelvis", 0.112, S * 110, 0.0115 + 0.003, PO)

# back panel: carbon, contoured, 0.30 m tall, spacer-mesh lined, 6 cable ports (square-ish corners so the ports, the
# spine-link pivots and the M5 cassettes all sit on it)
pw = lambda z: 38 + 4 * (z + 0.1) / 0.3
panel, _ = contour_part("chest", -0.075, 0.200, lambda z: 180 - pw(z), lambda z: 180 + pw(z), 0.009, 0.0035, axis_offset=CO,
                        fillet=0.0014, round_p=5.0, min_frac=0.62)
add("back_panel", panel, "chest", "basic", "carbon", "Back panel (Dock, 600 cm2)", group="panel")
pliner, _ = contour_part("chest", -0.079, 0.204, lambda z: 180 - pw(z) - 4, lambda z: 180 + pw(z) + 4, 0.0012, 0.0072,
                         axis_offset=CO, round_p=5.0, min_frac=0.62)
add("back_panel_liner", pliner, "chest", "basic", "foam", None, printed=True, group="liner")
PANEL_OUT = 0.009 + 0.0035
ports = {"knee": (-0.056, 31), "hip": (-0.062, 17), "shoulder": (0.155, 32)}   # the M5 cassette docks over its port
for key, (zz, dth) in ports.items():
    for sd in ("l", "r"):
        S = 1 if sd == "l" else -1
        th = 180 - S * dth
        b = at(boss(15, 6), "chest", zz, th, skin("chest", zz, th, CO) + PANEL_OUT, CO)
        add(f"port_{key}_{sd}", b, "chest", "basic", "alu", "Cable port (6 per Dock)" if key == "knee" and sd == "l" else None,
            printed=False, group="port")
        anchor(f"port_{key}_{sd}", "chest", zz, th, PANEL_OUT + 0.007, CO)
# M2 lift leaf on the panel centre (root at the bottom, tip with the whiffletree at the top)
leaf_off = lambda z: PANEL_OUT + 0.002 + 0.024 * max(0.0, (z + 0.058) / 0.105) ** 1.5
rr = skin("chest", -0.02, 180, CO)
wd = lambda w: math.degrees(w / rr)
m2, _ = contour_part("chest", -0.058, 0.047, lambda z: 180 - wd(0.018 - 0.007 * (z + 0.058) / 0.105),
                     lambda z: 180 + wd(0.018 - 0.007 * (z + 0.058) / 0.105), leaf_off, 0.0045,
                     nz=10, nth=7, axis_offset=CO, round_p=6, min_frac=0.8, fillet=0.0015)
add("m2_leaf", m2, "chest", "basic", "leaf", "M2 lift leaf 3.1 N/mm (slack below 35 deg)", group="m2")
m2c = pod("chest", -0.072, -0.046, 180, 46, PANEL_OUT, 0.014, fillet=0.005, axis_offset=CO)
add("m2_leaf_root", m2c, "chest", "basic", "alu", None, group="leaf_clamp")
# whiffletree: a 32 mm floating pulley on the leaf tip (axle along the panel normal). One lift tendon runs over its
# top groove, so left and right always share equally
LEAF_TIP = 0.047
wz = LEAF_TIP - 0.006
wt_base = skin("chest", wz, 180, CO) + leaf_off(wz) + 0.0045 - 0.001
wt_c = wt_base + 0.005
wt = at(bd.Cylinder(16, 10, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.CENTER)), "chest", wz, 180, wt_c, CO)
try:
    wt = bd.fillet(wt.edges(), 2.5)
except Exception:
    pass
add("whiffletree", wt, "chest", "basic", "accent", "Whiffletree (equal L/R share)", group="m2")
for sd in ("l", "r"):
    S = 1 if sd == "l" else -1
    a50 = math.radians(50)
    ANCH["t3_whiffle_" + sd] = dict(seg="chest", p=[v / MM for v in point("chest", wz + 0.0145 * math.cos(a50),
                                                                          180 - S * math.degrees(0.0145 * math.sin(a50) / wt_c), wt_c, CO)])
    gp = pod("chest", -0.040, -0.014, 180 - S * 24, 20, PANEL_OUT, 0.010, fillet=0.0035, axis_offset=CO)
    add("panel_guide_" + sd, gp, "chest", "basic", "alu", None, group="standoff")
    anchor("t3_panel_" + sd, "chest", -0.027, 180 - S * 24, PANEL_OUT + 0.012, CO)
    anchor_xyz("harness_top_" + sd, "chest", np.array(point("chest", 0.192, 180 - S * 18, outer_r("back_panel", "chest", 0.192, 180 - S * 18, CO) - 0.0015, CO)) / MM)
    # spine link, panel end: a pivot pin across the back at the panel's lower edge (pairs with spine_pivot_belt)
    pv = pod("chest", -0.073, -0.055, 180 - S * 23, 22, PANEL_OUT - 0.001, 0.006, fillet=0.002, axis_offset=CO)
    pc = np.array(point("chest", -0.064, 180 - S * 23, skin("chest", -0.064, 180 - S * 23, CO) + PANEL_OUT + 0.011, CO))
    pv += bd.Pos(*pc) * bd.Rot(0, 90, 0) * bd.Cylinder(6, 18, align=(bd.Align.CENTER,) * 3)
    add("spine_pivot_panel_" + sd, pv, "chest", "basic", "alu", "Spine link pivot (panel)" if sd == "l" else None, group="spine")
    ANCH["spine_panel_" + sd] = dict(seg="chest", p=[float(v) / MM for v in pc])
    anchor_xyz("cc_panel_" + sd, "chest", np.array(point("chest", 0.100, 180 - S * 38, outer_r("back_panel", "chest", 0.100, 180 - S * 38, CO) - 0.0015, CO)) / MM)
    # shoulder harness way-points (snapped to the skin per pose by the assembler)
    anchor("harness_shoulder_" + sd, "chest", 0.315, 180 - S * 132, 0.008, CO)
    anchor("harness_chest_" + sd, "chest", 0.200, S * 32, 0.006, CO)
    anchor("harness_low_" + sd, "chest", 0.020, S * 30, 0.006, CO)

# ---------------- P1: one motor on the back panel (upgrade) ----------------
mz, mth = 0.130, 180
mr = skin("chest", mz, mth, CO) + PANEL_OUT
motor = bd.Cylinder(49, 40, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
try:
    motor = bd.fillet(motor.edges().group_by(bd.Axis.Z)[-1], 10)
except Exception:
    pass
add("p1_motor", at(motor, "chest", mz, mth, mr + 0.004, CO), "chest", "upgrade", "motor", "P1: one AK10-9 + hub drum, 2 dog clutches", group="p1")
drum = bd.Cylinder(30, 18, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN))
try:
    drum = bd.fillet(drum.edges().group_by(bd.Axis.Z)[-1], 4)
except Exception:
    pass
add("p1_drum", at(drum, "chest", mz, mth, mr + 0.044, CO), "chest", "upgrade", "accent", None, group="p1")
for sd in ("l", "r"):
    S = 1 if sd == "l" else -1
    dc = pod("chest", 0.085, 0.120, 180 - S * 28, 24, PANEL_OUT, 0.020, fillet=0.006, axis_offset=CO)
    add("p1_dogclutch_" + sd, dc, "chest", "upgrade", "motor", None, group="p1")
    # Bowden from the hub to the knee port, along the panel (static)
    pts = [point("chest", 0.100, 180 - S * 28, skin("chest", 0.10, 180 - S * 28, CO) + PANEL_OUT + 0.012, CO),
           point("chest", 0.020, 180 - S * 33, skin("chest", 0.02, 180 - S * 33, CO) + PANEL_OUT + 0.004, CO),
           point("chest", -0.040, 180 - S * 32, skin("chest", -0.04, 180 - S * 32, CO) + PANEL_OUT + 0.005, CO),
           point("chest", -0.056, 180 - S * 31, skin("chest", -0.056, 180 - S * 31, CO) + PANEL_OUT + 0.010, CO)]
    add("bowden_panel_" + sd, oval_sweep(pts, 5, 5), "chest", "upgrade", "bowden", None, group="bowden")
bat = pod("pelvis", 0.074, 0.146, 180, 128, 0.0145, 0.026, fillet=0.008, axis_offset=PO)
add("p1_battery", bat, "pelvis", "upgrade", "motor", "97 Wh pack (under the FAA 100 Wh line)", group="p1")

# ---------------- M5 shoulder springs (upgrade) ----------------
for sd in ("l", "r"):
    S = 1 if sd == "l" else -1
    cas = pod("chest", 0.125, 0.185, 180 - S * 32, 48, PANEL_OUT - 0.0015, 0.022, fillet=0.008, axis_offset=CO)
    add("m5_cassette_" + sd, cas, "chest", "upgrade", "carbon_gloss", "M5 shoulder spring cassette" if sd == "l" else None, group="m5")
    anchor("m5_pivot_" + sd, "chest", 0.160, 180 - S * 36, PANEL_OUT + 0.016, CO)
    U = "uarm_" + sd
    ac, _ = contour_part(U, 0.120, 0.215, lambda z: 66, lambda z: 176, 0.009, 0.003, fillet=0.0012, round_p=3, min_frac=0.6)
    add("m5_armcuff_" + sd, ac, U, "upgrade", "carbon", "M5 arm cuff" if sd == "l" else None, group="m5")
    acl, _ = contour_part(U, 0.116, 0.219, lambda z: 62, lambda z: 180, 0.0012, 0.0070, round_p=3, min_frac=0.6)
    add("m5_armliner_" + sd, acl, U, "upgrade", "foam", None, printed=True, group="m5")
    anchor("m5_cuff_" + sd, U, 0.150, 128, 0.011)

# the back panel and everything on it ride the "panel" frame: the chest frame in the build, re-fitted per pose and per
# frame by assemble.py (the panel hangs on the spine link and lies on the back, it is not glued to one vertebra)
PANEL_ANCH = ("port_", "t3_whiffle_", "t3_panel_", "harness_top_", "cc_panel_", "m5_pivot_", "spine_panel_")
for p in PARTS:
    if p["seg"] == "chest":
        p["seg"] = "panel"
for k, a in ANCH.items():
    if a.get("seg") == "chest" and k.startswith(PANEL_ANCH):
        a["seg"] = "panel"

# =====================================================================================
# EXPORT
# =====================================================================================
man = []
asm = []
for p in PARTS:
    nm = p["name"]
    rec = {k: v for k, v in p.items() if k != "shape"}
    if p["shape"] is not None:
        sh = p["shape"]
        if isinstance(sh, bd.Compound) or not hasattr(sh, "volume"):
            pass
        bd.export_step(sh, os.path.join(OUT["step"], nm + ".step"))
        # own tessellation -> GLB (y-up): build123d's glTF writer drops the axis swap on located shapes
        import trimesh
        vv, ff = sh.tessellate(0.5, 0.3)
        tm = trimesh.Trimesh(np.array([tuple(v) for v in vv]) / MM, np.array(ff), process=True)
        tm.apply_transform(np.array([[1, 0, 0, 0], [0, 0, 1, 0], [0, -1, 0, 0], [0, 0, 0, 1.0]]))
        tm.export(os.path.join(OUT["glb"], nm + ".glb"))
        PRINT_GROUPS = {"standoff", "clip", "fairlead", "guide", "leaf_clamp", "port", "dring", "anchor", "clevis",
                        "manifold", "lever", "buckle", "m4", "m5", "liner"}
        if p["printed"] or p["group"] in PRINT_GROUPS:
            bd.export_stl(sh, os.path.join(OUT["stl"], nm + ".stl"), tolerance=0.25, angular_tolerance=0.3)
            rec["stl"] = True
        # standing-pose assembly copy (world frame)
        Aw = A("stand", "chest" if p["seg"] == "panel" else p["seg"])
        from OCP.gp import gp_Trsf
        tr = gp_Trsf()
        tr.SetValues(*[float(Aw[i, j] * (MM if j == 3 else 1)) for i in range(3) for j in range(4)])
        loc = bd.Location(tr)
        try:
            asm.append(sh.moved(loc))
            asm[-1].label = nm
        except Exception:
            pass
        rec["volume_cm3"] = round(sh.volume / 1000, 2)
    man.append(rec)
    print(f"{time.time() - T0:6.1f}s  {nm}")

frames = {pose: {seg: A(pose, seg).tolist() for seg in
                 ["pelvis", "chest", "thigh_l", "thigh_r", "shin_l", "shin_r", "knee_l", "knee_r",
                  "foot_l", "foot_r", "uarm_l", "uarm_r"]} for pose in POSES}
for pose in POSES:
    frames[pose]["panel"] = frames[pose]["chest"]       # refitted per pose by assemble.py
json.dump(dict(parts=man, anchors=ANCH, frames=frames,
               poses={p: dict(label=FR[p]["label"], mode=FR[p]["mode"]) for p in POSES}),
          open(os.path.join(OUT["build"], "manifest.json"), "w"), indent=1)
try:
    bd.export_step(bd.Compound(children=asm, label="sitka_standing"), os.path.join(OUT["step"], "sitka_assembly_standing.step"))
except Exception as e:
    print("assembly step failed", e)
print("done", len(PARTS), "parts in", round(time.time() - T0, 1), "s")
