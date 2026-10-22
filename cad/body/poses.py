"""Sitka render-two poses for the MakeHuman (MPFB, CC0 base mesh) game_engine rig.

Axes (MPFB): +X = wearer's left, -Y = forward, +Z = up.
Each entry gives a segment's forward pitch in degrees, measured in the world from its rest
(standing) direction:
  up-pointing segments (pelvis, spine, neck, head): + = top tips forward
  down-pointing segments (thigh, calf, upper arm, forearm): + = distal end swings forward
  foot: + = toes up (dorsiflexion) from the standing foot, absolute in the world
Knee flexion = thigh - calf. Hip flexion = thigh + pelvis tilt.
Arms are given as (pitch, abduction) of a straight-down reference, forearm as a pitch.
"""
import math

UP = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head"]

# Recline 10 deg on the back panel, thigh 15 deg below horizontal, shank 15 deg forward:
# the tendon_sketch.html design point (chair, 10 deg recline, 4 deg strut).
POSES = {
    "stand": dict(
        label="Standing",
        trunk=[0, 0, 0, 0, 0, 0],
        L=dict(thigh=0, calf=0, foot=0), R=dict(thigh=0, calf=0, foot=0),
        armL=(3, 13, 10), armR=(3, 13, 10),
        mode="WALK",
    ),
    "walk": dict(
        label="Walking, mid-stance",
        trunk=[2, 2, 2, 2, 0, -2],
        R=dict(thigh=3, calf=-5, foot=0),            # stance: knee 8 deg
        L=dict(thigh=22, calf=-36, foot=0),          # swing: hip 22, knee 58 deg
        armR=(16, 7, 40), armL=(-10, 7, -4),
        mode="WALK",
    ),
    "run": dict(
        label="Running, mid-stance",
        trunk=[8, 8, 8, 8, 2, -4],
        R=dict(thigh=20, calf=-20, foot=0),          # stance: knee 40 deg
        L=dict(thigh=48, calf=-58, foot=-20),        # swing: hip 48, knee 106 deg
        armR=(28, 10, 110), armL=(-22, 12, 62),
        mode="RUN",
    ),
    "chair": dict(
        label="Chair, 10 deg recline",
        trunk=[-10, -10, -10, -10, -2, 4],
        L=dict(thigh=75, calf=-15, foot=0), R=dict(thigh=75, calf=-15, foot=0),
        armL=(24, 12, 66), armR=(24, 12, 66),
        mode="SIT",
    ),
    "stoop": dict(
        label="Stoop lift",
        trunk=[48, 58, 68, 74, 56, 40],
        L=dict(thigh=6, calf=-16, foot=0), R=dict(thigh=6, calf=-16, foot=0),
        armL=(0, 4, 4), armR=(0, 4, 4),
        mode="LIFT",
    ),
}
ORDER = ["stand", "walk", "run", "chair", "stoop"]


def apply_pose(rig, name, bpy, Matrix, Vector):
    """Pose the rig in place. Uses the rest (edit) bone directions as the reference."""
    apply_params(rig, POSES[name], bpy, Matrix, Vector)


def lerp_params(a, b, t):
    """blend two pose dicts (numbers, lists and tuples blend; labels/modes come from b)"""
    def mix(x, y):
        if isinstance(x, dict):
            return {k: mix(x[k], y[k]) for k in x}
        if isinstance(x, (list, tuple)):
            return type(x)(mix(u, v) for u, v in zip(x, y))
        if isinstance(x, (int, float)):
            return x + (y - x) * t
        return y
    return mix(a, b)


def apply_params(rig, p, bpy, Matrix, Vector):
    for pb in rig.pose.bones:
        pb.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()
    rest = {b.name: (b.tail_local - b.head_local).normalized() for b in rig.data.bones}

    def set_dir(bone, d):
        pb = rig.pose.bones[bone]
        cur = (pb.tail - pb.head).normalized()
        q = cur.rotation_difference(d.normalized())
        h = pb.head.copy()
        M = Matrix.Translation(h) @ q.to_matrix().to_4x4() @ Matrix.Translation(-h)
        pb.matrix = M @ pb.matrix
        bpy.context.view_layer.update()

    def rx(deg):
        return Matrix.Rotation(math.radians(deg), 3, 'X')

    for bone, a in zip(UP, p["trunk"]):
        set_dir(bone, rx(a) @ rest[bone])
    for side, key in (("l", "L"), ("r", "R")):
        leg = p[key]
        set_dir("thigh_" + side, rx(-leg["thigh"]) @ rest["thigh_" + side])
        set_dir("calf_" + side, rx(-leg["calf"]) @ rest["calf_" + side])
        set_dir("foot_" + side, rx(leg["foot"]) @ rest["foot_" + side])
        set_dir("ball_" + side, rx(leg["foot"]) @ rest["ball_" + side])
        pitch, abd, fore = p["arm" + key]
        sx = 1 if side == "l" else -1
        down = Vector((sx * math.sin(math.radians(abd)), 0, -math.cos(math.radians(abd))))
        set_dir("upperarm_" + side, rx(-pitch) @ down)
        fdown = Vector((sx * math.sin(math.radians(abd * 0.6)), 0, -1)).normalized()
        set_dir("lowerarm_" + side, rx(-fore) @ fdown)


# ------------------------------------------------------------------ animation sequences
import copy


def _interp(ps, vs, p):
    import numpy as np
    return float(np.interp(p, ps, vs))


def _smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


GAIT = {
    # one leg, heel strike at p = 0. thigh = forward pitch of the thigh, knee = flexion, foot = toes-up
    "walk": dict(p=[0, .10, .30, .50, .62, .73, .87, 1.0],
                 thigh=[24, 20, 6, -10, -14, -2, 18, 24],
                 knee=[3, 16, 8, 6, 36, 60, 30, 3],
                 foot=[4, -4, 4, 10, -14, -6, 2, 4],
                 trunk=2, arm_gain=0.75, elbow=12, n=28, stance=0.60),
    "run": dict(p=[0, .12, .25, .38, .50, .65, .80, .90, 1.0],
                thigh=[30, 16, -2, -16, -8, 24, 48, 44, 30],
                knee=[22, 40, 26, 14, 62, 106, 88, 40, 22],
                foot=[4, -6, 0, -18, -24, -10, 0, 6, 4],
                trunk=8, arm_gain=1.0, elbow=88, n=22, stance=0.38),
}


def gait_frame(kind, p):
    g = GAIT[kind]
    out = copy.deepcopy(POSES["walk" if kind == "walk" else "run"])
    st = {}
    for key, ph in (("R", p), ("L", (p + 0.5) % 1.0)):
        th = _interp(g["p"], g["thigh"], ph)
        kn = _interp(g["p"], g["knee"], ph)
        ft = _interp(g["p"], g["foot"], ph)
        out[key] = dict(thigh=th, calf=th - kn, foot=ft)
        sd = key.lower()
        stance = ph < g["stance"]
        st["ea_" + sd] = 1.0 if (kind == "walk" and stance and ph < 0.45) else 0.0       # stance clutch gate
        st["m3_" + sd] = max(0.0, min(1.0, -th / 15.0))                                   # hip extension stretches it
        st["ham_" + sd] = max(0.0, min(1.0, (ph - 0.80) / 0.12)) if ph > 0.80 else 0.0    # late swing
        st["t1_" + sd] = 0.0
    t = g["trunk"]
    out["trunk"] = [t, t, t, t, 0, -t / 2]
    thR, thL = out["R"]["thigh"], out["L"]["thigh"]
    # arms swing opposite to the legs
    out["armR"] = (-g["arm_gain"] * (thL - 6), 8, g["elbow"] + 0.5 * max(0, -g["arm_gain"] * (thL - 6)))
    out["armL"] = (-g["arm_gain"] * (thR - 6), 8, g["elbow"] + 0.5 * max(0, -g["arm_gain"] * (thR - 6)))
    if kind == "run":
        st["runband"] = 1.0
    out["mode"] = "RUN" if kind == "run" else "WALK"
    return out, st


def sequences():
    S = {}
    for kind in ("walk", "run"):
        n = GAIT[kind]["n"]
        fr = []
        for i in range(n):
            prm, st = gait_frame(kind, i / n)
            fr.append(dict(params=prm, states=st, strut=0.0, cc=False, ground="pelvis", loop=True))
        S[kind] = fr
    stand, chair, stoop = POSES["stand"], POSES["chair"], POSES["stoop"]
    # sit-down: knees start to bend, the strut swings down and plants, the leaf loads, the cam locks
    fr = []
    n = 34
    for i in range(n):
        t = i / (n - 1)
        b = _smooth((t - 0.05) / 0.85)
        prm = lerp_params(stand, chair, b)
        knee = (prm["L"]["thigh"] - prm["L"]["calf"]) / 90.0
        st = {"sit_leaf": max(0.0, knee), "lock": 1.0 if t > 0.93 else 0.0, "cc": _smooth((t - 0.80) / 0.15),
              "t3_off": 1.0 if t > 0.5 else 0.0}
        fr.append(dict(params=prm, states=st, strut=_smooth((t - 0.12) / 0.33), cc=t > 0.80, ground="foot", loop=False))
    S["sitdown"] = fr
    # stand-up: the cam opens, the leaf gives its energy back, the strut stows
    fr = []
    for i in range(n):
        t = i / (n - 1)
        b = _smooth((t - 0.08) / 0.80)
        prm = lerp_params(chair, stand, b)
        knee = (prm["L"]["thigh"] - prm["L"]["calf"]) / 90.0
        st = {"sit_return": max(0.0, knee) if t > 0.06 else 0.0, "lock": 1.0 if t < 0.06 else 0.0,
              "cc": 1.0 - _smooth(t / 0.12)}
        fr.append(dict(params=prm, states=st, strut=1.0 - _smooth((t - 0.62) / 0.33), cc=t < 0.12, ground="foot", loop=False))
    S["standup"] = fr
    # stoop lift: the lift tendon goes taut past 35 deg of bend, loads, and returns on the lift
    fr = []
    n = 40
    for i in range(n):
        t = i / (n - 1)
        if t < 0.45:
            b = _smooth(t / 0.45); down = True
        elif t < 0.55:
            b = 1.0; down = True
        else:
            b = 1.0 - _smooth((t - 0.55) / 0.45); down = False
        prm = lerp_params(stand, stoop, b)
        flex = prm["trunk"][2]
        load = max(0.0, min(1.0, (flex - 25) / 43.0))
        st = {"t3_load" if down else "t3_return": load, "sit_leaf_lift": 0.4 * load}
        fr.append(dict(params=prm, states=st, strut=0.0, cc=False, ground="foot", loop=False))
    S["stoop"] = fr
    return S
