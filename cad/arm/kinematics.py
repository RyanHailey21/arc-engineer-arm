# -*- coding: utf-8 -*-
"""Kinematics and poses: joints, ik, placements (arm + active gripper), placed, part_mass_g, static_torques,
POSES / SEQUENCES / pose_q.
"""
from arm.core import *  # noqa: F401,F403
from arm.wrist import *  # noqa: F401,F403
from arm.bodies import *  # noqa: F401,F403


# ------------------------------------------------------------------ poses
def joints(th1, th2):
    S = (K["SX"], K["SZ"])
    E = add(S, u(th1, K["L2"]))
    D = add(E, u(th2, K["L3"]))
    B = add(E, u(th2, -K["L1"]))
    A = add(S, u(th2, -K["L1"]))
    v1 = u(K["V1_ANG"], K["V1_LEN"])
    return dict(S=S, E=E, D=D, A=A, B=B, G1=add(S, v1), v1=v1, Ev1=add(E, v1))


def ik(tcp_x, tcp_z, pitch):
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    wx = tcp_x - K["GRIP"] * c - K["DROP"] * s
    wz = tcp_z - K["GRIP"] * s + K["DROP"] * c
    dx, dz = wx - K["SX"], wz - K["SZ"]
    r = math.hypot(dx, dz)
    L2, L3 = K["L2"], K["L3"]
    if not abs(L2 - L3) <= r <= L2 + L3:
        raise ValueError("unreachable r=%.0f" % r)
    beta = math.acos((L2 ** 2 + r ** 2 - L3 ** 2) / (2 * L2 * r))
    th1 = math.degrees(math.atan2(dz, dx) + beta)
    E = add((K["SX"], K["SZ"]), u(th1, L2))
    th2 = math.degrees(math.atan2(wz - E[1], wx - E[0]))
    return th1, th2


def _pl(origin, ang):
    return App.Placement(V(origin[0], 0, origin[1]), App.Rotation(V(0, 1, 0), -ang))


def placements(th1, th2, pitch, roll=0.0, jaw=2 * O_REF):
    """World placement of every body.  The gripper module of the active variant (GRIPPERS[GRIP]) places
    its own bodies relative to the roll head Hd."""
    J = joints(th1, th2)
    G = _pl(J["D"], pitch)
    Hd = G.multiply(App.Placement(V(0, 0, 0), App.Rotation(V(1, 0, 0), roll), V(0, 0, ROLL_Z)))
    out = dict(GROUND=App.Placement(), UPPER=_pl(J["S"], th1), CRANK=_pl(J["S"], th2 + 180),
               ROD_AB=_pl(J["A"], th1), ROD1=_pl(J["G1"], th1), FOREARM=_pl(J["E"], th2),
               ROCKER=_pl(J["E"], 0), ROD2=_pl(add(J["E"], u(K["V2_ANG"], K["V2_LEN"])), th2),
               LEVEL=_pl(J["D"], 0), GRIPPER=G, HEAD=Hd)
    out.update(GRIPPERS[GRIP]["placements"](Hd, jaw))
    return out


def placed(bodies, th1, th2, pitch, roll=0.0, jaw=2 * O_REF, which="chk"):
    plc = placements(th1, th2, pitch, roll, jaw)
    out = []
    for bname, parts in bodies.items():
        for p in parts:
            src = p.chk if which == "chk" else p.vis
            s_ = src.copy()
            s_.Placement = plc[bname].multiply(src.Placement)
            out.append((bname, p, s_))
    return out


def part_mass_g(p):
    if p.kind == "CAT":
        m = CAT[p.src]["mass"] if p.src in CAT else 0
        return m
    return p.chk.Volume / 1000.0 * MAT.get(p.kind, 1.0)


def static_torques(bodies, th1, th2, pitch, roll=0.0, payload_g=300.0, payload_arm=None, jaw=2 * O_REF):
    """Static torques J1..J4 (N*m) by virtual work on the modelled masses."""
    coms = {}
    for bn, parts in bodies.items():
        for p in parts:
            m = part_mass_g(p) / 1000.0
            if m <= 0:
                continue
            try:
                c = p.chk.CenterOfMass if hasattr(p.chk, "CenterOfMass") else p.chk.BoundBox.Center
            except Exception:
                c = p.chk.BoundBox.Center
            coms.setdefault(bn, []).append((m, c))

    def U(q):
        plc = placements(*q, jaw=jaw)
        tot = 0.0
        for bn, lst in coms.items():
            if bn == "GROUND":
                continue
            for m, cm in lst:
                tot += m * 9.81 * plc[bn].multVec(cm).z / 1000.0
        tcp = plc["HEAD"].multVec(V(K["GRIP"], 0, -K["DROP"] - (payload_arm or 0.0)))
        return tot + payload_g / 1000.0 * 9.81 * tcp.z / 1000.0
    q = [th1, th2, pitch, roll]
    tau = []
    for i in range(4):
        qp, qm = list(q), list(q)
        qp[i] += 0.05
        qm[i] -= 0.05
        tau.append((U(qp) - U(qm)) / math.radians(0.1))
    return tau


POSES = {
    "STOW": dict(q=(160.0, 10.0, 0.0, 0.0), jaw=30.0),
    "DONUT_APPROACH": dict(tcp=(130, 300, 0), jaw=112.0),
    "DONUT_PICK": dict(tcp=(130, 228.5, 0), jaw=100.0),
    "DONUT_LIFT": dict(tcp=(130, 720, 0), jaw=100.0),
    "DONUT_LIFT_ROLL+": dict(tcp=(130, 720, 0), roll=25.0, jaw=100.0),
    "DONUT_LIFT_ROLL-": dict(tcp=(130, 720, 0), roll=-25.0, jaw=100.0),
    "DONUT_PLACE": dict(tcp=(300, 62.5, 0), jaw=100.0),   # x 300 (was 210): keeps the elbow >= -82.6 deg for the stage-2 parallelogram
    "PIPE_APPROACH": dict(tcp=(-30, 455, 0), jaw=50.0),
    "PIPE_GRASP": dict(tcp=(40, 455, 0), jaw=PIPE_JAW),
    "PIPE_GRASP_ROLL+": dict(tcp=(40, 455, 0), roll=30.0, jaw=PIPE_JAW),
    "PIPE_GRASP_ROLL-": dict(tcp=(40, 455, 0), roll=-30.0, jaw=PIPE_JAW),
    "PIPE_LIFT": dict(tcp=(40, 740, 0), jaw=PIPE_JAW),    # z 740 (was 790): elbow <= 48 deg; pipe bottom still 37 mm over the bucket rim
    "PIPE_CHUTE": dict(tcp=(150, 600, 90), jaw=PIPE_JAW),
    "PIPE_CHUTE_ROLL90": dict(tcp=(150, 600, 90), roll=90.0, jaw=PIPE_JAW),
}
SEQUENCES = {
    "donut": ["STOW", "DONUT_APPROACH", "DONUT_PICK", "DONUT_LIFT", "DONUT_LIFT_ROLL+", "DONUT_LIFT_ROLL-",
              "DONUT_LIFT", "DONUT_PLACE", "STOW"],
    "pipe": ["STOW", "PIPE_APPROACH", "PIPE_GRASP_ROLL-", "PIPE_GRASP_ROLL+", "PIPE_GRASP", "PIPE_LIFT",
             "PIPE_CHUTE", "PIPE_CHUTE_ROLL90", "PIPE_CHUTE", "STOW"],
}


def pose_q(name):
    p = POSES[name]
    if "q" in p:
        return p["q"], p["jaw"]
    th1, th2 = ik(*p["tcp"])
    return (th1, th2, p["tcp"][2], p.get("roll", 0.0)), p["jaw"]
