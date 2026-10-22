"""Shared body data for the Sitka render-two parts: anatomical segment frames per pose and a
body-surface sampler that returns the skin radius around a segment axis, taken as the MAX over
every pose, so a shell contoured to it never cuts into the body in any pose.

Frames: every segment gets a right-handed anatomical frame, fixed to its bone:
  Z = along the segment (legs/arms: proximal -> distal; trunk: up), Y = anterior, X = Y x Z (= world +X
  in the standing pose). Lateral for a side is s*X with s = +1 (left), -1 (right).
Angles theta around Z are measured from anterior (0) toward lateral (+90), so code is mirror-safe.
"""
import json, os, math
import numpy as np
import trimesh

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # .../cad
BODY = os.path.join(ROOT, "body")
POSES = ["stand", "walk", "run", "chair", "stoop"]
FR = json.load(open(os.path.join(BODY, "frames.json")))

SEGS = {  # segment -> (bone, axis kind)
    "pelvis": ("pelvis", "up"), "chest": ("spine_03", "up"), "lumbar": ("spine_01", "up"),
    "thigh_l": ("thigh_l", "bone"), "thigh_r": ("thigh_r", "bone"),
    "shin_l": ("calf_l", "bone"), "shin_r": ("calf_r", "bone"),
    "foot_l": ("foot_l", "down"), "foot_r": ("foot_r", "down"),
    "uarm_l": ("upperarm_l", "bone"), "uarm_r": ("upperarm_r", "bone"),
}


def M(pose, bone):
    return np.array(FR[pose]["bones"][bone]["M"])


def _anat_stand(seg):
    bone, kind = SEGS[seg]
    b = FR["stand"]["bones"][bone]
    h, t = np.array(b["head"]), np.array(b["tail"])
    if kind == "bone":
        z = (t - h) / np.linalg.norm(t - h)
    elif kind == "up":
        z = np.array([0, 0, 1.0])
    else:  # foot: frame with Z down (sole normal), origin at the ankle
        z = np.array([0, 0, -1.0])
    y = np.array([0, -1.0, 0])
    y = y - z * (y @ z); y /= np.linalg.norm(y)
    x = np.cross(y, z)
    A = np.eye(4); A[:3, 0], A[:3, 1], A[:3, 2], A[:3, 3] = x, y, z, h
    return A


_LOCAL = {s: np.linalg.inv(M("stand", SEGS[s][0])) @ _anat_stand(s) for s in SEGS}


def A(pose, seg):
    """world <- anatomical segment frame, for a pose"""
    return M(pose, SEGS[seg][0]) @ _LOCAL[seg]


def side_s(seg):
    return -1.0 if seg.endswith("_r") else 1.0


def seg_len(seg):
    b = FR["stand"]["bones"][SEGS[seg][0]]
    return float(np.linalg.norm(np.array(b["tail"]) - np.array(b["head"])))


_MESH = {}


def mesh(pose):
    if pose not in _MESH:
        d = np.load(os.path.join(BODY, f"mesh_{pose}.npz"))
        V, Q, T = d["V"], d["Q"], d["T"]
        F = np.vstack([Q[:, [0, 1, 2]], Q[:, [0, 2, 3]]] + ([T] if len(T) else []))
        m = trimesh.Trimesh(V, F, process=False)
        try:
            from trimesh.ray.ray_pyembree import RayMeshIntersector
            m.ray = RayMeshIntersector(m)
        except Exception:
            pass
        _MESH[pose] = m
    return _MESH[pose]


def radial(seg, zs, thetas, poses=POSES, axis_offset=(0.0, 0.0), fallback=None):
    """Skin radius r[z, theta] around the segment Z axis (offset in x, y of the anat frame),
    max over poses. theta in degrees from anterior toward lateral."""
    s = side_s(seg)
    zs, th = np.asarray(zs, float), np.radians(np.asarray(thetas, float))
    Z, TH = np.meshgrid(zs, th, indexing="ij")
    dl = np.stack([s * np.sin(TH), np.cos(TH), np.zeros_like(TH)], -1).reshape(-1, 3)
    ol = np.stack([np.full_like(Z, axis_offset[0]), np.full_like(Z, axis_offset[1]), Z], -1).reshape(-1, 3)
    R = np.zeros(len(dl))
    for p in poses:
        Aw = A(p, seg)
        o = ol @ Aw[:3, :3].T + Aw[:3, 3]
        d = dl @ Aw[:3, :3].T
        loc, ri, _ = mesh(p).ray.intersects_location(o, d, multiple_hits=False)
        r = np.full(len(dl), np.nan)
        r[ri] = np.linalg.norm(loc - o[ri], axis=1)
        R = np.fmax(R, np.nan_to_num(r, nan=0.0))
    R = R.reshape(Z.shape)
    if fallback is not None:
        R[R <= 0] = fallback
    return R


def to_world(seg, pts, pose="stand"):
    Aw = A(pose, seg)
    return np.asarray(pts) @ Aw[:3, :3].T + Aw[:3, 3]


def to_local(seg, pts, pose="stand"):
    Aw = np.linalg.inv(A(pose, seg))
    return np.asarray(pts) @ Aw[:3, :3].T + Aw[:3, 3]


def smooth2(R, it=2):
    """light Laplacian smoothing of a radius grid (keeps shells fair, never pulls inward)"""
    R = R.copy()
    for _ in range(it):
        P = np.pad(R, 1, mode="edge")
        S = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4
        R = np.maximum(R, 0.5 * R + 0.5 * S)
    return R


def _quat_from_R(R):
    from scipy.spatial.transform import Rotation
    return Rotation.from_matrix(R)


def A_knee(pose, side):
    """knee frame: origin at the knee axis (calf head), rotation halfway between thigh and shin
    (the centre plate of a geared bicentric hinge turns at half the knee angle)"""
    from scipy.spatial.transform import Rotation, Slerp
    At, As = A(pose, "thigh_" + side), A(pose, "shin_" + side)
    sl = Slerp([0, 1], Rotation.from_matrix([At[:3, :3], As[:3, :3]]))
    K = np.eye(4); K[:3, :3] = sl(0.5).as_matrix(); K[:3, 3] = As[:3, 3]
    return K


_A_seg = A


def A(pose, seg):  # noqa: F811  (extends A with the knee frames)
    if seg.startswith("knee_"):
        return A_knee(pose, seg[-1])
    return _A_seg(pose, seg)


def side_s(seg):  # noqa: F811
    """+1 where theta>0 points to the wearer's left in the world: legs/arms of the left side and,
    because the trunk frames have X = world -X, the trunk frames take -1"""
    if seg in ("pelvis", "chest", "lumbar"):
        return -1.0
    return -1.0 if seg.endswith("_r") else 1.0
