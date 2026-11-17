# -*- coding: utf-8 -*-
"""
Four-bar gripper grip-force budget from params/gripper_fourbar.toml ([FB], [SERVO], [SPRING], [GRIP_REQ]) and
params/pads.toml.  Pure Python (no FreeCAD):  python -I cad/tools/grip_budget.py
-> cad/out/fourbar/grip_budget.txt + an evidence record.

Mechanics (direct drive, the two drive links tied 1:1 by the sector gears):
  jaw half-gap o = y_cp - E with y_cp = YG + L sin(theta)  ->  d(o)/d(theta) = L cos(theta) per jaw
  virtual work: servo torque into both jaws  T_servo - T_spring = 2 F L cos(theta)
  spring (on the right drive pivot) winds as the jaws close: T_spring = k (preload + theta_open - theta)
Check: the clamp force each object needs is available within the servo's RATED (continuous) torque, and its
STALL torque gives the margin.  The power-off release needs T_spring(open) > unpowered back-drive torque of the
servo, which is NOT known - it has to be bench-measured (the spring is swappable on the same arbor).
"""
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
os.environ.setdefault("GRIP", "FOURBAR")
import params  # noqa: E402

P = params.load("gripper_fourbar")
FB, SV, SP, REQ = P["FB"], P["SERVO"], P["SPRING"], P["GRIP_REQ"]
PAD = params.load("pads")
O_PIPE = PAD["PIPE_OD"] / 2 * math.sqrt(2) - PAD["NOTCH"]


def theta(jaw):
    return math.degrees(math.asin((jaw / 2 + FB["E"] - FB["YG"]) / FB["L"]))


def main():
    th_open = theta(112.0)
    rows, ok = [], True
    out = ["Four-bar grip budget (params/gripper_fourbar.toml); servo rated %.2f / stall %.2f N*m; spring %s, "
           "k %.5f N*m/deg, preload %.0f deg at open" % (SV["rated_Nm"], SV["stall_Nm"], SP["pn"], SP["rate_Nm_per_deg"], SP["preload_deg"]),
           "", "%-22s %6s %7s %8s %9s %9s %9s %8s" % ("case", "jaw", "theta", "spring", "need F/jaw", "T_servo", "% rated", "% stall")]
    cases = [("open (release)", 112.0, 0.0), ("donut", 100.0, REQ["donut"]), ("pipe, wrist rolled 90", 2 * O_PIPE, REQ["pipe"]),
             ("pipe, friction only", 2 * O_PIPE, REQ["pipe_friction_only"])]
    for name, jaw, F in cases:
        th = theta(jaw)
        wind = SP["preload_deg"] + th_open - th
        t_sp = SP["rate_Nm_per_deg"] * wind
        t_need = t_sp + 2 * F * FB["L"] / 1000.0 * math.cos(math.radians(th))
        pr, ps = 100 * t_need / SV["rated_Nm"], 100 * t_need / SV["stall_Nm"]
        if wind > 90.0 + 1e-6 or t_sp > SP["max_torque_Nm"] + 1e-9:
            ok = False
            name += "  ** spring over-wound **"
        out.append("%-22s %6.1f %7.1f %8.3f %9.1f %9.3f %8.0f%% %7.0f%%" % (name, jaw, th, t_sp, F, t_need, pr, ps))
        rows.append(dict(case=name, jaw=jaw, theta=th, spring_Nm=t_sp, F=F, T=t_need, pct_rated=pr, pct_stall=ps))
    f_max_rated = (SV["rated_Nm"] - rows[2]["spring_Nm"]) / (2 * FB["L"] / 1000.0 * math.cos(math.radians(rows[2]["theta"])))
    f_max_stall = (SV["stall_Nm"] - rows[2]["spring_Nm"]) / (2 * FB["L"] / 1000.0 * math.cos(math.radians(rows[2]["theta"])))
    out += ["", "max clamp per jaw at the pipe grip: %.1f N within rated torque, %.1f N at stall" % (f_max_rated, f_max_stall),
            "opening torque at full open (must beat the unpowered servo back-drive, to be bench-measured): %.3f N*m" % rows[0]["spring_Nm"]]
    within = [r["case"] for r in rows[1:3] if r["pct_rated"] <= 100]
    over = [r["case"] for r in rows[1:] if r["pct_rated"] > 100]
    out.append("within rated torque: %s; above rated (short-duty, below stall): %s" % (", ".join(within) or "-", ", ".join(over) or "-"))
    if any(r["pct_stall"] > 100 for r in rows):
        ok = False
    txt = "\n".join(out) + "\n"
    rep = os.path.join(params.out_dir(), "grip_budget.txt")
    open(rep, "w", encoding="utf-8").write(txt)
    print(txt)
    status = "PASS" if ok and rows[1]["pct_rated"] <= 100 and rows[2]["pct_stall"] <= 100 else "FAIL"
    if status == "PASS" and over:
        status = "WARN"
    params.record("grip_budget", status, [rep], "pipe %.0f%% of rated / %.0f%% of stall; open spring %.2f N*m"
                  % (rows[2]["pct_rated"], rows[2]["pct_stall"], rows[0]["spring_Nm"]))
    print("GRIP BUDGET:", status)
    return 0


if __name__ == "__main__":
    sys.exit(main())
