"""Retarget CMU BVH motion capture onto the Sitka wearer (MPFB game_engine rig).

Method (free, plain Python):
  * long limb bones (thigh, calf, upper arm, forearm, hand): DIRECTION-EXACT. The target bone points
    exactly where the source segment points (joint -> child joint), and the twist about the bone comes
    from the source joint's rotation (its "front" vector), so shells on the thigh/shin keep facing forward.
    This is the rest-pose correction: CMU's zero pose has splayed legs and T-pose arms, MPFB rests in an
    A-pose, so only directions are transferred, never raw local angles.
  * pelvis, spine, neck, head, clavicles, feet, toes: WORLD DELTA from the (upright, world-aligned) BVH
    zero pose, applied on top of the MPFB rest orientation (both rests are upright and facing -Y).
  * a constant yaw per clip aligns the walking direction with -Y (the film's convention).
  * clips are cut into pieces, looped (seam crossfade) or chained; blending is quaternion slerp of the
    retargeted bone rotations, so limbs never shrink.
Root translation is NOT taken from the mocap: the engine's foot lock (stance foot planted, root
travels) and floor grounding give zero foot sliding by construction on the Sitka proportions.
"""
import os, sys, math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from bvh import BVH, AX as AX_  # noqa: E402
import anatomy as AN  # noqa: E402

SRC = os.path.join(HERE, "src")

DIR = {  # target bone: (source joint, source child joint or None for its end site)
    "thigh_l": ("LeftUpLeg", "LeftLeg"), "calf_l": ("LeftLeg", "LeftFoot"),
    "thigh_r": ("RightUpLeg", "RightLeg"), "calf_r": ("RightLeg", "RightFoot"),
    "upperarm_l": ("LeftArm", "LeftForeArm"), "lowerarm_l": ("LeftForeArm", "LeftHand"),
    "upperarm_r": ("RightArm", "RightForeArm"), "lowerarm_r": ("RightForeArm", "RightHand"),
    "hand_l": ("LeftHand", "LeftHandIndex1"), "hand_r": ("RightHand", "RightHandIndex1"),
}
DELTA = {
    "pelvis": "Hips", "spine_01": "LowerBack", "spine_02": "Spine", "spine_03": "Spine1",
    "neck_01": "Neck1", "head": "Head", "clavicle_l": "LeftShoulder", "clavicle_r": "RightShoulder",
    "foot_l": "LeftFoot", "foot_r": "RightFoot", "ball_l": "LeftToeBase", "ball_r": "RightToeBase",
}
ORDER = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "upperarm_l", "lowerarm_l",
         "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "thigh_l", "calf_l", "foot_l", "ball_l",
         "thigh_r", "calf_r", "foot_r", "ball_r"]
FWD = np.array([0.0, -1.0, 0.0])


def _basis(d, s):
    e1 = d / np.linalg.norm(d)
    e2 = s - e1 * np.dot(e1, s)
    e2 /= np.linalg.norm(e2)
    return np.stack([e1, e2, np.cross(e1, e2)], axis=1)


def _rot_between(a, b):
    a = a / np.linalg.norm(a); b = b / np.linalg.norm(b)
    v = np.cross(a, b); c = float(np.dot(a, b))
    if c < -0.9999:
        return -np.eye(3)
    K = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + K + K @ K / (1 + c)


def _axis_angle(axis, deg):
    a = np.asarray(axis, float); a = a / np.linalg.norm(a)
    th = math.radians(deg)
    K = np.array([[0, -a[2], a[1]], [a[2], 0, -a[0]], [-a[1], a[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def _rz(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), -math.sin(a), 0], [math.sin(a), math.cos(a), 0], [0, 0, 1]])


def _rx(deg):
    a = math.radians(deg)
    return np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])


def _ry(deg):
    a = math.radians(deg)
    return np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])


# ------------------------------------------------------------------ quaternion helpers (w, x, y, z)
def m2q(M):
    t = np.trace(M)
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = np.array([0.25 * s, (M[2, 1] - M[1, 2]) / s, (M[0, 2] - M[2, 0]) / s, (M[1, 0] - M[0, 1]) / s])
    elif M[0, 0] > M[1, 1] and M[0, 0] > M[2, 2]:
        s = math.sqrt(1.0 + M[0, 0] - M[1, 1] - M[2, 2]) * 2
        q = np.array([(M[2, 1] - M[1, 2]) / s, 0.25 * s, (M[0, 1] + M[1, 0]) / s, (M[0, 2] + M[2, 0]) / s])
    elif M[1, 1] > M[2, 2]:
        s = math.sqrt(1.0 + M[1, 1] - M[0, 0] - M[2, 2]) * 2
        q = np.array([(M[0, 2] - M[2, 0]) / s, (M[0, 1] + M[1, 0]) / s, 0.25 * s, (M[1, 2] + M[2, 1]) / s])
    else:
        s = math.sqrt(1.0 + M[2, 2] - M[0, 0] - M[1, 1]) * 2
        q = np.array([(M[1, 0] - M[0, 1]) / s, (M[0, 2] + M[2, 0]) / s, (M[1, 2] + M[2, 1]) / s, 0.25 * s])
    return q / np.linalg.norm(q)


def q2m(q):
    w, x, y, z = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def slerp(a, b, s):
    d = float(np.dot(a, b))
    if d < 0:
        b = -b; d = -d
    if d > 0.9995:
        q = a + (b - a) * s
        return q / np.linalg.norm(q)
    th = math.acos(d)
    return (math.sin((1 - s) * th) * a + math.sin(s * th) * b) / math.sin(th)


def blend(A, B, s):
    """blend two states (rotations dict, positions dict)"""
    if s <= 0:
        return A
    if s >= 1:
        return B
    return ({k: q2m(slerp(m2q(A[0][k]), m2q(B[0][k]), s)) for k in A[0]},
            {k: A[1][k] * (1 - s) + B[1][k] * s for k in A[1]})


# ------------------------------------------------------------------ source clips
_CACHE = {}


class Clip:
    def __init__(self, name, yaw=None, yaw_window=None):
        self.name = name
        b = BVH(os.path.join(SRC, name + ".bvh"))
        I = b.idx
        leg = np.linalg.norm(b.offset[I["LeftLeg"]]) + np.linalg.norm(b.offset[I["LeftFoot"]])
        b.to_sitka(0.94 / leg)
        self.b, self.I, self.dt = b, I, b.dt
        self.nf = b.nf
        if yaw is None:
            # heading of the hips' travel over a window (default: the whole clip, skipping the T-pose frame 0)
            a, c = yaw_window or (1, b.nf - 1)
            a = int(a / b.dt) if isinstance(a, float) else a
            c = int(c / b.dt) if isinstance(c, float) else c
            v = b.Ps[I["Hips"], c] - b.Ps[I["Hips"], a]
            yaw = -math.degrees(math.atan2(v[0], -v[1]))        # rotate travel onto -Y
        self.yaw = yaw
        Rz = _rz(yaw)
        # each source leg's own length (CMU skeletons are not symmetric: 115_01's right leg is 1.5 % shorter)
        self.leg_len = {sd: (np.linalg.norm(b.offset[I[s + "Leg"]]) + np.linalg.norm(b.offset[I[s + "Foot"]])) * b.scale
                        for sd, s in (("l", "Left"), ("r", "Right"))}
        self.R = np.einsum("ab,jfbc->jfac", Rz, b.Rs)
        self.P = np.einsum("ab,jfb->jfa", Rz, b.Ps)
        self.dur = (b.nf - 1) * b.dt
        self.fix = {sd: self._contact_fix(sd) for sd in ("l", "r")}
        self.pitch_fix = {sd: self._pitch_fix(sd) for sd in ("l", "r")}

    def _pitch_fix(self, sd):
        """foot pitch (deg) of this subject's PLANTED foot relative to its zero-pose foot: the delta retarget
        assumes the zero pose is a flat foot; a subject whose planted foot reads toes-up/down gets corrected"""
        I = self.I
        a, b = ("LeftFoot", "LeftToeBase") if sd == "l" else ("RightFoot", "RightToeBase")
        v = self.P[I[b]] - self.P[I[a]]
        pitch = np.degrees(np.arctan2(v[:, 2], np.linalg.norm(v[:, :2], axis=1)))
        r = (AX_ @ self.b.offset[I[b]])
        rest = np.degrees(np.arctan2(r[2], np.linalg.norm(r[:2])))
        sel = np.zeros(self.nf, bool)
        for t0, t1 in self.runs[sd]:
            sel[1 + int(t0 / self.dt):1 + int(t1 / self.dt)] = True
        if sel.sum() < 10:
            return 0.0
        return float(np.median(pitch[sel]) - rest)

    def _contact_fix(self, sd, v_max=0.3, z_tol=0.025, blend_s=0.1):
        """foot contact clean-up: while the ball of the foot is down and slow, it is pinned to one spot on a
        common floor height (mocap marker drift and floor bumps removed); the correction fades in/out over
        blend_s. Returns the per-frame correction (nf, 3) added to that side's ankle."""
        I = self.I
        ball = self.P[I["LeftToeBase" if sd == "l" else "RightToeBase"]]
        nf, dt = self.nf, self.dt
        v = np.zeros(nf)
        v[1:-1] = np.linalg.norm(ball[2:, :2] - ball[:-2, :2], axis=1) / (2 * dt)
        v[0], v[-1] = v[1], v[-2]
        k = np.ones(9) / 9; v = np.convolve(v, k, mode="same")
        floor = np.percentile(ball[1:, 2], 10)
        ank = self.P[I["LeftFoot" if sd == "l" else "RightFoot"]]
        va = np.zeros(nf)
        va[1:-1] = np.linalg.norm(ank[2:, :2] - ank[:-2, :2], axis=1) / (2 * dt)
        va = np.convolve(va, k, mode="same")
        # planted = ball down and slow, OR the whole foot resting still (seated feet with the toes a bit up)
        m = ((v < v_max) & (ball[:, 2] < floor + z_tol)) | ((v < 0.08) & (va < 0.08) & (ball[:, 2] < floor + 0.06))
        m[0] = False
        runs, i = [], 1
        while i < nf:
            if m[i]:
                j = i
                while j + 1 < nf and m[j + 1]:
                    j += 1
                if (j - i + 1) * dt >= 0.08:
                    runs.append((i, j))
                i = j + 1
            else:
                i += 1
        C = np.zeros((nf, 3)); W = np.zeros(nf)
        nb = max(1, int(blend_s / dt))
        for i0, i1 in runs:
            tgt = np.array([ball[i0:i1 + 1, 0].mean(), ball[i0:i1 + 1, 1].mean(), floor])
            for f in range(max(1, i0 - nb), min(nf, i1 + nb + 1)):
                g = tgt - ball[min(max(f, i0), i1)] if f < i0 or f > i1 else tgt - ball[f]
                if f < i0:
                    w = 1 - (i0 - f) / nb
                elif f > i1:
                    w = 1 - (f - i1) / nb
                else:
                    w = 1.0
                w = w * w * (3 - 2 * w)
                if w > W[f]:
                    W[f] = w
                    C[f] = g * w
        self.runs = getattr(self, "runs", {}); self.runs[sd] = [(i0 * dt - dt, i1 * dt - dt) for i0, i1 in runs]
        # height: one constant shift per foot (the median planted correction), everywhere, so a resting foot,
        # a walking foot and a swinging foot all sit at the same consistent height
        dz = [floor - ball[f, 2] for i0, i1 in runs for f in range(i0, i1 + 1) if ball[f, 2] < floor + z_tol]
        C[:, 2] = float(np.median(dz)) if dz else 0.0
        return C

    def fix_at(self, sd, t):
        x = 1 + t / self.dt
        x = min(max(x, 1), self.nf - 1.001)
        i = int(x); f = x - i
        return self.fix[sd][i] * (1 - f) + self.fix[sd][i + 1] * f

    def sample(self, t):
        """joint world rotations/positions at clip time t (s); frame 0 (the T-pose) is skipped"""
        x = 1 + t / self.dt
        x = min(max(x, 1), self.nf - 1.001)
        i = int(x); f = x - i
        R = self.R[:, i] * (1 - f) + self.R[:, i + 1] * f
        P = self.P[:, i] * (1 - f) + self.P[:, i + 1] * f
        return R, P


def clip(name, **kw):
    key = (name, tuple(sorted(kw.items())))
    if key not in _CACHE:
        _CACHE[key] = Clip(name, **kw)
    return _CACHE[key]


# ------------------------------------------------------------------ the retarget
class Target:
    def __init__(self, rig):
        self.rest = {}
        self.d0, self.f0 = {}, {}
        self.parent = {}
        self.local = {}
        for bn in rig.data.bones:
            M = np.array(bn.matrix_local)
            self.rest[bn.name] = M
            self.parent[bn.name] = bn.parent.name if bn.parent else None
        for b in DIR:
            bn = rig.data.bones[b]
            d = np.array(bn.tail_local) - np.array(bn.head_local)
            self.d0[b] = d / np.linalg.norm(d)
        self.order = [bn.name for bn in rig.data.bones]   # parents come first
        self.foot_pitch = 0.0
        self.arm_abd = 0.0
        self.oz = 0.0          # grounding offset (calibrated per shot)
        self.lat = 0.0
        self.lat_gain = 1.0    # 1 = feet as far apart as the (wider) Sitka hips
        self.contact_fix = True
        self.arm_carry = 0.0
        self.neck_gain = 1.0
        self.finger_curl = 0.0
        self.relaxed_arms = False
        self.abd_range = (4.0, 9.0)       # deg sideways lift of the upper arm (chest frame)
        self.swing_gain = 0.9
        self.elbow_range = (14.0, 45.0)
        self.swing_max = 24.0
        self.shift = np.zeros(3)  # world placement of the whole motion
        self.recline = 0.0        # deg, seated lean-back on the back panel
        self.abd_extra = {"l": 0.0, "r": 0.0}   # per-frame clearance lift (deg), solved in the shot pre-pass
        self.rest_along, self.rest_up, self.rest_out = 0.58, 0.115, 0.035   # seated hand spot on the thigh
        self.arm_calm = 0.0       # 0..1: settle the arms to hang still (damps source gestures)
        self.use_pitch_fix = False
        self.pitch_trim = {"l": 0.0, "r": 0.0}   # calibrated per shot: planted feet flat on the ground
        self.side_dz = {"l": 0.0, "r": 0.0}   # per-foot grounding trim (calibrated per shot)
        self.foot_dir0 = {}
        for sd in ("l", "r"):
            v = np.array(rig.data.bones["ball_" + sd].tail_local) - np.array(rig.data.bones["foot_" + sd].head_local)
            self.foot_dir0[sd] = v / np.linalg.norm(v)
        self.len = {}
        for b in ("thigh_l", "calf_l", "thigh_r", "calf_r", "upperarm_l", "lowerarm_l", "upperarm_r", "lowerarm_r"):
            bn = rig.data.bones[b]
            self.len[b] = float(np.linalg.norm(np.array(bn.tail_local) - np.array(bn.head_local)))

    POLE_SRC_MM = (0.015, 0.05)   # source knee offset (m) below which the mocap knee has no say in the bend plane
    REACH = 0.999                 # the straightest a leg gets (~5 deg knee bend) before the pelvis drops
    POLE_MAX_DEG = 6.0            # most the mocap knee may turn the bend plane off the leg's forward direction

    ARM_BONES = ("clavicle_l", "upperarm_l", "lowerarm_l", "hand_l", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r")

    def state(self, clp, t, shift=None, arms=None):
        """(bone rotations, IK positions) for clip time t; shift = xy offset added to positions (loops).
        arms = (clip2, time_map, weight_fn): an ARM LAYER - the arms come from another mocap clip, carried in
        the chest's frame (so they ride on this clip's trunk), blended in with weight_fn(t)."""
        st = self._state(clp, t, shift)
        if arms:
            c2, tmap, wfn = arms
            w = float(wfn(t))
            if w > 0:
                R2, P2 = c2.sample(tmap(t))
                r2 = self.rotations_from(R2, P2, c2.I)
                rots = st[0]
                # carry the layer in a frame part-way between the world and the chest (self.arm_carry: 0 world, 1 chest)
                Cw = q2m(slerp(m2q(np.eye(3)), m2q(rots["spine_03"] @ r2["spine_03"].T), self.arm_carry))
                for b in self.ARM_BONES:
                    want = Cw @ r2[b]
                    rots[b] = q2m(slerp(m2q(rots[b]), m2q(want), w)) if w < 1 else want
        return st

    def _state(self, clp, t, shift=None):
        R, P = clp.sample(t)
        I = clp.I
        pos = {"mid_hip": 0.5 * (P[I["LeftUpLeg"]] + P[I["RightUpLeg"]]),
               "ank_l": P[I["LeftFoot"]], "ank_r": P[I["RightFoot"]],
               "knee_l": P[I["LeftLeg"]], "knee_r": P[I["RightLeg"]],
               "hip_l": P[I["LeftUpLeg"]], "hip_r": P[I["RightUpLeg"]]}
        # how straight each source leg is (hip-ankle distance / that leg's length): the knee bend to reproduce
        for sd, s in (("l", "Left"), ("r", "Right")):
            pos["ext_" + sd] = np.array([np.linalg.norm(P[I[s + "Foot"]] - P[I[s + "UpLeg"]]) / clp.leg_len[sd]])
        if self.contact_fix:
            pos["ank_l"] = pos["ank_l"] + clp.fix_at("l", t)
            pos["ank_r"] = pos["ank_r"] + clp.fix_at("r", t)
        # target hips are wider than CMU's: push each ankle out along the pelvis' lateral axis
        lx = R[I["Hips"]] @ np.array([1.0, 0.0, 0.0]); lx[2] = 0.0; lx /= np.linalg.norm(lx)
        half = 0.5 * np.linalg.norm(P[I["LeftUpLeg"]] - P[I["RightUpLeg"]])
        extra = (self.rest["thigh_l"][0, 3] - half) * self.lat_gain
        pos["ank_l"] = pos["ank_l"] + lx * extra
        pos["ank_r"] = pos["ank_r"] - lx * extra
        if shift is not None:
            pos = {k: v + shift for k, v in pos.items()}
        rots = self.rotations_from(R, P, I)
        if self.use_pitch_fix:
            for sd in ("l", "r"):
                ang = self.pitch_trim[sd]       # deg; + turns the toes down
                if abs(ang) > 0.5:
                    lat = rots["foot_" + sd] @ np.linalg.inv(self.rest["foot_" + sd][:3, :3]) @ np.array([1.0, 0.0, 0.0])
                    Rq = _axis_angle(lat, ang)
                    for b in ("foot_", "ball_"):
                        rots[b + sd] = Rq @ rots[b + sd]
        return rots, pos

    def rotations_from(self, R, P, I):
        """target bone world (armature) rotations from source world rotations/positions"""
        out = {}
        for b, j in DELTA.items():
            Rj = R[I[j]]
            out[b] = Rj @ self.rest[b][:3, :3]
        for b, (j, c) in DIR.items():
            d = P[I[c]] - P[I[j]]
            s = R[I[j]] @ FWD
            out[b] = _basis(d, s) @ _basis(self.d0[b], FWD).T @ self.rest[b][:3, :3]
        if self.neck_gain < 1.0:
            # the MPFB neck skins badly when folded hard (CMU looks down a lot while sitting): keep a share of the
            # mocap neck/head motion relative to the chest, the rest follows the chest rigidly
            for b in ("neck_01", "head"):
                rigid = out["spine_03"] @ self.rest["spine_03"][:3, :3].T @ self.rest[b][:3, :3]
                out[b] = q2m(slerp(m2q(rigid), m2q(out[b]), self.neck_gain))
        if self.foot_pitch:
            for sd in ("l", "r"):
                for b in ("foot_", "ball_"):
                    # pitch about the foot's own lateral axis (world X rotated by the foot yaw)
                    Rf = out[b + sd]
                    out[b + sd] = Rf @ np.linalg.inv(self.rest[b + sd][:3, :3]) @ _rx(self.foot_pitch) @ self.rest[b + sd][:3, :3]
        if self.recline:
            # lean back on the seat: the trunk (and everything above it) rotates back about the hips' lateral axis
            Rr = _axis_angle(np.array([1.0, 0.0, 0.0]), -self.recline)
            for b in ("pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r",
                      "upperarm_l", "lowerarm_l", "hand_l", "upperarm_r", "lowerarm_r", "hand_r"):
                out[b] = Rr @ out[b]
        if self.relaxed_arms:
            self._relax_arms(out, R, P, I)
        if self.arm_abd:
            for sd, sg in (("l", -1), ("r", 1)):
                Rab = _ry(sg * self.arm_abd)  # about forward-ish axis: lifts the arm sideways
                for b in ("upperarm_", "lowerarm_", "hand_"):
                    out[b + sd] = Rab @ out[b + sd]
        return out

    def _relax_arms(self, out, R, P, I):
        """relaxed, natural arms: shoulders ride the chest (no shrug), the upper arm/forearm DIRECTIONS come from
        the mocap but the twist is carried down the chain from the rest pose (palms face the thighs, elbows point
        back), sideways lift is capped, the elbow keeps a soft bend, and the wrist is neutral (follows the forearm)."""
        rs = lambda b: self.rest[b][:3, :3]
        C = out["spine_03"] @ rs("spine_03").T
        lat_w = C @ np.array([1.0, 0.0, 0.0]); up_w = C @ np.array([0.0, 0.0, 1.0])
        for sd, A, F, H in (("l", "LeftArm", "LeftForeArm", "LeftHand"), ("r", "RightArm", "RightForeArm", "RightHand")):
            sg = 1.0 if sd == "l" else -1.0
            out["clavicle_" + sd] = C @ rs("clavicle_" + sd)
            u = P[I[F]] - P[I[A]]; u /= np.linalg.norm(u)
            f = P[I[H]] - P[I[F]]; f /= np.linalg.norm(f)
            # cap the sideways lift (in the chest frame); keep the fore/aft swing, scaled
            side = np.dot(u, lat_w) * sg
            down = -np.dot(u, up_w)
            fwd = u - lat_w * np.dot(u, lat_w) - up_w * np.dot(u, up_w)
            abd = math.degrees(math.atan2(side, max(down, 1e-3)))
            abd_c = min(max(abd, self.abd_range[0]), self.abd_range[1]) + self.abd_extra[sd]
            fwd *= self.swing_gain
            # cap the fore/aft swing (a relaxed arm never lifts far forward; damps source gestures)
            sm = self.swing_max + (5.0 - self.swing_max) * self.arm_calm
            fl = np.linalg.norm(fwd); fmax = math.sin(math.radians(sm))
            if fl > fmax:
                fwd *= fmax / fl
            h = math.sqrt(max(1e-6, 1.0 - np.dot(fwd, fwd)))
            u2 = fwd + h * (lat_w * sg * math.sin(math.radians(abd_c)) - up_w * math.cos(math.radians(abd_c)))
            u2 /= np.linalg.norm(u2)
            follow = out["clavicle_" + sd] @ rs("clavicle_" + sd).T @ rs("upperarm_" + sd)
            d_now = follow @ np.linalg.inv(rs("upperarm_" + sd)) @ self.d0["upperarm_" + sd]
            out["upperarm_" + sd] = _rot_between(d_now, u2) @ follow
            # forearm: same bend plane as the mocap, elbow flexion kept in a soft range
            el = math.degrees(math.acos(min(1.0, max(-1.0, np.dot(u, f)))))
            el_hi = self.elbow_range[1] + (18.0 - self.elbow_range[1]) * self.arm_calm
            el_c = min(max(el, self.elbow_range[0]), el_hi)
            ax = np.cross(u, f)
            if np.linalg.norm(ax) < 1e-4:
                ax = np.cross(u2, lat_w * sg)
            ax /= np.linalg.norm(ax)
            Rmap = _rot_between(u, u2)
            f2 = _axis_angle(Rmap @ ax, el_c) @ u2
            follow = out["upperarm_" + sd] @ rs("upperarm_" + sd).T @ rs("lowerarm_" + sd)
            d_now = follow @ np.linalg.inv(rs("lowerarm_" + sd)) @ self.d0["lowerarm_" + sd]
            out["lowerarm_" + sd] = _rot_between(d_now, f2) @ follow
            out["hand_" + sd] = out["lowerarm_" + sd] @ rs("lowerarm_" + sd).T @ rs("hand_" + sd)

    def rest_hands_on_thighs(self, rots, w):
        """seated: wrists settle on top of the thighs (about 60 % toward the knee), hands lying along the thigh"""
        if w <= 0:
            return
        pose, _ = self.fk(rots)
        for sd in ("l", "r"):
            H = pose["thigh_" + sd][:3, 3]; K = pose["calf_" + sd][:3, 3]
            ax = (K - H) / np.linalg.norm(K - H)
            upv = np.array([0.0, 0.0, 1.0]) - ax * ax[2]; upv /= np.linalg.norm(upv)
            sg = 1.0 if sd == "l" else -1.0
            tgt = H + (K - H) * self.rest_along + upv * self.rest_up + np.array([sg * self.rest_out, 0.0, 0.0])
            Wr = pose["hand_" + sd][:3, 3]
            self.arm_shift(rots, sd, (tgt - Wr) * w, pose)
            pose, _ = self.fk(rots)
            # hand lies along the thigh, palm down
            Rh = pose["hand_" + sd][:3, :3] @ np.linalg.inv(self.rest["hand_" + sd][:3, :3])
            hd = Rh @ self._hand_dir(sd); pn = Rh @ self._palm_normal(sd)
            dd = ax * 0.9 - upv * 0.35; dd /= np.linalg.norm(dd)
            want = _basis(dd, -upv) @ _basis(hd, pn).T @ rots["hand_" + sd]   # along the thigh, palm down
            rots["hand_" + sd] = q2m(slerp(m2q(rots["hand_" + sd]), m2q(want), w))
            # elbow swivel out (clearance solve drives abd_extra): the hand stays put on the thigh
            sw = self.abd_extra[sd] * w
            if sw > 0:
                pose, _ = self.fk(rots)
                S = pose["upperarm_" + sd][:3, 3]; Wr = pose["hand_" + sd][:3, 3]; E = pose["lowerarm_" + sd][:3, 3]
                axw = (Wr - S) / np.linalg.norm(Wr - S)
                best = None
                for sgn in (1.0, -1.0):
                    Rq = _axis_angle(axw, sgn * sw)
                    En = S + Rq @ (E - S)
                    if best is None or En[0] * sg > best[0]:
                        best = (En[0] * sg, Rq)
                Rq = best[1]
                for b in ("upperarm_", "lowerarm_"):
                    rots[b + sd] = Rq @ rots[b + sd]

    def _palm_normal(self, sd):
        r = self.rest
        across = r["index_01_" + sd][:3, 3] - r["pinky_01_" + sd][:3, 3]
        n = np.cross(self._hand_dir(sd), across)
        n /= np.linalg.norm(n)
        # rest A-pose palms face the body (medial): +X side hand -> normal points to -X
        if (sd == "l" and n[0] > 0) or (sd == "r" and n[0] < 0):
            n = -n
        return n

    def _hand_dir(self, sd):
        r = self.rest
        d = r["middle_01_" + sd][:3, 3] - r["hand_" + sd][:3, 3]
        return d / np.linalg.norm(d)

    def solve_legs(self, rots, pos):
        """two-bone IK: ankles go where the (scaled) mocap ankles are, so planted feet stay planted.
        Returns the armature->world translation (rig location; the rig is never rotated)."""
        Rp = rots["pelvis"]
        rest_p = self.rest["pelvis"]
        pel = np.eye(4); pel[:3, :3] = Rp; pel[:3, 3] = rest_p[:3, 3]
        hips = {sd: (pel @ np.linalg.inv(rest_p) @ self.rest["thigh_" + sd])[:3, 3] for sd in ("l", "r")}
        m_arm = 0.5 * (hips["l"] + hips["r"])
        T = pos["mid_hip"] - m_arm + np.array([0.0, 0.0, self.oz]) + self.shift
        # reach: when an ankle target is further than the straight leg (the source leg is a little shorter, or
        # the grounding lifted the body), the pelvis drops just enough instead of the foot leaving the floor
        drop = 0.0
        self.ext_dz = {}
        for sd in ("l", "r"):
            lat = np.array([(1 if sd == "l" else -1) * self.lat, 0.0, 0.0])
            v = pos["ank_" + sd] + lat + np.array([0.0, 0.0, self.oz + self.side_dz[sd]]) + self.shift - T - hips[sd]
            Lt = self.len["thigh_" + sd] + self.len["calf_" + sd]
            L = Lt * self.REACH
            h2 = v[0] * v[0] + v[1] * v[1]
            r2 = L * L - h2
            if r2 > 0 and v[2] < 0:
                drop = max(drop, -v[2] - math.sqrt(r2))
            # how far the hip would have to move up for this leg to be exactly as straight as the source leg
            # (read by the grounding calibration in sequences.py, which sets the root height from it)
            dt = min(float(pos["ext_" + sd][0]) if "ext_" + sd in pos else 1.0, self.REACH) * Lt
            self.ext_dz[sd] = (math.sqrt(dt * dt - h2) + v[2]) if dt * dt > h2 and v[2] < 0 else 0.0
        T = T - np.array([0.0, 0.0, drop])
        self.ik_err = 0.0
        for sd in ("l", "r"):
            h = hips[sd]
            lat = np.array([(1 if sd == "l" else -1) * self.lat, 0.0, 0.0])
            a = pos["ank_" + sd] + lat + np.array([0.0, 0.0, self.oz + self.side_dz[sd]]) + self.shift - T
            L1, L2 = self.len["thigh_" + sd], self.len["calf_" + sd]
            v = a - h
            d0 = np.linalg.norm(v)
            d = min(max(d0, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.9995)
            self.ik_err = max(self.ik_err, d0 - d)
            u = v / d0
            pole = self._knee_pole(rots, pos, sd, u)
            x = (L1 * L1 - L2 * L2 + d * d) / (2 * d)
            y = math.sqrt(max(L1 * L1 - x * x, 0.0))
            knee = h + u * x + pole * y
            ank = h + u * d
            for b, new in (("thigh_" + sd, knee - h), ("calf_" + sd, ank - knee)):
                old = rots[b] @ np.linalg.inv(self.rest[b][:3, :3]) @ self.d0[b]
                rots[b] = _rot_between(old, new) @ rots[b]
        return T

    def _knee_pole(self, rots, pos, sd, u):
        """the direction the knee bends to (unit, perpendicular to the hip->ankle line u).

        The knee is a hinge that tracks over the toes, so the bend plane is anchored on the leg's own forward
        direction (the bisector of the pelvis heading and the foot heading). The mocap knee only steers it
        when the source leg is clearly bent, and never more than POLE_MAX_DEG sideways.

        Why: CMU skeletons have unequal left/right leg lengths (115_01: the right leg is 1.5 % shorter than the
        left, which sets the scale), so the Sitka leg must bend ~19 deg to reach an ankle that the subject's
        locked-straight leg puts closer. The old pole was the source knee's offset from the hip-ankle line,
        which on a straight source leg is a few mm of marker noise: the forced bend went backwards
        (hyperextended), sideways (bowed/knocked) and flipped frame to frame - the knee buckle and crossed
        shin at the end of the stoop."""
        fp = rots["pelvis"] @ np.linalg.inv(self.rest["pelvis"][:3, :3]) @ FWD
        fp[2] = 0.0; fp /= max(np.linalg.norm(fp), 1e-9)
        ff = rots["foot_" + sd] @ np.linalg.inv(self.rest["foot_" + sd][:3, :3]) @ self.foot_dir0[sd]
        lf = AN.leg_forward(fp, ff)
        anat = lf - u * np.dot(lf, u)
        if np.linalg.norm(anat) < 1e-3:              # leg along the heading: bend up/forward
            anat = np.array([0.0, 0.0, 1.0]) - u * u[2]
        anat /= np.linalg.norm(anat)
        ks = pos["knee_" + sd] - 0.5 * (pos["hip_" + sd] + pos["ank_" + sd])
        src = ks - u * np.dot(ks, u)
        m = np.linalg.norm(src)
        w = min(1.0, max(0.0, (m - self.POLE_SRC_MM[0]) / (self.POLE_SRC_MM[1] - self.POLE_SRC_MM[0])))
        w = w * w * (3 - 2 * w)
        if m < 1e-6 or w <= 0.0:
            return anat
        p = w * src / m + (1 - w) * anat
        if np.linalg.norm(p) < 1e-6:
            return anat
        p /= np.linalg.norm(p)
        phi = math.atan2(np.dot(np.cross(anat, p), u), np.dot(anat, p))
        if abs(phi) > math.pi / 2:                   # a backwards bend (hyperextension) never comes from the source
            return anat
        lim = math.radians(self.POLE_MAX_DEG)
        phi = max(-lim, min(lim, phi))
        side = np.cross(u, anat)
        return anat * math.cos(phi) + side * math.sin(phi)

    def fk(self, rots, only=None):
        """armature-space pose matrices (and the bases that produce them)"""
        pose, bases = {}, {}
        for name in self.order:
            rest = self.rest[name]
            par = self.parent[name]
            if only is not None and name not in only and (par is None or par not in pose):
                continue
            base = rest if par is None else pose[par] @ self._inv(par) @ rest
            if name in rots:
                want = np.eye(4)
                want[:3, :3] = rots[name]
                want[:3, 3] = base[:3, 3]
                bases[name] = np.linalg.inv(base) @ want
                pose[name] = want
            else:
                bases[name] = self.finger_basis(name)
                pose[name] = base @ bases[name]
        return pose, bases

    CURL = {"01": 24.0, "02": 34.0, "03": 22.0}

    def finger_basis(self, name):
        """relaxed hand: a gentle curl on the finger joints (mocap has no finger data)"""
        if not name.startswith(("index", "middle", "ring", "pinky", "thumb")) or not self.finger_curl:
            return np.eye(4)
        j = name.split("_")[1]
        a = self.CURL.get(j, 0.0) * (0.5 if name.startswith("thumb") else 1.0) * self.finger_curl
        M = np.eye(4); M[:3, :3] = _rx(a)
        return M

    def _inv(self, name):
        c = self.__dict__.setdefault("_invc", {})
        if name not in c:
            c[name] = np.linalg.inv(self.rest[name])
        return c[name]

    # ---------------------------------------------------------- hands off the thighs
    def set_thigh_profile(self, body_rest_co, dom):
        """radius of the thigh (skin) along its axis, from the rest mesh: 95th percentile per slice"""
        self.thigh_R = {}
        for sd, seg in (("l", "thigh_l"), ("r", "thigh_r"), ("cl", "calf_l"), ("cr", "calf_r")):
            bn_h = self.rest[seg][:3, 3]
            ax = self.rest[seg][:3, 1]
            L = self.len[seg]
            pts = body_rest_co[dom == seg]
            s = (pts - bn_h) @ ax
            radial = np.linalg.norm((pts - bn_h) - np.outer(s, ax), axis=1)
            R = []
            for k in range(11):
                m = np.abs(s - k * L / 10) < L / 20
                R.append(float(np.percentile(radial[m], 95)) if m.sum() > 5 else 0.07)
            self.thigh_R[sd] = np.array(R)

    def clear_hands(self, rots, margin=0.04, iters=5):
        """if a hand/forearm would sink into a thigh (skin + exo shell/straps margin), lift the wrist out along
        the thigh's outward normal and re-solve the arm (two-bone IK, elbow kept on its mocap side)"""
        if not getattr(self, "thigh_R", None):
            return 0.0
        worst = 0.0
        for it in range(iters):
            pose, _ = self.fk(rots)
            moved = False
            for arm in ("l", "r"):
                S = pose["upperarm_" + arm][:3, 3]; E = pose["lowerarm_" + arm][:3, 3]; Wr = pose["hand_" + arm][:3, 3]
                Hm = pose["hand_" + arm] @ self._inv("hand_" + arm)
                pts = [E + (Wr - E) * f for f in (0.35, 0.55, 0.75, 0.9, 1.0)]
                for fg in ("index", "middle", "ring", "pinky", "thumb"):
                    for j in ("01", "03"):
                        r = self.rest[f"{fg}_{j}_{arm}"]
                        pts.append((Hm @ np.append(r[:3, 3], 1.0))[:3])
                    r = self.rest[f"{fg}_03_{arm}"]
                    pts.append((Hm @ np.append(r[:3, 3] + r[:3, 1] * 0.022, 1.0))[:3])
                best = (0.0, None)
                for leg, a_, b_ in (("l", "thigh_l", "calf_l"), ("r", "thigh_r", "calf_r"), ("cl", "calf_l", "foot_l"), ("cr", "calf_r", "foot_r")):
                    H = pose[a_][:3, 3]; K = pose[b_][:3, 3]
                    ax = K - H; L = np.linalg.norm(ax); ax /= L
                    for q in pts:
                        sq = np.dot(q - H, ax)
                        if sq < -0.05 or sq > L + 0.06:
                            continue
                        u = min(max(sq / L, 0.0), 1.0)
                        R = np.interp(u * 10, np.arange(11), self.thigh_R[leg]) + margin
                        c = H + ax * min(max(sq, 0.0), L)
                        dv = q - c; dist = np.linalg.norm(dv)
                        if dist < R and R - dist > best[0]:
                            nrm = dv / dist if dist > 1e-6 else np.array([0.0, 0.0, 1.0])
                            best = (R - dist, nrm)
                if best[1] is None:
                    continue
                worst = max(worst, best[0])
                self.arm_shift(rots, arm, best[1] * (best[0] + 0.002), pose)
                moved = True
            if not moved:
                break
        return worst

    def arm_shift(self, rots, arm, disp, pose=None):
        """move the wrist by disp (armature space): two-bone IK, elbow stays on its side, hand keeps its rotation"""
        if pose is None:
            pose, _ = self.fk(rots)
        S = pose["upperarm_" + arm][:3, 3]; E = pose["lowerarm_" + arm][:3, 3]; Wr = pose["hand_" + arm][:3, 3]
        Wt = Wr + disp
        L1 = np.linalg.norm(E - S); L2 = np.linalg.norm(Wr - E)
        v = Wt - S; d0 = np.linalg.norm(v); d = min(max(d0, abs(L1 - L2) + 1e-3), (L1 + L2) * 0.999)
        u = v / d0
        pole = (E - S) - u * np.dot(E - S, u)
        if np.linalg.norm(pole) < 1e-5:
            return
        pole /= np.linalg.norm(pole)
        x = (L1 * L1 - L2 * L2 + d * d) / (2 * d); y = math.sqrt(max(L1 * L1 - x * x, 0.0))
        En = S + u * x + pole * y; Wn = S + u * d
        rots["upperarm_" + arm] = _rot_between(E - S, En - S) @ rots["upperarm_" + arm]
        rots["lowerarm_" + arm] = _rot_between(Wr - E, Wn - En) @ rots["lowerarm_" + arm]

    def apply(self, rig, rots, Matrix):
        """write matrix_basis for every bone so the posed bones have the given armature-space rotations"""
        _, bases = self.fk(rots)
        for name, basis in bases.items():
            rig.pose.bones[name].matrix_basis = Matrix(basis.tolist())


# ------------------------------------------------------------------ timelines
class Loop:
    """one clip piece [a, a+T) repeated, the last `w` seconds crossfaded into the start"""
    def __init__(self, clp, a, T, w=0.15, offset=0.0):
        self.c, self.a, self.T, self.w, self.off = clp, a, T, w, offset

    def state(self, tg, t):
        tt = t + self.off
        k = math.floor(tt / self.T)
        u = tt - k * self.T
        H = self.c.P[self.c.I["LeftUpLeg"]] * 0.5 + self.c.P[self.c.I["RightUpLeg"]] * 0.5
        i0 = 1 + int(round(self.a / self.c.dt)); i1 = 1 + int(round((self.a + self.T) / self.c.dt))
        D = H[i1] - H[i0]; D[2] = 0.0
        A = tg.state(self.c, self.a + u, D * k)
        if u > self.T - self.w:
            B = tg.state(self.c, self.a + u - self.T, D * (k + 1))
            s = (u - (self.T - self.w)) / self.w
            s = s * s * (3 - 2 * s)
            return blend(A, B, s)
        return A


def piecewise(pairs):
    """time map through landmark pairs [(t_src, t_dst), ...], linear in between, slope 1 outside"""
    xs = [a for a, _ in pairs]; ys = [b for _, b in pairs]
    def f(t):
        if t <= xs[0]:
            return ys[0] + t - xs[0]
        if t >= xs[-1]:
            return ys[-1] + t - xs[-1]
        return float(np.interp(t, xs, ys))
    return f


def window(a, b, c, d):
    """0 before a, smooth up to 1 at b, 1 until c, smooth down to 0 at d"""
    def f(t):
        def sm(x):
            x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)
        return sm((t - a) / (b - a)) * (1 - sm((t - c) / (d - c)))
    return f


class Chain:
    """pieces [(clip, src_a, src_b)], played back to back; joins crossfaded over w seconds"""
    def __init__(self, pieces, w=0.3, arms=None):
        self.p, self.w, self.arms = pieces, w, arms
        self.starts = []
        t = 0.0
        for c, a, b in pieces:
            self.starts.append(t); t += b - a
        self.dur = t

    def state(self, tg, t):
        k = 0
        while k + 1 < len(self.p) and t >= self.starts[k + 1]:
            k += 1
        c, a, b = self.p[k]
        A = tg.state(c, a + t - self.starts[k], arms=self.arms)
        # blend into the next piece near the join, out of the previous one just after it
        if k + 1 < len(self.p) and t > self.starts[k + 1] - self.w / 2:
            c2, a2, _ = self.p[k + 1]
            B = tg.state(c2, a2 + t - self.starts[k + 1], arms=self.arms)
            s = (t - (self.starts[k + 1] - self.w / 2)) / self.w
            return blend(A, B, s * s * (3 - 2 * s))
        if k > 0 and t < self.starts[k] + self.w / 2:
            c0, a0, b0 = self.p[k - 1]
            B = tg.state(c0, b0 + t - self.starts[k], arms=self.arms)
            s = (t - (self.starts[k] - self.w / 2)) / self.w
            return blend(B, A, s * s * (3 - 2 * s))
        return A


def find_loop(clp, a_range, T_range, step=1):
    """best seamless stride: minimise the pose difference between t and t+T (bone directions)"""
    I = clp.I
    js = ["LeftUpLeg", "LeftLeg", "LeftFoot", "RightUpLeg", "RightLeg", "RightFoot", "LeftArm", "LeftForeArm",
          "RightArm", "RightForeArm", "Spine1"]
    kids = {"LeftUpLeg": "LeftLeg", "LeftLeg": "LeftFoot", "LeftFoot": "LeftToeBase", "RightUpLeg": "RightLeg",
            "RightLeg": "RightFoot", "RightFoot": "RightToeBase", "LeftArm": "LeftForeArm", "LeftForeArm": "LeftHand",
            "RightArm": "RightForeArm", "RightForeArm": "RightHand", "Spine1": "Neck1"}
    P = clp.P
    D = np.stack([P[I[kids[j]]] - P[I[j]] for j in js], 1)
    D /= np.linalg.norm(D, axis=-1, keepdims=True)
    dt = clp.dt
    best = None
    for a in range(int(a_range[0] / dt), int(a_range[1] / dt), step):
        for T in range(int(T_range[0] / dt), int(T_range[1] / dt)):
            if a + T + 2 >= clp.nf:
                break
            e = np.sum((D[a] - D[a + T]) ** 2) + np.sum((D[a + 1] - D[a + T + 1] - (D[a] - D[a + T])) ** 2) * 50
            if best is None or e < best[0]:
                best = (e, a * dt - dt, T * dt)
    return best
