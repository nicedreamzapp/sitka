"""Leg anatomy measures for one posed frame (numpy only; used by the bake's pole check and by anatomy_gate.py).

Joints (world, metres; +X = wearer's left, -Y = forward, +Z = up), per side "l"/"r":
  hip_  thigh head      knee_  calf head      ank_  foot head      toe_  ball tail

Measures, per leg:
  frontal   deg, the knee's sideways angle off the leg's own bend plane (the plane through hip and ankle that
            holds the leg's forward direction = the bisector of the pelvis heading and the foot heading, i.e.
            "the knee tracks over the toes"). + = knee outside (bow-leg / varus), - = knee inside (knock-knee /
            valgus). asin(sideways knee offset / thigh length).
  flex      deg, knee flexion (0 = straight), signed: negative = the knee bends backwards (hyperextension)
Per frame:
  knee_gap, ank_gap   m, left minus right along the pelvis' lateral axis (> 0 = legs on their own sides)
  knee_mid, ank_mid   m, each knee/ankle's distance to its own side of the pelvis midline (min over l/r)
  width_ratio         ankle gap / hip-joint gap (stance width)
"""
import numpy as np

UP = np.array([0.0, 0.0, 1.0])


def _h(v):
    v = np.array(v, dtype=float); v[2] = 0.0
    n = np.linalg.norm(v)
    return v / n if n > 1e-9 else v


def leg_forward(fp, foot):
    """the leg's forward direction (horizontal unit): the pelvis heading fp, turned halfway toward the foot's
    heading when the foot is near flat. A pointed foot (swing, toes down) has no reliable heading: pelvis only."""
    foot = np.array(foot, dtype=float)
    L = np.linalg.norm(foot)
    hz = np.linalg.norm(foot[:2])
    if L < 1e-9 or hz < 1e-9:
        return fp
    hfrac = hz / L                                   # cos of the foot pitch
    w = min(1.0, max(0.0, (hfrac - 0.75) / 0.17)); w = w * w * (3 - 2 * w)
    ff = _h(foot)
    if np.dot(ff, fp) < 0.3:                         # heading more than ~73 deg off the pelvis: not a stance foot
        return fp
    v = fp + w * ff
    return v / np.linalg.norm(v)


def frame_axes(J):
    lat = _h(J["hip_l"] - J["hip_r"])               # +: toward the wearer's left
    fwd = np.cross(lat, UP)                         # (1,0,0) x (0,0,1) = (0,-1,0) = forward
    return lat, fwd


def leg(J, sd, fwd):
    h, k, a, t = J["hip_" + sd], J["knee_" + sd], J["ank_" + sd], J["toe_" + sd]
    lf = leg_forward(fwd, t - a)
    u = (a - h) / np.linalg.norm(a - h)
    n = np.cross(u, lf)                             # normal of the bend plane (hip-ankle line + forward)
    if np.linalg.norm(n) < 1e-6:
        return 0.0, 0.0
    n /= np.linalg.norm(n)
    # n points to the wearer's right for a vertical leg (u = -Z, lf = -Y: (-Z) x (-Y) = -X). Outward = +n for
    # the right leg, -n for the left.
    side = 1.0 if sd == "r" else -1.0
    L1 = np.linalg.norm(k - h)
    off = np.dot(k - h, n) * side
    frontal = float(np.degrees(np.arcsin(np.clip(off / L1, -1, 1))))
    th, sh = k - h, a - k
    flex = float(np.degrees(np.arccos(np.clip(np.dot(th, sh) / np.linalg.norm(th) / np.linalg.norm(sh), -1, 1))))
    # sign: the knee is ahead of the hip-ankle line (normal) or behind it (hyperextension)
    perp = (k - h) - u * np.dot(k - h, u)
    if np.dot(perp, lf) < 0 and np.linalg.norm(perp) > 1e-4:
        flex = -flex
    return frontal, flex


def measure(J):
    lat, fwd = frame_axes(J)
    mid = 0.5 * (J["hip_l"] + J["hip_r"])
    out = {}
    for sd in "lr":
        out["frontal_" + sd], out["flex_" + sd] = leg(J, sd, fwd)
    lx = {k: float(np.dot(J[k] - mid, lat)) for k in J}
    out["knee_gap"] = lx["knee_l"] - lx["knee_r"]
    out["ank_gap"] = lx["ank_l"] - lx["ank_r"]
    out["knee_mid"] = min(lx["knee_l"], -lx["knee_r"])
    out["ank_mid"] = min(lx["ank_l"], -lx["ank_r"])
    hip_gap = lx["hip_l"] - lx["hip_r"]
    out["width_ratio"] = out["ank_gap"] / hip_gap if hip_gap > 1e-6 else 0.0
    return out
