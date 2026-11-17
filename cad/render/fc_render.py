# -*- coding: utf-8 -*-
"""
FreeCAD-native (Coin3D/OpenGL) high-quality renders of the mated assembly.
Run inside the FreeCAD GUI:
    exec(open(r"...\\cad\\render\\fc_render.py").read())
    setup()                      # open assembly, field items, materials, lights
    still("hero_donut_lift")     # -> render/out_fc/<name>.png  (4K render, 1920x1080 AA output)
    frames(0, 60)                # animation frames -> render/out_fc/frames/f_0000.png ...

Look comes from prebuilt CC0 assets (render/assets): ambientCG Fabric004
(carbon fibre), Metal012 (brushed), Metal032 (smooth metal), Plastic011,
Rubber004; Poly Haven plywood + studio_small_03 (as a sphere-map for metal
reflections).  Textures are applied with Coin's own texture nodes, the same
mechanism as FreeCAD's Std_TextureMapping command.
"""
import json
import math
import os
import sys

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin

RENDER = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad\render"
RENDER = r"C:\Users\ryanh\light_weight_arm\cad\render"
CAD = os.path.dirname(RENDER)
A = os.path.join(RENDER, "assets")
OUT = os.path.join(RENDER, "out_fc")
os.makedirs(os.path.join(OUT, "frames"), exist_ok=True)
sys.path.insert(0, CAD)
import field as F  # noqa: E402

TEX = dict(cf=os.path.join(A, "Fabric004", "Fabric004_1K-JPG_Color.jpg"),
           brushed=os.path.join(A, "brushed_norm.jpg"),        # ambientCG Metal012, levels-normalised
           metal=os.path.join(A, "metal_norm.jpg"),            # ambientCG Metal032, levels-normalised
           plastic=os.path.join(A, "plastic_norm.jpg"),        # ambientCG Plastic011, levels-normalised
           rubber=os.path.join(A, "rubber_norm.jpg"),          # ambientCG Rubber004, levels-normalised
           ply=os.path.join(A, "polyhaven", "plywood_diff_1k.jpg"))
ENV = dict(full=os.path.join(A, "env_full.png"), metal=os.path.join(A, "env_metal.png"),
           dark=os.path.join(A, "env_dark.png"), coat=os.path.join(A, "env_coat.png"))

# key: (texture, mapping, tile_mm, diffuse, specular, shininess, env)
LOOK = {
    "cf":      ("cf", "planeXZ", 30.0, (0.95, 0.95, 1.0), (0.55, 0.55, 0.58), 0.75, "coat"),
    "alu":     ("brushed", "cube", None, (0.48, 0.48, 0.51), (0.85, 0.85, 0.9), 0.65, "dark"),
    "steel":   ("metal", "cube", None, (0.22, 0.22, 0.24), (0.55, 0.55, 0.6), 0.6, "dark"),
    "motor":   ("metal", "cube", None, (0.07, 0.07, 0.08), (0.6, 0.6, 0.65), 0.55, "coat"),
    "brass":   ("metal", "cube", None, (0.85, 0.62, 0.25), (0.9, 0.75, 0.4), 0.6, "metal"),
    "pla":     ("plastic", "cube", None, (0.95, 0.40, 0.07), (0.15, 0.13, 0.1), 0.15, None),
    "pad":     ("rubber", "cube", None, (0.55, 0.55, 0.6), (0.08, 0.08, 0.08), 0.05, None),
    "pom":     ("plastic", "cube", None, (0.95, 0.95, 0.92), (0.3, 0.3, 0.3), 0.3, None),
    "pcb":     (None, None, None, (0.05, 0.32, 0.10), (0.45, 0.45, 0.45), 0.6, None),
    "donut":   ("plastic", "cube", None, (0.95, 0.70, 0.08), (0.2, 0.2, 0.18), 0.25, None),
    "red":     ("plastic", "cube", None, (0.85, 0.10, 0.08), (0.45, 0.4, 0.4), 0.55, None),
    "blue":    ("plastic", "cube", None, (0.10, 0.25, 0.85), (0.45, 0.45, 0.5), 0.55, None),
    "field":   ("metal", "cube", None, (0.36, 0.37, 0.39), (0.22, 0.22, 0.22), 0.35, None),
    "wood":    ("ply", "cube", None, (1.0, 1.0, 1.0), (0.08, 0.08, 0.08), 0.1, None),
    "bowden":  (None, None, None, (0.03, 0.03, 0.03), (0.3, 0.3, 0.3), 0.4, None),
    "wire":    (None, None, None, (0.6, 0.05, 0.05), (0.3, 0.3, 0.3), 0.4, None),
}
STATE = {}


def _texgroup(look):
    tex, mapping, tile, *_rest, env = look
    g = coin.SoGroup()
    g.setName("ARC_TEX")
    cx = coin.SoComplexity()
    cx.textureQuality = 1.0
    g.addChild(cx)
    if tex:
        u0 = coin.SoTextureUnit()
        u0.unit = 0
        g.addChild(u0)
        t = coin.SoTexture2()
        t.filename = TEX[tex]
        t.model = coin.SoTexture2.MODULATE
        g.addChild(t)
        if mapping == "planeXZ":
            tc = coin.SoTextureCoordinatePlane()
            tc.directionS = coin.SbVec3f(1.0 / tile, 0, 0)
            tc.directionT = coin.SbVec3f(0, 0, 1.0 / tile)
        else:
            tc = coin.SoTextureCoordinateCube()
        g.addChild(tc)
    if env:
        u1 = coin.SoTextureUnit()
        u1.unit = 1 if tex else 0
        g.addChild(u1)
        e = coin.SoTexture2()
        e.filename = ENV[env]
        e.model = coin.SoTexture2.BLEND
        e.blendColor = coin.SbColor(1, 1, 1)
        g.addChild(e)
        g.addChild(coin.SoTextureCoordinateEnvironment())
        back = coin.SoTextureUnit()
        back.unit = 0
        g.addChild(back)
    return g


def apply_look(obj, key):
    vo = obj.ViewObject
    if not vo or key not in LOOK:
        return
    look = LOOK[key]
    STATE.setdefault("looks", {})[obj.Name] = key
    _t, _m, _tile, dif, spec, shin, _env = look
    try:
        vo.DisplayMode = "Shaded"
    except Exception:
        pass
    try:
        vo.Deviation = 0.15
        vo.AngularDeflection = 12.0
    except Exception:
        pass
    mat = App.Material(DiffuseColor=dif, SpecularColor=spec, AmbientColor=tuple(c * 0.25 for c in dif), Shininess=shin)
    vo.ShapeAppearance = [mat]
    root = vo.RootNode
    for i in reversed(range(root.getNumChildren())):
        if root.getChild(i).getName() == "ARC_TEX":
            root.removeChild(i)
    root.insertChild(_texgroup(look), 0)


def reapply():
    """Re-apply LOOK/TEX after editing them (no need to re-run setup)."""
    doc = STATE["doc"]
    for n, k in STATE.get("looks", {}).items():
        o = doc.getObject(n)
        if o:
            apply_look(o, k)
    lights(STATE["view"])


def lights(view):
    sg = view.getSceneGraph()
    for i in reversed(range(sg.getNumChildren())):
        if sg.getChild(i).getName() == "ARC_LIGHTS":
            sg.removeChild(i)
    g = coin.SoGroup()
    g.setName("ARC_LIGHTS")
    for d, inten, col in (((-0.55, 0.6, -0.6), 1.0, (1.0, 0.97, 0.92)),      # key from front-left-above
                          ((0.7, 0.5, -0.3), 0.55, (0.85, 0.9, 1.0)),       # fill
                          ((0.2, -0.9, -0.4), 0.7, (1.0, 1.0, 1.0)),        # rim from behind
                          ((0.0, 0.0, -1.0), 0.35, (1.0, 1.0, 1.0))):       # top
        l = coin.SoDirectionalLight()
        l.direction = coin.SbVec3f(*d)
        l.intensity = inten
        l.color = coin.SbColor(*col)
        g.addChild(l)
    sg.insertChild(g, 0)
    try:
        view.setHeadlight(True)
    except Exception:
        pass


def setup(scene_doc=r"C:\Users\ryanh\light_weight_arm\cad\ARC_Engineer_Arm.FCStd"):
    for n in list(App.listDocuments()):
        App.closeDocument(n)
    doc = App.openDocument(scene_doc)
    Gui.ActiveDocument = Gui.getDocument(doc.Name)
    view = Gui.ActiveDocument.ActiveView
    data = json.load(open(os.path.join(RENDER, "anim.json")))
    hide = ("Datum_", "BELT_EQUIV", "Belt_equiv", "Bowden_", "Cable_", "Harness", "Joints", "Origin")
    for o in doc.Objects:
        if not o.ViewObject:
            continue
        if o.Name.startswith(hide) or o.TypeId in ("App::Origin", "App::Line", "App::Plane", "Assembly::JointGroup"):
            o.ViewObject.Visibility = False
            continue
        if o.TypeId in ("Part::Feature", "App::Part", "Assembly::AssemblyObject", "App::DocumentObjectGroup"):
            o.ViewObject.Visibility = True
        k = getattr(o, "ColorKey", None)
        if k:
            apply_look(o, k)
    # field items for both clips + held objects (placed per frame in HEAD frame)
    fg = doc.addObject("App::DocumentObjectGroup", "RenderField")
    fld = {}
    for scene in ("DONUT_PICK", "PIPE_GRASP", "PIPE_CHUTE"):
        for n, s, c in F.scene_items(scene):
            if n in fld:
                continue
            o = doc.addObject("Part::Feature", "RF_" + n.replace(".", "_"))
            o.Shape = s
            fg.addObject(o)
            apply_look(o, c)
            fld[n] = o
    for scene, key in (("DONUT_LIFT", "held_donut"), ("PIPE_LIFT", "held_pipe")):
        h = F.held_object(scene)
        o = doc.addObject("Part::Feature", "RF_" + key)
        o.Shape = h[1]
        fg.addObject(o)
        apply_look(o, h[2])
        fld[key] = o
    lights(view)
    view.setAnimationEnabled(False)
    STATE.update(doc=doc, view=view, data=data, field=fld,
                 bodies={o.Name: o for o in doc.Objects if o.TypeId == "App::Part"})
    return doc


FIELD_SETS = {"donut": ("Side_High_Ground_Lower_Tier", "ZigZag_Pole_PLACEHOLDER", "Objective_C_Donut"),
              "pipe": ("Objective_B_Bucket", "Objective_B_Pipe", "Perimeter_Wall", "Pipe_Chute_D52.5")}


def _mat(a):
    m = App.Matrix(*a)
    return App.Placement(m)


def set_frame(rec, clip):
    bodies = STATE["bodies"]
    for b, a in rec["bodies"].items():
        if b in bodies:
            bodies[b].Placement = _mat(a)
    grab = rec.get("grab")
    on = FIELD_SETS[clip] if clip else ()
    for n, o in STATE["field"].items():
        vis = any(n.startswith(k) for k in on)
        if n == "Objective_C_Donut" and grab == "donut":
            vis = False
        if n == "Objective_B_Pipe_Target" and grab == "pipe":
            vis = False
        if n == "held_donut":
            vis = grab == "donut"
            o.Placement = bodies["HEAD"].Placement
        if n == "held_pipe":
            vis = grab == "pipe"
            o.Placement = bodies["HEAD"].Placement
        if clip == "pipe" and n in ("Perimeter_Wall", "Pipe_Chute_D52.5"):
            o.Placement = App.Placement(App.Vector(rec.get("wall", 0.0), 0, 0), App.Rotation())
        o.ViewObject.Visibility = vis


def camera(pos_m, target_m, fov_deg=27.0):
    """Perspective camera at pos (m) looking at target (m); model units are mm."""
    view = STATE["view"]
    view.setCameraType("Perspective")
    cam = view.getCameraNode()
    p = coin.SbVec3f(*[v * 1000 for v in pos_m])
    t = coin.SbVec3f(*[v * 1000 for v in target_m])
    cam.position = p
    cam.pointAt(t, coin.SbVec3f(0, 0, 1))
    try:
        cam.heightAngle = math.radians(fov_deg)
    except Exception:
        pass
    cam.nearDistance = 50
    cam.farDistance = 20000
    cam.focalDistance = (t - p).length()


_BG = {}


def _bg(w, h):
    from PIL import Image
    if (w, h) in _BG:
        return _BG[(w, h)].copy()
    top, bot = (54, 57, 63), (14, 15, 18)
    img = Image.new("RGB", (w, h))
    px = img.load()
    for y in range(h):
        k = (y / (h - 1)) ** 0.8
        c = tuple(int(top[i] + (bot[i] - top[i]) * k) for i in range(3))
        for x in range(w):
            px[x, y] = c
    _BG[(w, h)] = img
    return img.copy()


def grab_image(path, w, h, ss=2):
    from PIL import Image, ImageFilter
    view = STATE["view"]
    tmp = path + ".tmp.png"
    view.saveImage(tmp, w * ss, h * ss, "Transparent")
    im = Image.open(tmp).convert("RGBA").resize((w, h), Image.LANCZOS)
    bg = _bg(w, h).convert("RGBA")
    # contact shadow: blurred silhouette under the alpha, offset down
    a = im.split()[3]
    sh = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    sh.putalpha(a.point(lambda v: int(v * 0.35)).filter(ImageFilter.GaussianBlur(max(4, w // 150))))
    bg.alpha_composite(sh, (int(w * 0.006), int(h * 0.012)))
    bg.alpha_composite(im)
    bg.convert("RGB").save(path)
    os.remove(tmp)


VIEWS = {"hero_donut_lift": ((1.05, -1.0, 1.02), (-0.02, 0.0, 0.52), "donut"),
         "hero_pipe_chute": ((0.55, -1.25, 0.95), (0.08, 0.0, 0.47), "pipe"),
         "hero_stow": ((0.62, -0.78, 0.62), (-0.20, 0.0, 0.28), None),
         "detail_wrist": ((0.30, -0.42, 0.86), (0.02, 0.0, 0.70), "donut"),
         "detail_base": ((0.12, -0.62, 0.42), (-0.22, 0.0, 0.20), None)}


def still(name, w=1920, h=1080):
    data = STATE["data"]
    pos, tgt, clip = VIEWS[name]
    rec_name = {"detail_wrist": "hero_donut_lift", "detail_base": "hero_stow"}.get(name, name)
    rec = data["stills"][rec_name]
    set_frame(rec, clip)
    camera(pos, tgt)
    Gui.updateGui()
    path = os.path.join(OUT, name + ".png")
    grab_image(path, w, h)
    return path


def frames(start, end, w=1280, h=720):
    data = STATE["data"]
    seq = [("donut", r) for r in data["clips"]["donut"]] + [("pipe", r) for r in data["clips"]["pipe"]]
    n_d = len(data["clips"]["donut"])
    for i in range(start, min(end, len(seq))):
        clip, rec = seq[i]
        set_frame(rec, clip)
        j = i if clip == "donut" else i - n_d
        L = n_d if clip == "donut" else len(seq) - n_d
        a0, a1, zc = (-48, -8, 1.05) if clip == "donut" else (-112, -72, 1.25)
        a = math.radians(a0 + (a1 - a0) * j / max(1, L - 1))
        r = 1.9
        camera((r * math.cos(a) + 0.05, r * math.sin(a), zc + 0.12 * math.sin(math.pi * j / L)), (0.08, 0.0, 0.52))
        Gui.updateGui()
        grab_image(os.path.join(OUT, "frames", "f_%04d.png" % i), w, h)
    return len(seq)
