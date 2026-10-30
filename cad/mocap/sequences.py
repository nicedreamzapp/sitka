"""Viewer animation sequences from REAL motion capture (CMU Graphics Lab, see CREDITS.md).

Used by cad/assemble/assemble.py -- --anim (default; `--procedural` keeps the old keyframed poses.py sequences).
Same motion choices as the Sitka promo film (sitka-video/blender/shots_v4.py):
  walk     CMU 35_01  Loop(a=1.125, T=1.125, w=0.12)
  run      CMU 35_17  Loop(a=0.375, T=0.75,  w=0.08)
  sitdown  CMU 86_09  yaw 90, clip 8.45-10.8 s  (the film's 7.3 s start walks in and turns; the viewer starts
                      as the turn ends and the sit begins; the feet are held where they settle at 9.0 s)
  standup  CMU 86_09  yaw 90, clip 23.2-25.0 s
  stoop    CMU 115_01 "pick up box, bend from waist", clip 0.35-2.15 s, the last 0.4 s eased back into the 0.35 s
           pose so the Lift program's replay has no seam
Look settings as the film: relaxed arms (per-category ranges), finger curl 1.0, neck gain 0.6, planted-foot pitch
fix, wide-hip stance (lat_gain 1.4), seated hands resting on the thighs (0.85, 0.10, 0.08).

build() returns {name: [frame, ...]}; every frame is a dict with
  apply(rig) -> world rig location (np 3-vector): poses the rig (matrix_basis) and returns where it goes
  states / strut / cc / loop : the same semantics as poses.sequences()
  fps (per sequence playback rate; seconds of real motion per frame = 1 / fps)
Grounding is calibrated per sequence like the film's pelvis_path(): each foot's pitch is trimmed so the planted
foot is flat, then each foot's height so its planted sole sits at SOLE. The vertical bob is the mocap's own.
Walk/run: the average travel is removed (the body walks on the spot, its natural pelvis sway kept) so the loop
is seamless and the root never drifts. Sit/stand/stoop: one constant shift per sequence (feet under the origin).
"""
import math
import numpy as np
import retarget as RT

SOLE = 0.022

ARMS = {"walk": dict(abd=(4, 9), swing=24, elbow=(14, 45)),
        "run": dict(abd=(4, 12), swing=55, elbow=(55, 110)),
        "sit": dict(abd=(4, 9), swing=24, elbow=(14, 45)),
        "lift": dict(abd=(4, 14), swing=95, elbow=(10, 120))}


def ease(x):
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


def ramp(t, a, b):
    return ease((t - a) / (b - a))


class Clipped:
    """a clip played in its own time (t = clip seconds)"""
    def __init__(self, clp):
        self.c = clp

    def state(self, tg, t):
        return tg.state(self.c, t)


class FeetLocked:
    """the feet stay exactly where (and as) they were at t_ref: ankle IK targets and foot/toe rotations held.
    The seated subject of 86_09 shuffles both feet a few cm after sitting down; the viewer keeps them set."""
    def __init__(self, inner, t_ref):
        self.inner, self.t_ref = inner, t_ref

    def state(self, tg, t):
        rots, pos = self.inner.state(tg, t)
        r0, p0 = self.inner.state(tg, self.t_ref)      # with the current trims (they vary per frame)
        rots, pos = dict(rots), dict(pos)
        for sd in ("l", "r"):
            pos["ank_" + sd] = p0["ank_" + sd]
            rots["foot_" + sd] = r0["foot_" + sd]; rots["ball_" + sd] = r0["ball_" + sd]
        return rots, pos


class Settle:
    """the clip played as is, then eased back into its own t_ref pose over [a, b] (rotations slerped, IK targets
    lerped). The Lift program replays the stoop back to back: 115_01's subject stands back up ~3 cm further
    forward over the feet than he started, so without this the replay snaps the hips back at the seam."""
    def __init__(self, inner, t_ref, a, b):
        self.inner, self.t_ref, self.a, self.b = inner, t_ref, a, b

    def state(self, tg, t):
        A = self.inner.state(tg, t)
        if t <= self.a:
            return A
        return RT.blend(A, self.inner.state(tg, self.t_ref), ramp(t, self.a, self.b))


C86 = None


def specs():
    global C86
    C86 = RT.clip("86_09", yaw=90.0)
    hands = RT.window(9.4, 10.2, 23.55, 24.15)          # = the film's SIT2_HANDS, in clip time
    calm = lambda t: ramp(t, 23.85, 24.3)               # after standing: arms hang (the subject gestures)
    walk = RT.Loop(RT.clip("35_01"), a=1.125, T=1.125, w=0.12)
    run = RT.Loop(RT.clip("35_17"), a=0.375, T=0.75, w=0.08)
    S = {
        "walk": dict(track=walk, t0=0.0, t1=walk.T, n=27, loop=True, arms="walk", group="walk"),
        # lat: CMU 35_17 runs with a crossover gait (each foot lands up to 4 cm past the body's midline); on the
        # wider Sitka hips and thigh shells that reads as crossed legs, so the run's feet go 5 cm further out
        "run": dict(track=run, t0=0.0, t1=run.T, n=24, loop=True, arms="run", group="run", lat=0.05),
        "sitdown": dict(track=FeetLocked(Clipped(C86), 9.0), t0=8.45, t1=10.8, n=36, loop=False, arms="sit", hands=hands, calm=calm,
                        group="sit", strut=lambda t: ramp(t, 8.45, 9.7)),
        "standup": dict(track=FeetLocked(Clipped(C86), 9.0), t0=23.2, t1=25.0, n=28, loop=False, arms="sit", hands=hands, calm=calm,
                        group="sit", strut=lambda t: 1.0 - ramp(t, 23.75, 24.5)),     # the film's SIT2_DEPLOY stow
        "stoop": dict(track=Settle(Clipped(RT.clip("115_01")), 0.35, 1.75, 2.15), t0=0.35, t1=2.15, n=37, loop=False, arms="lift", group="stoop"),
    }
    for k, s in S.items():
        dur = s["t1"] - s["t0"]
        s["times"] = [s["t0"] + dur * i / (s["n"] if s["loop"] else s["n"] - 1) for i in range(s["n"])]
        s["fps"] = (s["n"] if s["loop"] else s["n"] - 1) / dur
    return S


def build(rig, body, bpy, Matrix, dom, foot_ref_xy, log=print):
    """foot_ref_xy: where the midpoint of the two ankles goes for sit/stand/stoop (the standing pose's)"""
    tg = RT.Target(rig)
    tg.lat_gain = 1.4; tg.arm_carry = 0.0; tg.arm_abd = 0.0
    tg.finger_curl = 1.0; tg.relaxed_arms = True; tg.use_pitch_fix = True; tg.neck_gain = 0.6
    tg.rest_along, tg.rest_up, tg.rest_out = 0.85, 0.10, 0.08
    FOOT = {sd: np.where(np.isin(dom, ["foot_" + sd, "ball_" + sd]))[0] for sd in ("l", "r")}
    S = specs()
    CAL = {}        # group -> (pitch_trim, side_dz)
    ROOT = {}       # group -> root height offset (m): planted knees bend like the source's
    CURVE = {}      # sequence -> per-frame planted-foot trims
    for k, s_ in S.items():
        s_["name"] = k

    def configure(s, t):
        a = ARMS[s["arms"]]
        tg.abd_range, tg.swing_max, tg.elbow_range = a["abd"], a["swing"], a["elbow"]
        tg.arm_calm = s["calm"](t) if "calm" in s else 0.0
        tg.lat = s.get("lat", 0.0)
        pt, sz = CAL.get(s["group"], ({"l": 0.0, "r": 0.0}, {"l": 0.0, "r": 0.0}))
        # grounding: sz lifts each ankle so its sole sits on the floor; the root (pelvis) height is calibrated
        # separately (ROOT) so the planted legs bend as much as the subject's did. Before, the root stayed at the
        # mocap height while the ankles were lifted 1.5-6 cm, which folded every standing knee 17-43 deg.
        root = ROOT.get(s["group"], 0.0)
        tg.oz = root
        tg.pitch_trim, tg.side_dz = dict(pt), {sd: sz[sd] - root for sd in ("l", "r")}
        cv = CURVE.get(s["name"])
        if cv is not None:       # per-frame planted-foot trims (sit / stand / stoop)
            for sd in ("l", "r"):
                tg.pitch_trim[sd] += float(np.interp(t, cv["t"], cv["p_" + sd]))
                tg.side_dz[sd] += float(np.interp(t, cv["t"], cv["z_" + sd]))

    def pose(s, t):
        configure(s, t)
        rots, pos = s["track"].state(tg, t)
        rots = dict(rots)
        T = tg.solve_legs(rots, pos)
        if "hands" in s:
            tg.rest_hands_on_thighs(rots, s["hands"](t))
        tg.apply(rig, rots, Matrix)
        return T

    def sample(s, t):
        """pose + read back: world body verts (rig at T), bone vectors"""
        rig.location = (0, 0, 0)
        T = pose(s, t)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(dg); me = ev.to_mesh()
        co = np.empty(len(me.vertices) * 3); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
        V = co.reshape(-1, 3) + T
        B = {b: (np.array(rig.pose.bones[b].head) + T, np.array(rig.pose.bones[b].tail) + T)
             for b in ("pelvis", "spine_02", "thigh_l", "calf_l", "thigh_r", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r")}
        return T, V, B

    def foot_info(V, B, sd):
        ix = FOOT[sd]
        v = B["ball_" + sd][1] - B["foot_" + sd][0]
        r0 = np.array(rig.data.bones["ball_" + sd].tail_local) - np.array(rig.data.bones["foot_" + sd].head_local)
        fp = math.degrees(math.atan2(v[2], np.linalg.norm(v[:2]))) - math.degrees(math.atan2(r0[2], np.linalg.norm(r0[:2])))
        return V[ix, 0].mean(), V[ix, 1].mean(), V[ix, 2].min(), fp

    # ---------------------------------------------------------- grounding calibration (the film's pelvis_path)
    groups = {}
    for k, s in S.items():
        groups.setdefault(s["group"], []).append(k)
    for g, names in groups.items():
        CAL[g] = ({"l": 0.0, "r": 0.0}, {"l": 0.0, "r": 0.0})
        for it in range(3):
            FP = {"l": [], "r": []}
            EX = []
            for k in names:
                s = S[k]
                ts = np.arange(s["t0"], s["t1"] + 1e-6, 1 / 60.0)
                rec = {"l": [], "r": []}
                exd = {"l": [], "r": []}
                for t in ts:
                    _, V, B = sample(s, t)
                    for sd in ("l", "r"):
                        rec[sd].append(foot_info(V, B, sd))
                        exd[sd].append(tg.ext_dz[sd])
                for sd in ("l", "r"):
                    A = np.array(rec[sd])
                    v = np.zeros(len(A)); v[1:] = np.linalg.norm(np.diff(A[:, :2], axis=0), axis=1) * 60
                    low = A[:, 2] < np.percentile(A[:, 2], 20) + 0.03
                    sel = (v < (0.12 if k == "run" else 0.08)) & low
                    if sel.sum() < 6:
                        # short stances (running): the foot's lowest tenth of the samples is its contact
                        sel = A[:, 2] <= np.percentile(A[:, 2], 10)
                    FP[sd].append(A[sel])
                    EX.append(np.array(exd[sd])[sel])
            pt, sz = CAL[g]
            for sd in ("l", "r"):
                A = np.concatenate(FP[sd]) if FP[sd] else np.zeros((0, 4))
                if len(A) < 4:
                    log("CAL %s %s: only %d planted samples" % (g, sd, len(A)))
                    continue
                if it == 0:
                    pt[sd] = float(np.clip(np.median(A[:, 3]), -30, 30))
                else:
                    sz[sd] += SOLE - float(np.median(A[:, 2]))
            if it >= 1:
                ex = np.concatenate(EX) if EX else np.zeros(0)
                if len(ex):
                    ROOT[g] = ROOT.get(g, 0.0) + float(np.median(ex))
            log("CAL %s pass %d root %.4f pitch %s side_dz %s planted %s" % (g, it, ROOT.get(g, 0.0), {k: round(v, 1) for k, v in pt.items()},
                {k: round(v, 4) for k, v in sz.items()}, {sd: sum(len(a) for a in FP[sd]) for sd in FP}))

    # ---------------------------------------------------------- per-frame planted-foot trims (feet that stay down)
    # The constant trims leave a few mm-cm of sink/float where the source foot rolls (seated heel lifts, marker
    # drift). For the non-cyclic sequences: on every planted sample the foot is made flat and its sole put on
    # SOLE; across a lifted step the trim is interpolated between the planted samples; then smoothed.
    def measure(s):
        ts = np.arange(s["t0"] - 0.1, s["t1"] + 0.1 + 1e-6, 1 / 60.0)
        rec = {"l": [], "r": []}
        for t in ts:
            _, V, B = sample(s, t)
            for sd in ("l", "r"):
                rec[sd].append(foot_info(V, B, sd))
        return ts, {sd: np.array(rec[sd]) for sd in rec}

    def smooth(x, sig=4):
        k = np.arange(-3 * sig, 3 * sig + 1); g = np.exp(-0.5 * (k / sig) ** 2); g /= g.sum()
        return np.convolve(np.pad(x, (3 * sig, 3 * sig), mode="edge"), g, mode="valid")

    for k, s in S.items():
        if s["loop"]:
            continue
        cv = None
        for it, what in enumerate(("p", "z", "z")):
            ts, A = measure(s)
            if cv is None:
                cv = {"t": ts, **{w + "_" + sd: np.zeros(len(ts)) for w in "pz" for sd in "lr"}}
            msg = []
            for sd in ("l", "r"):
                a = A[sd]
                v = np.zeros(len(a)); v[1:] = np.linalg.norm(np.diff(a[:, :2], axis=0), axis=1) * 60; v[0] = v[1]
                pl = (v < 0.10) & (a[:, 2] < SOLE + 0.025)
                if pl.sum() < 3:
                    continue
                e = a[:, 3] if what == "p" else SOLE - a[:, 2]
                cv[what + "_" + sd] += smooth(np.interp(ts, ts[pl], e[pl]))
                msg.append("%s planted %d/%d err %s max %.1f" % (sd, pl.sum(), len(ts), what, np.abs(e[pl]).max() * (1 if what == "p" else 1000)))
            CURVE[k] = cv
            log("TRIM %s pass %d: %s" % (k, it, "; ".join(msg)))

    # ---------------------------------------------------------- frames + states
    out = {}
    sit_off = None
    for k, s in S.items():
        rec = []
        for t in s["times"]:
            T, V, B = sample(s, t)
            d = lambda b: B[b][1] - B[b][0]
            ang = lambda a, b: math.degrees(math.acos(max(-1.0, min(1.0, np.dot(a, b) / np.linalg.norm(a) / np.linalg.norm(b)))))
            knee = {sd: ang(d("thigh_" + sd), d("calf_" + sd)) for sd in ("l", "r")}
            th = {}
            for sd in ("l", "r"):      # thigh forward pitch (+ = knee ahead of the hip), world sagittal plane
                u = d("thigh_" + sd); th[sd] = math.degrees(math.atan2(-u[1], -u[2]))
            flex = ang(d("spine_02"), np.array([0.0, 0.0, 1.0]))
            feet = {sd: foot_info(V, B, sd) for sd in ("l", "r")}
            ank = 0.5 * (B["foot_l"][0] + B["foot_r"][0])
            rec.append(dict(t=t, T=T, pel=B["pelvis"][0], knee=knee, th=th, flex=flex, feet=feet, ank=ank))
        n = len(rec)
        # placement
        if s["loop"]:
            # travel per period: the track at t0 + period is the same pose moved by D
            T_end, _, B_end = sample(s, s["t1"])
            D = B_end["pelvis"][0] - rec[0]["pel"]; D[2] = 0.0
            per = s["t1"] - s["t0"]
            rel = [r["pel"] - D * (r["t"] - s["t0"]) / per for r in rec]
            c = np.mean(rel, axis=0); c[2] = 0.0
            offs = [-D * (r["t"] - s["t0"]) / per - c for r in rec]
            log("SEQ %s travel per loop %.3f m, speed %.2f m/s" % (k, np.linalg.norm(D), np.linalg.norm(D) / per))
        else:
            if k == "standup" and sit_off is not None:
                o = sit_off            # same clip, same world: the stand-up starts where the sit-down ended
            else:
                o = np.array([foot_ref_xy[0] - rec[0]["ank"][0], foot_ref_xy[1] - rec[0]["ank"][1], 0.0])
            if k == "sitdown":
                sit_off = o
            offs = [o] * n
        # states
        frames = []
        if s["loop"]:
            # gait phase per leg from the heel strike (first planted frame of each stance, cyclic)
            con = {}
            for sd in ("l", "r"):
                z = np.array([r["feet"][sd][2] for r in rec])
                xy = np.array([[r["feet"][sd][0], r["feet"][sd][1]] for r in rec])     # world (travelling) frame
                sp = np.linalg.norm(xy - np.roll(xy, 1, axis=0), axis=1) * s["fps"]
                sp[0] = sp[1]          # (frame 0 vs the last frame straddle the loop seam)
                con[sd] = (z < SOLE + 0.012) & (sp < 1.0)
            strike = {}
            for sd in ("l", "r"):
                c_ = con[sd]
                idx = [i for i in range(n) if c_[i] and not c_[i - 1]]
                strike[sd] = idx[0] if idx else (0 if sd == "r" else n // 2)
            for i, r in enumerate(rec):
                st = {}
                for sd in ("l", "r"):
                    ph = ((i - strike[sd]) % n) / n
                    stance = bool(con[sd][i])
                    st["ea_" + sd] = 1.0 if (k == "walk" and stance and ph < 0.45) else 0.0
                    st["m3_" + sd] = max(0.0, min(1.0, -r["th"][sd] / 15.0))
                    st["ham_" + sd] = max(0.0, min(1.0, (ph - 0.80) / 0.12)) if (ph > 0.80 and not stance) else 0.0
                    st["t1_" + sd] = 0.0
                if k == "run":
                    st["runband"] = 1.0
                frames.append(dict(states=st, strut=0.0, cc=False))
        elif k == "sitdown":
            z = np.array([r["pel"][2] for r in rec]); z0, zf = z[0], z.min()
            desc = np.clip((z0 - z) / max(1e-3, z0 - zf), 0, 1)
            i_seat = int(np.argmax(desc >= 0.97)); t_seat = rec[i_seat]["t"]
            for i, r in enumerate(rec):
                t = r["t"]
                kn = 0.5 * (r["knee"]["l"] + r["knee"]["r"])
                cc = ease((t - (t_seat - 0.25)) / 0.4)
                st = {"sit_leaf": max(0.0, min(1.0, (kn - 12) / 78.0)), "lock": 1.0 if t >= t_seat + 0.15 else 0.0,
                      "cc": cc, "t3_off": 1.0 if desc[i] > 0.5 else 0.0}
                frames.append(dict(states=st, strut=s["strut"](t), cc=cc > 0.0))
            log("SEQ sitdown seated at clip %.2f s (frame %d of %d)" % (t_seat, i_seat, n))
        elif k == "standup":
            z = np.array([r["pel"][2] for r in rec]); zs, zt = z[0], z.max()
            rise = np.clip((z - zs) / max(1e-3, zt - zs), 0, 1)
            i_rise = int(np.argmax(rise > 0.03)); t_rise = rec[i_rise]["t"]
            for i, r in enumerate(rec):
                t = r["t"]
                kn = 0.5 * (r["knee"]["l"] + r["knee"]["r"])
                cc = 1.0 - ease((t - s["t0"]) / max(0.2, t_rise - s["t0"]))
                st = {"sit_return": max(0.0, min(1.0, (kn - 12) / 78.0)) if t >= t_rise - 0.05 else 0.0,
                      "lock": 1.0 if t < t_rise - 0.05 else 0.0, "cc": cc}
                frames.append(dict(states=st, strut=s["strut"](t), cc=cc > 0.0))
            log("SEQ standup rises at clip %.2f s (frame %d of %d)" % (t_rise, i_rise, n))
        else:   # stoop
            flex = np.array([r["flex"] for r in rec]); i_low = int(np.argmax(flex))
            for i, r in enumerate(rec):
                load = max(0.0, min(1.0, (r["flex"] - 25) / 43.0))
                st = {"t3_load" if i <= i_low else "t3_return": load, "sit_leaf_lift": 0.4 * load}
                frames.append(dict(states=st, strut=0.0, cc=False))
            log("SEQ stoop max trunk flexion %.0f deg at frame %d of %d" % (flex.max(), i_low, n))
        for i, (fr, r) in enumerate(zip(frames, rec)):
            fr.update(loop=s["loop"], fps=s["fps"], ground="mocap", t=r["t"])
            fr["apply"] = (lambda s_, t_, o_: (lambda rg: pose(s_, t_) + o_))(s, r["t"], offs[i])
        out[k] = frames
        log("SEQ %s %d frames, %.2f fps, clip %.2f-%.2f s" % (k, n, s["fps"], s["t0"], s["t1"]))
    return out
