"""Full ARC tasks in MuJoCo: donut (pick off the zigzag pole, lift up and off it, drive, place on the scoring
platform) and pipe (pick from the bucket, lift out, drive, push 300 mm into the chute, release).

Scene: sim/arc_arm_<variant>/tasks.xml (cad/sim/build_tasks.py): the arm on a chassis with slide joints, the four
CAD field stations side by side, a free donut and pipe. Motion comes from CAD: task poses (task_poses.json), the
donut-lift path with chassis strafe + wrist roll (task_field.json, field.donut_lift_path), and the arm IK below
(same formula as arm.kinematics.ik; checked against the CAD poses at start).

KINEMATIC GRASP: when the jaws close at a grasp pose and the object is where it should be (geometric check), a weld
locks it to the head; opening the jaws releases it. Held objects don't collide with the arm, but do with the field
and chassis, so the run reports every arm-field and object-field contact: e.g. the donut touching the pole during
the lift would show there.

Control: host-side setpoints every 10 ms (min-jerk over each move), clamped to the joint limits; MuJoCo position
actuators per joint (the DM-J4340 MIT-mode law), position servos on the chassis slides.

    python cad/sim/tasks.py [--task donut|pipe|both] [--no-viewer] [--speed 0.5]
Needs: pip install mujoco. Writes sim/arc_arm_<variant>/task_run.json.
"""
import argparse
import json
import math
import os
import sys
import time
import tomllib
import xml.etree.ElementTree as ET

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from joint_command import ACT, REPO, load_limits, min_jerk  # noqa: E402

LANES = dict(pick=0.0, place=1.6, bucket=-1.6, chute=-3.2)       # must match build_tasks.py
CTRL_DT = 0.01                                                  # host setpoint period (100 Hz)
GRIP_SETTLE_S = 0.25                                           # ignore the weld-attach transient in grasp loads
V_CART = 150.0                                                  # mm/s for Cartesian lines
V_LIFT = 100.0                                                  # mm/s up the pole
V_BASE = 0.4                                                    # m/s chassis


class Kin:
    """Arm IK/jaw maps in plain Python (the CAD formulas: arm.kinematics.ik, fourbar jaw <-> drive angle)."""

    def __init__(self, variant):
        self.K = tomllib.load(open(os.path.join(REPO, "cad", "params", "arm.toml"), "rb"))["K"]
        spec = json.load(open(os.path.join(REPO, "sim", "arc_arm_%s" % variant, "robot_spec.json"), encoding="utf-8"))
        self.fb, self.th_ref = spec["fb"], spec["theta_ref_deg"]

    def ik(self, tcp_x, tcp_z, pitch):
        K = self.K
        c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        wx = tcp_x - K["GRIP"] * c - K["DROP"] * s
        wz = tcp_z - K["GRIP"] * s + K["DROP"] * c
        dx, dz = wx - K["SX"], wz - K["SZ"]
        r = math.hypot(dx, dz)
        if not abs(K["L2"] - K["L3"]) <= r <= K["L2"] + K["L3"]:
            raise ValueError("unreachable r=%.0f" % r)
        beta = math.acos((K["L2"] ** 2 + r ** 2 - K["L3"] ** 2) / (2 * K["L2"] * r))
        th1 = math.degrees(math.atan2(dz, dx) + beta)
        ex, ez = K["SX"] + K["L2"] * math.cos(math.radians(th1)), K["SZ"] + K["L2"] * math.sin(math.radians(th1))
        return th1, math.degrees(math.atan2(wz - ez, wx - ex))

    def grip(self, jaw):
        """gripper joint (deg) for a pad gap: jaw = 2*(YG + L*sin(theta_ref + d) - E)."""
        fb = self.fb
        return math.degrees(math.asin((jaw / 2 + fb["E"] - fb["YG"]) / fb["L"])) - self.th_ref

    def q(self, tcp_x, tcp_z, pitch=0.0, roll=0.0, jaw=30.0):
        th1, th2 = self.ik(tcp_x, tcp_z, pitch)
        return dict(shoulder=th1, elbow=th2, wrist_pitch=pitch, wrist_roll=roll, gripper=self.grip(jaw))


class TaskSim:
    def __init__(self, variant="fourbar", viewer=True, speed=0.5):
        import mujoco
        self.mj = mujoco
        root = os.path.join(REPO, "sim", "arc_arm_%s" % variant)
        self.model = mujoco.MjModel.from_xml_path(os.path.join(root, "tasks.xml"))
        self.data = mujoco.MjData(self.model)
        self.limits = load_limits(variant)
        self.speed = speed
        m, d = self.model, self.data
        nm = lambda t, n: mujoco.mj_name2id(m, t, n)  # noqa: E731
        self.act = {j: nm(mujoco.mjtObj.mjOBJ_ACTUATOR, j) for j in ACT + ("base_x", "base_y")}
        self.qadr = {j: m.jnt_qposadr[nm(mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ACT + ("base_x", "base_y")}
        self.tcp = nm(mujoco.mjtObj.mjOBJ_SITE, "tcp")
        self.head = nm(mujoco.mjtObj.mjOBJ_BODY, "head")
        self.obj = {o: nm(mujoco.mjtObj.mjOBJ_BODY, o) for o in ("donut", "pipe")}
        self.weld = {o: nm(mujoco.mjtObj.mjOBJ_EQUALITY, "grasp_" + o) for o in ("donut", "pipe")}
        # start at STOW at the pick station: the arm's own stow keyframe (arc_arm.xml) for the 16 arm qpos
        key = ET.parse(os.path.join(root, "arc_arm.xml")).getroot().find("keyframe/key[@name='stow']")
        arm_q = [float(v) for v in key.get("qpos").split()]
        a0 = self.qadr["base_y"] + 1                               # arm qpos follow the two chassis slides
        d.qpos[a0:a0 + len(arm_q)] = arm_q
        self.q = {j: math.degrees(float(d.qpos[self.qadr[j]])) for j in ACT}
        self.base = [0.0, LANES["pick"]]
        d.qpos[self.qadr["base_y"]] = self.base[1]
        self._apply()
        mujoco.mj_forward(m, d)
        # geom categories for contact reporting
        chassis = nm(mujoco.mjtObj.mjOBJ_BODY, "chassis")
        robot = set()
        for b in range(m.nbody):
            p = b
            while p > 0 and p != chassis:
                p = m.body_parentid[p]
            if p == chassis:
                robot.add(b)
        self.cat = []
        for g in range(m.ngeom):
            b = m.geom_bodyid[g]
            name = mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_GEOM, g) or "geom%d" % g
            if b in robot:
                self.cat.append(("robot", mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_BODY, b)))
            elif b == self.obj["donut"]:
                self.cat.append(("donut", "donut"))
            elif b == self.obj["pipe"]:
                self.cat.append(("pipe", "pipe"))
            else:
                self.cat.append(("field", name.rstrip("0123456789_") or name))
        self.viewer = None
        if viewer:
            import mujoco.viewer
            self.viewer = mujoco.viewer.launch_passive(m, d)
        self.report, self.phase = [], None
        self.t_wall = time.perf_counter()
        self.video, self.task_label = None, ""

    def record(self, path, w=1280, h=720, fps=30, crf=26):
        """Offscreen H.264 video (imageio-ffmpeg): camera follows the chassis, phase captions, drives at 2x."""
        import imageio_ffmpeg
        mj, m = self.mj, self.model
        m.vis.global_.offwidth, m.vis.global_.offheight = max(w, m.vis.global_.offwidth), max(h, m.vis.global_.offheight)
        self.renderer = mj.Renderer(m, h, w)
        self.cam = mj.MjvCamera()
        self.cam.type = mj.mjtCamera.mjCAMERA_FREE
        self.cam.distance, self.cam.azimuth, self.cam.elevation = 1.55, 140.0, -20.0
        self.chassis_id = mj.mj_name2id(m, mj.mjtObj.mjOBJ_BODY, "chassis")
        self.fps, self.next_frame, self.frames = fps, 0.0, 0
        self.video = imageio_ffmpeg.write_frames(path, (w, h), fps=fps, codec="libx264", pix_fmt_out="yuv420p",
                                                 output_params=["-crf", str(crf), "-preset", "slow", "-movflags", "+faststart"])
        self.video.send(None)
        from PIL import ImageFont
        try:
            self.font = ImageFont.truetype("arialbd.ttf", 30)
            self.font_s = ImageFont.truetype("arial.ttf", 22)
        except OSError:
            self.font = self.font_s = ImageFont.load_default()

    def _frame(self):
        from PIL import Image, ImageDraw
        d = self.data
        self.cam.lookat[:] = d.xpos[self.chassis_id] + np.array([0.08, 0.0, 0.33])
        self.renderer.update_scene(d, camera=self.cam)
        img = Image.fromarray(self.renderer.render())
        dr = ImageDraw.Draw(img, "RGBA")
        name = self.phase["phase"] if self.phase else ""
        fast = name.startswith("drive")
        dr.rectangle([0, 0, img.width, 92], fill=(0, 0, 0, 150))
        dr.text((24, 12), "%s%s" % (self.task_label, name), font=self.font, fill=(255, 255, 255, 255))
        dr.text((24, 54), "ARC S2 Engineer arm, four-bar gripper  |  MuJoCo  |  t = %.1f s%s"
                % (d.time, "   (2x)" if fast else ""), font=self.font_s, fill=(210, 210, 210, 255))
        self.video.send(np.ascontiguousarray(np.asarray(img)))
        self.frames += 1

    def finish_video(self):
        if self.video is not None:
            self.video.close()
            self.video = None

    # ---------------------------------------------------------------- low level
    def _apply(self):
        """MIT-mode style control (as the DM-J4340s run): tau = kp*(q_des - q) + kd*(v_des - v). MuJoCo's position
        actuator gives kp*(ctrl - q) - kd*v, so the velocity feed-forward goes in as ctrl = q_des + (kd/kp)*v_des.
        Without it the damping term fights every commanded motion and the effort overstates what the drive needs."""
        vff = getattr(self, "v_des", {})
        for j in ACT:
            lo, hi, _ = self.limits[j]
            a = self.act[j]
            kp = float(self.model.actuator_gainprm[a, 0])
            kd = -float(self.model.actuator_biasprm[a, 2])
            q = math.radians(min(max(self.q[j], lo), hi))
            self.data.ctrl[a] = q + (kd / kp) * math.radians(vff.get(j, 0.0)) if kp > 0 else q
        self.data.ctrl[self.act["base_x"]], self.data.ctrl[self.act["base_y"]] = self.base

    def _stats_init(self):
        """Actuation statistics for the compliance report: per arm joint peak |torque|, RMS torque (thermal, vs the
        continuous rating), peak |speed|; per held object the force and moment the grasp must carry (the weld's
        constraint force: gravity + inertia, i.e. what the jaws have to supply)."""
        mj, m = self.mj, self.model
        self.dof = {j: m.jnt_dofadr[mj.mj_name2id(m, mj.mjtObj.mjOBJ_JOINT, j)] for j in ACT}
        self.stats = {j: dict(tau_max=0.0, tau_sq=0.0, vel_max=0.0, n=0, tau_at="", vel_at="") for j in ACT}
        self.hold = {o: dict(F_max=0.0, M_max=0.0, steps=0) for o in self.obj}

    def _stats_step(self):
        d = self.data
        for j in ACT:
            s = self.stats[j]
            t = float(d.actuator_force[self.act[j]])
            ph = self.phase["phase"] if self.phase else ""
            if abs(t) > s["tau_max"]:
                s["tau_max"], s["tau_at"] = abs(t), ph
            s["tau_sq"] += t * t
            s["n"] += 1
            v = abs(float(d.qvel[self.dof[j]]))
            if v > s["vel_max"]:
                s["vel_max"], s["vel_at"] = v, ph
        eqc = self.mj.mjtConstraint.mjCNSTR_EQUALITY
        for o, e in self.weld.items():
            if not d.eq_active[e]:
                continue
            rows = [i for i in range(d.nefc) if d.efc_type[i] == eqc and d.efc_id[i] == e]
            if len(rows) >= 6:
                f = np.array([d.efc_force[i] for i in rows[:3]])
                mmt = np.array([d.efc_force[i] for i in rows[3:6]])
                h = self.hold[o]
                h["F_max"] = max(h["F_max"], float(np.linalg.norm(f)))
                h["M_max"] = max(h["M_max"], float(np.linalg.norm(mmt)))
                h["steps"] += 1
                # the weld anchors at the object origin: move the wrench to the TCP, then into the gripper frame
                # (head axes = gripper axes: x roll axis, y across the jaws, z up), so the grip check can split
                # pad-normal force from shear and see the moment the jaws carry. Skip the attach transient.
                if h["steps"] * self.model.opt.timestep < GRIP_SETTLE_S:
                    continue
                R = np.array(d.xmat[self.head]).reshape(3, 3)
                m_tcp = mmt + np.cross(np.array(d.xpos[self.obj[o]]) - self.tcp_world(), f)
                fh, mh = R.T @ f, R.T @ m_tcp
                touch = any({self.cat[c.geom1][0], self.cat[c.geom2][0]} == {o, "field"} for c in d.contact[:d.ncon])
                h.setdefault("w", []).append(np.concatenate((fh, mh)))
                h.setdefault("ph", []).append(self.phase["phase"] if self.phase else "")
                h.setdefault("touch", []).append(touch)

    def actuation_summary(self):
        out = {}
        for j, s in self.stats.items():
            out[j] = dict(tau_peak_Nm=round(s["tau_max"], 3), tau_peak_in=s["tau_at"],
                          tau_rms_Nm=round(math.sqrt(s["tau_sq"] / max(1, s["n"])), 3),
                          speed_peak_rad_s=round(s["vel_max"], 3), speed_peak_in=s["vel_at"])
        hold = {}
        for o, h in self.hold.items():
            hold[o] = dict(force_peak_N=round(h["F_max"], 2), moment_peak_Nm=round(h["M_max"], 3),
                           held_s=round(h["steps"] * self.model.opt.timestep, 2), settle_s=GRIP_SETTLE_S)
            if not h.get("w"):
                continue
            w_all, ph_all, touch = np.abs(np.array(h["w"])), h["ph"], np.array(h["touch"])
            names = ("Fx", "Fy", "Fz", "Mx", "My", "Mz")
            # TCP wrench in the gripper frame, per component Fx Fy Fz (N) Mx My Mz (N*m), while the object is CARRIED
            # (no contact with the field: lift-off, touchdown and the release in the chute are contact events, not
            # holding cases): peak (and its phase), 99th percentile and median (the quasi-static hold)
            free = ~touch
            w, ph = w_all[free], [p for p, f in zip(ph_all, free) if f]
            hold[o]["carried_s"] = round(float(free.sum()) * self.model.opt.timestep, 2)
            hold[o]["tcp_wrench"] = {k: dict(peak=round(float(w[:, i].max()), 3), peak_in=ph[int(w[:, i].argmax())],
                                             p99=round(float(np.percentile(w[:, i], 99)), 3),
                                             median=round(float(np.median(w[:, i])), 3))
                                     for i, k in enumerate(names)}
            per = {}                                   # per phase peak, to see which motion sets the demand
            for row, p in zip(w, ph):
                per[p] = np.maximum(per.get(p, np.zeros(6)), row)
            hold[o]["tcp_wrench_by_phase"] = {p: [round(float(v), 3) for v in a] for p, a in per.items()}
            if touch.any():                            # the contact events, reported apart
                wc = w_all[touch]
                hold[o]["tcp_wrench_in_contact_peak"] = {k: round(float(wc[:, i].max()), 3) for i, k in enumerate(names)}
        return dict(joints=out, grasp_loads=hold)

    def tick(self):
        """One 10 ms control period: apply the setpoint, step the physics, log contacts, sync the viewer.
        The setpoint is ramped linearly across the physics substeps (first-order hold, as a drive interpolating its
        host stream): a 10 ms zero-order-hold step kicks the stiff joint PDs at 100 Hz, which showed up as a
        sign-alternating chatter in the grasp wrench (pipe moment 1.15 vs 0.5 N*m averaged) and in the torque peaks."""
        prev = np.array(self.data.ctrl)
        self._apply()
        new = np.array(self.data.ctrl)
        if not getattr(self, "_ctrl_started", False):          # first tick: no previous setpoint to ramp from
            prev, self._ctrl_started = new, True
        n = int(round(CTRL_DT / self.model.opt.timestep))
        if not hasattr(self, "stats"):
            self._stats_init()
        for i in range(n):
            self.data.ctrl[:] = prev + (new - prev) * (i + 1) / n
            self.mj.mj_step(self.model, self.data)
            self._stats_step()
            for c in self.data.contact[:self.data.ncon]:
                a, b = self.cat[c.geom1], self.cat[c.geom2]
                kinds = {a[0], b[0]}
                if kinds in ({"robot", "field"}, {"donut", "field"}, {"pipe", "field"}, {"robot", "donut"}, {"robot", "pipe"}):
                    if a[0] == "field" and b[0] != "field":
                        a, b = b, a
                    if a[1] == "chassis" and b[1] == "floor":
                        continue
                    k = "%s:%s / %s" % (a[0], a[1], b[1])
                    self.phase["contacts"][k] = max(self.phase["contacts"].get(k, 0.0), -1000.0 * c.dist)
        if self.video is not None and self.data.time >= self.next_frame:
            self._frame()
            fast = self.phase is not None and self.phase["phase"].startswith("drive")
            self.next_frame = self.data.time + (2.0 if fast else 1.0) / self.fps
        if self.viewer is not None:
            self.viewer.sync()
            lag = self.data.time - (time.perf_counter() - self.t_wall)
            if lag > 0:
                time.sleep(lag)

    def begin(self, name):
        self.phase = dict(phase=name, t0=round(self.data.time, 2), contacts={})
        self.report.append(self.phase)
        print("%-34s" % name, end="", flush=True)

    def end(self, **kw):
        q = {j: math.degrees(float(self.data.qpos[self.qadr[j]])) for j in ACT}
        self.phase.update(kw, t1=round(self.data.time, 2),
                          max_track_err_deg=round(max(abs(q[j] - min(max(self.q[j], self.limits[j][0]), self.limits[j][1]))
                                                      for j in ACT), 2))
        cs = self.phase["contacts"]
        print("%5.1f s  track %.2f deg  %s%s" % (self.phase["t1"] - self.phase["t0"], self.phase["max_track_err_deg"],
                                                ", ".join("%s %.1f mm" % kv for kv in sorted(cs.items())) or "no contacts",
                                                ("  " + " ".join("%s=%s" % kv for kv in kw.items())) if kw else ""))

    def running(self):
        return self.viewer is None or self.viewer.is_running()

    # ---------------------------------------------------------------- motions (host-side trajectory generation)
    def _stream(self, fn, T):
        steps = max(1, int(math.ceil(T / CTRL_DT)))
        for k in range(1, steps + 1):
            q, base = fn(min_jerk(k / steps))
            # desired joint speed (deg/s) for the velocity feed-forward: the setpoint's own rate of change
            self.v_des = {j: (q[j] - self.q[j]) / CTRL_DT for j in ACT}
            self.q, self.base = dict(q), list(base)
            self.tick()
            if not self.running():
                raise SystemExit("viewer closed")
        self.v_des = {}

    def joints(self, q_to, hold=0.3, speed=None):
        """Joint-space min-jerk move, timed by the joint speed limits (speed: fraction of them; default self.speed)."""
        q0, b = dict(self.q), list(self.base)
        sp = speed or self.speed
        T = max([0.3] + [1.875 * abs(q_to[j] - q0[j]) / (sp * self.limits[j][2]) for j in ACT])
        self._stream(lambda s: ({j: q0[j] + (q_to[j] - q0[j]) * s for j in ACT}, b), T)
        self.settle(hold)

    def path(self, wps, T, hold=0.3):
        """Follow waypoints [(q, base)] at a min-jerk pace over the whole path (piecewise linear between them)."""
        n = len(wps) - 1

        def at(s):
            x = s * n
            i = min(int(x), n - 1)
            u = x - i
            (qa, ba), (qb, bb) = wps[i], wps[i + 1]
            return {j: qa[j] + (qb[j] - qa[j]) * u for j in ACT}, [ba[0] + (bb[0] - ba[0]) * u, ba[1] + (bb[1] - ba[1]) * u]
        self._stream(at, T)
        self.settle(hold)

    def line(self, kin, p0, p1, pitch=0.0, roll=0.0, jaw=30.0, v=V_CART, n=40):
        """Straight TCP line p0 -> p1 (mm, x/z in the robot frame) through the IK."""
        L = math.dist(p0, p1)
        wps = [(kin.q(p0[0] + (p1[0] - p0[0]) * i / n, p0[1] + (p1[1] - p0[1]) * i / n, pitch, roll, jaw), self.base)
               for i in range(n + 1)]
        self.path(wps, max(0.3, 1.875 * L / v))

    def drive(self, x=None, y=None, hold=0.5):
        b0 = list(self.base)
        b1 = [b0[0] if x is None else x, b0[1] if y is None else y]
        q = dict(self.q)
        T = max(0.5, 1.875 * math.dist(b0, b1) / V_BASE)
        self._stream(lambda s: (q, [b0[0] + (b1[0] - b0[0]) * s, b0[1] + (b1[1] - b0[1]) * s]), T)
        self.settle(hold)

    def settle(self, t):
        for _ in range(int(t / CTRL_DT)):
            self.tick()

    # ---------------------------------------------------------------- kinematic grasp
    def tcp_world(self):
        return np.array(self.data.site_xpos[self.tcp])

    def grasp_error_mm(self, o):
        """donut: TCP to donut centre; pipe: TCP to the pipe axis (and inside its length)."""
        p = self.tcp_world()
        c = np.array(self.data.xpos[self.obj[o]])
        if o == "donut":
            return 1000 * float(np.linalg.norm(p - c))
        ax = np.array(self.data.xmat[self.obj[o]]).reshape(3, 3)[:, 2]
        v = p - c
        along = float(v @ ax)
        return 1000 * float(np.linalg.norm(v - along * ax)) if abs(along) < 0.25 else 1e9

    def attach(self, o, tol_mm=8.0):
        err = self.grasp_error_mm(o)
        if err > tol_mm:
            raise RuntimeError("grasp %s failed: object %.1f mm from the TCP (tolerance %.0f)" % (o, err, tol_mm))
        m, d, mj = self.model, self.data, self.mj
        h, b = self.head, self.obj[o]
        qh_inv = np.zeros(4)
        mj.mju_negQuat(qh_inv, d.xquat[h])
        rel_p = np.zeros(3)
        mj.mju_rotVecQuat(rel_p, d.xpos[b] - d.xpos[h], qh_inv)
        rel_q = np.zeros(4)
        mj.mju_mulQuat(rel_q, qh_inv, d.xquat[b])
        e = self.weld[o]
        m.eq_data[e, 0:3] = 0.0
        m.eq_data[e, 3:6] = rel_p
        m.eq_data[e, 6:10] = rel_q
        d.eq_active[e] = 1
        return round(err, 2)

    def detach(self, o):
        self.data.eq_active[self.weld[o]] = 0


# -------------------------------------------------------------------- tasks
def donut_task(sim, kin, tp, F):
    P = lambda n: tp["poses"][n]["joints_deg"]  # noqa: E731
    sim.begin("drive to the pick station")
    sim.drive(x=0.0, y=LANES["pick"])
    sim.end()
    # A straight joint-space move STOW -> DONUT_APPROACH sweeps the left jaw ~11 mm through the pole (real mesh,
    # found in this sim; CAD checks poses, not transits). Approach from behind the pole instead, jaws open, and
    # slide forward so the pole enters between the jaws (head parts above the jaws stay behind x 135.5 by design).
    sim.begin("pre-approach behind the pole")
    sim.joints(kin.q(20, 300, jaw=112))
    sim.end()
    sim.begin("slide in to DONUT_APPROACH")
    sim.line(kin, (20, 300), (130, 300), jaw=112)
    sim.end()
    sim.begin("descend onto the donut")
    sim.line(kin, (130, 300), (130, 228.5), jaw=112)
    sim.end()
    sim.begin("close jaws (donut grip 100)")
    sim.joints(P("DONUT_PICK"))
    err = sim.attach("donut")
    sim.end(grasp_err_mm=err)
    sim.begin("lift up the pole (strafe + roll)")
    L = F["donut_lift"]
    wps = [(s["joints_deg"], [0.0, LANES["pick"] + s["chassis_y"] / 1000.0]) for s in L]
    sim.path(wps, 1.875 * (L[-1]["tcp_z"] - L[0]["tcp_z"]) / V_LIFT)
    sim.end()
    for pose in ("DONUT_LIFT_ROLL+", "DONUT_LIFT_ROLL-", "DONUT_LIFT"):
        sim.begin(pose)
        sim.joints(P(pose))
        sim.end()
    sim.begin("drive to the scoring platform")
    sim.drive(y=LANES["place"])
    sim.end()
    px, pz = tp["poses"]["DONUT_PLACE"]["tcp_mm"][:2]          # CAD pose (arm.kinematics.POSES)
    sim.begin("move above the platform")
    sim.joints(kin.q(px, pz + 77.5, jaw=100))
    sim.end()
    sim.begin("lower to DONUT_PLACE")
    sim.line(kin, (px, pz + 77.5), (px, pz), jaw=100)
    sim.end()
    sim.begin("open jaws (release)")
    sim.detach("donut")
    sim.joints(kin.q(px, pz, jaw=112))
    sim.end()
    sim.begin("retreat up")
    sim.line(kin, (px, pz), (px, pz + 97.5), jaw=112)
    sim.end()
    sim.begin("STOW")
    sim.joints(P("STOW"))
    sim.end()
    d = sim.data.xpos[sim.obj["donut"]]
    on = abs(d[1] - LANES["place"]) < 0.15 and 0.0608 + 0.05 < d[0] < 0.3608 - 0.05 and abs(d[2] - 0.0625) < 0.005
    return dict(donut_final_mm=[round(1000 * float(v), 1) for v in (d[0], d[1] - LANES["place"], d[2])], donut_on_platform=bool(on))


def pipe_task(sim, kin, tp, F):
    P = lambda n: tp["poses"][n]["joints_deg"]  # noqa: E731
    sim.begin("drive to the bucket")
    sim.drive(x=0.0, y=LANES["bucket"])
    sim.end()
    sim.begin("PIPE_APPROACH (jaws 50)")
    sim.joints(P("PIPE_APPROACH"))
    sim.end()
    sim.begin("reach in to the pipe")
    sim.line(kin, (-30, 455), (40, 455), jaw=50)
    sim.end()
    sim.begin("close jaws (pipe grip 13.8)")
    sim.joints(P("PIPE_GRASP"))
    err = sim.attach("pipe")
    sim.end(grasp_err_mm=err)
    lx, lz = tp["poses"]["PIPE_LIFT"]["tcp_mm"][:2]
    sim.begin("lift straight out (PIPE_LIFT)")
    sim.line(kin, (40, 455), (lx, lz), jaw=13.8)
    sim.end()
    sim.begin("back away from the bucket")
    sim.drive(x=-0.45)
    sim.end()
    sim.begin("swing to PIPE_CHUTE (pitch 90)")
    # slow swing: the 500 mm pipe's inertia dominates the J3 torque (at the default 0.5 speed the DS3225 needed
    # ~2.1 N*m, ~85 % of its stall); a quarter of the speed limit roughly halves the inertial part
    sim.joints(P("PIPE_CHUTE"), speed=0.25)
    sim.end()
    ins = F["stations"]["chute"]["chute"]["insert_mm"] / 1000.0
    sim.begin("drive to the chute (pipe at the face)")
    sim.drive(x=-ins, y=LANES["chute"])
    sim.end()
    sim.begin("drive in: pipe 300 mm into the chute")
    sim.drive(x=0.0)
    sim.end()
    sim.begin("open jaws (release)")
    sim.detach("pipe")
    sim.joints(kin.q(150, 600, pitch=90, jaw=50))
    sim.end()
    sim.begin("back off")
    sim.drive(x=-ins)
    sim.end()
    sim.begin("STOW")
    sim.joints(P("STOW"))
    sim.settle(1.0)
    sim.end()
    p = sim.data.xpos[sim.obj["pipe"]]
    ax = np.array(sim.data.xmat[sim.obj["pipe"]]).reshape(3, 3)[:, 2]
    face = F["stations"]["chute"]["boxes"][0]["lo"][0] / 1000.0
    tip = max(p[0] + 0.25 * ax[0], p[0] - 0.25 * ax[0])
    return dict(pipe_centre_mm=[round(1000 * float(v), 1) for v in (p[0], p[1] - LANES["chute"], p[2])],
                pipe_tip_past_wall_face_mm=round(1000 * float(tip - face), 1), pipe_in_chute=bool(tip - face > 0.1))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("variant", nargs="?", default="fourbar")
    ap.add_argument("--task", default="both", choices=("donut", "pipe", "both"))
    ap.add_argument("--no-viewer", action="store_true", help="run headless, faster than real time")
    ap.add_argument("--speed", type=float, default=0.5, help="fraction of each joint's speed limit")
    ap.add_argument("--video", help="write an MP4 (1280x720, 30 fps, drives at 2x); needs imageio-ffmpeg")
    a = ap.parse_args()
    root = os.path.join(REPO, "sim", "arc_arm_%s" % a.variant)
    tp = json.load(open(os.path.join(root, "task_poses.json"), encoding="utf-8"))
    F = json.load(open(os.path.join(root, "task_field.json"), encoding="utf-8"))
    kin = Kin(a.variant)
    # the IK copy must reproduce the CAD poses (guards against drift from arm.kinematics.ik)
    worst = 0.0
    for s in F["donut_lift"]:
        th1, th2 = kin.ik(130.0, s["tcp_z"], 0.0)
        worst = max(worst, abs(th1 - s["joints_deg"]["shoulder"]), abs(th2 - s["joints_deg"]["elbow"]))
    for name in ("DONUT_PICK", "PIPE_GRASP"):
        worst = max(worst, abs(kin.grip(tp["poses"][name]["jaw_mm"]) - tp["poses"][name]["joints_deg"]["gripper"]))
    if worst > 1e-6:
        sys.exit("IK/jaw copy disagrees with CAD by %.2g deg" % worst)
    sim = TaskSim(a.variant, viewer=not a.no_viewer, speed=a.speed)
    if a.video:
        sim.record(a.video)
    sim.begin("settle at STOW (start)")
    sim.settle(0.5)
    sim.end()
    result = dict(variant=a.variant, ik_vs_cad_max_deg=worst)
    try:
        if a.task in ("donut", "both"):
            sim.task_label = "Donut: "
            result["donut"] = donut_task(sim, kin, tp, F)
            print("donut:", result["donut"])
        if a.task in ("pipe", "both"):
            sim.task_label = "Pipe: "
            result["pipe"] = pipe_task(sim, kin, tp, F)
            print("pipe:", result["pipe"])
        if a.video:
            sim.task_label = ""
            sim.begin("done: donut on the platform, pipe in the chute")
            sim.settle(2.0)
            sim.end()
    finally:
        sim.finish_video()
        result["actuation"] = sim.actuation_summary()
        result["phases"] = sim.report
        result["sim_time_s"] = round(sim.data.time, 2)
        json.dump(result, open(os.path.join(root, "task_run.json"), "w", encoding="utf-8"), indent=1)
    print("task run: %.1f s simulated -> %s" % (sim.data.time, os.path.join(root, "task_run.json")))
    if sim.viewer is not None:
        print("viewer stays open; close it to exit", flush=True)
        while sim.viewer.is_running():
            time.sleep(0.2)


if __name__ == "__main__":
    main()
