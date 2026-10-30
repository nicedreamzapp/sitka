"""Connection gate: every part is attached to the part it hangs on, in every baked frame and every static pose.

  cad/.venv/bin/python cad/assemble/connection_gate.py            (exit 1 on a fail)
  cad/.venv/bin/python cad/assemble/connection_gate.py --verbose  (every link, not just the worst per group)

Reads cad/viewer/sitka_anim.js (5 sequences), cad/build/poses.json + cad/body/mesh_<pose>.npz (5 static poses),
cad/glb/sitka_parts.glb (every part in its own frame) and cad/build/manifest.json (part segments, strut pin axis).
Wired into cad/build_all.sh after the animation bake; the build stops on a fail.

Checks, per frame of every sequence and every static pose:
  link     an attached part's surface to its parent's surface (LINKS below): FAIL if the gap is over GAP_MAX
  cable    each end of a cable / band / strap to the part it is anchored on (CABLE_ENDS): FAIL if the end sits more
           than GAP_MAX + the cable's half thickness off that part
  body     every part into the skin of the segment(s) it is strapped to: FAIL past PEN_MAX. Foam liners, pads and the
           belt are soft, so they may compress by FOAM_SQUASH of their own thickness first (reported raw too). Where the
           skinned body mesh folds through itself (the belly through the thighs in a deep stoop) the overlap is listed
           as "other", not gated: that is the body mesh, not the part
  clear    parts that must NOT touch (CLEAR below, e.g. the two seat cups at the midline): FAIL under CLEAR_MIN
  floor    a deployed strut foot: FAIL if it sinks more than FLOOR_SINK below the floor or floats over FLOOR_FLOAT
  stow     a stowed strut: the tube must sit in both stow clips (gap <= GAP_MAX)
  rodend   the strut's ball eye must stay on the hinge pin, and the tube's angle off the pin's plane must stay inside
           the rod end's misalignment (ROD_MISALIGN)
"""
import json, os, sys, base64, math
import numpy as np
import trimesh
from scipy.spatial import cKDTree

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAP_MAX = 0.0015
PEN_MAX = 0.005
FOAM_SQUASH = 0.5
CLEAR_MIN = 0.003
FLOOR_SINK = 0.001
FLOOR_FLOAT = 0.002
ROD_MISALIGN = 16.0          # deg, high-misalignment rod end with cone spacers (EST, VERIFY on the bought part)
VERBOSE = "--verbose" in sys.argv
STATIC_ONLY = "--static" in sys.argv          # quick: the 5 static poses only

# ------------------------------------------------------------------ what hangs on what (per side; "~" = other side)
def side_links(s):
    L = [
        ("thigh_shell", "thigh_liner"), ("thigh_cuff", "thigh_cuff_liner"),
        ("thigh_strap0", "thigh_shell"), ("thigh_strap1", "thigh_shell"),
        ("thigh_buckle0", "thigh_strap0"), ("thigh_buckle1", "thigh_strap1"),
        ("thigh_arm_lat", "thigh_shell"), ("thigh_arm_med", "thigh_shell"),
        ("knee_manifold", "thigh_shell"), ("mode_lever", "knee_manifold"), ("tendon_fairlead", "thigh_shell"),
        ("sit_leaf_root", "thigh_shell"), ("sit_leaf", "sit_leaf_root"),
        ("sit_leaf_link", "sit_leaf"), ("sit_leaf_link", "knee_manifold"),
        ("ea_clutch", "thigh_shell"), ("bowden_stop", "knee_manifold"),
        ("seat_cup", "seat_cup_liner"),
        ("strut_fork", "seat_cup"), ("strut_hingepin", "strut_fork"),
        ("cup_eyelets", "seat_cup"), ("shell_eyelets", "thigh_shell"),
        ("cup_lacing", "cup_eyelets"), ("cup_lacing", "cuff_eyelets"),
        ("cuff_eyelets", "thigh_cuff"), ("cup_bridge", "cup_eyelets"), ("cup_bridge", "shell_eyelets"),
        ("strut_clip_hi", "seat_cup"), ("strut_clip", "thigh_cuff"),
        ("dring_cc", "thigh_shell"), ("dring_m3", "thigh_shell"), ("dring_t3", "thigh_cuff"),
        ("dring_ham", "seat_cup"), ("dring_calf", "thigh_cuff"),
        # knee: the hinge discs ride on the hubs, the hubs carry the yoke, arc, guide and condyle pads
        ("knee_hub_lat", "thigh_arm_lat"), ("knee_hub_lat", "shin_arm_lat"),
        ("knee_hub_med", "thigh_arm_med"), ("knee_hub_med", "shin_arm_med"),
        ("condyle_pad_lat", "knee_hub_lat"), ("condyle_pad_med", "knee_hub_med"),
        ("knee_yoke", "knee_hub_lat"), ("knee_yoke", "knee_hub_med"), ("knee_arc", "knee_yoke"),
        ("knee_guide", "knee_hub_lat"),
        ("ptb_shell", "shin_liner"), ("ptb_shell", "shin_arm_lat"), ("ptb_shell", "shin_arm_med"),
        ("calf_cuff", "calf_liner"), ("calf_cuff", "shin_arm_lat"), ("calf_cuff", "shin_arm_med"),
        ("shin_strap0", "ptb_shell"), ("shin_strap1", "calf_cuff"),
        ("shin_anchor", "ptb_shell"), ("runband_clip", "calf_cuff"), ("dring_ham_calf", "calf_cuff"),
        ("m4_clutch", "calf_cuff"), ("m4_spring", "m4_clutch"), ("m4_heelclip", "shoe"),
        # trunk
        ("lumbar_standoff", "lumbar_plate"), ("glute_guide", "hip_belt"), ("m3_standoff", "hip_belt"),
        ("belt_sideclip", "hip_belt"), ("port_knee", "back_panel"), ("port_hip", "back_panel"),
        ("port_shoulder", "back_panel"), ("panel_guide", "back_panel"), ("p1_dogclutch", "back_panel"),
        ("bowden_panel", "p1_dogclutch"), ("bowden_panel", "port_knee"), ("m5_cassette", "back_panel"),
        ("m5_armcuff", "m5_armliner"), ("spine_pivot_panel", "back_panel"), ("spine_pivot_belt", "lumbar_plate"),
    ]
    ONE = ("lumbar_plate", "hip_belt", "back_panel")      # trunk parts with no side
    return [(a + "_" + s, b if b in ONE else b + "_" + s) for a, b in L]


LINKS = side_links("l") + side_links("r") + [
    ("belt_buckle", "hip_belt"), ("lumbar_plate", "hip_belt"), ("back_panel", "back_panel_liner"),
    ("m2_leaf_root", "back_panel"), ("m2_leaf", "m2_leaf_root"), ("whiffletree", "m2_leaf"),
    ("p1_motor", "back_panel"), ("p1_drum", "p1_motor"), ("p1_battery", "lumbar_plate"),
]
SKIN = ("thigh_liner", "thigh_cuff_liner", "seat_cup_liner", "shin_liner", "calf_liner", "condyle_pad", "back_panel_liner",
        "hip_belt", "m5_armliner")

# cable ends: (route name, anchor key, part that anchor is on). Ends tied to another strap (harness waypoints) are skipped.
def cable_ends(s):
    E = [
        ("t1_tendon", "t1_manifold", "knee_manifold"), ("t1_tendon", "t1_shin", "shin_anchor"),
        ("t3_tendon", "t3_whiffle", "whiffletree"), ("t3_tendon", "t3_cuff", "dring_t3"),
        ("m3_band", "m3_belt", "m3_standoff"), ("m3_band", "m3_thigh", "dring_m3"),
        ("harness", "harness_top", "back_panel"), ("harness", "harness_belt", "hip_belt"),
        ("crazycreek", "cc_panel", "back_panel"), ("crazycreek", "cc_belt", "belt_sideclip"),
        ("crazycreek", "cc_thigh", "dring_cc"),
        ("hamstring_band", "ham_cup", "dring_ham"), ("hamstring_band", "ham_calf", "dring_ham_calf"),
        ("calf_band", "calfband_thigh", "dring_calf"), ("calf_band", "heel", "m4_heelclip"),
        ("m4_cable", "m4_spring", "m4_spring"), ("m4_cable", "heel", "m4_heelclip"),
        ("bowden", "port_knee", "port_knee"), ("bowden", "bowden_thigh", "bowden_stop"),
        ("m5_lever", "m5_pivot", "m5_cassette"), ("m5_lever", "m5_cuff", "m5_armcuff"),
        ("spine_link", "spine_belt", "spine_pivot_belt"), ("spine_link", "spine_panel", "spine_pivot_panel"),
        ("running_band", "runband", "runband_clip"),
    ]
    return [(a + "_" + s if a != "running_band" else a, k + "_" + s, p + "_" + s if p not in ("back_panel", "hip_belt", "whiffletree") else p)
            for a, k, p in E]


CABLE_ENDS = cable_ends("l") + cable_ends("r")
CLEAR = [("seat_cup_l", "seat_cup_r"), ("seat_cup_liner_l", "seat_cup_liner_r")]


# ------------------------------------------------------------------ data
def load_parts():
    sc = trimesh.load(os.path.join(CAD, "glb", "sitka_parts.glb"))
    out = {}
    for node in sc.graph.nodes_geometry:
        T, g = sc.graph[node]
        m = sc.geometry[g].copy()
        m.apply_transform(T)
        v = m.vertices
        out[node] = trimesh.Trimesh(np.c_[v[:, 0], -v[:, 2], v[:, 1]], m.faces, process=False)  # glTF y-up -> z-up
    return out


def samples(m, n=1500):
    """surface points: every vertex plus an even area sample (big flat faces have few vertices)"""
    try:
        p, _ = trimesh.sample.sample_surface(m, n, seed=1)
    except TypeError:
        p, _ = trimesh.sample.sample_surface(m, n)
    return np.vstack([m.vertices, p])


def xf(M, P):
    return P @ M[:3, :3].T + M[:3, 3]


# body check region: a part is checked against the skin of the segment(s) it is strapped to (dominant skinning bone of
# each body vertex). Where the posed mesh folds one region through another (the belly through the thighs in a deep
# stoop, LBS skinning with no flesh contact), that is the body mesh, not the part: reported as "other", not gated.
DOM = np.load(os.path.join(CAD, "body", "stand_weights.npz"))["dom"]
REGION_BONES = {
    "thigh": lambda s: {"thigh_" + s, "pelvis"}, "knee": lambda s: {"thigh_" + s, "calf_" + s},
    "shin": lambda s: {"calf_" + s, "thigh_" + s}, "foot": lambda s: {"foot_" + s, "ball_" + s, "calf_" + s},
    "uarm": lambda s: {"upperarm_" + s}, "pelvis": lambda s: {"pelvis", "spine_01", "thigh_l", "thigh_r"},
    "panel": lambda s: {"spine_01", "spine_02", "spine_03", "clavicle_l", "clavicle_r"},
    "strut": lambda s: {"pelvis", "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"},
}


def region_of(name, seg):
    if name.startswith("strut_") and seg is None:
        return REGION_BONES["strut"]("")
    seg = seg or "panel"
    base, s = (seg.rsplit("_", 1) + [""])[:2] if seg[-2:] in ("_l", "_r") else (seg, "")
    return REGION_BONES.get(base, REGION_BONES["panel"])(s)


class Gate:
    def __init__(self):
        self.parts = load_parts()
        self.S = {k: samples(m) for k, m in self.parts.items()}
        self.thick = {}
        self.res = {}         # (kind, key) -> [worst, where, limit, ok]
        man = json.load(open(os.path.join(CAD, "build", "manifest.json")))
        self.segs = {p["name"]: p["seg"] for p in man["parts"]}
        self.axis = {k[len("strut_axis_"):]: np.array(a["axis"]) for k, a in man["anchors"].items() if k.startswith("strut_axis_")}
        self.cache = {}

    def note(self, kind, key, val, where, limit, bad):
        r = self.res.get((kind, key))
        worse = r is None or (bad(val) and not bad(r[0])) or (bad(val) == bad(r[0]) and
                                                                 ((val > r[0]) if kind not in ("clear", "floor_lo") else (val < r[0])))
        if worse:
            self.res[(kind, key)] = [val, where, limit, not bad(val)]

    def surf_gap(self, a, Ma, b, Mb):
        """min distance between the surfaces of parts a and b (posed by Ma, Mb); 0 when they overlap"""
        rel = np.round(np.linalg.inv(Mb) @ Ma, 5).tobytes()
        ck = (a, b, rel)
        if ck in self.cache:
            return self.cache[ck]
        A = xf(np.linalg.inv(Mb) @ Ma, self.S[a])          # a's samples in b's frame
        mb = self.parts[b]
        tb = cKDTree(self.S[b])
        d0, _ = tb.query(A)
        k = np.argsort(d0)[:60]
        cp, dist, tri = trimesh.proximity.closest_point(mb, A[k])
        g = float(dist.min())
        # overlap: some of a's points inside b (watertight b only) -> 0
        if g > 1e-4 and mb.is_watertight:
            if mb.contains(A[k[:20]]).any():
                g = 0.0
        # and the other way (b's samples onto a)
        if g > 1e-4:
            B = xf(np.linalg.inv(Ma) @ Mb, self.S[b])
            ta = cKDTree(self.S[a]); d1, _ = ta.query(B); k1 = np.argsort(d1)[:60]
            cp, dist1, _ = trimesh.proximity.closest_point(self.parts[a], B[k1])
            g = min(g, float(dist1.min()))
        self.cache[ck] = g
        return g

    def point_gap(self, p, b, Mb):
        """distance from a point to part b's surface, 0 when the point is inside b"""
        q = xf(np.linalg.inv(Mb), np.array([p]))
        mb = self.parts[b]
        cp, dist, tri = trimesh.proximity.closest_point(mb, q)
        if (q[0] - cp[0]) @ mb.face_normals[tri[0]] < 0:
            return 0.0
        return float(dist[0])

    def frame(self, tag, mats, body_v, body_f, cables, strut_blend, cable_r):
        names = list(mats.keys())
        # ---- links
        for a, b in LINKS:
            if a not in mats or b not in mats:
                if a in self.parts or b in self.parts:
                    self.note("link", f"{a} -> {b}", 9.999, tag + " (part missing)", GAP_MAX, lambda v: v > GAP_MAX)
                continue
            g = self.surf_gap(a, mats[a], b, mats[b])
            self.note("link", f"{a} -> {b}", g, tag, GAP_MAX, lambda v: v > GAP_MAX)
        # ---- clear
        for a, b in CLEAR:
            if a in mats and b in mats:
                g = self.surf_gap(a, mats[a], b, mats[b])
                self.note("clear", f"{a} | {b}", g, tag, CLEAR_MIN, lambda v: v < CLEAR_MIN)
        # ---- cable ends (cables[route] = (points, [first anchor key, last anchor key]))
        END_PART = {k: p for r, k, p in CABLE_ENDS}
        for route, (P, keys) in cables.items():
            for end, key in ((P[0], keys[0]), (P[-1], keys[1])):
                part = END_PART.get(key)
                if part is None or part not in mats:
                    continue
                g = max(0.0, self.point_gap(end, part, mats[part]) - cable_r.get(route, 0.0))
                self.note("cable", f"{route} @ {key} on {part}", g, tag, GAP_MAX, lambda v: v > GAP_MAX)
        # ---- body penetration (signed distance from the nearest skin vertex, refined on the mesh)
        body = trimesh.Trimesh(body_v, body_f, process=False)
        vn = body.vertex_normals
        fdom = DOM[body_f[:, 0]]
        kd = cKDTree(body_v)
        for nm in names:
            if nm.startswith("shoe") or nm not in self.parts:
                continue
            P = xf(mats[nm], self.parts[nm].vertices[:: max(1, len(self.parts[nm].vertices) // 700)])
            d, i = kd.query(P)
            sd = np.einsum("ij,ij->i", P - body_v[i], vn[i])
            cand = np.where(sd < -0.002)[0]
            pen, other = 0.0, 0.0
            if len(cand):
                cand = cand[np.argsort(sd[cand])[:60]]
                cp, dist, tri = trimesh.proximity.closest_point(body, P[cand])
                s = np.einsum("ij,ij->i", P[cand] - cp, body.face_normals[tri])
                inside = s < 0
                own = np.isin(fdom[tri], list(region_of(nm, self.segs.get(nm))))
                if (inside & own).any():
                    pen = float(dist[inside & own].max())
                if (inside & ~own).any():
                    other = float(dist[inside & ~own].max())
            if other > PEN_MAX:
                self.note("other", nm, other, tag, PEN_MAX, lambda v: False)
            soft = any(nm.startswith(k) for k in SKIN) or nm.startswith(("strap", "thigh_strap", "shin_strap"))
            allow = FOAM_SQUASH * self.part_thick(nm) if any(nm.startswith(k) for k in SKIN) else 0.0
            self.note("body", nm, pen - allow, f"{tag} (raw {pen * 1000:.1f} mm)", PEN_MAX, lambda v: v > PEN_MAX)
        # ---- strut
        for sd in ("l", "r"):
            bl = strut_blend.get(sd)
            foot = "strut_foot_" + sd
            if foot not in mats:
                continue
            fz = xf(mats[foot], self.parts[foot].vertices)[:, 2].min()
            if bl is not None and bl >= 0.999:
                self.note("floor_lo", foot + " sinks", -fz, tag, FLOOR_SINK, lambda v: v > FLOOR_SINK)
                self.note("floor", foot + " floats", fz, tag, FLOOR_FLOAT, lambda v: v > FLOOR_FLOAT)
            if bl is not None and bl <= 0.001:
                for clip in ("strut_clip_hi_" + sd, "strut_clip_" + sd):
                    if clip in mats:
                        g = min(self.surf_gap(f"strut_tube{k}_{sd}", mats[f"strut_tube{k}_{sd}"], clip, mats[clip])
                                for k in range(5) if f"strut_tube{k}_{sd}" in mats)
                        self.note("stow", f"strut_tube -> {clip}", g, tag, GAP_MAX, lambda v: v > GAP_MAX)
            eye, pin = "strut_rodend_" + sd, "strut_hingepin_" + sd
            if eye in mats and pin in mats:
                g = self.surf_gap(eye, mats[eye], pin, mats[pin])
                self.note("rodend", f"{eye} on {pin}", g, tag, GAP_MAX, lambda v: v > GAP_MAX)
                ax_pin = mats[pin][:3, :3] @ self.axis[sd]       # pin axis, carried in the thigh frame
                ax_tube = mats["strut_tube0_" + sd][:3, 2]
                mis = abs(90.0 - math.degrees(math.acos(abs(float(np.clip(ax_pin @ ax_tube, -1, 1))))))
                self.note("rodend", f"{eye} misalignment deg", mis, tag, ROD_MISALIGN, lambda v: v > ROD_MISALIGN)

    def part_thick(self, nm):
        if nm not in self.thick:
            m = self.parts[nm]
            # thickness ~ 2 x volume / area for a thin shell
            self.thick[nm] = float(2 * abs(m.volume) / max(m.area, 1e-9)) if m.is_volume else 0.008
        return self.thick[nm]

    def report(self):
        ok = True
        groups = {}
        for (kind, key), (v, where, lim, good) in self.res.items():
            groups.setdefault(kind, []).append((key, v, where, lim, good))
            ok &= good
        print("CONNECTION GATE (%s)" % ("PASS" if ok else "FAIL"))
        for kind in ("link", "cable", "rodend", "stow", "floor", "floor_lo", "clear", "body", "other"):
            rows = groups.get(kind, [])
            if not rows:
                continue
            bad = [r for r in rows if not r[4]]
            worst = sorted(rows, key=lambda r: (r[4], -r[1] if kind not in ("clear",) else r[1]))
            if kind == "other":
                print("  other   (not gated) the posed body mesh folds through itself here, e.g. the belly through the thighs:")
                for key, v, where, lim, good in sorted(rows, key=lambda r: -r[1])[:12]:
                    print(f"           {key:40s} {v * 1000:6.1f} mm inside another body region at {where}")
                continue
            print(f"  {kind:7s} {len(rows) - len(bad):3d}/{len(rows)} pass" + (f", worst {worst[0][0]} {worst[0][1] * (1 if 'deg' in worst[0][0] else 1000):.1f}"
                                                                                + (" deg" if 'deg' in worst[0][0] else " mm") + f" ({worst[0][2]})" if rows else ""))
            for key, v, where, lim, good in (worst if VERBOSE else bad):
                u = (" deg", 1) if "deg" in key else (" mm", 1000)
                print(f"      {'ok  ' if good else 'FAIL'} {key:52s} {v * u[1]:7.1f}{u[0]} (limit {lim * u[1]:.1f}) at {where}")
        return ok


def main():
    G = Gate()
    PJ = json.load(open(os.path.join(CAD, "build", "poses.json")))
    # ---------- static poses
    for pose, P in PJ["parts"].items():
        mats = {k: np.array(v) for k, v in P.items()}
        d = np.load(os.path.join(CAD, "body", f"mesh_{pose}.npz"))
        bv = d["V"]
        bf = np.vstack([d["Q"][:, [0, 1, 2]], d["Q"][:, [0, 2, 3]]] + ([d["T"]] if len(d["T"]) else []))
        cab = {k: (np.vstack([c["ends"][0], c["ends"][1]]), c["end_keys"]) for k, c in PJ["cables"][pose].items() if "ends" in c}
        cr = {k: c.get("half", 0.0) for k, c in PJ["cables"][pose].items()}
        mode = PJ["poses"][pose]["mode"]
        G.frame(f"pose {pose}", mats, bv, bf, cab, {"l": 1.0 if mode == "SIT" else 0.0, "r": 1.0 if mode == "SIT" else 0.0}, cr)
        print("pose", pose, "checked", flush=True)
    # ---------- baked sequences
    if STATIC_ONLY:
        sys.exit(0 if G.report() else 1)
    txt = open(os.path.join(CAD, "viewer", "sitka_anim.js")).read()
    A = json.loads(txt[txt.index("{"): txt.rindex("}") + 1])
    body = np.frombuffer(base64.b64decode(A["body_b64"]), dtype=np.int16).astype(np.float64) / 10000.0
    cabb = np.frombuffer(base64.b64decode(A["cab_b64"]), dtype=np.int16).astype(np.float64) / 10000.0
    F = np.array(A["tris"]).reshape(-1, 3)
    nv, nres = A["nv"], A["nres"]
    cr = {k: (c.get("r") or c.get("t", 0) / 2) for k, c in A["cables"].items()}
    for sname, S in A["seqs"].items():
        for f in range(S["n"]):
            gf = S["start"] + f
            bv = body[gf * nv * 3:(gf + 1) * nv * 3].reshape(-1, 3)
            mats = {}
            for nm, m in zip(A["parts"], S["parts"][f]):
                M = np.eye(4); M[:3, :] = np.array(m).reshape(3, 4); mats[nm] = M
            cab = {c["name"]: (cabb[c["o"]: c["o"] + nres * 3].reshape(-1, 3), c.get("k") or A["cables"][c["name"]].get("end_keys", ["?", "?"]))
                   for c in S["cables"][f]}
            sb = S.get("strut", [None] * S["n"])[f]
            G.frame(f"{sname} f{f:02d}", mats, bv, F, cab, {"l": sb, "r": sb}, cr)
        print("seq", sname, S["n"], "frames checked", flush=True)
    ok = G.report()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
