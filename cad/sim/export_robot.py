# -*- coding: utf-8 -*-
"""
Export the arm as a simulation robot description, step 1 of 2 (headless FreeCAD):
    set GRIP=FOURBAR & freecadcmd cad/sim/export_robot.py
-> <repo>/sim/arc_arm_<variant>/meshes/{visual,collision}/*.stl, robot_spec.json, fk_reference.json
Step 2 (plain Python with mujoco/yourdfpy, cad/sim/build_robot.py) writes the URDF and MJCF and validates them.

Kinematic tree (every passive joint follows exactly ONE actuated joint, so the same tree is a URDF with <mimic>
and an MJCF with joint-equality constraints).  Joint values equal arm_model's own angles:
    shoulder    base -> upper        th1 (J1, STS3215 via 3:1 spur stage)
    rod1        base -> rod1         = shoulder            (level-keeping stage-1 rod, parallel to the upper arm)
    rocker      rod1 -> rocker       = -shoulder           (rocker keeps a constant absolute angle)
    elbow       rocker -> forearm    th2 (J2, STS3215 via 3:1 spur stage; absolute because the rocker never rotates)
    crank       base -> crank        = elbow               (J2 crank, built rotated 180 deg)
    crank_pin   crank -> crank_pin   = -elbow              (massless: absolute angle 0 at crank pin A)
    rod_ab      crank_pin -> rod_ab  = shoulder            (forearm drive rod, parallel to the upper arm)
    level       forearm -> level     = -elbow              (GT2 1:1 belt keeps the level member level)
    wrist_pitch level -> gripper     pitch (J3, STS3215)
    wrist_roll  gripper -> head      roll (J4, STS3215)
    gripper     head -> lk_ld        d = theta - theta_ref (STS3215; 0 at the pipe grip)
    jaw_l       lk_ld -> jaw_l       = -gripper            (parallelogram: jaw stays parallel)
    lk_li       head -> lk_li        = gripper
    lk_rd       head -> lk_rd        = -gripper            (sector gears 1:1)
    lk_ri       head -> lk_ri        = -gripper
    jaw_r       lk_rd -> jaw_r       = gripper
Link frames sit on their joint, axes aligned with the CAD body frame at joint value 0; meshes are in the CAD body
frame (mm) and placed with a constant visual offset.  Masses and inertias come from the CAD parts (density per
material, catalogue masses for purchased parts).
"""
import json
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import FreeCAD as App  # noqa: E402
import MeshPart        # noqa: E402
import Part            # noqa: E402
import arm_model as M  # noqa: E402

V = App.Vector
VAR = M.GRIP.lower()
ROOT = os.path.join(os.path.dirname(CAD), "sim", "arc_arm_%s" % VAR)
MESH = os.path.join(ROOT, "meshes")
FASTENER_KINDS = {"BHCS", "SHCS", "CSK", "INSERT", "SETSCREW", "ECLIP", "DOWEL", "WASHER-D4", "NYLOC", "SHOULDER",
                  "PCLIP", "CLIP", "SHIM"}
RGBA = {"cf": (0.12, 0.12, 0.13, 1), "pla": (0.90, 0.32, 0.06, 1), "alu": (0.80, 0.81, 0.84, 1), "steel": (0.30, 0.31, 0.33, 1),
        "motor": (0.08, 0.08, 0.09, 1), "pad": (0.12, 0.35, 0.85, 1), "brass": (0.85, 0.65, 0.30, 1), "pcb": (0.05, 0.30, 0.10, 1),
        "pom": (0.92, 0.91, 0.86, 1), "field": (0.4, 0.4, 0.4, 1)}


def tree():
    K, Y = M.K, M.Y
    S = (K["SX"], 0.0, K["SZ"])
    v1 = M.u(K["V1_ANG"], K["V1_LEN"])
    v2 = M.u(K["V2_ANG"], K["V2_LEN"])
    G1 = (S[0] + v1[0], 0.0, S[2] + v1[1])
    gd, gi, cd, ci = M.fb_pivots(1)
    gr, gri, cr, cri = M.fb_pivots(-1)
    rz = M.ROLL_Z
    Ym = (0, -1, 0)
    Z = (0, 0, 1)
    # name, CAD body, parent, joint, axis, origin xyz in parent link frame (mm), origin rot about y (deg),
    # F = link-frame origin in the CAD body frame (mm), mimic (leader, multiplier) or None
    # passive joints are named <link>_joint: SDF (Gazebo) puts links and joints in one frame namespace
    return [
        ("base_link", "GROUND", None, None, None, (0, 0, 0), 0, (0, 0, 0), None),
        ("upper", "UPPER", "base_link", "shoulder", Ym, S, 0, (0, 0, 0), None),
        ("rod1", "ROD1", "base_link", "rod1_joint", Ym, G1, 0, (0, 0, 0), ("shoulder", 1.0)),
        ("rocker", "ROCKER", "rod1", "rocker_joint", Ym, (K["L2"], 0, 0), 0, (v1[0], 0, v1[1]), ("shoulder", -1.0)),
        ("forearm", "FOREARM", "rocker", "elbow", Ym, (-v1[0], 0, -v1[1]), 0, (0, 0, 0), None),
        ("crank", "CRANK", "base_link", "crank_joint", Ym, S, 180, (0, 0, 0), ("elbow", 1.0)),
        ("crank_pin", None, "crank", "crank_pin_joint", Ym, (K["L1"], 0, 0), -180, (0, 0, 0), ("elbow", -1.0)),
        ("rod_ab", "ROD_AB", "crank_pin", "rod_ab_joint", Ym, (0, 0, 0), 0, (0, 0, 0), ("shoulder", 1.0)),
        ("level", "LEVEL", "forearm", "level_joint", Ym, (K["L3"], 0, 0), 0, (0, 0, 0), ("elbow", -1.0)),
        # level-keeping stage 2 (replaced the belt): rod 2 hangs off the rocker at its lever pin E+v2 and stays
        # parallel to the forearm (rocker absolute angle is constant, so its joint angle = th2 = elbow)
        ("rod2", "ROD2", "rocker", "rod2_joint", Ym, (v2[0] - v1[0], 0, v2[1] - v1[1]), 0, (0, 0, 0), ("elbow", 1.0)),
        ("gripper_frame", "GRIPPER", "level", "wrist_pitch", Ym, (0, 0, 0), 0, (0, 0, 0), None),
        ("head", "HEAD", "gripper_frame", "wrist_roll", (1, 0, 0), (0, 0, rz), 0, (0, 0, rz), None),
        ("lk_ld", "LK_LD", "head", "gripper", Z, (gd[0], gd[1], -rz), 0, (gd[0], gd[1], 0), None),
        ("jaw_l", "JAW_L", "lk_ld", "jaw_l_joint", Z, (cd[0] - gd[0], cd[1] - gd[1], 0), 0, (cd[0], cd[1], 0), ("gripper", -1.0)),
        ("lk_li", "LK_LI", "head", "lk_li_joint", Z, (gi[0], gi[1], -rz), 0, (gi[0], gi[1], 0), ("gripper", 1.0)),
        ("lk_rd", "LK_RD", "head", "lk_rd_joint", Z, (gr[0], gr[1], -rz), 0, (gr[0], gr[1], 0), ("gripper", -1.0)),
        ("lk_ri", "LK_RI", "head", "lk_ri_joint", Z, (gri[0], gri[1], -rz), 0, (gri[0], gri[1], 0), ("gripper", -1.0)),
        ("jaw_r", "JAW_R", "lk_rd", "jaw_r_joint", Z, (cr[0] - gr[0], cr[1] - gr[1], 0), 0, (cr[0], cr[1], 0), ("gripper", 1.0)),
    ]


def solids(shape):
    try:
        ss = list(shape.Solids)
    except Exception:
        ss = []
    return [s for s in ss if s.isValid() and s.Volume > 1e-6]


def mass_props(parts):
    """-> mass kg, com (mm, CAD body frame), inertia about com (kg*mm^2, 3x3)."""
    items = []
    for p in parts:
        m = M.part_mass_g(p) / 1000.0
        if m <= 0:
            continue
        ss = solids(p.chk) or solids(p.vis)
        vol = sum(s.Volume for s in ss)
        if vol <= 0:
            c = p.chk.BoundBox.Center if not p.chk.isNull() else p.vis.BoundBox.Center
            items.append((m, c, [[0.0] * 3 for _ in range(3)]))
            continue
        rho = m / vol
        for s in ss:
            ms = rho * s.Volume
            I = s.MatrixOfInertia               # unit density, about the solid's centre of mass
            Im = [[I.A11 * rho, I.A12 * rho, I.A13 * rho], [I.A21 * rho, I.A22 * rho, I.A23 * rho], [I.A31 * rho, I.A32 * rho, I.A33 * rho]]
            items.append((ms, s.CenterOfMass, Im))
    mt = sum(i[0] for i in items)
    if mt <= 0:
        return 0.0, V(0, 0, 0), [[0.0] * 3 for _ in range(3)]
    com = V(0, 0, 0)
    for m, c, _I in items:
        com = com + c * (m / mt)
    It = [[0.0] * 3 for _ in range(3)]
    for m, c, I in items:
        r = c - com
        rr = [r.x, r.y, r.z]
        d2 = r.Length ** 2
        for a in range(3):
            for b in range(3):
                It[a][b] += I[a][b] + m * ((d2 if a == b else 0.0) - rr[a] * rr[b])
    return mt, com, It


def write_mesh(shape, path, lin):
    m = MeshPart.meshFromShape(Shape=shape, LinearDeflection=lin, AngularDeflection=0.4, Relative=False)
    m.write(path)
    return m.CountFacets


def plc_matrix(p):
    m = p.toMatrix()
    return [[m.A11, m.A12, m.A13, m.A14], [m.A21, m.A22, m.A23, m.A24], [m.A31, m.A32, m.A33, m.A34]]


def main():
    import Part
    bodies = M.build_bodies()
    for d in ("visual", "collision"):
        os.makedirs(os.path.join(MESH, d), exist_ok=True)
    links = []
    for (name, body, parent, joint, axis, xyz, ry, F, mimic) in tree():
        L = dict(name=name, cad_body=body, parent=parent, joint=joint, axis=axis, origin_xyz_mm=list(xyz), origin_rot_y_deg=ry,
                 frame_in_cad_mm=list(F), mimic=mimic, visuals=[], collisions=[])
        if body is None:
            L.update(mass_kg=0.0, com_mm=[0, 0, 0], inertia_kgmm2=[[0] * 3] * 3)
            links.append(L)
            continue
        parts = bodies[body]
        m, com, I = mass_props(parts)
        L.update(mass_kg=m, com_mm=[com.x, com.y, com.z], inertia_kgmm2=I)
        groups = {}
        for p in parts:
            if not p.vis.isNull() and p.vis.Faces:
                groups.setdefault(p.color, []).append(p.vis)
        for col, shapes in sorted(groups.items()):
            fn = "%s__%s.stl" % (name, col)
            # vendor motor STEPs are very fine (15 MB at 0.15 mm): a coarser tolerance keeps simulators fast
            n = write_mesh(Part.makeCompound(shapes), os.path.join(MESH, "visual", fn), 0.8 if col == "motor" else 0.15)
            L["visuals"].append(dict(file="meshes/visual/" + fn, rgba=list(RGBA.get(col, (0.5, 0.5, 0.5, 1))), facets=n))
        for p in parts:
            if p.kind == "CAT" and (p.src in FASTENER_KINDS or p.src.startswith(("PIN-", "HORN", "GEAR-", "COLLAR", "NUT-"))):
                continue
            if M.part_mass_g(p) < 3.0 or p.chk.isNull() or not getattr(p, "check", True):
                continue
            # simulators collide each mesh as its CONVEX HULL. A strongly concave part gets split into pieces whose
            # hulls stay inside it: the four-bar jaw block steps back above the top finger (the pole keep-out at
            # XMAX), and one hull over the whole block filled that step and grazed the pole during the donut lift
            pieces = [p.chk]
            if p.name.startswith("Jaw_Block_") and hasattr(M, "FB"):
                zc_ = M.FB["ZFT"][1]
                pieces = [p.chk.common(Part.makeBox(1000, 1000, 500, App.Vector(-500, -500, zc_ - 500))),
                          p.chk.common(Part.makeBox(1000, 1000, 500, App.Vector(-500, -500, zc_)))]
                pieces = [s for s in pieces if not s.isNull() and s.Volume > 1.0]
            for k, sh in enumerate(pieces):
                fn = "%s__%s%s.stl" % (name, p.name, "" if len(pieces) == 1 else "_%d" % k)
                n = write_mesh(sh, os.path.join(MESH, "collision", fn), 0.5)
                L["collisions"].append(dict(file="meshes/collision/" + fn, part=p.name, facets=n))
        links.append(L)
        print("link %-14s %-8s %6.3f kg  %d visual, %d collision meshes" % (name, body, m, len(L["visuals"]), len(L["collisions"])))
    th_ref = M.FB_TREF
    _g = M.BASE_R["ratio"] * M.BASE_R["efficiency"]                 # J1/J2 spur stage
    _BS, _BR = M.STS_R["stall_Nm"] * _g, M.STS_R["rated_Nm"] * _g
    actuators = dict(
        shoulder=dict(source="STS3215 + 3:1 spur stage (J1)", peak_Nm=round(_BS, 2), rated_Nm=round(_BR, 2)),
        elbow=dict(source="STS3215 + 3:1 spur stage (J2, via crank + rod AB)", peak_Nm=round(_BS, 2), rated_Nm=round(_BR, 2)),
        wrist_pitch=dict(source="STS3215 (J3)", peak_Nm=M.STS_R["stall_Nm"], rated_Nm=M.STS_R["rated_Nm"]),
        wrist_roll=dict(source="STS3215 (J4)", peak_Nm=M.STS_R["stall_Nm"], rated_Nm=M.STS_R["rated_Nm"]),
        gripper=dict(source="STS3215 12 V (four-bar drive)", peak_Nm=M.SERVO["stall_Nm"], rated_Nm=M.SERVO["rated_Nm"]))
    limits = dict(shoulder=(0.0, 180.0), elbow=(-86.0, 51.0), wrist_pitch=(-30.0, 120.0), wrist_roll=(-95.0, 95.0),
                  gripper=(0.0, M.fb_theta(112.0) - th_ref))
    spring = dict(joint="gripper", k_Nm_per_rad=M.SPRING["rate_Nm_per_deg"] * 180 / math.pi,
                  free_angle_deg=(M.fb_theta(112.0) - th_ref) + M.SPRING["preload_deg"], part=M.SPRING["pn"])
    spec = dict(variant=M.GRIP, units="CAD mm / deg (generator converts to m / rad)", links=links, actuators=actuators,
                limits_deg=limits, spring=spring, theta_ref_deg=th_ref, tcp_in_gripper_frame_mm=[M.K["GRIP"], 0, -M.K["DROP"]],
                jaw_of_gripper_deg="jaw = 2*(YG + L*sin(theta_ref + d) - E)",
                fb=dict(YG=M.FB["YG"], L=M.FB["L"], E=M.FB["E"]))
    json.dump(spec, open(os.path.join(ROOT, "robot_spec.json"), "w"), indent=1)
    # forward-kinematics reference: CAD body placements at task poses, with the joint values that produce them
    ref = []
    for pose in ("STOW", "DONUT_APPROACH", "DONUT_LIFT", "DONUT_LIFT_ROLL+", "PIPE_GRASP", "PIPE_CHUTE", "PIPE_CHUTE_ROLL90"):
        q, jaw = M.pose_q(pose)
        th1, th2, pitch, roll = q
        d = M.fb_theta(jaw) - th_ref
        plc = M.placements(th1, th2, pitch, roll, jaw=jaw)
        ref.append(dict(pose=pose, jaw_mm=jaw, joints_deg=dict(shoulder=th1, elbow=th2, wrist_pitch=pitch, wrist_roll=roll, gripper=d),
                        bodies={k: plc_matrix(v) for k, v in plc.items()},
                        tcp_mm=list(plc["HEAD"].multVec(V(M.K["GRIP"], 0, -M.K["DROP"])))))
    json.dump(ref, open(os.path.join(ROOT, "fk_reference.json"), "w"), indent=1)
    write_task_poses()
    write_task_field()
    print("EXPORT %s: %d links, total %.3f kg -> %s" % (M.GRIP, len(links), sum(l["mass_kg"] for l in links), ROOT))


def write_task_poses():
    """task_poses.json: joint targets (deg, simulator joint convention) for every CAD task pose (arm.kinematics.POSES)
    and the task SEQUENCES - what a controller or demo driver commands."""
    th_ref = M.FB_TREF
    poses = {}
    for pose in M.POSES:
        q, jaw = M.pose_q(pose)
        th1, th2, pitch, roll = q
        tcp = M.POSES[pose].get("tcp")
        poses[pose] = dict(jaw_mm=jaw, tcp_mm=list(tcp) if tcp else None,   # (x, z, pitch) in the robot frame
                           joints_deg=dict(shoulder=th1, elbow=th2, wrist_pitch=pitch, wrist_roll=roll,
                                           gripper=M.fb_theta(jaw) - th_ref))
    json.dump(dict(units="deg; jaw_mm = pad gap at the TCP", poses=poses, sequences=M.SEQUENCES),
              open(os.path.join(ROOT, "task_poses.json"), "w"), indent=1)
    print("task poses: %d poses, sequences %s" % (len(poses), list(M.SEQUENCES)))


def write_task_field():
    """task_field.json: the per-station field items (cad/field.py scene_items, as primitives) and the CAD donut-lift
    path with arm joints, for the MuJoCo task simulation (cad/sim/build_tasks.py). mm / deg, robot frame at each
    station (X forward from the bumper, Z up from the floor)."""
    import field as Fd
    th_ref = M.FB_TREF
    lift = []
    for z_u, cy, roll in Fd.donut_lift_path():
        th1, th2 = M.ik(Fd.POLE_X, z_u, 0.0)
        lift.append(dict(tcp_z=z_u, chassis_y=cy, roll_deg=roll,
                         joints_deg=dict(shoulder=th1, elbow=th2, wrist_pitch=0.0, wrist_roll=roll,
                                         gripper=M.fb_theta(100.0) - th_ref)))
    face = 150 + 453 - 300                                     # as field.scene_items(): pipe 300 mm into the chute
    cx = 110.0                                                 # bucket centre, rim 10 mm off the bumper
    lean = []
    for ang in (-100, -60, -20, 20, 60, 100):
        a = math.radians(ang)
        lean.append(dict(p=[cx + 62 * math.cos(a), 62 * math.sin(a), 2.0],
                         d=[0.12 * math.cos(a), 0.12 * math.sin(a), 1.0]))
    out = dict(
        units="mm, deg; robot frame at each station",
        source="cad/field.py (scene_items, zigzag_pole, donut_lift_path); arm.kinematics.ik",
        donut=dict(R=Fd.DONUT_R, r=Fd.DONUT_r, start=[Fd.POLE_X, 0.0, Fd.POLE_Z0 + 6.0 + Fd.DONUT_r], mass_g=300.0),
        pipe=dict(r=Fd.PIPE_R, ri=Fd.PIPE_RI, L=500.0, mass_g=165.0),
        stations=dict(
            pick=dict(boxes=[dict(name="lower_tier", lo=[30, -500, 0], hi=[1030, 500, Fd.POLE_Z0]),
                             dict(name="pole_base", lo=[Fd.POLE_X - 125, -125, Fd.POLE_Z0], hi=[Fd.POLE_X + 125, 125, Fd.POLE_Z0 + 6])],
                      pole=dict(r=12.0, centreline=[[Fd.POLE_X, Fd.pole_lat(h), Fd.POLE_Z0 + 6 + h]
                                                    for h in (Fd.POLE_H * i / 60 for i in range(61))])),
            place=dict(boxes=[dict(name="scoring_platform", lo=[60.8, -150, 0], hi=[360.8, 150, 50])]),
            bucket=dict(bucket=dict(c=[cx, 0.0], R=100.0, wall=2.0, h=250.0), target_pipe=dict(p=[40.0, 0.0, 2.0], d=[0, 0, 1]),
                        leaning_pipes=lean),
            chute=dict(boxes=[dict(name="perimeter_wall", lo=[face, -600, 0], hi=[face + 40, 600, 500])],
                       chute=dict(lo=[face, -100, 500], hi=[face + 60, 100, 700], hole_r=26.25, hole_z=600.0, insert_mm=300.0))),
        donut_lift=lift)
    json.dump(out, open(os.path.join(ROOT, "task_field.json"), "w"), indent=1)
    print("task field: %d lift samples, stations %s" % (len(lift), list(out["stations"])))


if os.environ.get("EXPORT_ONLY") == "poses":   # just task_poses.json + task_field.json (no meshes / mass properties)
    write_task_poses()
    write_task_field()
else:
    main()
