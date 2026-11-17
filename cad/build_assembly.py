# -*- coding: utf-8 -*-
"""
Build the mated FreeCAD Assembly (Assembly workbench, FreeCAD >= 1.0) headless:
    freecadcmd build_assembly.py

* One App::Part per rigid body (GROUND, UPPER, CRANK, ROD_AB, ROD1, FOREARM,
  ROCKER, LEVEL, GRIPPER, HEAD, SCREW, MGEAR, JAW_L, JAW_R).  Components inside a body are
  located on their mating features (bolt circles, bearing seats, dowels).
* Joints between bodies:
    Grounded GROUND
    Revolute  S (GROUND-UPPER), S (GROUND-CRANK), A (CRANK-ROD_AB),
              B (ROD_AB-FOREARM), E (UPPER-FOREARM), G1 (GROUND-ROD1),
              E+v1 (ROD1-ROCKER), E (FOREARM-ROCKER), D (FOREARM-LEVEL),
              D (FOREARM-GRIPPER), roll (GRIPPER-HEAD), lead screw + motor gear (HEAD)
    Parallel  ROCKER-LEVEL x-axes  (= 1:1 GT2 belt keeps the wrist level)
    Slider    JAW_L / JAW_R on the MGN9 rails (GRIPPER)
    Screw      SCREW-JAW_L (Tr8x8 RH), SCREW-JAW_R (LH)
    Gears      SCREW 20T - MGEAR 32T
* Saves cad/ARC_Engineer_Arm.FCStd (STOW) and cad/scenes/ARC_Arm_<POSE>.FCStd
  (re-solved at each task pose, with field items and the cable harness).
Run cad/color_assembly.py in the GUI afterwards to apply appearance.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, HERE)
import FreeCAD as App   # noqa: E402
import Part             # noqa: E402
import JointObject      # noqa: E402
import params   # noqa: E402
params.use_release_variant('build_assembly.py')   # writes the released package
import arm_model as M   # noqa: E402
import field as F       # noqa: E402

V = App.Vector
ROT_Y = App.Rotation(V(1, 0, 0), -90)      # JCS z -> world +Y
ROT_X = App.Rotation(V(0, 1, 0), 90)       # JCS z -> +X
ROT_Z = App.Rotation()


def jcs(x, y, z, rot=ROT_Y):
    return App.Placement(V(x, y, z), rot)


def harness(J, plc):
    """Pose-dependent cable runs (B-spline sweeps). Visual only."""
    sx, sz, zb = M.K["SX"], M.K["SZ"], M.K["DECK_Z"]
    UA = plc["UPPER"]; FA = plc["FOREARM"]; G = plc["HEAD"]; LV = plc["LEVEL"]; dx = M.HXJ
    runs = {
        "Cable_M2006_Gripper": (2.5, [G.multVec(V(M.XR, 64, M.ZM)), G.multVec(V(M.XR - 30, 66, M.ZM - 10)),
                                     G.multVec(V(dx - 25, -118, 10.5)),
                                     FA.multVec(V(M.K["L3"] - 70, -48, 16)), FA.multVec(V(45, -48, 16)),
                                     UA.multVec(V(M.UA_CLIP_X[1], M.UA_CLIP_YZ[0], M.UA_CLIP_YZ[1] + 1.9)),
                                     UA.multVec(V(M.UA_CLIP_X[0], M.UA_CLIP_YZ[0], M.UA_CLIP_YZ[1] + 1.9)),
                                     V(sx - 60, -78, sz - 35), V(sx - 120, -80, zb + 20)]),
        "Cable_Servo_J3": (1.8, [LV.multVec(App.Rotation(V(0, 1, 0), -M.SERVO_ANG).multVec(V(30, -70, 0))),
                                 FA.multVec(V(M.K["L3"] - 80, -52, 20)), FA.multVec(V(50, -52, 20)),
                                 UA.multVec(V(M.UA_CLIP_X[1], M.UA_CLIP_YZ[0], M.UA_CLIP_YZ[1] - 2.6)),
                                 UA.multVec(V(M.UA_CLIP_X[0], M.UA_CLIP_YZ[0], M.UA_CLIP_YZ[1] - 2.6)),
                                 V(sx - 70, -70, sz - 40), V(sx - 120, -80, zb + 20)]),
        "Cable_CAN_J1": (2.0, [V(sx, -105.5, sz - 12), V(sx - 15, -112, sz - 45), V(sx - 60, -95, zb + 25), V(sx - 120, -80, zb + 15)]),
        "Cable_CAN_J2": (2.0, [V(sx, 105.5, sz - 12), V(sx - 15, 112, sz - 45), V(sx - 120, 95, zb + 25), V(sx - 250, 40, zb + 15)]),
    }
    out = []
    for name, (r, pts) in runs.items():
        try:
            bs = Part.BSplineCurve()
            bs.interpolate(pts)
            e = bs.toShape()
            t0 = e.tangentAt(e.FirstParameter)
            prof = Part.Wire(Part.makeCircle(r, pts[0], t0))
            s = Part.Wire(e).makePipeShell([prof], True, False)
            out.append((name, s))
        except Exception as ex:
            print("harness", name, "failed:", ex)
    return out


# demo cycle for the native Assembly simulation: (time s, pose, overrides)
SIM_KEYS = [(0.0, "STOW", {}), (2.0, "DONUT_APPROACH", {}), (3.5, "DONUT_PICK", {"jaw": 112.0}),
            (4.5, "DONUT_PICK", {}), (6.5, "DONUT_LIFT", {}), (7.5, "DONUT_LIFT", {"roll": 25.0}),
            (8.5, "DONUT_LIFT", {"roll": -25.0}), (9.5, "DONUT_LIFT", {"roll": 0.0}),
            (11.5, "PIPE_CHUTE", {"jaw": None}), (13.5, "STOW", {})]


def _fourier_formula(vals, times, period, n_harm=16, n_samp=1024):
    """Periodic motion formula through keyframes (cosine-eased between keys) as a truncated
    Fourier series - the Assembly solver's formula parser only accepts sin/cos/polynomials."""
    def f(t):
        t = t % period
        for i in range(1, len(times)):
            if t <= times[i]:
                u_ = (t - times[i - 1]) / (times[i] - times[i - 1])
                e = 0.5 - 0.5 * math.cos(math.pi * u_)
                return vals[i - 1] + (vals[i] - vals[i - 1]) * e
        return vals[-1]
    ys = [f(period * k / n_samp) for k in range(n_samp)]
    w = 2 * math.pi / period
    terms = ["%.6f" % (sum(ys) / n_samp)]
    for h in range(1, n_harm + 1):
        ah = 2.0 / n_samp * sum(y * math.cos(2 * math.pi * h * k / n_samp) for k, y in enumerate(ys))
        bh = 2.0 / n_samp * sum(y * math.sin(2 * math.pi * h * k / n_samp) for k, y in enumerate(ys))
        if abs(ah) > 1e-6:
            terms.append("%.6f*cos(%.6f*time)" % (ah, h * w))
        if abs(bh) > 1e-6:
            terms.append("%.6f*sin(%.6f*time)" % (bh, h * w))
    return " + ".join(terms)


def add_simulation(doc, asm, jg):
    """Native FreeCAD 1.1 Assembly simulation: angular motions on J1, J2, wrist pitch,
    J4 roll and the lead screw (jaws follow through the Screw joints, the M2006 gear
    through the Gears joint - driving the motor gear directly stalls the solver).
    Play it from the 'Simulation' object (double-click) in the Assembly tree."""
    import CommandCreateSimulation as CS
    import UtilsAssembly
    J = {j.Label: j for j in jg.Group}
    times, cols = [], {k: [] for k in ("j1", "j2", "pitch", "roll", "mg")}
    for (t, pose, ov) in SIM_KEYS:
        q, jaw = M.pose_q(pose)
        q = list(q)
        if "roll" in ov:
            q[3] = ov["roll"]
        if "jaw" in ov:
            jaw = M.PIPE_JAW if ov["jaw"] is None else ov["jaw"]
        times.append(t)
        d = jaw / 2.0 - M.O_REF
        cols["j1"].append(-math.radians(q[0]))
        cols["j2"].append(-math.radians(q[1] + 180.0))
        cols["pitch"].append(-math.radians(q[2] - q[1]))           # GRIPPER relative to FOREARM
        cols["roll"].append(math.radians(q[3]))
        cols["mg"].append(-math.radians(360.0 * d / M.LEAD))          # lead-screw angle
    grp = UtilsAssembly.getSimulationGroup(asm)
    sim = grp.newObject("App::FeaturePython", "Simulation")
    CS.Simulation(sim)
    CS.ViewProviderSimulation(sim.ViewObject)
    sim.Label = "Simulation_demo_cycle"
    sim.bTimeEnd = times[-1]
    sim.cTimeStepOutput = 0.01          # the jaw moves spin the motor gear fast; coarser steps lose the solve
    sim.jFramesPerSecond = 100          # = real time
    motions = []
    for jl, key in (("Rev_S_J1_upper", "j1"), ("Rev_S_J2_crank", "j2"), ("Rev_D_forearm_gripper", "pitch"),
                    ("Rev_roll_J4", "roll"), ("Rev_leadscrew", "mg")):
        m = asm.newObject("App::FeaturePython", "Motion")
        CS.Motion(m, "Angular", J[jl], _fourier_formula(cols[key], times, times[-1]))
        CS.ViewProviderMotion(m.ViewObject)
        m.Label = "Motion_" + jl
        motions.append(m)
    sim.Group = motions
    doc.recompute()
    asm.generateSimulation(sim)
    return sim, asm.numberOfFrames()


def build(pose="STOW", with_field=False, path=None):
    name = "ARC_Engineer_Arm" if pose == "STOW" and not with_field else "ARC_Arm_" + pose
    doc = App.newDocument(name)
    asm = doc.addObject("Assembly::AssemblyObject", "Assembly")
    asm.Label = "ARC_Engineer_Arm_Assembly"
    jg = asm.newObject("Assembly::JointGroup", "Joints")
    bodies = M.build_bodies()
    q, jaw = M.pose_q(pose)
    plc = M.placements(*q, jaw=jaw)
    parts = {}
    first_child = {}
    for bname, plist in bodies.items():
        ap = asm.newObject("App::Part", bname)
        ap.Placement = plc[bname]
        for p in plist:
            f = doc.addObject("Part::Feature", p.name)
            f.Shape = p.vis
            f.addProperty("App::PropertyString", "ColorKey", "Arm")
            f.ColorKey = p.color
            f.addProperty("App::PropertyString", "Source", "Arm")
            f.Source = "%s | %s" % (p.src, p.note)
            ap.addObject(f)
        # identity-placed datum: joint frames (Detach=True) are expressed relative to the
        # referenced element's feature, so every joint references this datum
        dt = doc.addObject("Part::Feature", "Datum_" + bname)
        dt.Shape = Part.makeBox(0.2, 0.2, 0.2, V(-0.1, -0.1, -0.1))
        ap.addObject(dt)
        first_child[bname] = dt
        parts[bname] = ap
    doc.recompute()

    def ref(bname):
        f = first_child[bname]
        return [parts[bname], [f.Name + ".Vertex1", f.Name + ".Vertex1"]]

    g = jg.newObject("App::FeaturePython", "Grounded_Base")
    JointObject.GroundedJoint(g, parts["GROUND"])
    if App.GuiUp:                    # GUI build: attach view providers so the solver/drag tools work
        JointObject.ViewProviderGroundedJoint(g.ViewObject)

    skip = os.environ.get("SKIP", "").split(",")

    def joint(label, typ, b1, pl1, b2, pl2, **props):
        if label in skip:
            return None
        j = jg.newObject("App::FeaturePython", label)
        JointObject.Joint(j, JointObject.JointTypes.index(typ))
        if App.GuiUp:
            JointObject.ViewProviderJoint(j.ViewObject)
        j.Reference1 = ref(b1)
        j.Reference2 = ref(b2)
        j.Detach1 = True
        j.Detach2 = True
        j.Placement1 = pl1
        j.Placement2 = pl2
        for k, v in props.items():
            setattr(j, k, v)
        return j

    K = M.K
    sx, sz = K["SX"], K["SZ"]
    v1 = M.u(K["V1_ANG"], K["V1_LEN"])
    G1 = M.add((sx, sz), v1)
    joint("Rev_S_J1_upper", "Revolute", "GROUND", jcs(sx, -47, sz), "UPPER", jcs(0, -47, 0))
    joint("Rev_S_J2_crank", "Revolute", "GROUND", jcs(sx, 47, sz), "CRANK", jcs(0, 47, 0))
    joint("Rev_A_crank_rodAB", "Revolute", "CRANK", jcs(K["L1"], 29, 0), "ROD_AB", jcs(0, 29, 0))
    joint("Rev_B_rodAB_forearm", "Revolute", "ROD_AB", jcs(K["L2"], 29, 0), "FOREARM", jcs(-K["L1"], 29, 0))
    joint("Rev_E_upper_forearm", "Revolute", "UPPER", jcs(K["L2"], 0, 0), "FOREARM", jcs(0, 0, 0))
    joint("Rev_G1_ground_rod1", "Revolute", "GROUND", jcs(G1[0], -40, G1[1]), "ROD1", jcs(0, -40, 0))
    joint("Rev_Ev1_rod1_rocker", "Revolute", "ROD1", jcs(K["L2"], -40, 0), "ROCKER", jcs(v1[0], -40, v1[1]))
    joint("Rev_E_forearm_rocker", "Revolute", "FOREARM", jcs(0, -34.5, 0), "ROCKER", jcs(0, -34.5, 0))
    joint("Rev_D_forearm_level", "Revolute", "FOREARM", jcs(K["L3"], -34.5, 0), "LEVEL", jcs(0, -34.5, 0))
    joint("Rev_D_forearm_gripper", "Revolute", "FOREARM", jcs(K["L3"], 0, 0), "GRIPPER", jcs(0, 0, 0))
    # stage-2 level keeping: 1:1 GT2 30T belt, rocker pulley (E) -> wrist pulley (D), as a real Belt joint
    rp = M.GT2_T * 2.0 / math.pi / 2.0
    joint("Belt_GT2_stage2", "Belt", "ROCKER", jcs(0, -29, 0), "LEVEL", jcs(0, -29, 0), Distance=rp, Distance2=rp)
    xr = M.ROLL_XS
    joint("Rev_roll_J4", "Revolute", "GRIPPER", jcs(xr, 0, M.ROLL_Z, ROT_X), "HEAD", jcs(xr, 0, M.ROLL_Z, ROT_X))
    xs, zs, zm = M.XR, M.ZS, M.ZM
    joint("Slider_jaw_L", "Slider", "HEAD", jcs(xs, 0, 7, ROT_Y), "JAW_L", jcs(xs, 0, 7, ROT_Y))
    joint("Slider_jaw_R", "Slider", "HEAD", jcs(xs, 0, 7, ROT_Y), "JAW_R", jcs(xs, 0, 7, ROT_Y))
    joint("Rev_leadscrew", "Revolute", "HEAD", jcs(xs, 0, zs, ROT_Y), "SCREW", jcs(xs, 0, zs, ROT_Y))
    joint("Rev_motor_gear", "Revolute", "HEAD", jcs(xs, 0, zm, ROT_Y), "MGEAR", jcs(xs, 0, zm, ROT_Y))
    # Tr8x8 bidirectional: RH half drives JAW_L, LH half JAW_R (JCS z flipped = opposite hand)
    joint("Screw_nut_L", "Screw", "SCREW", jcs(xs, 0, zs, ROT_Y), "JAW_L", jcs(xs, 0, zs, ROT_Y), Distance=M.LEAD)
    joint("Screw_nut_R", "Screw", "SCREW", jcs(xs, 0, zs, ROT_Y), "JAW_R", jcs(xs, 0, zs, ROT_Y), Distance=-M.LEAD)
    joint("Gears_20T_32T", "Gears", "SCREW", jcs(xs, 0, zs, ROT_Y), "MGEAR", jcs(xs, 0, zm, ROT_Y),
          Distance=M.Z_SCREW_T / 2.0, Distance2=M.Z_MOTOR_T / 2.0)
    doc.recompute()
    before = {k: App.Placement(v.Placement) for k, v in parts.items()}
    res = asm.solve()
    doc.recompute()
    drift = max((parts[k].Placement.Base - before[k].Base).Length for k in parts)
    rdrift = max(parts[k].Placement.Rotation.multiply(before[k].Rotation.inverted()).Angle for k in parts)
    msg = "%-16s solve=%s  max drift %.4f mm / %.5f rad" % (pose, res, drift, rdrift)
    print(msg)
    with open(os.path.join(HERE, "assembly_solve_report.txt"), "a") as fh:
        fh.write(msg + chr(10))

    if with_field:
        fg = doc.addObject("App::DocumentObjectGroup", "Field")
        for n, s, c in F.scene_items(pose):
            o = doc.addObject("Part::Feature", n)
            o.Shape = s
            o.addProperty("App::PropertyString", "ColorKey", "Arm")
            o.ColorKey = c
            fg.addObject(o)
        h = F.held_object(pose)
        if h:
            s = h[1].copy()
            s.Placement = plc["HEAD"]
            o = doc.addObject("Part::Feature", h[0])
            o.Shape = s
            o.addProperty("App::PropertyString", "ColorKey", "Arm")
            o.ColorKey = h[2]
            fg.addObject(o)
    if App.GuiUp and pose == "STOW" and not with_field:
        try:
            sim, nfr = add_simulation(doc, asm, jg)
            msg = "simulation demo cycle: %d frames" % nfr
            asm.updateForFrame(0)
        except Exception as ex:
            msg = "simulation failed: %s" % ex
        print(msg)
        with open(os.path.join(HERE, "assembly_solve_report.txt"), "a") as fh:
            fh.write(msg + chr(10))
    hg = doc.addObject("App::DocumentObjectGroup", "Harness_pose_specific")
    J = M.joints(q[0], q[1])
    for n, s in harness(J, plc):
        o = doc.addObject("Part::Feature", n)
        o.Shape = s
        o.addProperty("App::PropertyString", "ColorKey", "Arm")
        o.ColorKey = "wire"
        hg.addObject(o)
    doc.recompute()
    out = path or os.path.join(HERE, (name + ".FCStd") if not with_field else os.path.join("scenes", name + ".FCStd"))
    doc.saveAs(out)
    if not (App.GuiUp and os.environ.get("KEEP_OPEN")):
        App.closeDocument(doc.Name)
    return res, drift


os.makedirs(os.path.join(HERE, "scenes"), exist_ok=True)
build("STOW")
if os.environ.get("FULL"):
  for p in ("DONUT_PICK", "DONUT_LIFT", "DONUT_LIFT_ROLL+", "DONUT_PLACE", "PIPE_GRASP", "PIPE_LIFT", "PIPE_CHUTE", "PIPE_CHUTE_ROLL90"):
    build(p, with_field=True)
