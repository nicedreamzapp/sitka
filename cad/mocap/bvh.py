"""Minimal BVH reader + forward kinematics (numpy only, works inside and outside Blender).

World output is in the Sitka/MPFB axes: +X = wearer's left, -Y = forward, +Z = up, metres.
CMU BVH axes are +X left, +Y up, +Z forward, so  tgt = (x, -z, y) * scale.
"""
import numpy as np

AX = np.array([[1, 0, 0], [0, 0, -1], [0, 1, 0]], dtype=float)  # bvh -> sitka (proper rotation)


def _rot(axis, deg):
    a = np.radians(deg)
    c, s = np.cos(a), np.sin(a)
    n = len(a)
    R = np.zeros((n, 3, 3))
    if axis == "X":
        R[:, 0, 0] = 1; R[:, 1, 1] = c; R[:, 1, 2] = -s; R[:, 2, 1] = s; R[:, 2, 2] = c
    elif axis == "Y":
        R[:, 1, 1] = 1; R[:, 0, 0] = c; R[:, 0, 2] = s; R[:, 2, 0] = -s; R[:, 2, 2] = c
    else:
        R[:, 2, 2] = 1; R[:, 0, 0] = c; R[:, 0, 1] = -s; R[:, 1, 0] = s; R[:, 1, 1] = c
    return R


class BVH:
    def __init__(self, path):
        tok = open(path).read().split()
        i = 0
        self.names, self.parent, self.offset, self.chans = [], [], [], []
        self.end = {}            # joint index -> end-site offset
        stack = []
        while tok[i] != "MOTION":
            t = tok[i]
            if t in ("ROOT", "JOINT"):
                self.names.append(tok[i + 1]); self.parent.append(stack[-1] if stack else -1)
                self.offset.append(None); self.chans.append([])
                cur = len(self.names) - 1; i += 2
                assert tok[i] == "{"; stack.append(cur); i += 1
            elif t == "End":
                # End Site { OFFSET x y z }
                j = stack[-1]
                self.end[j] = np.array([float(x) for x in tok[i + 4:i + 7]])
                i += 8
            elif t == "OFFSET":
                self.offset[stack[-1]] = np.array([float(x) for x in tok[i + 1:i + 4]]); i += 4
            elif t == "CHANNELS":
                n = int(tok[i + 1]); self.chans[stack[-1]] = tok[i + 2:i + 2 + n]; i += 2 + n
            elif t == "}":
                stack.pop(); i += 1
            else:
                i += 1
        i += 1
        assert tok[i] == "Frames:"; self.nf = int(tok[i + 1]); i += 2
        assert tok[i] == "Frame" and tok[i + 1] == "Time:"; self.dt = float(tok[i + 2]); i += 3
        nc = sum(len(c) for c in self.chans)
        self.data = np.array(tok[i:i + nc * self.nf], dtype=float).reshape(self.nf, nc)
        self.idx = {n: k for k, n in enumerate(self.names)}
        self.fk()

    def fk(self):
        """world rotations R[j] (nf,3,3) and positions P[j] (nf,3), in BVH axes and units"""
        nf, nj = self.nf, len(self.names)
        self.R = np.zeros((nj, nf, 3, 3)); self.P = np.zeros((nj, nf, 3))
        col = 0
        for j in range(nj):
            ch = self.chans[j]
            loc = np.tile(self.offset[j], (nf, 1))
            Rl = np.tile(np.eye(3), (nf, 1, 1))
            for c in ch:
                v = self.data[:, col]; col += 1
                if c.endswith("position"):
                    loc[:, "XYZ".index(c[0])] = v   # root channels are absolute
                else:
                    Rl = Rl @ _rot(c[0], v)
            p = self.parent[j]
            if p < 0:
                self.R[j] = Rl; self.P[j] = loc
            else:
                self.R[j] = self.R[p] @ Rl
                self.P[j] = self.P[p] + np.einsum("fij,j->fi", self.R[p], self.offset[j])
        # rest (all rotations zero) world rotations are identity; rest positions = summed offsets
        self.rest_P = np.zeros((nj, 3))
        for j in range(nj):
            p = self.parent[j]
            self.rest_P[j] = (self.rest_P[p] if p >= 0 else 0) + (self.offset[j] if p >= 0 else 0)

    def end_pos(self, j):
        """world position of joint j's end site (nf,3)"""
        return self.P[j] + np.einsum("fij,j->fi", self.R[j], self.end[j])

    # --------------------------------------------------------------- sitka axes
    def to_sitka(self, scale):
        self.scale = scale
        self.Rs = np.einsum("ab,jfbc,cd->jfad", AX, self.R, AX.T)       # world rotation in sitka axes
        self.Ps = np.einsum("ab,jfb->jfa", AX, self.P) * scale
        self.rest_Ps = (AX @ self.rest_P.T).T * scale
        return self

    def child_pos(self, j, child=None):
        """sitka-axes world position of the segment end of joint j: a named child joint or the end site"""
        if child is not None:
            return self.Ps[self.idx[child]]
        e = self.end_pos(j)
        return np.einsum("ab,fb->fa", AX, e) * self.scale
