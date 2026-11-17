"""
Kinematic + static sizing check for the ARC Engineer arm adapted from
Wang et al., "Lightweight Robotic Arm Based on a Load-Adaptive Hoisting
Mechanism", Actuators 2025, 14, 71.

Paper arm (planar palletizer, both joint motors at the base, parallelogram
level-keeping): l1 = 60 mm crank, l2 = 140 mm upper arm, l3 = 205 mm forearm,
reach 320 mm, max height 150 mm.  That is far short of what the ARC donut and
pipe tasks need, so the same topology is scaled and a wrist-pitch DOF added.

Frame: x forward from the chassis front bumper, z up from the Battlefield floor.
Run:  python analysis/arm_sizing.py
"""
import math

# ---------------- design parameters (keep in sync with cad/build_arm.py) ----
SHOULDER = (-160.0, 200.0)   # shoulder pivot (x, z) mm
L1 = 80.0                    # crank / parallelogram offset (paper l1 = 60)
L2 = 340.0                   # upper arm, shoulder -> elbow (paper l2 = 140)
L3 = 350.0                   # forearm, elbow -> wrist pitch axis (paper l3 = 205)
GRIP = 95.0                  # wrist pitch axis -> grip centre along fingers
DROP = 20.0                  # grip centre below pitch axis (gripper local -z)

# joint limits (deg)
TH1_LIM = (10.0, 165.0)      # upper-arm angle from +x
INTERIOR_LIM = (30.0, 165.0) # angle between upper arm & forearm (paper: >= 0.524 rad)

# masses (kg) - carbon tube / plate + PLA, scaled ~2x from paper Table 1
M_UPPER, M_FORE, M_WRIST, M_PAYLOAD = 0.28, 0.22, 0.40, 0.30
G = 9.81

# ---------------- ARC task targets (grip centre, floor frame) ---------------
# pitch 0  = fingers point forward (horizontal, jaws close sideways)
# pitch 90 = fingers point up (pipe held at its end now points forward)
TARGETS = {
    "A  donut pick on pole base (216+12.5)":       (130, 228.5, 0),
    "B  donut lifted over 456 mm pole (+40 clr)":  (130, 720, 0),
    "B2 donut over pole, reach +60 (zig-zag)":     (190, 720, 0),
    "C  donut placed on Scoring Area (50+12.5)":   (210, 63, 0),
    "D1 pipe top grasp, near side of bucket":      (40, 451, 0),
    "D2 pipe top grasp, far side of bucket":       (180, 451, 0),
    "E  pipe lifted clear of 250 mm bucket rim":   (40, 790, 0),
    "F1 pipe horizontal at chute height 600":      (0, 600, 90),
    "F2 pipe horizontal at chute, extended":       (150, 600, 90),
}


def wrist_from_grip(x, z, pitch):
    c, s = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
    return x - GRIP * c - DROP * s, z - GRIP * s + DROP * c


def ik(xw, zw):
    """Elbow-up 2R IK. Returns (th1, th2_abs, interior) in deg or None."""
    dx, dz = xw - SHOULDER[0], zw - SHOULDER[1]
    r = math.hypot(dx, dz)
    if r > L2 + L3 or r < abs(L2 - L3):
        return None
    c_int = (L2**2 + L3**2 - r**2) / (2 * L2 * L3)
    interior = math.degrees(math.acos(max(-1, min(1, c_int))))
    alpha = math.atan2(dz, dx)
    beta = math.acos((L2**2 + r**2 - L3**2) / (2 * L2 * r))
    th1 = math.degrees(alpha + beta)              # elbow-up branch
    th2 = th1 - (180 - interior)                  # forearm absolute angle
    return th1, th2, interior, r


def torques(th1, th2, xg):
    """Static joint torques (N*m). Parallelogram => elbow motor at base sees
    only forearm+wrist+payload moment about the elbow."""
    t1, t2 = math.radians(th1), math.radians(th2)
    ex = L2 * math.cos(t1)                       # elbow x rel shoulder
    fx = 0.5 * L3 * math.cos(t2)                 # forearm CoM rel elbow
    wx = L3 * math.cos(t2)                       # wrist rel elbow
    gx = xg - (SHOULDER[0] + ex)                 # grip rel elbow
    tau2 = G * (M_FORE * fx + M_WRIST * wx + M_PAYLOAD * gx) / 1000
    tau1 = G * (M_UPPER * 0.5 * ex + (M_FORE + M_WRIST + M_PAYLOAD) * ex) / 1000
    return tau1, tau2


def main():
    print(f"L1={L1} L2={L2} L3={L3} grip={GRIP} shoulder={SHOULDER}")
    print(f"{'target':46s} {'r':>6s} {'th1':>7s} {'th2':>7s} {'int':>6s} "
          f"{'tau1':>6s} {'tau2':>6s}  ok")
    worst1 = worst2 = 0
    all_ok = True
    for name, (x, z, p) in TARGETS.items():
        xw, zw = wrist_from_grip(x, z, p)
        sol = ik(xw, zw)
        if sol is None:
            print(f"{name:46s} UNREACHABLE"); all_ok = False; continue
        th1, th2, inter, r = sol
        ok = TH1_LIM[0] <= th1 <= TH1_LIM[1] and INTERIOR_LIM[0] <= inter <= INTERIOR_LIM[1]
        all_ok &= ok
        t1, t2 = torques(th1, th2, x)
        worst1, worst2 = max(worst1, abs(t1)), max(worst2, abs(t2))
        print(f"{name:46s} {r:6.0f} {th1:7.1f} {th2:7.1f} {inter:6.1f} "
              f"{t1:6.2f} {t2:6.2f}  {'OK' if ok else 'LIMIT'}")
    # absolute worst case: everything horizontal, fully stretched forward
    t1, t2 = torques(0, 0, SHOULDER[0] + L2 + L3 + GRIP)
    print(f"\nWorst static torque over task poses: shoulder {worst1:.2f} N*m, elbow {worst2:.2f} N*m")
    print(f"Fully-stretched horizontal (envelope): shoulder {t1:.2f} N*m, elbow {t2:.2f} N*m")
    print(f"Paper joint motor peak torque: 7 N*m  -> {'adequate' if t1 < 7*0.6 else 'NEEDS bigger motor / gearing / gravity spring'} "
          f"(60 % peak rule)")

    # Gripper force: pipe held at its end, horizontal cantilever
    m_pipe = 0.33 * 0.5          # 3/4" Sch40 PVC ~0.33 kg/m
    arm = 0.25 - 0.03            # pipe CoM to grip centre (m)
    M = m_pipe * G * arm
    mu, pad = 0.8, 0.060         # silicone pad, 60 mm pad length along pipe
    F_needed = 2.0 * M / (mu * pad / 2)  # 2 pads, torsional friction ~ mu*F*pad/4 each, SF 2
    print(f"\nPipe cantilever moment {M:.2f} N*m -> jaw force needed ~{F_needed:.0f} N (SF 2, mu {mu})")
    # LAHM: rope tension at r_min, jaw linkage ratio r2/r1
    tau_m, r_min, r_max, ratio = 1.0, 0.010, 0.0284, 0.6
    print(f"LAHM (paper motor 1 N*m): high-speed mode {tau_m/r_max*ratio:.0f} N, "
          f"high-force mode {tau_m/r_min*ratio:.0f} N jaw force (r2/r1 = {ratio})")

    # stow height (Z-fold): upper arm back at TH1_LIM max, forearm folded to min interior
    th1 = math.radians(TH1_LIM[1]); th2 = th1 - math.radians(180 - INTERIOR_LIM[0])
    ez = SHOULDER[1] + L2 * math.sin(th1)
    wz = ez + L3 * math.sin(th2)
    print(f"\nStowed (Z-fold) top of arm ~{max(ez, wz, SHOULDER[1]) + 40:.0f} mm "
          f"(central limbo 420, side limbo 300)")
    print("\nALL TARGETS REACHABLE" if all_ok else "\nSOME TARGETS FAIL")


if __name__ == "__main__":
    main()
