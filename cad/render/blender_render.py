# -*- coding: utf-8 -*-
"""
Blender (>= 4.2, tested 5.3) render/animation of the ARC Engineer arm.
    blender -b -P cad/render/blender_render.py -- --stills      (Cycles hero stills)
    blender -b -P cad/render/blender_render.py -- --anim        (EEVEE MP4, both clips)
    blender -b -P cad/render/blender_render.py -- --save        (just build + save .blend)
Inputs from export_render.py: meshes/*.obj + anim.json (body matrices in mm).
"""
import json
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
os.makedirs(OUT, exist_ok=True)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
DATA = json.load(open(os.path.join(HERE, "anim.json")))

ASSETS = os.path.join(HERE, "assets")
# key: (ambientCG set or None, tile mm, base colour (multiplied with the colour map if use_col), use_col,
#       metallic, roughness range, normal strength, extra)
MATS = {
    "cf": ("Fabric004", 30.0, (0.11, 0.11, 0.12), True, 0.0, (0.30, 0.55), 0.6, dict(coat=1.0, coat_rough=0.05)),
    "pla": ("Plastic011", 40.0, (0.90, 0.30, 0.04), False, 0.0, (0.50, 0.72), 0.35, {}),
    "alu": ("Metal012", 70.0, (0.92, 0.92, 0.94), True, 1.0, (0.30, 0.50), 0.35, {}),
    "steel": ("Metal032", 15.0, (0.10, 0.10, 0.11), True, 0.9, (0.22, 0.42), 0.25, {}),
    "motor": ("Metal032", 45.0, (0.08, 0.08, 0.09), True, 0.85, (0.28, 0.50), 0.25, {}),
    "pad": ("Rubber004", 25.0, (0.08, 0.30, 0.85), False, 0.0, (0.65, 0.90), 0.5, {}),
    "brass": ("Metal032", 15.0, (0.95, 0.70, 0.32), True, 1.0, (0.20, 0.35), 0.2, {}),
    "pcb": (None, 1.0, (0.02, 0.22, 0.07), False, 0.0, (0.40, 0.40), 0.0, {}),
    "pom": ("Plastic011", 30.0, (0.88, 0.88, 0.85), False, 0.0, (0.35, 0.50), 0.2, {}),
    "donut": ("Plastic011", 60.0, (0.92, 0.66, 0.05), False, 0.0, (0.40, 0.55), 0.2, {}),
    "red": ("Plastic011", 60.0, (0.75, 0.06, 0.05), False, 0.0, (0.30, 0.45), 0.15, {}),
    "blue": ("Plastic011", 60.0, (0.05, 0.15, 0.70), False, 0.0, (0.30, 0.45), 0.15, {}),
    "field": ("Metal032", 120.0, (0.30, 0.31, 0.33), True, 0.3, (0.45, 0.65), 0.2, {}),
    "wood": ("plywood", 400.0, (1.0, 1.0, 1.0), True, 0.0, (0.60, 0.75), 0.0, {}),
    "chassis": ("Metal032", 150.0, (0.07, 0.075, 0.08), True, 0.4, (0.40, 0.60), 0.2, {}),
    "floor": (None, 1.0, (0.055, 0.058, 0.062), False, 0.0, (0.55, 0.55), 0.0, {}),
}


def _img(path, noncolor):
    im = bpy.data.images.load(path, check_existing=True)
    if noncolor:
        im.colorspace_settings.name = "Non-Color"
    return im


def material(key):
    """Principled BSDF fed by tri-planar (box-projected, object-space mm) PBR maps."""
    name = "M_" + key
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    tex, tile, col, use_col, met, (r0, r1), nstr, ex = MATS.get(key, MATS["field"])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    N, L = nt.nodes, nt.links
    b = N.get("Principled BSDF")
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Metallic"].default_value = met
    b.inputs["Roughness"].default_value = (r0 + r1) / 2
    for nm, v in (("Coat Weight", ex.get("coat")), ("Coat Roughness", ex.get("coat_rough"))):
        if v is not None and nm in b.inputs:
            b.inputs[nm].default_value = v
    if not tex:
        return m
    if tex == "plywood":
        maps = {"Color": os.path.join(ASSETS, "polyhaven", "plywood_diff_1k.jpg")}
    else:
        base = os.path.join(ASSETS, tex, tex + "_1K-JPG_")
        maps = {k: base + k + ".jpg" for k in ("Color", "Roughness", "NormalGL")}
    tc = N.new("ShaderNodeTexCoord")
    mp = N.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile, 1.0 / tile, 1.0 / tile)
    L.new(tc.outputs["Object"], mp.inputs["Vector"])

    def image(k, noncolor):
        t = N.new("ShaderNodeTexImage")
        t.image = _img(maps[k], noncolor)
        t.projection = "BOX"
        t.projection_blend = 0.2
        L.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    if use_col and "Color" in maps:
        c = image("Color", False)
        mix = N.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = "MULTIPLY"
        mix.inputs["Factor"].default_value = 1.0
        L.new(c.outputs["Color"], mix.inputs[6])
        mix.inputs[7].default_value = (*col, 1.0)
        L.new(mix.outputs[2], b.inputs["Base Color"])
    if "Roughness" in maps:
        r = image("Roughness", True)
        mr = N.new("ShaderNodeMapRange")
        mr.inputs["To Min"].default_value = r0
        mr.inputs["To Max"].default_value = r1
        L.new(r.outputs["Color"], mr.inputs["Value"])
        L.new(mr.outputs["Result"], b.inputs["Roughness"])
    if "NormalGL" in maps and nstr > 0:
        n = image("NormalGL", True)
        nm_ = N.new("ShaderNodeNormalMap")
        nm_.inputs["Strength"].default_value = nstr
        L.new(n.outputs["Color"], nm_.inputs["Color"])
        L.new(nm_.outputs["Normal"], b.inputs["Normal"])     # clear coat stays smooth over the CF weave
    return m


def import_obj(path, name, mat_key, parent):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z")
    new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        o.name = name
        o.data.materials.clear()
        o.data.materials.append(material(mat_key))
        try:
            o.data.shade_smooth()
            o.data.set_sharp_from_angle(angle=math.radians(35))
        except Exception:
            pass
        o.parent = parent
        o.matrix_parent_inverse = Matrix.Identity(4)
        o.matrix_basis = Matrix.Identity(4)
    return new


def m4(a):
    return Matrix([a[0:4], a[4:8], a[8:12], a[12:16]])


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    root = bpy.data.objects.new("WORLD_mm", None)
    root.scale = (0.001, 0.001, 0.001)
    sc.collection.objects.link(root)
    robot = bpy.data.objects.new("ROBOT", None)          # chassis frame: strafes / drives in the clips
    sc.collection.objects.link(robot)
    robot.parent = root
    bodies = {}
    for f in DATA["files"]:
        b = f["body"]
        if b not in bodies:
            e = bpy.data.objects.new("BODY_" + b, None)
            sc.collection.objects.link(e)
            e.parent = robot
            bodies[b] = e
        import_obj(os.path.join(HERE, "meshes", f["file"]), "%s_%s" % (b, f["material"]), f["material"], bodies[b])
    field = {}
    for n, f in DATA["field"].items():
        par = bodies["HEAD"] if n.startswith("held_") else root
        objs = import_obj(os.path.join(HERE, "meshes", f["file"]), n, f["material"], par)
        field[n] = objs[0]
        off = DATA.get("field_offset", {}).get("pipe", {}).get(n)
        if off:
            objs[0].location = off
    # stylised chassis deck under the arm base (chassis itself is not designed yet)
    bpy.ops.mesh.primitive_cube_add(size=1)
    ch = bpy.context.active_object
    ch.name = "chassis_deck_placeholder"
    ch.parent = robot
    ch.scale = (580, 480, 80)
    ch.location = (-290, 0, 80)
    ch.data.materials.append(material("chassis"))
    bev = ch.modifiers.new("bevel", "BEVEL")
    bev.width = 0.02
    bev.segments = 4
    bpy.ops.mesh.primitive_plane_add(size=8)
    fl = bpy.context.active_object
    fl.name = "floor"
    fl.data.materials.append(material("floor"))
    # world: dim sky for reflections + studio area lights
    w = bpy.data.worlds.new("World")
    sc.world = w
    w.use_nodes = True
    bg = w.node_tree.nodes["Background"]
    # studio gradient: dark charcoal, slightly lighter towards the horizon
    tc = w.node_tree.nodes.new("ShaderNodeTexCoord")
    sep = w.node_tree.nodes.new("ShaderNodeSeparateXYZ")
    ramp = w.node_tree.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (0.10, 0.105, 0.115, 1)
    ramp.color_ramp.elements[1].position = 0.6
    ramp.color_ramp.elements[1].color = (0.018, 0.019, 0.022, 1)
    w.node_tree.links.new(tc.outputs["Generated"], sep.inputs[0])
    w.node_tree.links.new(sep.outputs["Z"], ramp.inputs[0])
    env = w.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = _img(os.path.join(ASSETS, "polyhaven", "studio_small_03_tonemapped.jpg"), False)
    lp = w.node_tree.nodes.new("ShaderNodeLightPath")
    mixw = w.node_tree.nodes.new("ShaderNodeMix")
    mixw.data_type = "RGBA"
    w.node_tree.links.new(lp.outputs["Is Camera Ray"], mixw.inputs["Factor"])
    w.node_tree.links.new(env.outputs["Color"], mixw.inputs[6])
    w.node_tree.links.new(ramp.outputs[0], mixw.inputs[7])
    w.node_tree.links.new(mixw.outputs[2], bg.inputs[0])
    bg.inputs[1].default_value = 0.8
    for nm, loc, size, energy, col in (("key", (1.6, -1.8, 2.2), 1.8, 260, (1.0, 0.96, 0.90)),
                                       ("fill", (-1.6, -1.4, 1.1), 2.5, 70, (0.82, 0.88, 1.0)),
                                       ("rim", (-0.6, 1.8, 1.9), 1.2, 220, (1.0, 1.0, 1.0)),
                                       ("top", (0.0, 0.0, 3.0), 3.0, 120, (1.0, 1.0, 1.0))):
        ld = bpy.data.lights.new(nm, "AREA")
        ld.size = size
        ld.energy = energy
        ld.color = col
        lo = bpy.data.objects.new(nm, ld)
        sc.collection.objects.link(lo)
        lo.location = loc
        d = Vector((0.0, 0.0, 0.45)) - lo.location
        lo.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    # camera + target
    tgt = bpy.data.objects.new("cam_target", None)
    sc.collection.objects.link(tgt)
    tgt.location = (0.05, 0.0, 0.42)
    cd = bpy.data.cameras.new("cam")
    cd.lens = 42
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    con = cam.constraints.new("TRACK_TO")
    con.target = tgt
    con.track_axis = "TRACK_NEGATIVE_Z"
    con.up_axis = "UP_Y"
    sc.camera = cam
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Medium High Contrast"
        sc.view_settings.exposure = -0.3
    except Exception:
        pass
    bodies["__robot__"] = robot
    return sc, bodies, field, cam, tgt


def set_pose(bodies, rec):
    for b, mat in rec["bodies"].items():
        if b in bodies:
            bodies[b].matrix_basis = m4(mat)
    bx, by = rec.get("base", (0.0, 0.0))
    bodies["__robot__"].location = (bx, by, 0.0)


FIELD_SETS = {"donut": ("Side_High_Ground_Lower_Tier", "ZigZag_Pole_PLACEHOLDER", "Objective_C_Donut"),
              "pipe": ("Objective_B_Bucket", "Objective_B_Pipe", "Objective_B_Pipe_Target", "Perimeter_Wall",
                       "Pipe_Chute_D52.5")}


def show_field(field, which, grab, frame=None):
    on = FIELD_SETS[which]
    for n, o in field.items():
        vis = any(n.startswith(k) for k in on)
        if n == "Objective_C_Donut" and grab == "donut":
            vis = False
        if n == "Objective_B_Pipe_Target" and grab == "pipe":
            vis = False
        if n == "held_donut":
            vis = grab == "donut"
        if n == "held_pipe":
            vis = grab == "pipe"
        o.hide_render = not vis
        o.hide_viewport = not vis
        if frame is not None:
            o.keyframe_insert("hide_render", frame=frame)
            o.keyframe_insert("hide_viewport", frame=frame)


def cycles(sc, samples=160):
    samples = int(os.environ.get("SAMPLES", samples))
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    try:
        sc.cycles.denoiser = "OPENIMAGEDENOISE"
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
    sc.render.resolution_percentage = int(os.environ.get("RESPCT", 100))
    sc.render.image_settings.file_format = "PNG"


def stills(sc, bodies, field, cam, tgt):
    cycles(sc)
    views = {"hero_donut_lift": ((1.05, -1.10, 1.02), (-0.02, 0.0, 0.53), "donut"),
             "hero_pipe_chute": ((0.85, -1.05, 0.95), (0.08, 0.0, 0.47), "pipe"),
             "hero_stow": ((0.62, -0.78, 0.62), (-0.20, 0.0, 0.28), None),
             # close-ups: camera / target offsets from the TCP in metres
             "detail_gripper_pipe": (("tcp", (0.30, -0.36, 0.22)), ("tcp", (-0.05, 0.0, 0.02)), "pipe"),
             "detail_gripper_donut": (("tcp", (0.28, -0.34, 0.26)), ("tcp", (-0.05, 0.0, 0.0)), "donut"),
             # review views and joint close-ups: ("body", NAME, local point mm) anchors, offsets in metres
             "overview_side": ((-0.12, -1.95, 0.40), (-0.12, 0.0, 0.36), None),
             "overview_rear": ((-1.15, 0.98, 0.94), (-0.06, 0.0, 0.40), None),
             "detail_shoulder": (("body", "UPPER", (0, 0, 0), (0.24, -0.40, 0.16)), ("body", "UPPER", (0, 0, 0), (0.0, 0.0, -0.02)), None),
             "detail_elbow": (("body", "FOREARM", (0, 0, 0), (0.30, -0.46, 0.16)), ("body", "FOREARM", (0, 0, 0), (0.03, 0.0, 0.02)), None),
             "detail_wrist_roll": (("body", "GRIPPER", (0, 0, 0), (0.20, -0.32, 0.20)), ("body", "GRIPPER", (60, 0, -10), (0.0, 0.0, 0.0)), None),
             "detail_jaw_drive": (("body", "HEAD", (90, 0, 0), (-0.16, -0.34, 0.30)), ("body", "HEAD", (90, 0, 0), (0.0, 0.0, 0.0)), None)}
    LENS = {"overview_side": 50, "overview_rear": 45}
    only = os.environ.get("ONLY")
    only = set(only.split(",")) if only else None
    for nm, rec in DATA["stills"].items():
        if only and nm not in only:
            continue
        set_pose(bodies, rec)
        loc, t, fs = views[nm]
        if loc[0] == "body":
            bpy.context.view_layer.update()

            def _anc(spec):
                p = bodies[spec[1]].matrix_world @ Vector(spec[2])
                return tuple(p[i] + spec[3][i] for i in range(3))
            loc, t = _anc(loc), _anc(t)
            cam.data.lens = 50
        elif loc[0] == "tcp":
            bpy.context.view_layer.update()
            tcp = bodies["HEAD"].matrix_world @ Vector((151.0, 0.0, -20.0))
            loc = tuple(tcp[i] + loc[1][i] for i in range(3))
            t = tuple(tcp[i] + t[1][i] for i in range(3))
            cam.data.lens = 55
        else:
            cam.data.lens = LENS.get(nm, 42)
        cam.location = loc
        tgt.location = t
        if fs:
            show_field(field, fs, rec["grab"])
        else:
            for o in field.values():
                o.hide_render = True
        sc.render.filepath = os.path.join(os.environ.get("OUTDIR", OUT), nm + ".png")
        bpy.ops.render.render(write_still=True)
        print("wrote", sc.render.filepath)


def anim(sc, bodies, field, cam, tgt, res=(1280, 720)):
    sc.render.engine = "BLENDER_EEVEE_NEXT" if "BLENDER_EEVEE_NEXT" in [e.identifier for e in
                                                                          bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items] else "BLENDER_EEVEE"
    try:
        sc.eevee.use_raytracing = bool(int(os.environ.get("EEVEE_RT", "0")))
        sc.eevee.taa_render_samples = int(os.environ.get("EEVEE_SAMPLES", "16"))
        sc.eevee.use_shadows = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    tgt.location = (0.08, 0.0, 0.52)
    fps = DATA["fps"]
    sc.render.fps = fps
    f = 1
    for clip in ("donut", "pipe"):
        frames = DATA["clips"][clip]
        last = None
        for i, rec in enumerate(frames):
            set_pose(bodies, rec)
            for k_, b in bodies.items():
                b.keyframe_insert("location", frame=f)
                if k_ != "__robot__":
                    b.keyframe_insert("rotation_quaternion" if b.rotation_mode == "QUATERNION" else "rotation_euler", frame=f)
            if i == 0 or rec["grab"] != last:
                show_field(field, clip, rec["grab"], frame=f)
                last = rec["grab"]
            # slow camera orbit per clip (pipe clip from the side so the wall doesn't block the view);
            # in the pipe clip the orbit centre follows the chassis as it drives to the chute
            bx, by = [v / 1000.0 for v in rec.get("base", (0.0, 0.0))]
            cx = 0.05 + (0.6 * bx if clip == "pipe" else 0.0)
            cy = 0.6 * by if clip == "pipe" else 0.0
            a0, a1, zc = (-48, -8, 1.05) if clip == "donut" else (-112, -72, 1.25)
            a = math.radians(a0 + (a1 - a0) * i / max(1, len(frames) - 1))
            r = 1.9
            cam.location = (r * math.cos(a) + cx, r * math.sin(a) + cy, zc + 0.12 * math.sin(math.pi * i / len(frames)))
            cam.keyframe_insert("location", frame=f)
            tgt.location = (cx + 0.03, cy, 0.52)
            tgt.keyframe_insert("location", frame=f)
            f += 1
    for b in list(bodies.values()) + [cam, tgt]:
        if b.animation_data and b.animation_data.action:
            for fc in getattr(b.animation_data.action, "fcurves", []):
                for kp in fc.keyframe_points:
                    kp.interpolation = "LINEAR"
    sc.frame_start, sc.frame_end = 1, f - 1
    if os.environ.get("TESTFRAMES"):
        sc.frame_start, sc.frame_end = [int(v) for v in os.environ["TESTFRAMES"].split(",")]
    sc.render.resolution_percentage = int(os.environ.get("RESPCT", 100))
    try:
        sc.render.image_settings.media_type = "VIDEO"      # Blender >= 5.0
    except Exception:
        pass
    sc.render.image_settings.file_format = "FFMPEG"
    sc.render.ffmpeg.format = "MPEG4"
    sc.render.ffmpeg.codec = "H264"
    sc.render.ffmpeg.constant_rate_factor = "HIGH"
    sc.render.filepath = os.path.join(OUT, "arc_engineer_arm_cycle.mp4")
    if os.environ.get("TESTFRAMES"):
        sc.render.image_settings.media_type = "IMAGE"
        sc.render.image_settings.file_format = "PNG"
        sc.render.filepath = os.path.join(OUT, "test_####.png")
    bpy.ops.render.render(animation=True)
    print("wrote", sc.render.filepath, "frames", f - 1)


sc, bodies, field, cam, tgt = build()
for k_, b in bodies.items():
    if k_ != "__robot__":
        b.rotation_mode = "QUATERNION"
set_pose(bodies, DATA["stills"]["hero_stow"])
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, "arc_engineer_arm.blend"))
if "--stills" in args:
    stills(sc, bodies, field, cam, tgt)
if "--anim" in args:
    anim(sc, bodies, field, cam, tgt)
