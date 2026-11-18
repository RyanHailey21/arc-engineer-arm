"""Joint command interface: host-side trajectory generation + fixed-rate setpoint streaming.

This mirrors how the real arm is driven. The DM-J4340 joints (MIT mode over CAN) and the DS3225 / STS3215 servos
all take streamed position setpoints and run their own control loops; nothing on the robot executes a whole
trajectory. So planning lives here, on the host, and only the backend changes between simulation and hardware:

    Commander (backend)    send(q_deg) / state_deg()
      GazeboCommander      gz-transport: /arc_arm/<joint>/cmd_pos (gz.msgs.Double, rad), reads /joint_state
      (HardwareCommander)  later: CAN (DM-J4340 MIT mode) + Feetech/servo bus, same two methods

    stream_move(cmd, q_from, q_to, ...)   minimum-jerk move, timed by the joint speed limits, streamed at rate_hz

Limits (position + speed) come from the generated model (robot_spec.json / model.urdf), so sim and planner agree.
Every setpoint is clamped to the joint limits before it is sent.
"""
import json
import math
import os
import threading
import time
import xml.etree.ElementTree as ET

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ACT = ("shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper")


def load_limits(variant="fourbar"):
    """-> {joint: (lo_deg, hi_deg, vmax_deg_s)} from the generated model."""
    root = os.path.join(REPO, "sim", "arc_arm_%s" % variant)
    spec = json.load(open(os.path.join(root, "robot_spec.json"), encoding="utf-8"))
    vel = {}
    for j in ET.parse(os.path.join(root, "model.urdf")).getroot().iter("joint"):
        lim = j.find("limit")
        if j.get("name") in ACT and lim is not None:
            vel[j.get("name")] = math.degrees(float(lim.get("velocity")))
    return {j: (spec["limits_deg"][j][0], spec["limits_deg"][j][1], vel[j]) for j in ACT}


class Commander:
    """Backend interface. Angles in degrees, simulator/CAD joint convention."""
    limits = {}

    def clamp(self, q):
        return {j: min(max(q[j], self.limits[j][0]), self.limits[j][1]) for j in ACT}

    def send(self, q_deg):
        raise NotImplementedError

    def state_deg(self):
        raise NotImplementedError


class GazeboCommander(Commander):
    """Streams setpoints to the Gazebo JointPositionControllers over gz-transport (one persistent node)."""

    def __init__(self, variant="fourbar"):
        from gz.msgs10.double_pb2 import Double
        from gz.msgs10.model_pb2 import Model
        from gz.transport13 import Node
        self.limits = load_limits(variant)
        self._Double = Double
        self.node = Node()
        self.pubs = {j: self.node.advertise("/arc_arm/%s/cmd_pos" % j, Double) for j in ACT}
        self._q, self._lock = {}, threading.Lock()
        topic = self._topic = "/world/arc_arm/model/arc_arm_%s/joint_state" % variant
        if not self.node.subscribe(Model, topic, self._on_state):
            raise RuntimeError("cannot subscribe to " + topic)
        # gz-transport discovery takes ~1 s: messages published before a controller connects are dropped
        t0 = time.time()
        while not all(p.has_connections() for p in self.pubs.values()):
            if time.time() - t0 > 10:
                missing = [j for j, p in self.pubs.items() if not p.has_connections()]
                raise RuntimeError("no controller listening on cmd_pos for %s - is the world running?" % missing)
            time.sleep(0.05)

    def _on_state(self, msg):
        with self._lock:
            for jt in msg.joint:
                if jt.name in ACT:
                    self._q[jt.name] = math.degrees(jt.axis1.position)

    def send(self, q_deg):
        q = self.clamp(q_deg)
        for j in ACT:
            m = self._Double()
            m.data = math.radians(q[j])
            self.pubs[j].publish(m)

    def state_deg(self):
        with self._lock:
            return dict(self._q)

    def close(self):
        """Unsubscribe before the interpreter exits: the gz-transport13 Python bindings segfault (exit 139) if a
        subscription callback is still live during interpreter teardown."""
        self.node.unsubscribe(self._topic)
        time.sleep(0.1)


class MujocoCommander(Commander):
    """Runs the MuJoCo model in real time in a background thread with the native viewer; send() sets the position
    actuator targets (same kp/kv as the MJCF actuators: the DM-J4340 MIT-mode law, tau = kp*e + kd*de).
    scene="free": scene.xml without the donut-pick station (lower tier + donut), for whole task sequences;
    scene="pick": scene.xml as generated (pick station)."""

    def __init__(self, variant="fourbar", scene="free", viewer=True):
        import mujoco
        import mujoco.viewer  # noqa: F401  (submodule; not imported by "import mujoco")
        self.mj = mujoco
        self.limits = load_limits(variant)
        root = os.path.join(REPO, "sim", "arc_arm_%s" % variant)
        spec = mujoco.MjSpec.from_file(os.path.join(root, "scene.xml"))
        if scene == "free":
            spec.delete(spec.geom("lower_tier"))
            spec.delete(spec.body("donut"))
        self.model = spec.compile()
        self.data = mujoco.MjData(self.model)
        k = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_KEY, "stow")
        mujoco.mj_resetDataKeyframe(self.model, self.data, k)
        mujoco.mj_forward(self.model, self.data)
        self._act = {j: mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_ACTUATOR, j) for j in ACT}
        self._qadr = {j: self.model.jnt_qposadr[mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_JOINT, j)] for j in ACT}
        self._lock = threading.Lock()
        self._run = True
        self.viewer = mujoco.viewer.launch_passive(self.model, self.data) if viewer else None
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _loop(self):
        dt = self.model.opt.timestep
        t0, n = time.perf_counter(), 0
        while self._run and (self.viewer is None or self.viewer.is_running()):
            with self._lock:
                for _ in range(max(1, int(0.005 / dt))):          # 5 ms of physics per viewer frame
                    self.mj.mj_step(self.model, self.data)
                    n += 1
            if self.viewer is not None:
                self.viewer.sync()
            time.sleep(max(0.0, t0 + n * dt - time.perf_counter()))  # lock to real time

    def running(self):
        return self._run and (self.viewer is None or self.viewer.is_running())

    def send(self, q_deg):
        q = self.clamp(q_deg)
        with self._lock:
            for j in ACT:
                self.data.ctrl[self._act[j]] = math.radians(q[j])

    def state_deg(self):
        with self._lock:
            return {j: math.degrees(float(self.data.qpos[self._qadr[j]])) for j in ACT}

    def close(self):
        self._run = False
        self._thread.join(timeout=2)
        if self.viewer is not None:
            self.viewer.close()


def min_jerk(s):
    """Minimum-jerk blend 0 -> 1 for s in [0, 1] (zero velocity and acceleration at both ends)."""
    s = min(max(s, 0.0), 1.0)
    return s * s * s * (10 - 15 * s + 6 * s * s)


def move_duration(cmd, q_from, q_to, speed_frac=0.5, t_min=0.3):
    """Shortest min-jerk duration that keeps every joint under speed_frac of its speed limit
    (a min-jerk move's peak speed is 1.875 * distance / duration)."""
    return max([t_min] + [1.875 * abs(q_to[j] - q_from[j]) / (speed_frac * cmd.limits[j][2]) for j in ACT])


def stream_move(cmd, q_from, q_to, rate_hz=100.0, speed_frac=0.5):
    """Stream a min-jerk move at a fixed rate; returns (duration_s, achieved_rate_hz)."""
    T = move_duration(cmd, q_from, q_to, speed_frac)
    dt = 1.0 / rate_hz
    t0 = time.perf_counter()
    n = 0
    while True:
        t = time.perf_counter() - t0
        b = min_jerk(t / T)
        cmd.send({j: q_from[j] + (q_to[j] - q_from[j]) * b for j in ACT})
        n += 1
        if t >= T:
            break
        time.sleep(max(0.0, t0 + n * dt - time.perf_counter()))
    el = time.perf_counter() - t0
    return T, n / el if el > 0 else 0.0
