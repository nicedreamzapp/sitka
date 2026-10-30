#!/usr/bin/env python3
"""Train Sitka's mode model from open motion capture (CMU), with no hardware yet.

  python3 brain/train_mode_model.py            # numpy only, plus node for the shared sensor code

1. Reads CMU BVH clips (cad/mocap/src, plus brain/mocap_extra if brain/fetch_mocap.sh was run).
2. Labels every 20 ms with offline rules that may look at the whole clip (speed, hip height, flight phase,
   trunk bend). Those rules use things a wearer's sensors cannot see; the model has to learn the mode from
   the sensors alone.
3. Turns the joint tracks into simulated sensors (thigh/shin/hub IMU, insoles) by calling
   brain/brain_cli.mjs, i.e. the SAME brain/sitka_brain.js the viewer runs.
4. Trains a tiny 1D CNN (numpy, fixed seed), writes brain/mode_model.json and brain/mode_model.js.
5. Reports accuracy on held-out clips and on the viewer's own sequences.
"""
import json
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(REPO, "cad", "mocap"))
from bvh import BVH  # noqa: E402

SRC_DIRS = [os.path.join(REPO, "cad", "mocap", "src"), os.path.join(HERE, "mocap_extra")]
HZ, WIN = 50, 50
CLASSES = ["STAND", "WALK", "RUN", "SIT", "LIFT"]
TRAIN = ["35_01", "35_02", "35_17", "35_18", "86_09", "115_01", "115_02"]
HELDOUT = ["35_03", "35_19", "35_20", "86_10", "115_03"]
WARPS = [0.85, 1.0, 1.18]                    # play each training clip slower / as is / faster
# viewer sequence -> (clip, clip start s): the same cuts as cad/mocap/sequences.py
VIEWER = {"walk": ("35_01", 1.125), "run": ("35_17", 0.375), "sitdown": ("86_09", 8.45),
          "standup": ("86_09", 23.2), "stoop": ("115_01", 0.35)}
J = dict(hipL="LeftUpLeg", hipR="RightUpLeg", kneeL="LeftLeg", kneeR="RightLeg", ankleL="LeftFoot",
         ankleR="RightFoot", toeL="LeftToeBase", toeR="RightToeBase", pelvis="Hips")
SEED = 7


def find(name):
    for d in SRC_DIRS:
        p = os.path.join(d, name + ".bvh")
        if os.path.exists(p):
            return p
    return None


class Clip:
    def __init__(self, name):
        b = BVH(find(name))
        I = b.idx
        leg = np.linalg.norm(b.offset[I["LeftLeg"]]) + np.linalg.norm(b.offset[I["LeftFoot"]])
        b.to_sitka(0.94 / leg)                      # same scaling as cad/mocap/retarget.py
        self.name, self.dt = name, b.dt
        self.t = np.arange(b.nf - 1) * b.dt         # frame 0 is the T-pose: skipped
        self.P = {k: b.Ps[I[v], 1:] for k, v in J.items()}
        tv = b.Ps[I["Neck"], 1:] - b.Ps[I["Hips"], 1:]
        self.P["trunk"] = tv / np.linalg.norm(tv, axis=1, keepdims=True)
        self.dur = self.t[-1]

    def at(self, k, tt):
        return np.stack([np.interp(tt, self.t, self.P[k][:, a]) for a in range(3)], 1)

    def tracks(self, tt):
        tr = {k: self.at(k, tt) for k in self.P}
        tr["trunk"] /= np.linalg.norm(tr["trunk"], axis=1, keepdims=True)
        return tr

    # ------------------------------------------------------------ offline labels (may use the whole clip)
    def labels(self, tt):
        P = self.tracks(tt)
        n = len(tt)
        hip = P["pelvis"]
        k = int(0.4 * HZ)
        v = np.zeros(n)
        for i in range(n):
            a, b = max(0, i - k), min(n - 1, i + k)
            v[i] = np.linalg.norm(hip[b, :2] - hip[a, :2]) / max(1e-6, tt[b] - tt[a])
        aF = np.percentile(np.r_[P["ankleL"][:, 2], P["ankleR"][:, 2]], 5)
        tF = np.percentile(np.r_[P["toeL"][:, 2], P["toeR"][:, 2]], 5)
        sole = {s: np.minimum(P["ankle" + s][:, 2] - aF, P["toe" + s][:, 2] - tF) for s in "LR"}
        air = (sole["L"] > 0.03) & (sole["R"] > 0.03)
        kf = int(0.5 * HZ)
        flight = np.array([air[max(0, i - kf):i + kf + 1].mean() for i in range(n)])
        thighL = np.linalg.norm(P["kneeL"] - P["hipL"], axis=1).mean()
        shinL = np.linalg.norm(P["ankleL"] - P["kneeL"], axis=1).mean()
        hmid = (P["hipL"][:, 2] + P["hipR"][:, 2]) / 2
        hrel = (hmid - tF) / (thighL + shinL + aF - tF)
        incl = lambda d: np.degrees(np.arccos(np.clip(-d[:, 2] / np.linalg.norm(d, axis=1), -1, 1)))
        thigh = (incl(P["kneeL"] - P["hipL"]) + incl(P["kneeR"] - P["hipR"])) / 2
        trunk = np.degrees(np.arccos(np.clip(P["trunk"][:, 2], -1, 1)))

        def grow(core, ok):
            m = core.copy()
            for _ in range(n):
                nxt = m | (ok & (np.r_[False, m[:-1]] | np.r_[m[1:], False]))
                if (nxt == m).all():
                    break
                m = nxt
            return m

        sit = grow((hrel < 0.92) & (thigh > 35), ((hrel < 0.95) | (trunk > 15)) & (v < 0.8))
        lift = grow((trunk > 30) & ~sit, (trunk > 12) & ~sit)
        run = (flight > 0.04) & (v > 1.0) & ~sit & ~lift
        walk = (v > 0.3) & ~sit & ~lift & ~run
        y = np.zeros(n, int)                         # STAND
        y[walk] = 1
        y[run] = 2
        y[sit] = 3
        y[lift] = 4
        return y


def tracks_json(clip, tt):
    tr = clip.tracks(tt)
    out = dict(fps=HZ, loop=False, n=len(tt), pad=1.0)
    for k, v in tr.items():
        out[k] = np.round(v.reshape(-1), 5).tolist()
    return out


def features(tracks):
    with tempfile.TemporaryDirectory() as d:
        a, b = os.path.join(d, "in.json"), os.path.join(d, "out.json")
        json.dump(tracks, open(a, "w"))
        subprocess.run(["node", os.path.join(HERE, "brain_cli.mjs"), "features", a, b], check=True)
        return json.load(open(b))


def windows(X, t0):
    X = np.asarray(X, np.float32)
    idx = np.arange(t0, len(X))[:, None] + np.arange(-WIN + 1, 1)[None, :]
    return X[np.maximum(idx, 0)]                     # (N, WIN, C)


# ---------------------------------------------------------------- tiny 1D CNN in numpy
ARCH = [(16, 5, 1), (24, 5, 2), (24, 5, 2)]          # (channels out, kernel, stride)


def init(C, K, rng):
    layers, cin = [], C
    for o, k, s in ARCH:
        layers.append(dict(W=rng.normal(0, np.sqrt(2 / (cin * k)), (o, cin, k)).astype(np.float32), b=np.zeros(o, np.float32), s=s))
        cin = o
    return dict(layers=layers, Wd=rng.normal(0, np.sqrt(1 / cin), (K, cin)).astype(np.float32), bd=np.zeros(K, np.float32))


def conv_f(x, L):
    O, C, K = L["W"].shape
    s = L["s"]
    To = (x.shape[2] - K) // s + 1
    idx = s * np.arange(To)[:, None] + np.arange(K)[None, :]
    cols = x[:, :, idx].transpose(0, 2, 1, 3).reshape(x.shape[0], To, C * K)
    y = cols @ L["W"].reshape(O, C * K).T + L["b"]
    return np.maximum(y, 0).transpose(0, 2, 1), (cols, y, idx, x.shape)


def conv_b(dy, L, cache):
    cols, y, idx, xs = cache
    O, C, K = L["W"].shape
    g = dy.transpose(0, 2, 1) * (y > 0)
    dW = np.einsum("bto,btc->oc", g, cols).reshape(O, C, K)
    db = g.sum((0, 1))
    dcols = (g @ L["W"].reshape(O, C * K)).reshape(xs[0], -1, C, K).transpose(0, 2, 1, 3)
    dx = np.zeros(xs, np.float32)
    for k in range(K):
        dx[:, :, idx[:, k]] += dcols[:, :, :, k]
    return dx, dW, db


def forward(M, x):
    caches, h = [], x
    for L in M["layers"]:
        h, c = conv_f(h, L)
        caches.append(c)
    g = h.mean(2)
    z = g @ M["Wd"].T + M["bd"]
    return z, (caches, h, g)


def softmax(z):
    e = np.exp(z - z.max(1, keepdims=True))
    return e / e.sum(1, keepdims=True)


def train(Xw, y, cw, rng, epochs=45, bs=128, lr=3e-3):
    C = Xw.shape[1]
    M = init(C, len(CLASSES), rng)
    params = [(L, "W") for L in M["layers"]] + [(L, "b") for L in M["layers"]] + [(M, "Wd"), (M, "bd")]
    mom = [np.zeros_like(p[k]) for p, k in params]
    vel = [np.zeros_like(p[k]) for p, k in params]
    step = 0
    for ep in range(epochs):
        order = rng.permutation(len(Xw))
        tot, hit = 0.0, 0
        for a in range(0, len(order), bs):
            bi = order[a:a + bs]
            xb, yb = augment(Xw[bi], rng), y[bi]
            z, (caches, h, g) = forward(M, xb)
            p = softmax(z)
            w = cw[yb]
            tot += float(-(w * np.log(p[np.arange(len(yb)), yb] + 1e-9)).sum())
            hit += int((p.argmax(1) == yb).sum())
            dz = p.copy()
            dz[np.arange(len(yb)), yb] -= 1
            dz *= (w / w.sum())[:, None]
            grads = {}
            grads[(id(M), "Wd")] = dz.T @ g
            grads[(id(M), "bd")] = dz.sum(0)
            dh = np.repeat((dz @ M["Wd"])[:, :, None], h.shape[2], 2) / h.shape[2]
            for L, c in zip(reversed(M["layers"]), reversed(caches)):
                dh, dW, db = conv_b(dh, L, c)
                grads[(id(L), "W")] = dW + 1e-4 * L["W"]
                grads[(id(L), "b")] = db
            step += 1
            lr_t = lr * (0.5 * (1 + np.cos(np.pi * ep / epochs)))
            for j, (p_, k) in enumerate(params):
                gr = grads[(id(p_), k)].astype(np.float32)
                mom[j] = 0.9 * mom[j] + 0.1 * gr
                vel[j] = 0.999 * vel[j] + 0.001 * gr * gr
                mh, vh = mom[j] / (1 - 0.9 ** step), vel[j] / (1 - 0.999 ** step)
                p_[k] = (p_[k] - lr_t * mh / (np.sqrt(vh) + 1e-8)).astype(np.float32)
        if ep % 5 == 0 or ep == epochs - 1:
            print(f"  epoch {ep:2d}  loss {tot / len(order):.3f}  train acc {hit / len(order):.3f}")
    return M


MIRROR = [6, 7, 8, 9, 10, 11, 0, 1, 2, 3, 4, 5, 12, 13, 14]
NORM = {}


def augment(xb, rng):
    """xb: (B, C, WIN) normalized. Augment in raw units, then re-normalize."""
    mean, std = NORM["mean"][None, :, None], NORM["std"][None, :, None]
    x = xb * std + mean
    B = len(x)
    flip = rng.random(B) < 0.5
    x[flip] = x[flip][:, MIRROR]
    for s in (0, 6):                                           # IMU mounting error, per window
        ot, os_ = rng.normal(0, 0.04, B), rng.normal(0, 0.04, B)
        x[:, s] += ot[:, None]
        x[:, s + 1] += os_[:, None]
        x[:, s + 2] += (ot - os_)[:, None]
        x[:, s + 5] *= rng.uniform(0.85, 1.15, B)[:, None]     # insole gain
    x[:, 12] += rng.normal(0, 0.06, B)[:, None]                # hub tilt on the back
    sig = np.array([0.01, 0.01, 0.014, 0.08, 0.08, 0.02] * 2 + [0.01, 0.08, 0.02], np.float32)
    x += rng.normal(0, 1, x.shape).astype(np.float32) * sig[None, :, None]
    return ((x - mean) / std).astype(np.float32)


def to_cw(Xw):                                   # (N, WIN, C) raw -> (N, C, WIN) normalized
    return ((Xw - NORM["mean"]) / NORM["std"]).transpose(0, 2, 1).astype(np.float32)


def predict(M, x):
    return softmax(forward(M, x)[0])


def report(title, y, pred):
    acc = (y == pred).mean()
    print(f"{title}: {acc * 100:.1f}% of {len(y)} steps")
    present = sorted(set(y.tolist()) | set(pred.tolist()))
    print("    truth\\called " + " ".join(f"{CLASSES[c]:>6}" for c in present))
    for t in present:
        if (y == t).sum():
            print(f"    {CLASSES[t]:>12} " + " ".join(f"{int(((y == t) & (pred == c)).sum()):6d}" for c in present))
    return acc


def main():
    rng = np.random.default_rng(SEED)
    have = [c for c in TRAIN + HELDOUT if find(c)]
    missing = [c for c in TRAIN + HELDOUT if not find(c)]
    if missing:
        print("not found (run brain/fetch_mocap.sh for the extra CMU clips):", ", ".join(missing))
    clips = {c: Clip(c) for c in have}

    # ---- simulated sensors for every clip, every time warp
    trk, lab = {}, {}
    for c, cl in clips.items():
        for w in (WARPS if c in TRAIN else [1.0]):
            tt_clip = np.arange(0, cl.dur / w, 1 / HZ) * w      # w > 1 plays the clip faster
            key = f"{c}@{w}"
            trk[key] = tracks_json(cl, tt_clip)
            lab[key] = label_at(cl, tt_clip)
    # still holds: any training frame frozen for 1.5 s. Standing still in a walking or running posture is
    # STAND (no steps, no gait mode); a frozen seated frame is still SIT, a frozen bent-over frame still LIFT.
    holds = {}
    for c, cl in clips.items():
        if c not in TRAIN:
            continue
        g = np.arange(0, cl.dur, 1 / HZ)
        yl = label_at(cl, g)
        for j, f in enumerate(rng.choice(len(g), size=min(60, len(g)), replace=False)):
            key = f"{c}#hold{j}"
            trk[key] = tracks_json(cl, g[f:f + 1])
            trk[key]["pad"] = 1.5
            holds[key] = {3: 3, 4: 4}.get(int(yl[f]), 0)
    print(f"simulating sensors for {len(trk)} clip variants and holds (node brain/brain_cli.mjs features)")
    F = features(trk)
    for k, yk in holds.items():
        lab[k] = np.full(5, yk)
        F[k]["X"] = F[k]["X"][-(WIN + 4):]
        F[k]["t0"] = WIN - 1

    def stack(keys):
        Xs, ys = [], []
        for k in keys:
            Xs.append(windows(F[k]["X"], F[k]["t0"]))
            ys.append(lab[k])
        return np.concatenate(Xs), np.concatenate(ys)

    train_keys = [k for k in trk if k.split("@")[0].split("#")[0] in TRAIN]
    Xr, y = stack(train_keys)
    rows = Xr.reshape(-1, Xr.shape[2])
    NORM["mean"] = rows.mean(0).astype(np.float32)
    NORM["std"] = (rows.std(0) + 1e-3).astype(np.float32)
    Xw = to_cw(Xr)
    counts = np.bincount(y, minlength=len(CLASSES))
    print("training windows per class:", dict(zip(CLASSES, counts.tolist())))
    cw = (counts.sum() / (len(CLASSES) * np.maximum(counts, 1))).astype(np.float32)
    cw = np.sqrt(cw)                                    # soften the class weights
    M = train(Xw, y, cw, rng)

    print()
    report("train (all warps, no noise)", y, predict(M, Xw).argmax(1))
    held = [k for k in trk if "#" not in k and k.split("@")[0] in HELDOUT]
    if held:
        Xh, yh = stack(held)
        report("HELD-OUT clips " + ", ".join(k.split("@")[0] for k in held), yh, predict(M, to_cw(Xh)).argmax(1))
        for k in held:
            Xk, yk = stack([k])
            pk = predict(M, to_cw(Xk)).argmax(1)
            print(f"    {k.split('@')[0]:>7}: {(pk == yk).mean() * 100:5.1f}%  truth {dict((str(u), int(c)) for u, c in zip(*np.unique([CLASSES[i] for i in yk], return_counts=True)))}")

    # ---- export
    out = dict(
        about="Sitka mode model: tiny 1D CNN on simulated thigh/shin/hub IMU + insole features, 50 Hz, 1 s window. "
              "Trained on CMU motion capture by brain/train_mode_model.py. Simulated sensors only; not yet trained on a real wearer.",
        classes=CLASSES,
        hz=HZ, win=WIN, seed=SEED, train_clips=[c for c in TRAIN if c in clips], heldout_clips=[c for c in HELDOUT if c in clips],
        mean=np.round(NORM["mean"], 6).tolist(), std=np.round(NORM["std"], 6).tolist(),
        layers=[dict(W=np.round(L["W"], 5).tolist(), b=np.round(L["b"], 5).tolist(), stride=L["s"]) for L in M["layers"]],
        dense=dict(W=np.round(M["Wd"], 5).tolist(), b=np.round(M["bd"], 5).tolist()))
    npar = sum(L["W"].size + L["b"].size for L in M["layers"]) + M["Wd"].size + M["bd"].size
    out["params"] = int(npar)
    js = json.dumps(out, separators=(",", ":"))
    open(os.path.join(HERE, "mode_model.json"), "w").write(js + "\n")
    open(os.path.join(HERE, "mode_model.js"), "w").write("window.SITKA_BRAIN_MODEL=" + js + ";\n")
    print(f"\nwrote brain/mode_model.json and .js: {npar} parameters ({npar / 1024:.1f} K; {npar} bytes at int8, {npar * 4 / 1024:.0f} KB float32)")

    # ---- the viewer's own sequences (whole brain: model + debounce + safety layer, run in node)
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "v.json")
        subprocess.run(["node", os.path.join(HERE, "brain_cli.mjs"), "viewer", "--json", p], check=True, stdout=subprocess.DEVNULL)
        V = json.load(open(p))
    print("\nviewer sequences (truth = the offline label rules on the source clip at the same moment)")
    rows = []
    for seq, (c, t0) in VIEWER.items():
        if seq not in V or c not in clips:
            continue
        modes = V[seq]["modes"]
        tt = t0 + np.arange(len(modes)) / HZ
        yt = label_at(clips[c], tt)
        called = np.array([CLASSES.index(m) if m in CLASSES else -1 for m in modes])
        raw = np.array([CLASSES.index(m) for m in V[seq]["rawModes"]])
        agree, agree_raw = (called == yt).mean(), (raw == yt).mean()
        tcount = dict(zip(*np.unique([CLASSES[i] for i in yt], return_counts=True)))
        tpct = {str(k): round(100 * float(v) / len(yt), 1) for k, v in tcount.items()}
        print(f"  {seq:8s} called {V[seq]['mode']}  truth {tpct}  agree {agree * 100:.1f}% (model alone {agree_raw * 100:.1f}%)  vetoes {V[seq]['vetoPct']}%")
        rows.append(dict(seq=seq, called=V[seq]["mode"], truth=tpct, agree=round(agree * 100, 1), agree_raw=round(agree_raw * 100, 1),
                         veto=V[seq]["vetoPct"], lockL=V[seq]["lockPctL"], lockR=V[seq]["lockPctR"], motor=V[seq]["motorPct"], vetoes=V[seq]["vetoes"]))
    json.dump(rows, open(os.path.join(HERE, "viewer_check.json"), "w"), indent=1)


_LABEL_CACHE = {}


def label_at(clip, tt):
    """offline labels of the whole clip on a 50 Hz grid, then looked up at times tt"""
    if clip.name not in _LABEL_CACHE:
        g = np.arange(0, clip.dur, 1 / HZ)
        _LABEL_CACHE[clip.name] = (g, clip.labels(g))
    g, y = _LABEL_CACHE[clip.name]
    return y[np.clip(np.round(np.asarray(tt) * HZ).astype(int), 0, len(y) - 1)]


if __name__ == "__main__":
    main()
