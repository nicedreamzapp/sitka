"""Anatomy gate for the baked viewer animation: every frame of every sequence must stand like a human.

  cad/.venv/bin/python cad/mocap/anatomy_gate.py            (reads cad/viewer/sitka_anim.js, exit 1 on a fail)

The bake (cad/assemble/assemble.py --anim) runs the same gate on the frames it just made and refuses to write
sitka_anim.js when it fails. Joints come from the rig (seq["joints"], world metres: hip/knee/ankle/toe per leg);
see anatomy.py for how each measure is defined.

Fails on, per frame:
  frontal   knee more than FRONTAL_MAX deg off the leg's bend plane (bow-leg +, knock-knee -)
  hyper     knee bent backwards more than HYPER_MAX deg (hyperextension)
  cross     knees closer than KNEE_GAP_MIN or ankles closer than ANK_GAP_MIN side to side (left minus right
            along the pelvis' lateral axis; < 0 = crossed), or a knee/ankle past the body midline by MIDLINE_MAX
  width     both feet down and the body upright: ankle gap outside WIDTH_RATIO x the hip-joint gap
  floor     a foot vertex sunk more than FLOOR_SINK below the sole line (SOLE)
  seam      loops, and the Lift program which replays: last frame -> first frame joint jump larger than the
            sequence's own largest frame-to-frame step x SEAM_FACTOR (and over SEAM_MIN)
"""
import json, os, sys, base64
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import anatomy as AN  # noqa: E402

CAD = os.path.dirname(HERE)
SOLE = 0.022
FRONTAL_MAX = 8.0
HYPER_MAX = 2.0
KNEE_GAP_MIN = 0.06
ANK_GAP_MIN = 0.02
MIDLINE_MAX = 0.01
WIDTH_RATIO = (0.5, 2.0)
UPRIGHT_HIP_Z = 0.88
PLANTED = 0.010
FLOOR_SINK = 0.006
SEAM_FACTOR = 1.5
SEAM_MIN = 0.02
REPLAYS = {"stoop"}            # non-loop sequences the viewer replays back to back (the Lift program)
JOINTS = ["hip_l", "knee_l", "ank_l", "toe_l", "hip_r", "knee_r", "ank_r", "toe_r"]


def check_seq(name, joints, loop, foot_z=None):
    """joints: (n, 8, 3); foot_z: {"l": (n,), "r": (n,)} lowest foot vertex per frame (or None).
    Returns (row dict, list of failure strings)."""
    J = np.asarray(joints, dtype=float)
    n = len(J)
    fails = []
    worst = dict(frontal=0.0, flex_min=999.0, knee_gap=9.0, ank_gap=9.0, mid=9.0, wr_lo=9.0, wr_hi=0.0, sink=0.0, seam=0.0)
    for i in range(n):
        D = {k: J[i, j] for j, k in enumerate(JOINTS)}
        m = AN.measure(D)
        for sd in "lr":
            f = m["frontal_" + sd]
            if abs(f) > abs(worst["frontal"]):
                worst["frontal"] = f
            if abs(f) > FRONTAL_MAX:
                fails.append("%s f%d %s knee %s %.1f deg" % (name, i, sd, "bowed out" if f > 0 else "knocked in", f))
            worst["flex_min"] = min(worst["flex_min"], m["flex_" + sd])
            if m["flex_" + sd] < -HYPER_MAX:
                fails.append("%s f%d %s knee hyperextended %.1f deg" % (name, i, sd, -m["flex_" + sd]))
        worst["knee_gap"] = min(worst["knee_gap"], m["knee_gap"])
        worst["ank_gap"] = min(worst["ank_gap"], m["ank_gap"])
        worst["mid"] = min(worst["mid"], m["knee_mid"], m["ank_mid"])
        if m["knee_gap"] < KNEE_GAP_MIN:
            fails.append("%s f%d knees cross/touch, gap %.3f m" % (name, i, m["knee_gap"]))
        if m["ank_gap"] < ANK_GAP_MIN:
            fails.append("%s f%d ankles cross/touch, gap %.3f m" % (name, i, m["ank_gap"]))
        if min(m["knee_mid"], m["ank_mid"]) < -MIDLINE_MAX:
            fails.append("%s f%d a leg past the midline by %.3f m" % (name, i, -min(m["knee_mid"], m["ank_mid"])))
        if foot_z is not None:
            planted = all(foot_z[sd][i] < SOLE + PLANTED for sd in "lr")
            sink = SOLE - min(foot_z["l"][i], foot_z["r"][i])
            worst["sink"] = max(worst["sink"], sink)
            if sink > FLOOR_SINK:
                fails.append("%s f%d foot through the floor by %.1f mm" % (name, i, sink * 1000))
        else:
            planted = all(J[i, JOINTS.index("toe_" + sd), 2] < 0.05 for sd in "lr")
        upright = 0.5 * (D["hip_l"][2] + D["hip_r"][2]) > UPRIGHT_HIP_Z
        if planted and upright:
            wr = m["width_ratio"]
            worst["wr_lo"] = min(worst["wr_lo"], wr); worst["wr_hi"] = max(worst["wr_hi"], wr)
            if not (WIDTH_RATIO[0] <= wr <= WIDTH_RATIO[1]):
                fails.append("%s f%d standing feet width %.2f x hip width" % (name, i, wr))
    if (loop or name in REPLAYS) and n > 2:
        step = np.linalg.norm(np.diff(J, axis=0), axis=2).max()
        seam = np.linalg.norm(J[0] - J[-1], axis=1).max()
        worst["seam"] = seam
        lim = max(SEAM_MIN, SEAM_FACTOR * step) if loop else SEAM_MIN
        if seam > lim:
            fails.append("%s loop seam: joints jump %.0f mm from the last frame to the first (limit %.0f)" % (name, seam * 1000, lim * 1000))
    worst["n"] = n
    return worst, fails


def table(rows):
    h = "%-8s %4s %9s %8s %8s %8s %8s %11s %7s %7s  %s" % ("seq", "n", "frontal", "minflex", "kneegap", "ankgap", "midline", "stand w/hip", "sink", "seam", "result")
    lines = [h, "-" * len(h)]
    for name, w, f in rows:
        wr = "%.2f-%.2f" % (w["wr_lo"], w["wr_hi"]) if w["wr_hi"] > 0 else "-"
        lines.append("%-8s %4d %+8.1f° %7.1f° %7.3fm %7.3fm %7.3fm %11s %5.1fmm %5.0fmm  %s" % (
            name, w["n"], w["frontal"], w["flex_min"], w["knee_gap"], w["ank_gap"], w["mid"], wr, w["sink"] * 1000,
            w["seam"] * 1000, "PASS" if not f else "FAIL (%d)" % len(f)))
    return "\n".join(lines)


def gate(seqs, log=print):
    """seqs: {name: dict(joints=(n,8,3), loop=bool, foot_z={l,r} or None)}. Prints the table; returns True on pass."""
    rows, allf = [], []
    for name, s in seqs.items():
        w, f = check_seq(name, s["joints"], s["loop"], s.get("foot_z"))
        rows.append((name, w, f)); allf += f
    log("ANATOMY GATE (frontal <= %.0f deg, hyperext <= %.0f deg, knee gap >= %.2f m, ankle gap >= %.2f m, standing width %.1f-%.1f x hips, sink <= %.0f mm)"
        % (FRONTAL_MAX, HYPER_MAX, KNEE_GAP_MIN, ANK_GAP_MIN, WIDTH_RATIO[0], WIDTH_RATIO[1], FLOOR_SINK * 1000))
    log(table(rows))
    for x in allf[:40]:
        log("  FAIL " + x)
    if len(allf) > 40:
        log("  ... %d more" % (len(allf) - 40))
    log("ANATOMY GATE " + ("PASS" if not allf else "FAIL"))
    return not allf


def from_anim_js(path):
    src = open(path).read()
    A = json.loads(src[src.index("=") + 1:src.rstrip().rindex(";")])
    if "joint_names" not in A:
        raise SystemExit("sitka_anim.js has no joints (baked before the anatomy gate): re-bake with assemble.py --anim")
    assert A["joint_names"] == JOINTS
    NV = A["nv"]
    body = np.frombuffer(base64.b64decode(A["body_b64"]), dtype=np.int16).reshape(-1, NV, 3) * 1e-4
    dom = np.load(os.path.join(CAD, "body", "stand_weights.npz"))["dom"]
    FOOT = {sd: np.where(np.isin(dom, ["foot_" + sd, "ball_" + sd]))[0] for sd in "lr"}
    seqs = {}
    for name, S in A["seqs"].items():
        V = body[S["start"]:S["start"] + S["n"]]
        seqs[name] = dict(joints=np.array(S["joints"]).reshape(S["n"], 8, 3), loop=S["loop"],
                          foot_z={sd: V[:, FOOT[sd], 2].min(axis=1) for sd in "lr"})
    return seqs


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(CAD, "viewer", "sitka_anim.js")
    sys.exit(0 if gate(from_anim_js(path)) else 1)
