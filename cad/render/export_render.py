# -*- coding: utf-8 -*-
"""
Export the arm for rendering (headless FreeCAD):
    freecadcmd cad/render/export_render.py
Writes cad/render/meshes/<BODY>__<material>.obj (body-local frame, mm),
field meshes, and cad/render/anim.json: per-frame body matrices for the
donut and pipe clips plus the hero-still poses, all from arm_model's own
kinematics (the same transforms the mated assembly solves to).
"""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad\render"
CAD = os.path.dirname(HERE)
sys.path.insert(0, CAD)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import MeshPart         # noqa: E402
import params   # noqa: E402
params.use_release_variant('export_render.py')   # writes the released package
import arm_model as M   # noqa: E402
import field as F       # noqa: E402

OUT = os.path.join(HERE, "meshes")
os.makedirs(OUT, exist_ok=True)
FPS = 24


def write_mesh(shape, path, lin=0.08, ang=0.35):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=ang, Relative=False)
    m.write(path)
    return m.CountFacets


def mat4(pl):
    m = pl.toMatrix()
    return [m.A11, m.A12, m.A13, m.A14, m.A21, m.A22, m.A23, m.A24,
            m.A31, m.A32, m.A33, m.A34, m.A41, m.A42, m.A43, m.A44]


def main():
    bodies = M.build_bodies()
    files = []
    for bname, parts in bodies.items():
        groups = {}
        for p in parts:
            if "rotor" in p.name and False:
                continue
            if p.vis.isNull() or not p.vis.Faces:
                print("skip empty", p.name)
                continue
            s = p.vis.copy()
            groups.setdefault(p.color, []).append(s)
        for col, shapes in groups.items():
            comp = Part.makeCompound(shapes)
            fn = "%s__%s.obj" % (bname, col)
            n = write_mesh(comp, os.path.join(OUT, fn), lin=0.05 if col in ("steel", "brass") else 0.08)
            files.append(dict(body=bname, material=col, file=fn, facets=n))
            print("mesh", fn, n)
    # field / objectives (world frame) and held objects (HEAD frame)
    fld = {}
    for scene in ("DONUT_PICK", "PIPE_GRASP", "PIPE_CHUTE"):
        for n_, s_, c_ in F.scene_items(scene):
            if n_ in fld:
                continue
            fn = "FIELD__%s.obj" % n_
            fine = "Pole" in n_ or "Donut" in n_            # curved tubes: fine tessellation
            write_mesh(s_, os.path.join(OUT, fn), lin=0.08 if fine else 0.3, ang=0.15 if fine else 0.5)
            fld[n_] = dict(file=fn, material=c_)
    for scene, key in (("DONUT_LIFT", "held_donut"), ("PIPE_LIFT", "held_pipe")):
        h = F.held_object(scene)
        fn = "HELD__%s.obj" % key
        write_mesh(h[1], os.path.join(OUT, fn), lin=0.2)
        fld[key] = dict(file=fn, material=h[2])

    # ---- animation.  Each key: (pose or ("tcp", z, chassis_y), duration s, opts).  Joint-space eased
    # interpolation between keys; the donut lift is a Cartesian path along the pole with the chassis
    # strafing (robot moves, field stays put); the chute insertion is a chassis drive towards the wall.
    def pose(name, **kw):
        q, jaw = M.pose_q(name)
        q = list(q)
        if "roll" in kw:
            q[3] = kw["roll"]
        return dict(q=q, jaw=kw.get("jaw", jaw), base=list(kw.get("base", (0.0, 0.0))))

    lift = F.donut_lift_path(n=48)
    donut = [("STOW", 0.0, {}), ("DONUT_APPROACH", 1.6, {"jaw": 112.0}), ("DONUT_PICK", 1.2, {"jaw": 112.0}),
             ("DONUT_PICK", 0.6, {"jaw": 100.0, "grab": "donut"})]
    seg = 4.4 / len(lift)
    for (z, yc, rl) in lift[1:]:
        donut.append((("tcp", z), seg, {"jaw": 100.0, "grab": "donut", "base": (0.0, yc), "roll": rl, "linear": True}))
    donut += [("DONUT_LIFT", 0.4, {"grab": "donut"}),
              ("DONUT_LIFT", 0.9, {"roll": 25.0, "grab": "donut"}), ("DONUT_LIFT", 0.9, {"roll": -25.0, "grab": "donut"}),
              ("DONUT_LIFT", 0.6, {"roll": 0.0, "grab": "donut"}), ("DONUT_LIFT", 0.5, {"grab": "donut"})]
    DX, DY = -350.0, 500.0                       # start: bucket in front of the bumper, chute 500 mm to the right
    pj = M.PIPE_JAW
    S0 = (DX, DY)
    pipe = [("STOW", 0.0, {"base": S0}), ("PIPE_APPROACH", 1.6, {"jaw": 50.0, "base": S0}),
            ("PIPE_GRASP", 1.0, {"jaw": 50.0, "base": S0}),
            ("PIPE_GRASP", 0.6, {"jaw": pj, "grab": "pipe", "base": S0}),
            ("PIPE_LIFT", 1.8, {"grab": "pipe", "base": S0}),
            ("PIPE_LIFT", 2.0, {"grab": "pipe", "base": (DX, 0.0)}),          # strafe across to line up
            ("PIPE_CHUTE", 1.6, {"grab": "pipe", "base": (DX, 0.0)}),         # pipe horizontal, 50 mm off the wall
            ("PIPE_CHUTE", 2.0, {"grab": "pipe", "base": (0.0, 0.0)}),        # drive in: 300 mm into the chute
            ("PIPE_CHUTE", 1.0, {"roll": 90.0, "grab": "pipe"}),
            ("PIPE_CHUTE", 0.8, {"roll": 0.0, "grab": "pipe"}), ("PIPE_CHUTE", 0.5, {"grab": "pipe"})]

    def resolve(key, kw):
        if isinstance(key, tuple):
            th1, th2 = M.ik(F.POLE_X, key[1], 0.0)
            return dict(q=[th1, th2, 0.0, kw.get("roll", 0.0)], jaw=kw.get("jaw", 100.0), base=list(kw.get("base", (0.0, 0.0))))
        return pose(key, **{k: v for k, v in kw.items() if k in ("roll", "jaw", "base")})

    def clip(keys, name):
        frames = []
        prev = None
        acc = 0.0
        for (key, dur, kw) in keys:
            cur = resolve(key, kw)
            grab = kw.get("grab")
            if prev is None:
                prev = cur
            acc += dur * FPS
            n = max(1, int(round(acc)))
            acc -= n
            for i in range(1 if frames else 0, n + 1):
                t = i / n
                e = t if kw.get("linear") else 0.5 - 0.5 * math.cos(math.pi * t)
                q = [a + (b - a) * e for a, b in zip(prev["q"], cur["q"])]
                jaw = prev["jaw"] + (cur["jaw"] - prev["jaw"]) * e
                base = [a + (b - a) * e for a, b in zip(prev["base"], cur["base"])]
                plc = M.placements(*q, jaw=jaw)
                frames.append(dict(bodies={k: mat4(v) for k, v in plc.items()}, grab=grab, base=base))
            prev = cur
        print("clip", name, len(frames), "frames")
        return frames

    stills = {}
    for nm, sc, kw in (("hero_donut_lift", "DONUT_LIFT", {"roll": 15.0}), ("hero_pipe_chute", "PIPE_CHUTE", {}),
                       ("hero_stow", "STOW", {}), ("detail_gripper_pipe", "PIPE_GRASP", {}),
                       ("detail_gripper_donut", "DONUT_PICK", {}),
                       # close-ups / review views (no field items, robot at the origin)
                       ("overview_side", "DONUT_APPROACH", {}), ("overview_rear", "DONUT_APPROACH", {}),
                       ("detail_shoulder", "DONUT_APPROACH", {}), ("detail_elbow", "DONUT_APPROACH", {}),
                       ("detail_wrist_roll", "DONUT_APPROACH", {"roll": 20.0}),
                       ("detail_jaw_drive", "DONUT_APPROACH", {"jaw": 60.0})):
        p_ = pose(sc, **kw)
        stills[nm] = dict(bodies={k: mat4(v) for k, v in M.placements(*p_["q"], jaw=p_["jaw"]).items()},
                          grab="donut" if "donut" in nm else ("pipe" if "pipe" in nm else None), scene=sc,
                          base=[DX, DY] if sc in ("PIPE_GRASP", "PIPE_LIFT") else [0.0, 0.0])
    data = dict(fps=FPS, files=files, field=fld, clips=dict(donut=clip(donut, "donut"), pipe=clip(pipe, "pipe")),
                stills=stills,
                # field items placed relative to the robot's start for the pipe clip (bucket stays with the start spot)
                field_offset=dict(pipe={k: [DX, DY, 0.0] for k in fld if k.startswith("Objective_B_")}))
    with open(os.path.join(HERE, "anim.json"), "w") as f:
        json.dump(data, f)
    print("anim.json written")


main()
