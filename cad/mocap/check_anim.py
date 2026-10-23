"""Frame-by-frame check of the baked viewer animation (cad/viewer/sitka_anim.js), plain numpy, no Blender.

  cad/.venv/bin/python cad/mocap/check_anim.py

Per sequence:
  sole     lowest foot vertex per foot (target SOLE = 22 mm); float/sink reported on planted frames
  slide    planted-foot drift between frames (walk/run: relative to the steady treadmill speed)
  jump     largest part rotation / body vertex move from one frame to the next (loops include the seam)
  follow   how much each exo part's distance to the nearest skin changes over the sequence (parts ride the body)
  strut    lowest strut point while the strut is deployed (sit)
"""
import json, os, base64, sys
import numpy as np

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLE = 0.022
src = open(os.path.join(CAD, "viewer", "sitka_anim.js")).read()
A = json.loads(src[src.index("=") + 1:src.rstrip().rindex(";")])
NV = A["nv"]
body = np.frombuffer(base64.b64decode(A["body_b64"]), dtype=np.int16).reshape(-1, NV, 3) * 1e-4
dom = np.load(os.path.join(CAD, "body", "stand_weights.npz"))["dom"]
FOOT = {sd: np.where(np.isin(dom, ["foot_" + sd, "ball_" + sd]))[0] for sd in "lr"}
parts = A["parts"]
SUB = np.arange(0, NV, 3)


def mats(seq):
    out = []
    for fr in seq["parts"]:
        M = np.array(fr).reshape(len(parts), 3, 4)
        out.append(M)
    return np.array(out)


def rot_angle(R0, R1):
    c = (np.trace(R0.T @ R1) - 1) / 2
    return np.degrees(np.arccos(np.clip(c, -1, 1)))


bad = 0
for name, S in A["seqs"].items():
    n, loop, fps = S["n"], S["loop"], S.get("fps")
    V = body[S["start"]:S["start"] + n]
    P = mats(S)
    print(f"== {name}: {n} frames, loop={loop}, fps={fps}, {(n if loop else n - 1) / fps:.2f} s")
    # soles
    sole = {sd: V[:, FOOT[sd], 2].min(axis=1) for sd in "lr"}
    pl = {sd: sole[sd] < SOLE + 0.006 for sd in "lr"}
    for sd in "lr":
        e = (sole[sd][pl[sd]] - SOLE) * 1000
        print(f"  sole {sd}: planted {pl[sd].sum():2d}/{n}  err mm min {e.min():+.1f} max {e.max():+.1f}" if len(e) else f"  sole {sd}: never planted")
    print(f"  body lowest point min {V[:, :, 2].min() * 1000:.1f} mm")
    # slide: contact vertices (within 4 mm of the floor) in contact in both frames
    pairs = [(i, i + 1) for i in range(n - 1)] + ([(n - 1, 0)] if loop else [])
    for sd in "lr":
        d = []
        for a, b in pairs:
            ca = V[a, FOOT[sd], 2] < SOLE + 0.004
            cb = V[b, FOOT[sd], 2] < SOLE + 0.004
            both = ca & cb
            if both.sum() >= 3:
                d.append((a, np.median(V[b, FOOT[sd]][both, :2] - V[a, FOOT[sd]][both, :2], axis=0)))
        if not d:
            continue
        D = np.array([x[1] for x in d])
        if loop:
            ref = np.median(D, axis=0)          # the treadmill: a planted foot moves back at the walking speed
            dev = np.linalg.norm(D - ref, axis=1) * 1000
            print(f"  slide {sd}: {len(d)} planted steps, treadmill {np.linalg.norm(ref) * fps:.2f} m/s, deviation mm/frame median {np.median(dev):.1f} max {dev.max():.1f}")
        else:
            dev = np.linalg.norm(D, axis=1) * 1000
            worst = d[int(np.argmax(dev))][0]
            print(f"  slide {sd}: {len(d)} planted steps, mm/frame median {np.median(dev):.1f} max {dev.max():.1f} (frame {worst})")
    # jumps
    pj, vj = [], []
    for a, b in pairs:
        pj.append(max(rot_angle(P[a, k, :, :3], P[b, k, :, :3]) for k in range(len(parts))))
        vj.append(np.linalg.norm(V[b] - V[a], axis=1).max())
    pj, vj = np.array(pj), np.array(vj)
    seam = f" seam: part {pj[-1]:.1f} deg, body {vj[-1] * 1000:.0f} mm" if loop else ""
    print(f"  jump: part rot deg/frame median {np.median(pj):.1f} max {pj.max():.1f} (pair {pairs[int(np.argmax(pj))]}); "
          f"body max move mm/frame median {np.median(vj) * 1000:.0f} max {vj.max() * 1000:.0f}{seam}")
    # follow: parts stay at a constant distance from the skin (not struts: they swing)
    var = []
    for k, pn in enumerate(parts):
        if pn.startswith("strut"):
            continue
        dist = []
        for i in range(n):
            o = P[i, k, :, 3]
            dist.append(np.sqrt(((V[i, SUB] - o) ** 2).sum(1).min()))
        dist = np.array(dist)
        var.append((dist.max() - dist.min(), pn))
    var.sort(reverse=True)
    print("  follow: part-to-skin distance change, worst: " + ", ".join(f"{p} {v * 1000:.0f} mm" for v, p in var[:4]))
    # struts
    if name in ("sitdown", "standup"):
        dep = [i for i, st in enumerate(S["states"]) if st.get("lock")]
        print(f"  strut: knee lock frames {dep[0] if dep else '-'}..{dep[-1] if dep else '-'}")
