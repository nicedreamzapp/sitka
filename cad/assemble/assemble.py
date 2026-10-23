"""Sitka render two: pose the wearer, place every part on its segment, route the cables/bands/straps per
pose, check fit against the body, export GLBs for the viewer and render studio PNGs.

Run (Blender headless):
  blender -b --factory-startup -noaudio --python cad/assemble/assemble.py -- [--no-render] [--poses stand,chair]
Reads  cad/build/manifest.json, cad/glb/parts/*.glb, cad/body/sitka_body.blend
Writes cad/glb/sitka_parts.glb, cad/glb/sitka_body_<pose>.glb, cad/glb/sitka_cables_<pose>.glb,
       cad/glb/sitka_<pose>.glb (full assembly), cad/build/poses.json, cad/build/fit_report.txt,
       cad/renders/<pose>_<view>.png
"""
import bpy, bmesh, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CAD, "body"))
import poses as PZ

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
RENDER = "--no-render" not in argv and "--anim" not in argv
ANIM = "--anim" in argv
FAST = "--fast" in argv
ONLY = None
for a in argv:
    if a.startswith("--poses="):
        ONLY = a.split("=", 1)[1].split(",")
SAMPLES = 96
for a in argv:
    if a.startswith("--samples="):
        SAMPLES = int(a.split("=")[1])
VIEWS = ["front", "side", "back", "34"]
for a in argv:
    if a.startswith("--views="):
        VIEWS = a.split("=")[1].split(",")

MAN = json.load(open(os.path.join(CAD, "build", "manifest.json")))
ANCH, FRAMES = MAN["anchors"], MAN["frames"]
POSES = ONLY or PZ.ORDER

bpy.ops.wm.open_mainfile(filepath=os.path.join(CAD, "body", "sitka_body.blend"))
scene = bpy.context.scene
RIG, BODY = bpy.data.objects["Rig"], bpy.data.objects["Body"]

# ------------------------------------------------------------------ materials
def mat(name, rgb, rough, metal=0.0, coat=0.0, coat_rough=0.1, alpha=1.0, sheen=0.0):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if coat:
        b.inputs["Coat Weight"].default_value = coat
        b.inputs["Coat Roughness"].default_value = coat_rough
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
    return m


def srgb(h):
    h = h.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + 0.055) / 1.055) ** 2.4 if x > 0.04045 else x / 12.92 for x in c)


MATS = {
    "carbon": mat("carbon", srgb("#202328"), 0.48, coat=0.25, coat_rough=0.3),
    "carbon_gloss": mat("carbon_gloss", srgb("#1a1c20"), 0.32, coat=0.6, coat_rough=0.12),
    "alu": mat("alu", srgb("#9ea4ab"), 0.36, metal=1.0),
    "accent": mat("accent", srgb("#d2602a"), 0.36, metal=0.85),
    "leaf": mat("leaf", srgb("#24364a"), 0.26, coat=0.9, coat_rough=0.06),
    "foam": mat("foam", srgb("#8d939a"), 0.92),
    "fabric": mat("fabric", srgb("#2a2e34"), 0.88, sheen=0.4),
    "cable": mat("cable", srgb("#d9a441"), 0.45),
    "band": mat("band", srgb("#2f8f8a"), 0.55),
    "latex": mat("latex", srgb("#c97d3a"), 0.45),
    "bowden": mat("bowden", srgb("#0d0e10"), 0.25, coat=0.6),
    "motor": mat("motor", srgb("#3a3f46"), 0.38, metal=1.0),
    "electronics": mat("electronics", srgb("#26292e"), 0.45, coat=0.5),
    "rubber": mat("rubber", srgb("#121314"), 0.8),
    "shoe": mat("shoe", srgb("#5d6168"), 0.86, sheen=0.3),
    "body": mat("body", srgb("#bdb3a7"), 0.62),
    "ghost": mat("ghost", srgb("#7fb2ff"), 0.4),
}
BODY.data.materials.clear()
BODY.data.materials.append(MATS["body"])
for poly in BODY.data.polygons:
    poly.use_smooth = True

# ------------------------------------------------------------------ parts
PARTCOL = bpy.data.collections.new("Sitka")
scene.collection.children.link(PARTCOL)
PART_OBJS = {}
for p in MAN["parts"]:
    fp = os.path.join(CAD, "glb", "parts", p["name"] + ".glb")
    if not os.path.exists(fp):
        print("missing glb", p["name"]); continue
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=fp)
    new = [o for o in bpy.data.objects if o not in before]
    meshes = [o for o in new if o.type == 'MESH']
    for o in new:
        o.select_set(False)
    # bake every imported node transform into one mesh in the part's local frame
    bm = bmesh.new()
    for o in meshes:
        me = o.data.copy()
        me.transform(o.matrix_world)
        bm.from_mesh(me)
        bpy.data.meshes.remove(me)
    me = bpy.data.meshes.new(p["name"])
    bm.to_mesh(me); bm.free()
    for o in new:
        bpy.data.objects.remove(o, do_unlink=True)
    me.materials.append(MATS[p["mat"]])
    for poly in me.polygons:
        poly.use_smooth = True
    ob = bpy.data.objects.new(p["name"], me)
    PARTCOL.objects.link(ob)
    if p["mat"] != "foam":
        # sharp rims stay crisp, curved faces smooth
        try:
            me.set_sharp_from_angle(angle=math.radians(40))
        except Exception:
            pass
    if p["name"].startswith("shoe"):
        md = ob.modifiers.new("smooth", 'SUBSURF'); md.levels = 2
        bpy.context.view_layer.objects.active = ob
        bpy.ops.object.modifier_apply(modifier="smooth")
    ob["module"], ob["seg"], ob["group"], ob["mat"] = p["module"], p["seg"], p["group"], p["mat"]
    ob["label"] = p.get("label") or ""
    PART_OBJS[p["name"]] = ob


def tube_mesh(name, pts, radius=None, w=None, t=None, normals=None, mat_name="cable", seg=12):
    """round tube (radius) or flat band (w x t, thin side along normals) through world points"""
    pts = [Vector(p) for p in pts]
    n = len(pts)
    bm = bmesh.new()
    rings = []
    prev_side = None
    for i, p in enumerate(pts):
        tan = (pts[min(i + 1, n - 1)] - pts[max(i - 1, 0)]).normalized()
        if normals is not None:
            nn = Vector(normals[i]); nn = (nn - tan * nn.dot(tan)).normalized()
        else:
            ref = Vector((0, 0, 1)) if abs(tan.z) < 0.9 else Vector((1, 0, 0))
            if prev_side is not None:
                ref = prev_side
            nn = tan.cross(ref).cross(tan).normalized() if prev_side is None else (prev_side - tan * prev_side.dot(tan)).normalized()
        prev_side = nn
        bn = tan.cross(nn).normalized()
        ring = []
        if radius:
            for k in range(seg):
                a = 2 * math.pi * k / seg
                ring.append(bm.verts.new(p + radius * (math.cos(a) * nn + math.sin(a) * bn)))
        else:
            # rounded rectangle, thin side along nn
            hw, ht = w / 2, t / 2
            prof = []
            for k in range(16):
                a = 2 * math.pi * (k + 0.5) / 16
                cx, cy = math.cos(a), math.sin(a)
                # superellipse
                ex = math.copysign(abs(cx) ** 0.35, cx) * hw
                ey = math.copysign(abs(cy) ** 0.35, cy) * ht
                prof.append((ex, ey))
            for ex, ey in prof:
                ring.append(bm.verts.new(p + ex * bn + ey * nn))
        rings.append(ring)
    m = len(rings[0])
    for i in range(n - 1):
        for k in range(m):
            bm.faces.new((rings[i][k], rings[i][(k + 1) % m], rings[i + 1][(k + 1) % m], rings[i + 1][k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me); bm.free()
    for poly in me.polygons:
        poly.use_smooth = True
    me.materials.append(MATS[mat_name])
    ob = bpy.data.objects.new(name, me)
    return ob


# ------------------------------------------------------------------ strut (3 telescoping carbon sections + foot)
def strut_objs():
    objs = []
    for k, (od, idd) in enumerate(((0.024, 0.021), (0.020, 0.017), (0.016, 0.013))):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=od / 2, depth=0.32, location=(0, 0, 0.16))
        o = bpy.context.active_object; o.name = f"strut_tube{k}"
        bpy.ops.object.transform_apply(location=True)
        o.data.materials.append(MATS["carbon_gloss"])
        for poly in o.data.polygons: poly.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(50))
        objs.append(o)
    # twist-lock collars
    for k, od in enumerate((0.0275, 0.0235)):
        bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=od / 2, depth=0.022, location=(0, 0, 0.011))
        o = bpy.context.active_object; o.name = f"strut_collar{k}"
        bpy.ops.object.transform_apply(location=True)
        o.data.materials.append(MATS["accent"]); objs.append(o)
        for poly in o.data.polygons: poly.use_smooth = True
        o.data.set_sharp_from_angle(angle=math.radians(50))
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, radius=0.019, location=(0, 0, 0))
    o = bpy.context.active_object; o.name = "strut_foot"; o.scale = (1, 1, 1.25)
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(MATS["rubber"]); objs.append(o)
    for poly in o.data.polygons: poly.use_smooth = True
    for o in objs:
        for c in list(o.users_collection):
            c.objects.unlink(o)
        PARTCOL.objects.link(o)
    return objs


STRUT = {}
for sd in ("l", "r"):
    objs = strut_objs()
    for o in objs:
        o.name = o.name + "_" + sd
        o["module"], o["group"], o["seg"] = "basic", "strut", "thigh_" + sd
        o["mat"] = "carbon_gloss"
        o["label"] = "Telescoping carbon strut 24/20/16 (5.2 kN)" if o.name.startswith("strut_tube0") else ""
        PART_OBJS[o.name] = o
    STRUT[sd] = objs


def M4(a):
    return Matrix([list(r) for r in a])


def frame(pose, seg):
    return M4(FRAMES[pose][seg])


def W(pose, key, extra=None):
    a = ANCH[key]
    return frame(pose, a["seg"]) @ Vector(a["p"])


def strut_foot(pin, sd):
    # foot on the floor, tilted 4 deg back and splayed 9 deg out (TENDON_CONCEPT section 2)
    S = 1 if sd == "l" else -1
    h = pin.z - 0.019 * 1.25
    return Vector((pin.x + S * math.tan(math.radians(9)) * h, pin.y + math.tan(math.radians(4)) * h, 0.019 * 1.25))


def place_strut(pose, sd, bvh, blend=None, foot_target=None, xlocal=None):
    """xlocal (animation): the strut's roll reference carried rigidly in the thigh frame while stowed, blended to
    the world-up reference as it deploys (a stowed strut is near vertical, where world-up flips its roll)"""
    pin = W(pose, "strut_pin_" + sd)
    objs = STRUT[sd]
    if blend is None:
        blend = 1.0 if PZ.POSES[pose]["mode"] == "SIT" else 0.0
    stow = W(pose, "strut_stow_" + sd)
    dst = (stow - pin).normalized()
    if blend <= 0.0:
        L, d = 0.36, dst
    else:
        foot_t = foot_target or strut_foot(pin, sd)
        ddp = (foot_t - pin)
        Lf = min(0.86, ddp.length)
        d = (dst * (1 - blend) + ddp.normalized() * blend).normalized()
        L = 0.36 + (Lf - 0.36) * blend
    foot = pin + d * L
    z = (foot - pin).normalized()
    x = Vector((0, 0, 1)).cross(z)
    if x.length < 1e-6:
        x = Vector((1, 0, 0))
    x.normalize()
    if xlocal is not None and blend < 1.0:
        # roll from the thigh-carried reference to the world-up one in proportion to the deploy (about the axis)
        xb = frame(pose, "thigh_" + sd).to_3x3() @ xlocal
        xb = (xb - z * xb.dot(z)).normalized()
        ang = math.atan2(z.dot(xb.cross(x)), xb.dot(x))
        x = (Matrix.Rotation(ang * blend, 3, z) @ xb).normalized()
    y = z.cross(x)
    R = Matrix((x, y, z)).transposed().to_4x4()
    # sections: tube0 at the top, tube1/tube2 slide out evenly
    ext = max(0.0, L - 0.36)
    offs = [0.0, 0.018 + ext / 2, 0.036 + ext]
    for k in range(3):
        objs[k].matrix_world = Matrix.Translation(pin) @ R @ Matrix.Translation((0, 0, offs[k]))
    objs[3].matrix_world = Matrix.Translation(pin) @ R @ Matrix.Translation((0, 0, offs[0] + 0.32 - 0.011))
    objs[4].matrix_world = Matrix.Translation(pin) @ R @ Matrix.Translation((0, 0, offs[1] + 0.32 - 0.011))
    objs[5].matrix_world = Matrix.Translation(pin) @ R @ Matrix.Translation((0, 0, offs[2] + 0.32 + 0.010))
    return L


# ------------------------------------------------------------------ routing helpers
def densify(pts, step=0.008):
    out = [Vector(pts[0])]
    P = [Vector(p) for p in pts]
    for i in range(len(P) - 1):
        p0, p1 = P[max(i - 1, 0)], P[i]
        p2, p3 = P[i + 1], P[min(i + 2, len(P) - 1)]
        n = max(2, int((p2 - p1).length / step))
        for k in range(1, n + 1):
            t = k / n
            # centripetal-ish Catmull-Rom (uniform)
            t2, t3 = t * t, t * t * t
            q = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2 + (-p0 + 3 * p1 - 3 * p2 + p3) * t3)
            out.append(q)
    return out


def straight(pts, step=0.006):
    out = [Vector(pts[0])]
    for i in range(len(pts) - 1):
        a, b = Vector(pts[i]), Vector(pts[i + 1])
        n = max(1, int((b - a).length / step))
        out += [a.lerp(b, k / n) for k in range(1, n + 1)]
    return out


def conform(pts, bvh, off, iters=4, keep_ends=True):
    P = [p.copy() for p in pts]
    N = [None] * len(P)
    for it in range(iters):
        for i, p in enumerate(P):
            loc, nor, idx, dist = bvh.find_nearest(p)
            if loc is None:
                continue
            d = (p - loc).dot(nor)
            N[i] = nor.copy()
            if (keep_ends and i in (0, len(P) - 1)):
                continue
            if d < off:
                P[i] = loc + nor * off
        if it < iters - 1:
            Q = [P[0]] + [(P[i - 1] + 2 * P[i] + P[i + 1]) / 4 for i in range(1, len(P) - 1)] + [P[-1]]
            P = Q
    for i, p in enumerate(P):
        loc, nor, idx, dist = bvh.find_nearest(p)
        N[i] = nor if loc is not None else Vector((0, 0, 1))
    return P, N


def clearance(pts, bvh, r):
    worst = 1.0
    for p in pts:
        loc, nor, idx, dist = bvh.find_nearest(p)
        if loc is None:
            continue
        worst = min(worst, (p - loc).dot(nor) - r)
    return worst


def arc_wrap(pose, sd, p_in, p_out):
    """tendon path over the 80 mm arc (in the knee frame, plane x = 0)"""
    K = frame(pose, "knee_" + sd)
    Ki = K.inverted()
    r = ANCH["arc_" + sd]["r"]
    alo, ahi = math.radians(ANCH["arc_" + sd]["lo"]), math.radians(ANCH["arc_" + sd]["hi"])
    a, b = Ki @ p_in, Ki @ p_out

    def tang(P, sign):
        d = math.hypot(P.y, P.z)
        return math.atan2(P.z, P.y) + sign * math.acos(min(1.0, r / d))
    f1, f2 = tang(a, +1), tang(b, -1)
    pts = []
    info = dict(wrap_deg=0.0, phi1=math.degrees(f1), phi2=math.degrees(f2))
    if f2 > f1:
        n = max(2, int((f2 - f1) / math.radians(4)))
        for k in range(n + 1):
            f = f1 + (f2 - f1) * k / n
            pts.append(K @ Vector((0.0, r * math.cos(f), r * math.sin(f))))
        info["wrap_deg"] = math.degrees(f2 - f1)
        info["inside_arc"] = (f1 >= alo - 0.06) and (f2 <= ahi + 0.06)
    else:
        info["inside_arc"] = True
    return pts, info


# ------------------------------------------------------------------ per-pose routing table
def routes(pose, mode=None, cc=None):
    mode = mode or PZ.POSES[pose]["mode"]
    ccd = (mode == "SIT") if cc is None else cc
    R = []
    for sd in ("l", "r"):
        S = 1 if sd == "l" else -1
        st = {"SIT": "LOCKED (cam holds 426 N)", "LIFT": "sit leaf ON (squat)", "RUN": "FREE", "WALK": "FREE (cam open)"}[mode]
        R.append(dict(name="t1_tendon_" + sd, kind="t1", side=sd, module="basic", mat="cable", r=0.0016,
                      label="Knee seat tendon T1 (Vectran, 80 mm arm)", state=st))
        t3 = {"LIFT": "ON: 30 Nm per side", "SIT": "OFF (switched)", "WALK": "slack (< 35 deg)", "RUN": "slack"}[mode]
        R.append(dict(name="t3_tendon_" + sd, pts=["t3_whiffle_" + sd, "t3_panel_" + sd, "t3_lumbar_" + sd,
                                                  "t3_glute_" + sd, "t3_cuff_" + sd], segs=[0.021, 0.024, 0.024, 0.005],
                      module="basic", mat="cable", r=0.0017, how="conform",
                      label="M2 lift tendon (whiffletree to thigh cuff)", state=t3))
        R.append(dict(name="m3_band_" + sd, pts=["m3_belt_" + sd, "m3_thigh_" + sd], module="basic", mat="band",
                      w=0.020, t=0.003, how="conform", off=0.007, label="M3 hip-flexor band 14 N/mm",
                      state="stretches past 0 deg hip extension" if mode in ("WALK", "RUN") else "slack"))
        R.append(dict(name="harness_" + sd, pts=["harness_top_" + sd, "harness_shoulder_" + sd, "harness_chest_" + sd,
                                                "harness_low_" + sd, "harness_belt_" + sd],
                      module="basic", mat="fabric", w=0.045, t=0.007, how="conform", off=0.0045,
                      label="Shoulder harness (Dock)" if sd == "l" else ""))
        R.append(dict(name="panelstrap_" + sd, pts=["panelstrap_top_" + sd, "panelstrap_belt_" + sd], module="basic",
                      mat="fabric", w=0.038, t=0.003, how="conform", off=0.0125, label=""))
        R.append(dict(name="cupstrap_" + sd, pts=["cupstrap_belt_" + sd, "cupstrap_" + sd], module="basic",
                      mat="fabric", w=0.030, t=0.003, how="conform", off=0.004, label="Seat-cup strap to the belt" if sd == "l" else ""))
        if ccd:
            R.append(dict(name="crazycreek_" + sd, pts=["cc_panel_" + sd, "cc_belt_" + sd, "cc_thigh_" + sd], module="basic", mat="fabric",
                          w=0.025, t=0.0025, how="conform", segs=[0.006, 0.017], label="Crazy Creek strap (94 N at 10 deg recline)", state="taut 94 N"))
        else:
            R.append(dict(name="crazycreek_" + sd, pts=["cc_panel_" + sd, "cc_belt_" + sd], module="basic", mat="fabric",
                          w=0.025, t=0.0025, how="conform", off=0.004, label="Crazy Creek strap (stowed)", state="stowed on the belt"))
        R.append(dict(name="hamstring_band_" + sd, pts=["ham_cup_" + sd, "knee_guide_" + sd, "ham_calf_" + sd],
                      module="coupling", mat="band", w=0.016, t=0.003, how="conform", segs=[0.018, 0.014],
                      label="Hamstring band (hip + knee coupling)" if sd == "l" else "",
                      state={"SIT": "OFF in SIT", "LIFT": "slack (knees nearly straight)", "RUN": "off in RUN"}.get(mode, "taut in late swing")))
        R.append(dict(name="calf_band_" + sd, pts=["calfband_thigh_" + sd, "knee_guide_" + sd, "heel_" + sd],
                      module="coupling", requires="upgrade", mat="cable", r=0.0015, how="conform", segs=[0.019, 0.014],
                      label="Calf band (knee + M4 ankle)" if sd == "l" else "", guide_dx=0.006))
        R.append(dict(name="m4_cable_" + sd, pts=["m4_spring_" + sd, "heel_" + sd], module="upgrade", mat="cable",
                      r=0.0014, how="conform", off=0.006, label=""))
        R.append(dict(name="bowden_" + sd, pts=["port_knee_" + sd, "bowden_belt_" + sd, "bowden_hip_" + sd, "bowden_thigh_" + sd],
                      module="upgrade", mat="bowden", r=0.0025, how="conform", off=0.018,
                      label="Bowden to the knee manifold (P1)" if sd == "l" else ""))
        R.append(dict(name="m5_lever_" + sd, pts=["m5_pivot_" + sd, "m5_cuff_" + sd], module="upgrade", mat="carbon",
                      w=0.012, t=0.006, how="conform", off=0.016, label="M5 arm lever" if sd == "l" else ""))
    R.append(dict(name="sternum_strap", pts=["harness_chest_l", "harness_chest_r"], module="basic", mat="fabric",
                  w=0.022, t=0.003, how="conform", off=0.009, label=""))
    if mode == "RUN":
        R.append(dict(name="running_band", pts=["runband_l", "runband_r"], module="basic", mat="latex", r=0.005,
                      how="taut", label="Running band, shin to shin (-6.4% running)", state="RUN only"))
    return R


# ------------------------------------------------------------------ main loop
REPORT = []
POSE_JSON = {"parts": {}, "cables": {}, "labels": {}}
os.makedirs(os.path.join(CAD, "glb"), exist_ok=True)
os.makedirs(os.path.join(CAD, "renders"), exist_ok=True)


def body_snapshot(pose):
    dg = bpy.context.evaluated_depsgraph_get()
    ev = BODY.evaluated_get(dg)
    me = bpy.data.meshes.new_from_object(ev, depsgraph=dg)
    me.transform(BODY.matrix_world)
    ob = bpy.data.objects.new("body_" + pose, me)
    ob.data.materials.clear(); ob.data.materials.append(MATS["body"])
    for poly in me.polygons:
        poly.use_smooth = True
    ob["module"], ob["group"], ob["label"] = "body", "body", ""
    return ob


def export_glb(objs, path):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objs:
        o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=path, export_format='GLB', use_selection=True, export_extras=True,
                              export_apply=True, export_yup=True, export_normals=True, export_texcoords=False,
                              export_materials='EXPORT')


def setup_render():
    scene.render.engine = 'CYCLES'
    try:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        prefs.compute_device_type = 'METAL'
        prefs.get_devices()
        for d in prefs.devices:
            d.use = True
        scene.cycles.device = 'GPU'
    except Exception as e:
        print("gpu?", e)
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = True
    scene.render.resolution_x, scene.render.resolution_y = (600, 750) if FAST else (1200, 1500)
    if FAST:
        scene.render.engine = 'BLENDER_EEVEE'

    scene.render.film_transparent = False
    scene.view_settings.view_transform = 'AgX'
    scene.view_settings.look = 'AgX - Base Contrast'
    w = bpy.data.worlds.new("studio"); scene.world = w
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.62, 0.64, 0.67, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.22
    # seamless studio sweep
    bpy.ops.mesh.primitive_plane_add(size=30, location=(0, 0, 0))
    fl = bpy.context.active_object; fl.name = "floor"
    fl.data.materials.append(mat("floor", (0.30, 0.31, 0.33), 0.8))
    for name, loc, rot, size, power, col in (
            ("key", (-2.6, -3.0, 3.6), (math.radians(52), 0, math.radians(-40)), 2.6, 700, (1, 0.97, 0.93)),
            ("fill", (3.2, -2.0, 2.0), (math.radians(65), 0, math.radians(55)), 3.0, 260, (0.92, 0.96, 1.0)),
            ("rim", (0.6, 3.4, 3.0), (math.radians(-55), 0, math.radians(170)), 2.0, 650, (1, 1, 1)),
            ("top", (0, 0, 4.5), (0, 0, 0), 3.0, 200, (1, 1, 1))):
        ld = bpy.data.lights.new(name, 'AREA'); ld.size = size; ld.energy = power; ld.color = col
        lo = bpy.data.objects.new(name, ld); lo.location = loc; lo.rotation_euler = rot
        scene.collection.objects.link(lo)
    cd = bpy.data.cameras.new("cam"); cd.lens = 70
    cam = bpy.data.objects.new("cam", cd); scene.collection.objects.link(cam); scene.camera = cam
    return cam


def aim(cam, target, direction, dist):
    d = Vector(direction).normalized()
    cam.location = Vector(target) + d * dist
    cam.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()


def route_path(pose, rt, bvh, report=True):
    if rt.get("kind") == "t1":
        sd = rt["side"]
        p0, p1, p3 = W(pose, "t1_manifold_" + sd), W(pose, "t1_fairlead_" + sd), W(pose, "t1_shin_" + sd)
        wrap, info = arc_wrap(pose, sd, p1, p3)
        pts = straight([p0, p1] + ([wrap[0]] if wrap else []))
        if wrap:
            pts += wrap[1:]
            pts += straight([wrap[-1], p3])[1:]
        else:
            pts += straight([p1, p3])[1:]
        if report: REPORT.append(f"{pose:6s} T1 {sd}: wrap {info['wrap_deg']:.0f} deg, phi {info['phi1']:.0f}..{info['phi2']:.0f}, on arc: {info['inside_arc']}")
        normals = None
    else:
        raw = [W(pose, k) for k in rt["pts"]]
        if rt.get("guide_dx"):
            raw = [r + (frame(pose, "knee_" + rt["name"][-1]).to_3x3() @ Vector((rt["guide_dx"] * (1 if rt["name"].endswith("_l") else -1), 0, 0)))
                   if k.startswith("knee_guide") else r for r, k in zip(raw, rt["pts"])]
        segs = rt.get("segs") or ([rt["off"]] * (len(raw) - 1) if rt["how"] == "conform" else ["t"] * (len(raw) - 1))
        pts, normals = [raw[0]], [None]
        half = rt.get("r") or rt.get("t", 0.004) / 2
        for i, md in enumerate(segs):
            seg_pts = straight([raw[i], raw[i + 1]], 0.008)
            if md == "t":
                nn = [None] * len(seg_pts)
            else:
                seg_pts, nn = conform(seg_pts, bvh, md + half, iters=5)
            pts += seg_pts[1:]; normals += nn[1:]
        if any(n is None for n in normals):
            normals = None
    if not rt.get("r") and normals is None:
        normals = []
        for p in pts:
            loc, nor, idx, dist = bvh.find_nearest(p)
            normals.append((p - loc).normalized() if loc is not None and (p - loc).length > 1e-5 else Vector((0, 0, 1)))
    return pts, normals



# ================================================================== animation export (--anim)
def resample(pts, n):
    P = [Vector(p) for p in pts]
    d = [0.0]
    for i in range(1, len(P)):
        d.append(d[-1] + (P[i] - P[i - 1]).length)
    if d[-1] < 1e-9:
        return [P[0].copy() for _ in range(n)], [0] * n
    out, idx = [], []
    j = 0
    for k in range(n):
        t = d[-1] * k / (n - 1)
        while j < len(d) - 2 and d[j + 1] < t:
            j += 1
        a = (t - d[j]) / max(1e-12, d[j + 1] - d[j])
        out.append(P[j].lerp(P[j + 1], min(1.0, max(0.0, a))))
        idx.append(j if a < 0.5 else j + 1)
    return out, idx


if ANIM:
    import numpy as np, base64
    SEGBONE = {"pelvis": "pelvis", "chest": "spine_03", "thigh_l": "thigh_l", "thigh_r": "thigh_r", "shin_l": "calf_l",
               "shin_r": "calf_r", "foot_l": "foot_l", "foot_r": "foot_r", "uarm_l": "upperarm_l", "uarm_r": "upperarm_r"}
    SOLE = 0.022
    frs = json.load(open(os.path.join(CAD, "body", "frames.json")))
    RIG.location = (0, 0, 0)
    PZ.apply_pose(RIG, "stand", bpy, Matrix, Vector)
    RIG.location = frs["stand"]["offset"]
    bpy.context.view_layer.update()
    LSEG = {sg: (RIG.matrix_world @ RIG.pose.bones[b].matrix).inverted() @ M4(FRAMES["stand"][sg]) for sg, b in SEGBONE.items()}
    FOOT_REF = (RIG.matrix_world @ RIG.pose.bones["foot_r"].head).copy()
    POLYS = [list(pl.vertices) for pl in BODY.data.polygons]
    TRIS = []
    for q in POLYS:
        for k in range(1, len(q) - 1):
            TRIS += [q[0], q[k], q[k + 1]]
    NV = len(BODY.data.vertices)
    # strut foot targets: where the strut plants in the final chair pose
    FT = {sd: strut_foot(W("chair", "strut_pin_" + sd), sd) for sd in ("l", "r")}

    def seg_frames():
        F = {sg: RIG.matrix_world @ RIG.pose.bones[b].matrix @ LSEG[sg] for sg, b in SEGBONE.items()}
        for sd in ("l", "r"):
            At, As = F["thigh_" + sd], F["shin_" + sd]
            q = At.to_quaternion().slerp(As.to_quaternion(), 0.5)
            K = q.to_matrix().to_4x4(); K.translation = As.translation
            F["knee_" + sd] = K
        return {k: [list(r) for r in v] for k, v in F.items()}

    if "--procedural" in argv:
        SEQ = PZ.sequences()            # the old keyframed poses (cad/body/poses.py)
    else:
        # real motion capture (CMU, cad/mocap/CREDITS.md), retargeted onto the same rig: cad/mocap/sequences.py
        sys.path.insert(0, os.path.join(CAD, "mocap"))
        import sequences as MOCAP
        _dom = np.load(os.path.join(CAD, "body", "stand_weights.npz"))["dom"]
        _fl, _fr = (RIG.matrix_world @ RIG.pose.bones["foot_" + sd].head for sd in ("l", "r"))
        SEQ = MOCAP.build(RIG, BODY, bpy, Matrix, _dom, ((_fl.x + _fr.x) / 2, (_fl.y + _fr.y) / 2),
                          log=lambda m: print(m, flush=True))
    # stowed-strut roll reference: the standing pose's (world-up based) roll, carried in the thigh frame
    XLOC = {}
    for sd in ("l", "r"):
        _z = (W("stand", "strut_stow_" + sd) - W("stand", "strut_pin_" + sd)).normalized()
        _x = Vector((0, 0, 1)).cross(_z).normalized()
        XLOC[sd] = frame("stand", "thigh_" + sd).to_3x3().inverted() @ _x
    _domv = np.load(os.path.join(CAD, "body", "stand_weights.npz"))["dom"]
    FOOT_VIDX = {sd: np.where(np.isin(_domv, ["foot_" + sd, "ball_" + sd]))[0] for sd in ("l", "r")}
    NRES = 40
    body_bin, cab_bin, nrm_bin = bytearray(), bytearray(), bytearray()
    out = dict(nv=NV, tris=TRIS, parts=[n for n in PART_OBJS], seqs={}, cables={})
    nframe = 0
    modes = {"walk": "WALK", "run": "RUN", "sitdown": "SIT", "standup": "SIT", "stoop": "LIFT"}
    for sname, frames in SEQ.items():
        seq = dict(n=len(frames), loop=frames[0]["loop"], start=nframe, states=[], parts=[], cables=[])
        if "fps" in frames[0]:
            seq["fps"] = round(frames[0]["fps"], 4)     # playback rate (viewer: seconds of motion = frame / fps)
        def pose_frame(fr):
            RIG.location = (0, 0, 0)
            if "apply" in fr:
                loc = fr["apply"](RIG)      # mocap: poses the rig, returns its grounded world location
            else:
                PZ.apply_params(RIG, fr["params"], bpy, Matrix, Vector)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            ev = BODY.evaluated_get(dg); me = ev.to_mesh()
            co = np.empty(NV * 3, dtype=np.float64); me.vertices.foreach_get("co", co); ev.to_mesh_clear()
            V = co.reshape(-1, 3)
            dz = -V[:, 2].min() + SOLE
            if fr["ground"] == "mocap":
                dx, dy, dz = (float(x) for x in loc)
            elif fr["ground"] == "pelvis":
                ph = RIG.pose.bones["pelvis"].head
                dx, dy = -ph.x, -ph.y
            else:
                a = RIG.pose.bones["foot_r"].head
                dx, dy = FOOT_REF.x - a.x, FOOT_REF.y - a.y
            RIG.location = (dx, dy, dz)
            bpy.context.view_layer.update()
            V = V + np.array([dx, dy, dz])
            FRAMES["__a__"] = seg_frames()
            return V

        if sname in ("sitdown", "standup"):
            pose_frame(frames[-1] if sname == "sitdown" else frames[0])
            FT = {sd: strut_foot(W("__a__", "strut_pin_" + sd), sd) for sd in ("l", "r")}
        for fi, fr in enumerate(frames):
            V = pose_frame(fr)
            bvh = BVHTree.FromPolygons([Vector(v) for v in V], POLYS)
            body_bin += np.round(V * 10000).astype(np.int16).tobytes()
            mats = []
            for nm, ob in PART_OBJS.items():
                if nm.startswith("strut"):
                    continue
                pp = next(p for p in MAN["parts"] if p["name"] == nm)
                ob.matrix_world = frame("__a__", pp["seg"])
            for sd in ("l", "r"):
                place_strut("__a__", sd, bvh, blend=fr["strut"], foot_target=FT[sd] if sname in ("sitdown", "standup") else None,
                            xlocal=XLOC[sd])
            for nm, ob in PART_OBJS.items():
                m = ob.matrix_world
                mats.append([round(m[i][j], 5) for i in range(3) for j in range(4)])
            seq["parts"].append(mats)
            cabs = []
            for rt in routes("__a__", mode=modes[sname], cc=fr["cc"]):
                pts, normals = route_path("__a__", rt, bvh, report=False)
                rp, idx = resample(pts, NRES)
                spec = out["cables"].setdefault(rt["name"], dict(module=rt["module"], requires=rt.get("requires", ""),
                                                                 mat=rt["mat"], r=rt.get("r", 0), w=rt.get("w", 0), t=rt.get("t", 0),
                                                                 label=rt.get("label", "")))
                c = np.array([tuple(p) for p in rp])
                cabs.append(dict(name=rt["name"], o=len(cab_bin) // 2))
                cab_bin += np.round(c * 10000).astype(np.int16).tobytes()
                if normals is not None:
                    nn = np.array([tuple(normals[i]) for i in idx])
                    cabs[-1]["no"] = len(nrm_bin)
                    nrm_bin += np.clip(np.round(nn * 127), -127, 127).astype(np.int8).tobytes()
            seq["cables"].append(cabs)
            seq["states"].append(fr["states"])
            # check line (log only): sole heights, foot pitch, strut tip heights, lowest body point
            fz = {sd: float(V[FOOT_VIDX[sd], 2].min()) for sd in ("l", "r")}
            sz = {sd: min((o.matrix_world @ v.co).z for o in STRUT[sd] for v in o.data.vertices) for sd in ("l", "r")}
            fp = {}
            for sd in ("l", "r"):
                v = RIG.pose.bones["ball_" + sd].tail - RIG.pose.bones["foot_" + sd].head
                r0 = RIG.data.bones["ball_" + sd].tail_local - RIG.data.bones["foot_" + sd].head_local
                fp[sd] = math.degrees(math.atan2(v.z, v.xy.length) - math.atan2(r0.z, r0.xy.length))
            print("CHK %s %02d sole %.4f %.4f pitch %.1f %.1f strut %.4f %.4f body %.4f" % (
                sname, fi, fz["l"], fz["r"], fp["l"], fp["r"], sz["l"], sz["r"], V[:, 2].min()), flush=True)
            nframe += 1
        out["seqs"][sname] = seq
        print("SEQ", sname, len(frames), flush=True)
    out["body_b64"] = base64.b64encode(bytes(body_bin)).decode()
    out["cab_b64"] = base64.b64encode(bytes(cab_bin)).decode()
    out["nrm_b64"] = base64.b64encode(bytes(nrm_bin)).decode()
    out["nres"] = NRES
    open(os.path.join(CAD, "viewer", "sitka_anim.js"), "w").write("window.SITKA_ANIM=" + json.dumps(out, separators=(",", ":")) + ";\n")
    print("ANIM OK", nframe, "frames", round(len(body_bin) / 1e6, 1), "MB body", flush=True)
    sys.exit(0)

cam = setup_render() if RENDER else None
VIEWDIR = {"front": (0, -1, 0.08), "side": (1, 0, 0.06), "back": (0, 1, 0.10), "34": (0.75, -0.8, 0.28)}

for pose in POSES:
    RIG.location = (0, 0, 0)
    PZ.apply_pose(RIG, pose, bpy, Matrix, Vector)
    fr0 = json.load(open(os.path.join(CAD, "body", "frames.json")))[pose]
    RIG.location = fr0["offset"]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    bodyob = body_snapshot(pose)
    scene.collection.objects.link(bodyob)
    bvh = BVHTree.FromPolygons([v.co.copy() for v in bodyob.data.vertices], [list(pl.vertices) for pl in bodyob.data.polygons])
    BODY.hide_render = True
    POSE_JSON["parts"][pose] = {}
    for p in MAN["parts"]:
        ob = PART_OBJS.get(p["name"])
        if ob is None:
            continue
        ob.matrix_world = frame(pose, p["seg"])
        POSE_JSON["parts"][pose][p["name"]] = [list(r) for r in ob.matrix_world]
    for sd in ("l", "r"):
        L = place_strut(pose, sd, bvh)
        for o in STRUT[sd]:
            POSE_JSON["parts"][pose][o.name] = [list(r) for r in o.matrix_world]
        REPORT.append(f"{pose:6s} strut_{sd}: length {L:.3f} m ({'deployed' if PZ.POSES[pose]['mode'] == 'SIT' else 'stowed'})")
    bpy.context.view_layer.update()

    # cables
    cab_objs = []
    POSE_JSON["cables"][pose] = {}
    for rt in routes(pose):
        pts, normals = route_path(pose, rt, bvh)
        c = clearance(pts[2:-2] if len(pts) > 6 else pts, bvh, rt.get("r") or rt.get("t", 0.003) / 2)
        if os.environ.get("DBG") and rt["name"] == os.environ.get("DBG"):
            for i, p in enumerate(pts):
                loc, nor, idx, dist = bvh.find_nearest(p)
                print("DBG", i, tuple(round(v, 3) for v in p), round((p - loc).dot(nor), 4), round(dist, 4))
        if c < -0.002:
            REPORT.append(f"{pose:6s} CABLE {rt['name']}: enters body by {-c * 1000:.0f} mm")
        if rt.get("r"):
            ob = tube_mesh(rt["name"], pts, radius=rt["r"], mat_name=rt["mat"])
        else:
            if normals is None:
                # flat band: thin side faces away from the body
                normals = []
                for p in pts:
                    loc, nor, idx, dist = bvh.find_nearest(p)
                    normals.append((p - loc).normalized() if loc is not None and (p - loc).length > 1e-5 else Vector((0, 0, 1)))
            ob = tube_mesh(rt["name"], pts, w=rt["w"], t=rt["t"], normals=normals, mat_name=rt["mat"])
        ob["module"], ob["group"], ob["label"] = rt["module"], "cable", rt.get("label", "")
        ob["state"] = rt.get("state", "")
        if rt.get("requires"):
            ob["requires"] = rt["requires"]
        scene.collection.objects.link(ob)
        cab_objs.append(ob)
        POSE_JSON["cables"][pose][rt["name"]] = dict(module=rt["module"], state=rt.get("state", ""),
                                                     pts=[list(map(float, p)) for p in pts[::3]])

    # fit check: every rigid part vs the posed body
    for name, ob in PART_OBJS.items():
        if ob.data is None or name.startswith("shoe"):
            continue
        me = ob.data
        Mw = ob.matrix_world
        vs = me.vertices
        stride = max(1, len(vs) // 600)
        worst, wp = 0.0, None
        for i in range(0, len(vs), stride):
            p = Mw @ vs[i].co
            loc, nor, idx, dist = bvh.find_nearest(p)
            if loc is None or dist > 0.05:
                continue
            d = (p - loc).dot(nor)
            if d < worst:
                worst, wp = d, p
        dmin = 9.0
        for i in range(0, len(vs), stride):
            loc, nor, idx, dist = bvh.find_nearest(Mw @ vs[i].co)
            if loc is not None:
                dmin = min(dmin, dist)
        if dmin > 0.03 and not name.startswith(("strut", "p1_", "whiffle")):
            REPORT.append(f"{pose:6s} FLOAT {name}: nearest skin {dmin * 1000:.0f} mm, at {tuple(round(v, 3) for v in (Mw @ vs[0].co))}")
        allow = -0.0025 if ob.get("mat") == "foam" else -0.0008
        if worst < allow:
            REPORT.append(f"{pose:6s} PART {name}: into body {-worst * 1000:.1f} mm at {tuple(round(v, 3) for v in wp)}")

    # exports
    export_glb([bodyob], os.path.join(CAD, "glb", f"sitka_body_{pose}.glb"))
    export_glb(cab_objs, os.path.join(CAD, "glb", f"sitka_cables_{pose}.glb"))
    export_glb([bodyob] + list(PART_OBJS.values()) + cab_objs, os.path.join(CAD, "glb", f"sitka_{pose}.glb"))

    if RENDER:
        g = MATS["ghost"]; g.blend_method = 'BLEND' if hasattr(g, "blend_method") else None
        bsdf = g.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Alpha"].default_value = 0.30
        swapped = []
        for o in list(PART_OBJS.values()) + cab_objs:
            if o.get("module") == "upgrade" or o.get("requires") == "upgrade":
                swapped.append((o, list(o.data.materials)))
                o.data.materials.clear(); o.data.materials.append(g)
        # frame the whole figure
        allv = [bodyob.matrix_world @ v.co for v in list(bodyob.data.vertices)[::25]]
        mn = Vector((min(v.x for v in allv), min(v.y for v in allv), 0))
        mx = Vector((max(v.x for v in allv), max(v.y for v in allv), max(v.z for v in allv)))
        ctr = (mn + mx) / 2
        hgt = mx.z
        for view in VIEWS:
            if view.startswith("cam"):
                v = [float(x) for x in os.environ["SITKA_CAM"].split(",")]
                cam.location = Vector(v[:3]); d = (Vector(v[3:6]) - Vector(v[:3]))
                cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
                cam.data.lens = float(os.environ.get("SITKA_LENS", "70"))
            else:
                cam.data.lens = 70
                aim(cam, ctr, VIEWDIR[view], 1.0 + hgt * 2.05)
            scene.render.filepath = os.path.join(CAD, "renders", f"{pose}_{view}.png")
            bpy.ops.render.render(write_still=True)
    if RENDER:
        for o, mats in swapped:
            o.data.materials.clear()
            for m in mats:
                o.data.materials.append(m)
    bpy.data.objects.remove(bodyob, do_unlink=True)
    for o in cab_objs:
        bpy.data.objects.remove(o, do_unlink=True)
    print("POSE DONE", pose, flush=True)

# parts in their local frames, once, for the viewer
for ob in PART_OBJS.values():
    ob.matrix_world = Matrix.Identity(4)
export_glb(list(PART_OBJS.values()), os.path.join(CAD, "glb", "sitka_parts.glb"))
POSE_JSON["poses"] = {p: dict(label=PZ.POSES[p]["label"], mode=PZ.POSES[p]["mode"]) for p in PZ.ORDER}
POSE_JSON["parts_meta"] = {n: dict(module=o.get("module"), group=o.get("group"), label=o.get("label"), mat=o.get("mat"))
                           for n, o in PART_OBJS.items()}
json.dump(POSE_JSON, open(os.path.join(CAD, "build", "poses.json"), "w"))
open(os.path.join(CAD, "build", "fit_report.txt"), "w").write("\n".join(REPORT) + "\n")
print("\n".join(REPORT))
print("ASSEMBLY OK")
