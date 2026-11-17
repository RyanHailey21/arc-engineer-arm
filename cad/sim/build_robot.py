# -*- coding: utf-8 -*-
"""
Robot description, step 2 of 2: write URDF (Gazebo / ROS) and MJCF (MuJoCo) from the CAD export, then validate.
    C:\\Users\\ryanh\\tools\\simenv\\Scripts\\python.exe cad/sim/build_robot.py [variant]      (default fourbar)
Needs: mujoco, yourdfpy, trimesh, numpy (the simenv venv).  Step 1 is cad/sim/export_robot.py (FreeCAD).

Writes into <repo>/sim/arc_arm_<variant>/:
    arc_arm.urdf    tree with <mimic> passive joints (actuated: shoulder, elbow, wrist_pitch, wrist_roll, gripper)
    arc_arm.xml     MJCF: same tree, passive joints as joint-equality constraints, position actuators with the real
                    torque limits, the gripper's opening torsion spring as a joint spring, task-pose keyframes
    scene.xml       MJCF scene: floor, lower tier, donut and pipe (free bodies) + the arm
    validation.json / validation.md
Validation:
    1. URDF loads (yourdfpy) and its forward kinematics reproduce arm_model.placements() at 7 task poses
    2. MJCF compiles and its forward kinematics reproduce the same placements; equality residuals ~ 0
    3. MuJoCo dynamics: hold STOW under gravity for 3 s (tracking error, constraint drift, no NaN)
    4. Power-off release: gripper actuator off at the pipe grip -> the spring opens the jaws (time to 90 % open)
    5. The URDF also compiles in MuJoCo's URDF importer (structure / mesh check; MuJoCo ignores <mimic>)
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
VAR = (sys.argv[1] if len(sys.argv) > 1 else "fourbar").lower()
ROOT = os.path.join(REPO, "sim", "arc_arm_%s" % VAR)
SPEC = json.load(open(os.path.join(ROOT, "robot_spec.json")))
REF = json.load(open(os.path.join(ROOT, "fk_reference.json")))
MM = 0.001
ACT = ["shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper"]
VEL = dict(shoulder=4.0, elbow=4.0, wrist_pitch=8.0, wrist_roll=8.0, gripper=4.7)       # rad/s (datasheet-class estimates)
KP = dict(shoulder=800.0, elbow=800.0, wrist_pitch=60.0, wrist_roll=30.0, gripper=50.0)   # N*m/rad: stiff position servos
ARMATURE = dict(shoulder=0.016, elbow=0.016, wrist_pitch=0.002, wrist_roll=0.002, gripper=0.002)   # kg*m^2 (rotor x ratio^2, estimates)
LINKS = SPEC["links"]
BY = {l["name"]: l for l in LINKS}


def f(v, n=6):
    return " ".join(("%.*f" % (n, x)).rstrip("0").rstrip(".") if abs(x) > 1e-12 else "0" for x in v)


def link_com(l):
    return [(c - F) * MM for c, F in zip(l["com_mm"], l["frame_in_cad_mm"])]


def inertia_m(l):
    return np.array(l["inertia_kgmm2"], float) * 1e-6


def mimic_value(joint, q):
    """Joint value (rad) of any joint from the actuated values q (rad)."""
    if joint in q:
        return q[joint]
    l = next(x for x in LINKS if x["joint"] == joint)
    leader, mult = l["mimic"]
    return mult * mimic_value(leader, q)


# ------------------------------------------------------------------ URDF
def build_urdf():
    r = ET.Element("robot", name="arc_arm_%s" % VAR)
    ET.SubElement(r, "link", name="world")
    j = ET.SubElement(r, "joint", name="world_to_base", type="fixed")
    ET.SubElement(j, "parent", link="world")
    ET.SubElement(j, "child", link="base_link")
    mats = {}
    for l in LINKS:
        L = ET.SubElement(r, "link", name=l["name"])
        m = max(l["mass_kg"], 1e-4)
        I = inertia_m(l) if l["mass_kg"] > 0 else np.eye(3) * 1e-8
        ine = ET.SubElement(L, "inertial")
        ET.SubElement(ine, "origin", xyz=f(link_com(l)), rpy="0 0 0")
        ET.SubElement(ine, "mass", value="%.6f" % m)
        ET.SubElement(ine, "inertia", ixx="%.4e" % I[0, 0], ixy="%.4e" % I[0, 1], ixz="%.4e" % I[0, 2],
                      iyy="%.4e" % I[1, 1], iyz="%.4e" % I[1, 2], izz="%.4e" % I[2, 2])
        off = f([-x * MM for x in l["frame_in_cad_mm"]])
        for v in l["visuals"]:
            vi = ET.SubElement(L, "visual")
            ET.SubElement(vi, "origin", xyz=off, rpy="0 0 0")
            g = ET.SubElement(vi, "geometry")
            ET.SubElement(g, "mesh", filename=v["file"], scale="0.001 0.001 0.001")
            key = tuple(v["rgba"])
            mn = mats.setdefault(key, "mat%d" % len(mats))
            mt = ET.SubElement(vi, "material", name=mn)
            ET.SubElement(mt, "color", rgba=f(v["rgba"], 3))
        for c in l["collisions"]:
            co = ET.SubElement(L, "collision")
            ET.SubElement(co, "origin", xyz=off, rpy="0 0 0")
            g = ET.SubElement(co, "geometry")
            ET.SubElement(g, "mesh", filename=c["file"], scale="0.001 0.001 0.001")
        if l["parent"] is None:
            continue
        act = l["joint"] in ACT
        J = ET.SubElement(r, "joint", name=l["joint"], type="revolute" if act else "continuous")
        ET.SubElement(J, "parent", link=l["parent"])
        ET.SubElement(J, "child", link=l["name"])
        ET.SubElement(J, "origin", xyz=f([x * MM for x in l["origin_xyz_mm"]]), rpy="0 %s 0" % f([-math.radians(l["origin_rot_y_deg"])]))
        ET.SubElement(J, "axis", xyz=f(l["axis"]))
        if act:
            lo, hi = SPEC["limits_deg"][l["joint"]]
            ET.SubElement(J, "limit", lower="%.5f" % math.radians(lo), upper="%.5f" % math.radians(hi),
                          effort="%.3f" % SPEC["actuators"][l["joint"]]["peak_Nm"], velocity="%.2f" % VEL[l["joint"]])
            ET.SubElement(J, "dynamics", damping="0.05", friction="0.0")
        else:
            ET.SubElement(J, "mimic", joint=l["mimic"][0], multiplier="%g" % l["mimic"][1], offset="0")
    sp = SPEC["spring"]
    r.append(ET.Comment(" gripper opening spring (%s): %.4f N*m/rad, free at %.1f deg of the gripper joint - model it with a "
                        "joint spring/stiffness in your simulator (Gazebo: <spring_stiffness>/<spring_reference> on the SDF joint) "
                        % (sp["part"], sp["k_Nm_per_rad"], sp["free_angle_deg"])))
    ET.indent(r)
    p = os.path.join(ROOT, "arc_arm.urdf")
    ET.ElementTree(r).write(p, encoding="utf-8", xml_declaration=True)
    return p


# ------------------------------------------------------------------ MJCF
def quat_rot_y_neg(deg):
    a = math.radians(deg) / 2           # rotation about -y by deg
    return [math.cos(a), 0.0, -math.sin(a), 0.0]


def build_mjcf():
    m = ET.Element("mujoco", model="arc_arm_%s" % VAR)
    ET.SubElement(m, "compiler", angle="radian", meshdir=".", autolimits="true", inertiafromgeom="false")
    ET.SubElement(m, "option", timestep="0.001", integrator="implicitfast")
    d = ET.SubElement(m, "default")
    ET.SubElement(d, "mesh", scale="0.001 0.001 0.001", inertia="shell")
    ET.SubElement(d, "joint", damping="0.002", armature="0.0001")   # passive pivots: light (unmeasured) losses
    vis = ET.SubElement(d, "default", **{"class": "visual"})
    ET.SubElement(vis, "geom", type="mesh", contype="0", conaffinity="0", group="2")
    col = ET.SubElement(d, "default", **{"class": "collision"})
    ET.SubElement(col, "geom", type="mesh", contype="2", conaffinity="1", group="3", rgba="0.8 0.2 0.2 0.3")
    asset = ET.SubElement(m, "asset")
    names = {}
    for l in LINKS:
        for v in l["visuals"] + l["collisions"]:
            nm = os.path.basename(v["file"])[:-4].replace(" ", "_")
            names[v["file"]] = nm
            ET.SubElement(asset, "mesh", name=nm, file=v["file"])
    wb = ET.SubElement(m, "worldbody")
    els = {None: wb}
    for l in LINKS:
        parent = els[l["parent"]]
        kw = dict(name=l["name"])
        if l["parent"] is not None:
            kw["pos"] = f([x * MM for x in l["origin_xyz_mm"]])
            if l["origin_rot_y_deg"]:
                kw["quat"] = f(quat_rot_y_neg(l["origin_rot_y_deg"]))
        B = ET.SubElement(parent, "body", **kw)
        els[l["name"]] = B
        mass = max(l["mass_kg"], 1e-4)
        I = inertia_m(l) if l["mass_kg"] > 0 else np.eye(3) * 1e-8
        ET.SubElement(B, "inertial", pos=f(link_com(l)), mass="%.6f" % mass,
                      fullinertia="%.4e %.4e %.4e %.4e %.4e %.4e" % (I[0, 0], I[1, 1], I[2, 2], I[0, 1], I[0, 2], I[1, 2]))
        if l["parent"] is not None:
            jkw = dict(name=l["joint"], type="hinge", axis=f(l["axis"]))
            if l["joint"] in ACT:
                lo, hi = SPEC["limits_deg"][l["joint"]]
                jkw.update(range="%.5f %.5f" % (math.radians(lo), math.radians(hi)), armature="%g" % ARMATURE[l["joint"]])
            if l["joint"] == SPEC["spring"]["joint"]:
                jkw.update(stiffness="%.5f" % SPEC["spring"]["k_Nm_per_rad"], springref="%.5f" % math.radians(SPEC["spring"]["free_angle_deg"]),
                           frictionloss="0.05")
            ET.SubElement(B, "joint", **jkw)
        off = f([-x * MM for x in l["frame_in_cad_mm"]])
        ET.SubElement(B, "site", name=l["name"] + "_cad", pos=off, size="0.004", group="5")
        for v in l["visuals"]:
            ET.SubElement(B, "geom", **{"class": "visual", "mesh": names[v["file"]], "pos": off, "rgba": f(v["rgba"], 3)})
        for c in l["collisions"]:
            ET.SubElement(B, "geom", **{"class": "collision", "mesh": names[c["file"]], "pos": off})
        if l["name"] == "head":
            tcp = SPEC["tcp_in_gripper_frame_mm"]
            ET.SubElement(B, "site", name="tcp", pos=f([(tcp[i] - l["frame_in_cad_mm"][i]) * MM for i in range(3)]), size="0.006", rgba="0 1 0 1")
    eq = ET.SubElement(m, "equality")
    for l in LINKS:
        if l["mimic"]:
            ET.SubElement(eq, "joint", joint1=l["joint"], joint2=l["mimic"][0], polycoef="0 %g 0 0 0" % l["mimic"][1],
                          solref="0.002 1", solimp="0.99 0.999 0.0005")
    ac = ET.SubElement(m, "actuator")
    for j in ACT:
        lo, hi = SPEC["limits_deg"][j]
        pk = SPEC["actuators"][j]["peak_Nm"]
        ET.SubElement(ac, "position", name=j, joint=j, kp="%g" % KP[j], kv="%g" % (0.05 * KP[j]),
                      ctrlrange="%.5f %.5f" % (math.radians(lo), math.radians(hi)), forcerange="%g %g" % (-pk, pk))
    ET.SubElement(m, "sensor")
    kf = ET.SubElement(m, "keyframe")
    order = []                                   # MuJoCo's qpos order = depth-first over the XML body tree

    def walk(name):
        for c in LINKS:
            if c["parent"] == name:
                order.append(c["joint"])
                walk(c["name"])
    walk("base_link")
    for r in REF:
        q = {k: math.radians(v) for k, v in r["joints_deg"].items()}
        qpos = [mimic_value(j, q) for j in order]
        ET.SubElement(kf, "key", name=r["pose"].lower().replace("+", "_pos"), qpos=f(qpos), ctrl=f([q[j] for j in ACT]))
    ET.indent(m)
    p = os.path.join(ROOT, "arc_arm.xml")
    ET.ElementTree(m).write(p, encoding="utf-8")
    return p, order


def build_scene():
    import trimesh
    tor = trimesh.creation.torus(major_radius=0.0375, minor_radius=0.0125, major_sections=48, minor_sections=16)
    os.makedirs(os.path.join(ROOT, "meshes", "objects"), exist_ok=True)
    tor.export(os.path.join(ROOT, "meshes", "objects", "donut.stl"))
    sc = """<mujoco model="arc_arm_%s_scene">
  <include file="arc_arm.xml"/>
  <statistic center="0 0 0.4" extent="1.0"/>
  <visual><headlight diffuse="0.6 0.6 0.6" ambient="0.3 0.3 0.3"/><global azimuth="-120" elevation="-20"/></visual>
  <asset>
    <texture type="2d" name="grid" builtin="checker" rgb1="0.2 0.3 0.4" rgb2="0.1 0.2 0.3" width="300" height="300" mark="edge" markrgb="0.2 0.3 0.4"/>
    <material name="grid" texture="grid" texrepeat="5 5" reflectance="0.1"/>
    <mesh name="donut" file="meshes/objects/donut.stl" scale="1 1 1" inertia="shell"/>
  </asset>
  <default><default class="world"><geom contype="1" conaffinity="3"/></default></default>
  <worldbody>
    <light pos="0.5 -1 2" dir="-0.2 0.5 -1" directional="true"/>
    <geom class="world" name="floor" type="plane" size="0 0 0.05" material="grid"/>
    <!-- chassis deck placeholder (the chassis is not designed yet): top at DECK_Z = 120 mm under the arm base -->
    <geom class="world" name="chassis_placeholder" type="box" pos="-0.29 0 0.08" size="0.29 0.24 0.04" rgba="0.15 0.16 0.17 1"/>
    <!-- ARC lower tier: 210 mm high, front edge 30 mm ahead of the bumper (field.py) -->
    <geom class="world" name="lower_tier" type="box" pos="0.53 0 0.105" size="0.5 0.5 0.105" rgba="0.55 0.45 0.33 1"/>
    <!-- donut (OD 100 / ID 50 / 25), 300 g, resting on the tier at the donut-pick position -->
    <body name="donut" pos="0.13 0 0.2235"><freejoint/>
      <inertial pos="0 0 0" mass="0.3" diaginertia="2.40e-4 2.40e-4 4.57e-4"/>
      <geom class="world" type="mesh" mesh="donut" mass="0.3" rgba="0.92 0.66 0.05 1" condim="4" friction="0.8 0.02 0.002"/></body>
    <!-- pipe: 3/4 in Sch40 PVC, OD 26.7, 500 mm, 165 g, lying on the floor beside the robot -->
    <body name="pipe" pos="0.1 0.62 0.0134" quat="0.7071 0 0.7071 0"><freejoint/>
      <inertial pos="0 0 0" mass="0.165" diaginertia="3.45e-3 3.45e-3 2.37e-5"/>
      <geom class="world" type="cylinder" size="0.01335 0.25" mass="0.165" rgba="0.8 0.15 0.15 1" condim="4" friction="0.8 0.02 0.002"/></body>
  </worldbody>
</mujoco>
""" % VAR
    p = os.path.join(ROOT, "scene.xml")
    open(p, "w", encoding="utf-8").write(sc)
    return p


# ------------------------------------------------------------------ validation
def ref_cad_world(r, body):
    mtx = np.array(r["bodies"][body], float)
    T = np.eye(4)
    T[:3, :] = mtx
    T[:3, 3] *= MM
    return T


def err_T(T, R):
    dp = np.linalg.norm(T[:3, 3] - R[:3, 3]) / MM
    cosang = (np.trace(T[:3, :3].T @ R[:3, :3]) - 1) / 2
    return dp, math.degrees(math.acos(max(-1.0, min(1.0, cosang))))


def validate(urdf, mjcf, order, scene):
    import mujoco
    import yourdfpy
    out = dict(variant=VAR)
    # 1. URDF FK
    u = yourdfpy.URDF.load(urdf, build_scene_graph=True, load_meshes=False)
    worst = [0.0, 0.0]
    for r in REF:
        q = {k: math.radians(v) for k, v in r["joints_deg"].items()}
        u.update_cfg({j: q[j] for j in ACT})
        for l in LINKS:
            if l["cad_body"] is None:
                continue
            T = u.get_transform(l["name"], "world") @ trans([-x * MM for x in l["frame_in_cad_mm"]])
            dp, da = err_T(T, ref_cad_world(r, l["cad_body"]))
            worst = [max(worst[0], dp), max(worst[1], da)]
    out["urdf_fk"] = dict(poses=len(REF), max_pos_err_mm=round(worst[0], 4), max_rot_err_deg=round(worst[1], 4),
                          ok=worst[0] < 0.01 and worst[1] < 0.01)
    # 2. MJCF FK + equality residuals
    model = mujoco.MjModel.from_xml_path(mjcf)
    data = mujoco.MjData(model)
    worst, eqres = [0.0, 0.0], 0.0
    for k, r in enumerate(REF):
        mujoco.mj_resetDataKeyframe(model, data, k)
        mujoco.mj_forward(model, data)
        for l in LINKS:
            if l["cad_body"] is None:
                continue
            sid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, l["name"] + "_cad")
            T = np.eye(4)
            T[:3, :3] = data.site_xmat[sid].reshape(3, 3)
            T[:3, 3] = data.site_xpos[sid]
            dp, da = err_T(T, ref_cad_world(r, l["cad_body"]))
            worst = [max(worst[0], dp), max(worst[1], da)]
        tcp = data.site_xpos[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_SITE, "tcp")] / MM
        worst[0] = max(worst[0], float(np.linalg.norm(tcp - np.array(r["tcp_mm"]))))
        if data.nefc:
            eqres = max(eqres, float(np.max(np.abs(data.efc_pos[:data.ne]))) if data.ne else 0.0)
    out["mjcf_fk"] = dict(poses=len(REF), max_pos_err_mm=round(worst[0], 4), max_rot_err_deg=round(worst[1], 4),
                          max_equality_residual=eqres, ok=worst[0] < 0.01 and worst[1] < 0.01 and eqres < 1e-6,
                          nq=int(model.nq), nu=int(model.nu), neq=int(model.neq), ngeom=int(model.ngeom))
    # 3. dynamics: hold STOW for 3 s
    mujoco.mj_resetDataKeyframe(model, data, 0)
    target = data.ctrl.copy()
    jid = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, j) for j in ACT]
    drift, track, nan = 0.0, 0.0, False
    for i in range(3000):
        mujoco.mj_step(model, data)
        if not np.all(np.isfinite(data.qpos)):
            nan = True
            break
        if data.ne:
            drift = max(drift, float(np.max(np.abs(data.efc_pos[:data.ne]))))
        if i > 1500:
            track = max(track, float(np.max(np.abs(data.qpos[[model.jnt_qposadr[j] for j in jid]] - target))))
    tf = [float(data.actuator_force[i]) for i in range(model.nu)]
    out["mjcf_hold_stow"] = dict(seconds=3.0, nan=nan, max_equality_drift=round(drift, 6), max_track_err_deg=round(math.degrees(track), 3),
                                 actuator_torque_Nm=dict(zip(ACT, [round(t, 3) for t in tf])), ok=(not nan) and drift < 1e-3 and math.degrees(track) < 1.0)
    # 4. power-off release from the pipe grip (gripper actuator off; spring + friction only)
    k = [r["pose"] for r in REF].index("PIPE_CHUTE")
    mujoco.mj_resetDataKeyframe(model, data, k)
    gi = ACT.index("gripper")
    model.actuator_gainprm[gi, 0] = 0.0
    model.actuator_biasprm[gi, :3] = 0.0
    gq = model.jnt_qposadr[mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, "gripper")]
    q_open = math.radians(SPEC["limits_deg"]["gripper"][1])
    q0 = float(data.qpos[gq])
    fb, th_ref = SPEC["fb"], math.radians(SPEC["theta_ref_deg"])

    def gap(dq):                                 # pad-arc gap (mm) for a gripper joint value
        return 2 * (fb["YG"] + fb["L"] * math.sin(th_ref + dq) - fb["E"])
    g0 = gap(q0)
    t90 = t10 = None
    for i in range(3000):
        mujoco.mj_step(model, data)
        t = (i + 1) * model.opt.timestep
        if t10 is None and gap(float(data.qpos[gq])) >= g0 + 10.0:
            t10 = t
        if t90 is None and data.qpos[gq] - q0 >= 0.9 * (q_open - q0):
            t90 = t
    out["mjcf_power_off_release"] = dict(start_gap_mm=round(g0, 1), end_gap_mm=round(gap(float(data.qpos[gq])), 1),
                                         t_open_10mm_s=t10, t_90pct_open_s=t90, ok=t10 is not None and t10 < 1.0,
                                         note="ARC rule: release within 1 s of power loss. Servo back-drive is modelled only as "
                                              "0.05 N*m friction + 0.002 kg*m^2 armature on the gripper joint - an estimate until "
                                              "bench-measured; the result is only as good as that estimate")
    # 5. scene + URDF in MuJoCo's URDF importer
    sm = mujoco.MjModel.from_xml_path(scene)
    out["scene"] = dict(compiles=True, nbody=int(sm.nbody), ngeom=int(sm.ngeom))
    try:
        um = mujoco.MjModel.from_xml_path(urdf)
        out["urdf_in_mujoco"] = dict(compiles=True, nbody=int(um.nbody), note="MuJoCo's URDF importer ignores <mimic>")
    except Exception as e:
        out["urdf_in_mujoco"] = dict(compiles=False, error=str(e)[:300])
    out["ok"] = all(v.get("ok", True) for v in out.values() if isinstance(v, dict))
    return out


def validate_gazebo(gz_urdf):
    """Structural checks of the Gazebo package (the run test is cad/sim/gz_check.py, see gazebo_run): model.urdf parses with
    yourdfpy, every model:// mesh resolves to a file in the model dir, mimic joints and plugins are present, the
    world references the model and bullet-featherstone physics."""
    import yourdfpy
    model = "arc_arm_%s" % VAR
    u = yourdfpy.URDF.load(gz_urdf, build_scene_graph=True, load_meshes=False)
    r = ET.parse(gz_urdf).getroot()
    uris = [m.get("filename") for m in r.iter("mesh")]
    missing = [x for x in uris if not os.path.exists(os.path.join(ROOT, x.replace("model://%s/" % model, "")))]
    mimics = len(list(r.iter("mimic")))
    plugins = [p.get("filename") for p in r.iter("plugin")]
    # SDF puts links and joints in one frame namespace: a joint named like a link makes gz-sim reject the model
    clash = sorted({l.get("name") for l in r.iter("link")} & {j.get("name") for j in r.iter("joint")})
    w = open(os.path.join(ROOT, "worlds", "arc_arm.sdf"), encoding="utf-8").read()
    ok = not missing and not clash and mimics == 11 and plugins.count("gz-sim-joint-position-controller-system") == 5 and         ("model://%s" % model) in w and "bullet-featherstone" in w and len(u.actuated_joint_names) == 5
    return dict(parses=True, mesh_uris=len(uris), missing_meshes=missing[:5], name_clashes=clash, mimic_joints=mimics,
                actuated=list(u.actuated_joint_names), plugins=len(plugins), ok=ok,
                note="structure only; the gz-sim run test is gazebo_run (cad/sim/gz_check.py)")


def gazebo_run(gz_urdf):
    """Summary of the last gz-sim run test (cad/sim/gz_check.py -> gazebo_validation.json), FRESH only if it ran on
    this exact model.urdf. Needs gz-sim 8, so it runs separately (WSL); a missing or stale result fails the build."""
    import hashlib
    f = os.path.join(ROOT, "gazebo_validation.json")
    if not os.path.exists(f):
        return dict(ok=False, status="MISSING", note="run cad/sim/gz_check.py in a gz-sim 8 environment")
    g = json.load(open(f, encoding="utf-8"))
    fresh = g.get("model_urdf_sha256") == hashlib.sha256(open(gz_urdf, "rb").read().replace(b"\r\n", b"\n")).hexdigest()   # EOL-neutral
    P = g.get("poses", [])
    return dict(ok=bool(g.get("ok")) and fresh, status="FRESH" if fresh else "STALE", gz_version=g.get("gz_version"),
                world=g.get("world"), poses=len(P),
                max_track_err_deg=max((max(abs(v) for v in p["track_err_deg"].values()) for p in P), default=None),
                max_mimic_err_deg=max((p["max_mimic_err_deg"] for p in P), default=None),
                max_tcp_err_mm=max((p["tcp_err_mm"] for p in P), default=None), tolerances=g.get("tolerances"),
                power_off_release={k: (g.get("power_off_release") or {}).get(k) for k in
                                   ("t_open_10mm_s", "t_90pct_open_s", "end_gap_mm", "ok")})


def trans(v):
    T = np.eye(4)
    T[:3, 3] = v
    return T


def lump_crank_pin(r, mp=0.003, ip=1e-5):
    """Give the massless crank_pin helper link 3 g and 1e-5 kg*m^2 (the crank-pin bolt + bearing; that hardware is
    also in the crank's mass, so the Gazebo model double-counts ~0.1 % of the arm mass).
    Why: crank_pin's joint and rod_ab's joint are coaxial at the same point, so with a ~0 inertia link between them
    the crank_pin DOF has a near-singular mass matrix and bullet-featherstone's stiff mimic (gear) constraints jam:
    the elbow stalled at ~0 deg whatever was commanded. (Taking the 3 g from the crank instead fails sdformat's
    inertia triangle check.)"""
    il = next(l for l in r.iter("link") if l.get("name") == "crank_pin").find("inertial")
    il.find("mass").set("value", "%.6f" % mp)
    il.find("inertia").attrib.update(ixx="%g" % ip, ixy="0", ixz="0", iyy="%g" % ip, iyz="0", izz="%g" % ip)


def build_gazebo(urdf):
    """Gazebo (Harmonic, gz-sim 8) model directory: model.config + model.urdf (model:// mesh URIs, gz-sim joint
    position controllers + joint state publisher, the gripper spring on the SDF joint) + worlds/arc_arm.sdf using
    bullet-featherstone physics (the gz-physics engine with mimic-joint constraints).
    Usage:  GZ_SIM_RESOURCE_PATH=<repo>/sim  gz sim <repo>/sim/arc_arm_<variant>/worlds/arc_arm.sdf"""
    model = "arc_arm_%s" % VAR
    t = ET.parse(urdf)
    r = t.getroot()
    for mesh in r.iter("mesh"):
        mesh.set("filename", "model://%s/%s" % (model, mesh.get("filename")))
    lump_crank_pin(r)
    sp = SPEC["spring"]
    # gz-physics 7 bullet-featherstone applies joint spring + viscous damping each step (not joint friction): the
    # power-off release run in cad/sim/gz_check.py shows this spring opening the jaws in Gazebo.
    g = ET.SubElement(r, "gazebo", reference="gripper")
    # sdformat's URDF parser copies unknown <gazebo reference="joint"> children into the SDF <joint>; these are SDF
    # joint-axis dynamics written in the URDF extension form that sdformat converts (springStiffness/springReference)
    ET.SubElement(g, "springStiffness").text = "%.5f" % sp["k_Nm_per_rad"]
    ET.SubElement(g, "springReference").text = "%.5f" % math.radians(sp["free_angle_deg"])
    gz = ET.SubElement(r, "gazebo")
    ET.SubElement(gz, "plugin", filename="gz-sim-joint-state-publisher-system", name="gz::sim::systems::JointStatePublisher")
    for j in ACT:
        p = ET.SubElement(gz, "plugin", filename="gz-sim-joint-position-controller-system", name="gz::sim::systems::JointPositionController")
        ET.SubElement(p, "joint_name").text = j
        ET.SubElement(p, "topic").text = "/arc_arm/%s/cmd_pos" % j
        # velocity mode: the plugin writes a joint velocity command (-error/dt, capped at cmd_max = the joint speed);
        # bullet-featherstone runs it through its implicit joint motor, whose impulse is limited by the URDF effort
        # limit (= actuator peak torque). Force-mode PID with MuJoCo gains is unstable on the light gripper links.
        ET.SubElement(p, "use_velocity_commands").text = "true"
        ET.SubElement(p, "cmd_max").text = "%g" % VEL[j]
        ET.SubElement(p, "cmd_min").text = "%g" % -VEL[j]
    ET.indent(r)
    t.write(os.path.join(ROOT, "model.urdf"), encoding="utf-8", xml_declaration=True)
    open(os.path.join(ROOT, "model.config"), "w", encoding="utf-8").write(
        '<?xml version="1.0"?>\n<model>\n  <name>%s</name>\n  <version>1.0</version>\n  <sdf version="1.11">model.urdf</sdf>\n'
        '  <description>ARC S2 Engineer arm (%s gripper), generated from the CAD model by cad/sim/build_robot.py</description>\n'
        '</model>\n' % (model, VAR))
    os.makedirs(os.path.join(ROOT, "worlds"), exist_ok=True)
    world = """<?xml version="1.0"?>
<sdf version="1.11">
  <world name="arc_arm">
    <physics name="1ms" type="ignored"><max_step_size>0.001</max_step_size><real_time_factor>1.0</real_time_factor></physics>
    <plugin filename="gz-sim-physics-system" name="gz::sim::systems::Physics"><engine><filename>gz-physics-bullet-featherstone-plugin</filename></engine></plugin>
    <plugin filename="gz-sim-user-commands-system" name="gz::sim::systems::UserCommands"/>
    <plugin filename="gz-sim-scene-broadcaster-system" name="gz::sim::systems::SceneBroadcaster"/>
    <plugin filename="gz-sim-sensors-system" name="gz::sim::systems::Sensors"><render_engine>ogre2</render_engine></plugin>
    <gravity>0 0 -9.81</gravity>
    <light type="directional" name="sun"><cast_shadows>true</cast_shadows><pose>0 0 10 0 0 0</pose><diffuse>0.8 0.8 0.8 1</diffuse><direction>-0.5 0.1 -0.9</direction></light>
    <model name="ground_plane"><static>true</static><link name="link">
      <collision name="c"><geometry><plane><normal>0 0 1</normal><size>10 10</size></plane></geometry></collision>
      <visual name="v"><geometry><plane><normal>0 0 1</normal><size>10 10</size></plane></geometry><material><diffuse>0.3 0.35 0.4 1</diffuse></material></visual>
    </link></model>
    <!-- chassis deck placeholder (chassis not designed yet): top at DECK_Z = 120 mm under the arm base -->
    <model name="chassis_placeholder"><static>true</static><pose>-0.29 0 0.08 0 0 0</pose><link name="link">
      <collision name="c"><geometry><box><size>0.58 0.48 0.08</size></box></geometry></collision>
      <visual name="v"><geometry><box><size>0.58 0.48 0.08</size></box></geometry><material><diffuse>0.15 0.16 0.17 1</diffuse></material></visual>
    </link></model>
    <!-- ARC lower tier, 210 mm high, front edge 30 mm ahead of the bumper (cad/field.py) -->
    <model name="lower_tier"><static>true</static><pose>0.53 0 0.105 0 0 0</pose><link name="link">
      <collision name="c"><geometry><box><size>1.0 1.0 0.21</size></box></geometry></collision>
      <visual name="v"><geometry><box><size>1.0 1.0 0.21</size></box></geometry><material><diffuse>0.55 0.45 0.33 1</diffuse></material></visual>
    </link></model>
    <include><uri>model://%s</uri><name>%s</name><pose>0 0 0 0 0 0</pose></include>
  </world>
</sdf>
""" % (model, model)
    open(os.path.join(ROOT, "worlds", "arc_arm.sdf"), "w", encoding="utf-8").write(world)
    return os.path.join(ROOT, "model.urdf")


MAX_FACES = 60000      # MuJoCo's STL limit is 200k faces; 60k keeps viewers and Gazebo fast


def decimate_meshes():
    """Quadric-decimate any exported mesh above MAX_FACES (vendor motor STEPs), in place."""
    import trimesh
    done = []
    for sub in ("visual", "collision"):
        d = os.path.join(ROOT, "meshes", sub)
        for fn in sorted(os.listdir(d)):
            p = os.path.join(d, fn)
            m = trimesh.load(p, force="mesh")
            if len(m.faces) > MAX_FACES:
                s = m.simplify_quadric_decimation(face_count=MAX_FACES)
                s.export(p)
                done.append("%s %d -> %d faces" % (fn, len(m.faces), len(s.faces)))
    for x in done:
        print("decimated", x)
    return done


def main():
    decimate_meshes()
    urdf = build_urdf()
    mjcf, order = build_mjcf()
    scene = build_scene()
    gz_urdf = build_gazebo(urdf)
    res = validate(urdf, mjcf, order, scene)
    res["gazebo_package"] = validate_gazebo(gz_urdf)
    res["gazebo_run"] = gazebo_run(gz_urdf)
    res["ok"] = all(v.get("ok", True) for v in res.values() if isinstance(v, dict))
    json.dump(res, open(os.path.join(ROOT, "validation.json"), "w"), indent=1)
    lines = ["# Validation - arc_arm_%s" % VAR, ""] + ["- **%s**: `%s`" % (k, json.dumps(v)) for k, v in res.items() if k != "variant"]
    open(os.path.join(ROOT, "validation.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(json.dumps(res, indent=1))
    print("BUILD_ROBOT:", "PASS" if res["ok"] else "FAIL")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
