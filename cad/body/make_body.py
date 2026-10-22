"""Build the Sitka reference wearer from the CC0 MakeHuman base mesh (via MPFB) and pose it.

Run (headless, isolated Blender profile with MPFB installed):
  BLENDER_USER_RESOURCES=cad/.blender blender -b -noaudio --python cad/body/make_body.py

Writes
  cad/body/sitka_body.blend      human + game_engine rig, rest pose
  cad/body/frames.json           per pose: bone world matrices + ground offset
  cad/body/mesh_<pose>.npz       per pose: posed body vertices/faces (for fit checks)
  cad/body/stand_weights.npz     standing mesh + dominant bone per vertex (for contouring shells)
Target: 1.874 m, 130 kg (params.mjs PERSON.stature95 / mass95), male, heavy build.
"""
import bpy, sys, os, json, math
import numpy as np
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import poses as P
from bl_ext.blender_org.mpfb.services.humanservice import HumanService

STATURE = 1.874
SOLE = 0.022  # shoe sole under the bare-foot mesh (shoes are modelled as parts)
for o in list(bpy.data.objects):
    bpy.data.objects.remove(o)

macro = {"gender": 1.0, "age": 0.5, "muscle": 0.6, "weight": 1.0, "proportions": 0.5, "height": 0.615,
         "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.33, "caucasian": 0.34, "african": 0.33}}
body = HumanService.create_human(mask_helpers=True, detailed_helpers=True, extra_vertex_groups=True,
                                 feet_on_ground=True, scale=0.1, macro_detail_dict=macro)
# heavy build for 130 kg at 1.874 m (BMI ~37): MakeHuman's max-weight macro reads closer to BMI ~28,
# so add CC0 MakeHuman measure targets (waist, belly, hips, thighs, arms)
from bl_ext.blender_org.mpfb.services.targetservice import TargetService
TD = os.path.join(os.path.dirname(sys.modules["bl_ext.blender_org.mpfb"].__file__), "data", "targets")
for rel, w in [("stomach/stomach-pregnant-incr", 0.4), ("torso/measure-waist-circ-incr", 0.85),
               ("torso/measure-hips-circ-incr", 0.45), ("buttocks/buttocks-volume-incr", 0.45),
               ("torso/torso-scale-depth-incr", 0.35), ("torso/measure-bust-circ-incr", 0.35),
               ("legs/measure-thigh-circ-incr", 0.7), ("legs/measure-calf-circ-incr", 0.35),
               ("arms/measure-upperarm-circ-incr", 0.45), ("neck/neck-scale-horiz-incr", 0.3)]:
    fp = os.path.join(TD, rel + ".target.gz")
    if os.path.exists(fp):
        TargetService.load_target(body, fp, weight=w)
    else:
        print("missing target", rel)
rig = HumanService.add_builtin_rig(body, "game_engine")
body.name, rig.name = "Body", "Rig"

# bake targets, drop helper geometry
bpy.context.view_layer.objects.active = body
bpy.ops.object.select_all(action='DESELECT')
body.select_set(True)
if body.data.shape_keys:
    bpy.ops.object.shape_key_remove(all=True, apply_mix=True)
for m in list(body.modifiers):
    if m.type == 'MASK':
        bpy.ops.object.modifier_apply(modifier=m.name)

zs = [v.co.z for v in body.data.vertices]
h = max(zs) - min(zs); s = 1.0
print("macro stature", h, "mods", [(m.type, m.name) for m in body.modifiers], "parent", body.parent)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, "sitka_body.blend"))

frames = {}
KEEP = ["pelvis", "spine_01", "spine_02", "spine_03", "neck_01", "head", "clavicle_l", "clavicle_r",
        "upperarm_l", "upperarm_r", "lowerarm_l", "lowerarm_r", "hand_l", "hand_r",
        "thigh_l", "thigh_r", "calf_l", "calf_r", "foot_l", "foot_r", "ball_l", "ball_r"]
for name in P.ORDER:
    rig.location = (0, 0, 0)
    P.apply_pose(rig, name, bpy, Matrix, Vector)
    dg = bpy.context.evaluated_depsgraph_get()
    me = body.evaluated_get(dg).to_mesh()
    V = np.array([v.co[:] for v in me.vertices])
    dz = -V[:, 2].min() + SOLE  # stand on the shoe sole
    # centre the pelvis over the origin in plan
    ph = rig.matrix_world @ rig.pose.bones["pelvis"].head
    dx, dy = -ph.x, -ph.y
    rig.location = (dx, dy, dz)
    bpy.context.view_layer.update()
    me = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).to_mesh()
    V = np.array([v.co[:] for v in me.vertices]) + np.array([dx, dy, dz])
    F = np.array([list(p.vertices) for p in me.polygons if len(p.vertices) == 4])
    T = np.array([list(p.vertices) for p in me.polygons if len(p.vertices) == 3]).reshape(-1, 3)
    np.savez_compressed(os.path.join(HERE, f"mesh_{name}.npz"), V=V, Q=F, T=T)
    fr = {}
    for b in KEEP:
        pb = rig.pose.bones[b]
        M = rig.matrix_world @ pb.matrix
        fr[b] = dict(M=[list(r) for r in M], head=list(rig.matrix_world @ pb.head), tail=list(rig.matrix_world @ pb.tail))
    frames[name] = dict(offset=[dx, dy, dz], bones=fr, label=P.POSES[name]["label"], mode=P.POSES[name]["mode"])
    print("posed", name, "ground dz", round(dz, 3), "V", len(V))
    if name == "stand":
        groups = {g.index: g.name for g in body.vertex_groups}
        dom = []
        for v in body.data.vertices:
            best, bw = "", 0.0
            for g in v.groups:
                gn = groups[g.group]
                if gn in rig.pose.bones and g.weight > bw:
                    best, bw = gn, g.weight
            dom.append(best)
        np.savez_compressed(os.path.join(HERE, "stand_weights.npz"), V=V, Q=F, T=T, dom=np.array(dom))

json.dump(frames, open(os.path.join(HERE, "frames.json"), "w"), indent=1)
print("OK body", h * s)
