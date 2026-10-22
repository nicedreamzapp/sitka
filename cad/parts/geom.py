"""build123d helpers for body-contoured Sitka parts. Units inside build123d: mm."""
import math
import numpy as np
import build123d as bd
from common import radial, side_s

MM = 1000.0


def _rows(z0, z1, lo, hi, nz, nth, round_p, min_frac):
    """theta grid per row: the span narrows toward both ends on a superellipse, so the outline
    of the part has soft, rounded ends instead of square corners"""
    zs = np.linspace(z0, z1, nz)
    rows = []
    zc, hz = (z0 + z1) / 2, (z1 - z0) / 2
    for z in zs:
        a, b = lo(z), hi(z)
        c, h = (a + b) / 2, (b - a) / 2
        q = abs((z - zc) / hz) if hz > 0 else 0
        f = max(min_frac, (max(0.0, 1 - q ** round_p)) ** (1 / round_p))
        rows.append(c + h * f * np.linspace(-1, 1, nth))
    return zs, np.array(rows)


def skin_grid(seg, zs, TH, poses=None, cap=0.03, axis_offset=(0, 0)):
    """skin radius on an irregular theta grid (one theta row per z). Max over poses, but a pose may
    add at most `cap` m over the standing skin (stops spikes from other limbs)."""
    from common import POSES
    poses = poses or POSES
    dense = np.arange(-200, 381, 2.0)
    Rs = radial(seg, zs, dense, poses=["stand"], axis_offset=axis_offset)
    Rm = radial(seg, zs, dense, poses=poses, axis_offset=axis_offset)
    Rm = np.minimum(Rm, Rs + cap)
    out = np.zeros(TH.shape)
    for i in range(len(zs)):
        r = Rm[i].copy()
        good = r > 0
        r = np.interp(dense, dense[good], r[good])
        out[i] = np.interp(TH[i], dense, r)
    return out


def point(seg, z, th_deg, r, axis_offset=(0, 0)):
    s = side_s(seg)
    t = math.radians(th_deg)
    return ((axis_offset[0] + s * r * math.sin(t)) * MM, (axis_offset[1] + r * math.cos(t)) * MM, z * MM)


def contour_part(seg, z0, z1, lo, hi, off, thick, nz=16, nth=15, round_p=3.0, min_frac=0.45,
                 poses=None, fillet=None, axis_offset=(0, 0), skin=None, cap=0.03):
    """A body-contoured plate/shell: inner surface = skin + off (m, may be a function of z),
    thickened outward by `thick` (m). lo/hi(z) = theta bounds in degrees."""
    zs, TH = _rows(z0, z1, lo, hi, nz, nth, round_p, min_frac)
    R = skin if skin is not None else skin_grid(seg, zs, TH, poses=poses, cap=cap, axis_offset=axis_offset)
    # fair the surface: smooth along both directions, never pulling inward
    for _ in range(2):
        P = np.pad(R, 1, mode="edge")
        S = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4
        R = np.maximum(R, 0.5 * R + 0.5 * S)
    import inspect
    two = callable(off) and len([q for q in inspect.signature(off).parameters.values() if q.default is q.empty]) == 2
    O = np.array([[off(z, t) if two else (off(z) if callable(off) else off) for t in TH[i]]
                  for i, z in enumerate(zs)])
    offs = O[:, O.shape[1] // 2]
    s = side_s(seg)
    solid, err = None, None
    for attempt in range(4):
        Ra = R.copy()
        for _ in range(attempt * 3):
            P = np.pad(Ra, 1, mode="edge")
            S = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4
            Ra = np.maximum(Ra, S)
        step = 1 if attempt < 2 else 2
        cols = list(range(0, TH.shape[1], step))
        if cols[-1] != TH.shape[1] - 1:
            cols.append(TH.shape[1] - 1)
        pts = [[point(seg, zs[i], TH[i, j], Ra[i, j] + O[i, j], axis_offset) for j in cols]
               for i in range(len(zs))]
        try:
            face = bd.Face.make_surface_from_array_of_points(pts, tol=0.05 * (1 + attempt))
            ic, jc = len(zs) // 2, TH.shape[1] // 2
            t = math.radians(TH[ic, jc])
            n = (s * math.sin(t), math.cos(t), 0.0)
            solid = bd.thicken(face, thick * MM, normal_override=n)
            if solid.volume <= 0:
                raise ValueError("empty")
            break
        except Exception as e:
            err = e
            solid = None
    if solid is None:
        raise err
    if fillet:
        solid = safe_fillet(solid, fillet * MM)
    return solid, dict(zs=zs, TH=TH, R=R, offs=offs)


def sweep_profile(pts_mm, w, h, rounded=True):
    """sweep a rounded-rectangle (w x h mm) along a smooth spline through pts_mm"""
    path = bd.Spline(*[bd.Vector(*p) for p in pts_mm])
    pl = bd.Plane(origin=path @ 0, z_dir=path % 0)
    with bd.BuildSketch(pl) as sk:
        if rounded:
            bd.RectangleRounded(w, h, min(w, h) * 0.45)
        else:
            bd.Rectangle(w, h)
    return bd.sweep(sk.sketch, path=path)


# ---- fillets in a worker process: OpenCascade can hang on an awkward fillet, so time-box it ----
import concurrent.futures as _cf
import multiprocessing as _mp
_POOL = None


def _fillet_job(shape, r):
    return bd.fillet(shape.edges(), r)


def _pool():
    global _POOL
    if _POOL is None:
        _POOL = _cf.ProcessPoolExecutor(1, mp_context=_mp.get_context("fork"))
    return _POOL


def safe_fillet(shape, r_mm, timeout=12.0):
    """fillet every edge at r_mm; on failure or hang try half the radius; else return the shape unchanged"""
    global _POOL
    for rr in (r_mm, r_mm * 0.5):
        fut = _pool().submit(_fillet_job, shape, rr)
        try:
            return fut.result(timeout=timeout)
        except _cf.TimeoutError:
            for p in list(_POOL._processes.values()):
                p.kill()
            _POOL.shutdown(wait=False, cancel_futures=True)
            _POOL = None
        except Exception:
            pass
    return shape


def _row_wire(pin, pout, round_caps=True):
    """closed section: inner spline, rounded cap, outer spline back, rounded cap"""
    pin = [bd.Vector(*p) for p in pin]
    pout = [bd.Vector(*p) for p in pout]
    e_in = bd.Spline(*pin)
    e_out = bd.Spline(*reversed(pout))
    if round_caps:
        def cap(a, b, prev):
            mid = (a + b) * 0.5
            t = (a - prev)
            t = t.normalized() if t.length > 1e-9 else bd.Vector(0, 0, 0)
            m = mid + t * ((a - b).length * 0.5)
            return bd.ThreePointArc(a, m, b)
        c1 = cap(pin[-1], pout[-1], pin[-2])
        c2 = cap(pout[0], pin[0], pout[1])
    else:
        c1 = bd.Line(pin[-1], pout[-1]); c2 = bd.Line(pout[0], pin[0])
    return bd.Wire([e_in, c1, e_out, c2])


def loft_part(seg, z0, z1, lo, hi, off, thick, nz=14, nth=15, round_p=3.0, min_frac=0.45,
              poses=None, axis_offset=(0, 0), cap=0.03, round_caps=True, end_scale=0.0):
    """Body-contoured plate built as a loft of closed sections (radial thickness, rounded long edges).
    Robust where an OCC offset would self-intersect. thick may be a function of z."""
    zs, TH = _rows(z0, z1, lo, hi, nz, nth, round_p, min_frac)
    R = skin_grid(seg, zs, TH, poses=poses, cap=cap, axis_offset=axis_offset)
    for _ in range(2):
        P = np.pad(R, 1, mode="edge")
        S = (P[:-2, 1:-1] + P[2:, 1:-1] + P[1:-1, :-2] + P[1:-1, 2:]) / 4
        R = np.maximum(R, 0.5 * R + 0.5 * S)
    import inspect
    two = callable(off) and len([q for q in inspect.signature(off).parameters.values() if q.default is q.empty]) == 2
    O = np.array([[off(z, t) if two else (off(z) if callable(off) else off) for t in TH[i]] for i, z in enumerate(zs)])
    tk = np.array([thick(z) if callable(thick) else thick for z in zs])
    wires = []
    for i in range(len(zs)):
        pin = [point(seg, zs[i], TH[i, j], R[i, j] + O[i, j], axis_offset) for j in range(TH.shape[1])]
        pout = [point(seg, zs[i], TH[i, j], R[i, j] + O[i, j] + tk[i], axis_offset) for j in range(TH.shape[1])]
        wires.append(_row_wire(pin, pout, round_caps))
    solid = bd.Solid.make_loft(wires, ruled=False)
    return solid, dict(zs=zs, TH=TH, R=R, O=O)


def contour_part(seg, z0, z1, lo, hi, off, thick, nz=14, nth=15, round_p=3.0, min_frac=0.45,  # noqa: F811
                 poses=None, fillet=None, axis_offset=(0, 0), skin=None, cap=0.03):
    """(loft version) body-contoured plate: rounded long edges, radial thickness, never self-intersects"""
    return loft_part(seg, z0, z1, lo, hi, off, thick, nz=nz, nth=nth, round_p=round_p, min_frac=min_frac,
                     poses=poses, axis_offset=axis_offset, cap=cap)
