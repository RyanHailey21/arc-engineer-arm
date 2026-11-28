# -*- coding: utf-8 -*-
"""
Step pictures for the prototype build guide (Blender >= 4.2, tested 5.3; Workbench engine, about 2 s a picture):

    tools/blender-5.3.0-windows-x64/blender.exe -b -P cad/render/build_steps.py [-- --variant fourbar] [-- --only elbow]

Reads cad/out/<variant>/build/steps.json and its meshes (cad/tools/build_guide.py) and writes
cad/docs/paper/fig/build_<nn>_<key>.jpg. Colours: orange = the parts this step adds, blue = the bench
sub-assemblies it mounts, light grey = what is already built. Orthographic, framed on the orange and blue parts.
"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(HERE)
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
VARIANT = args[args.index("--variant") + 1] if "--variant" in args else "fourbar"
ONLY = args[args.index("--only") + 1] if "--only" in args else None
SRC = os.path.join(CAD, "out", VARIANT, "build")
FIG = os.path.join(CAD, "docs", "paper", "fig")
COL = {"new": (0.95, 0.42, 0.08, 1.0), "mount": (0.22, 0.45, 0.85, 1.0), "context": (0.80, 0.80, 0.82, 1.0)}
RES = (1600, 1100)


def material(role):
    m = bpy.data.materials.get("B_" + role) or bpy.data.materials.new("B_" + role)
    m.diffuse_color = COL[role]
    return m


def clear():
    for o in list(bpy.data.objects):
        bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        bpy.data.meshes.remove(me)


def scene_setup():
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"
    sh = sc.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_object_outline = True
    sh.object_outline_color = (0.05, 0.05, 0.05)
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    sh.show_shadows = False
    sc.display.render_aa = "16"
    sc.render.resolution_x, sc.render.resolution_y = RES
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.world = sc.world or bpy.data.worlds.new("W")
    sc.world.color = (1.0, 1.0, 1.0)               # Workbench renders take the world colour as the background
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 90
    sc.view_settings.view_transform = "Standard"   # AgX / Filmic would turn the white background grey
    return sc


def frame_camera(sc, lo, hi, view):
    d = Vector(view).normalized()
    c = (Vector(lo) + Vector(hi)) / 2
    cam_d = bpy.data.cameras.new("C")
    cam_d.type = "ORTHO"
    cam = bpy.data.objects.new("C", cam_d)
    sc.collection.objects.link(cam)
    span = (Vector(hi) - Vector(lo)).length
    cam.location = c + d * (span * 3 + 500)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    cam_d.clip_start, cam_d.clip_end = 1.0, span * 6 + 3000
    # orthographic scale: the frame box's corners projected on the camera plane
    right = d.cross(Vector((0, 0, 1))).normalized()
    up = right.cross(d).normalized()
    xs, ys = [], []
    for i in range(8):
        p = Vector((hi[0] if i & 1 else lo[0], hi[1] if i & 2 else lo[1], hi[2] if i & 4 else lo[2])) - c
        xs.append(p.dot(right))
        ys.append(p.dot(up))
    w, h = max(xs) - min(xs), max(ys) - min(ys)
    aspect = RES[0] / RES[1]
    cam_d.ortho_scale = 1.12 * max(w, h * aspect)
    sc.camera = cam


def main():
    data = json.load(open(os.path.join(SRC, "steps.json")))
    sc = scene_setup()
    os.makedirs(FIG, exist_ok=True)
    for st in data["steps"]:
        if ONLY and st["key"] != ONLY:
            continue
        clear()
        for role in ("context", "mount", "new"):
            f = st["files"].get(role)
            if not f:
                continue
            bpy.ops.wm.obj_import(filepath=os.path.join(SRC, f), forward_axis="Y", up_axis="Z")
            for o in bpy.context.selected_objects:
                o.data.materials.clear()
                o.data.materials.append(material(role))
        fr = st["frame"]
        frame_camera(sc, fr[:3], fr[3:], st["view"])
        sc.render.filepath = os.path.join(FIG, st["png"])
        bpy.ops.render.render(write_still=True)
        print("BUILD_STEPS wrote", st["png"])


main()
