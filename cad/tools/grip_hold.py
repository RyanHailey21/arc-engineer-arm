# -*- coding: utf-8 -*-
"""
Does the four-bar gripper HOLD the donut and the pipe through the full ARC tasks?

Demand: the grasp wrench from the MuJoCo task run (sim/arc_arm_<variant>/task_run.json, actuation.grasp_loads):
gravity + inertia of the held object, moved to the TCP and expressed in the gripper frame (x roll axis / along
the fingers, y across the jaws, z up), peak per component after the weld-attach transient.
Capacity: per unit clamp force F (each jaw), from the pad geometry (params/pads.toml) and a pad friction
coefficient MU. Supply: the clamp force the STS3215 gives at its rated (continuous) and stall torque at that
grip, after the opening spring.  Also checks the spring itself: opening torque at full open (it must beat the
unpowered servo back-drive, to be bench-measured) and its wind at the tightest grip (<= 90 deg and its rated torque).

Load paths per unit clamp F (each jaw). A V flank or arc that wedges the jaws open needs, per unit of load
along it, a clamp of r = tan(b - atan MU) (b = the contact normal's angle off the load: 45 deg on the V flanks, ~72 on the donut arcs; friction on the flank
resists the slide that would wedge the jaws open). The jaws are gear-locked to each other, so a load across them
(Fy) only shifts clamp from one jaw to the other: it is held while the far jaw keeps contact, Fy < 2F.
  pipe  (axis along z, in the two 90 deg V-notches, four contact lines of length LC = pad height, a = 45 deg)
    Fx  along the fingers: wedges both flanks                         -> 2 / r
    Fy  across the jaws                                               -> 2
    Fz  axial slip: friction on 4 lines, total normal 2*sqrt2*F       -> 2*sqrt2*MU
    My  tilt in the pad plane (gravity once the pipe is horizontal): end flank loads, linear pressure on the
        compliant rubber -> clamp 1.5*r*M/LC per jaw                     -> LC / (1.5*r)
    Mx  tilt across the jaws: unloads one end of each pad at F*LC/6 per jaw -> LC / 3
    Mz  twist about its axis: friction at the pipe radius             -> 2*sqrt2*MU*r_pipe
  donut (lying flat, axis along z, held on its OD by the R50 arcs from the notch edge to WRAP, mean angle a_m)
    Fx  along the fingers: arc wedge                                  -> 2 / r(a_m)
    Fy  across the jaws                                               -> 2
    Fz  slip down: friction                                           -> 2*MU
    Mx  tilt about the finger axis: friction at the OD radius        -> 2*MU*R
    My  tilt about the jaw line (the coin-between-two-fingers axis): friction at the arc points' x offset
                                                                      -> 2*MU*R*mean|sin a|
    Mz  spin: friction at the OD radius                               -> 2*MU*R
Demand: per-component peak while the object is carried free; samples where it touches the field (lift-off from
the pole base or bucket floor, touchdown on the platform, the release in the chute) are contact events, not
holding cases, and the sim reports them apart (tcp_wrench_in_contact_peak).
Required clamp = sum of the component utilisations (linear interaction, conservative).
PASS: the RATED-torque clamp >= SF_RATED x required (the hold lasts ~20 s: continuous duty) and the STALL clamp
>= SF_STALL x required; WARN: holds within rated at SF >= 1 and at stall with SF_STALL, so the margin needs
short-duty torque above rated (thermal bench test); FAIL otherwise.  python -I cad/tools/grip_hold.py [--mu 0.5]
"""
import argparse
import json
import math
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, CAD)
os.environ.setdefault("GRIP", "FOURBAR")
import params  # noqa: E402

P = params.load("gripper_fourbar")
FB, SP = P["FB"], P["SPRING"]
SV = params.load("actuators")["STS3215"]          # the jaw servo
PAD = params.load("pads")
MU_DESIGN = 0.5          # neoprene sheet on PVC / PLA, dry: published 0.6-0.9; 0.5 for design, 0.3 as the low case
SF_RATED, SF_STALL = 1.5, 2.0
LC = FB["ZPAD"][1] - FB["ZPAD"][0]                 # pad height = contact line length on the pipe (46 mm)
R_PIPE = PAD["PIPE_OD"] / 2
R_DONUT = PAD["PAD_R"]
NOTCH_HALF_W = PAD["NOTCH"]                         # 90 deg V: half-width at the face = depth
A0 = math.asin(NOTCH_HALF_W / R_DONUT)              # donut contact starts at the notch edge ...
A1 = math.radians(PAD["WRAP"])                      # ... and ends at the arc wrap
O_PIPE = R_PIPE * math.sqrt(2) - PAD["NOTCH"]


def theta(jaw):
    return math.asin((jaw / 2 + FB["E"] - FB["YG"]) / FB["L"])


def clamp(jaw, torque):
    """clamp force per jaw (N) at servo torque (N*m), net of the opening spring."""
    th, th_open = theta(jaw), theta(112.0)
    t_sp = SP["rate_Nm_per_deg"] * (SP["preload_deg"] + math.degrees(th_open - th))
    return (torque - t_sp) / (2 * FB["L"] / 1000.0 * math.cos(th)), t_sp


def wedge(beta_deg, mu):
    """clamp (jaw-opening force) per unit load along the fingers, for a contact whose normal is beta_deg off the
    load direction: frictionless tan(beta); friction on the surface resists the slide -> tan(beta - atan MU)."""
    return max(1e-6, math.tan(math.radians(beta_deg) - math.atan(mu)))


def capacities(obj, mu):
    """N of load (or N*m) carried per N of clamp per jaw, per gripper-frame component."""
    if obj == "pipe":
        r = wedge(45.0, mu)                                  # V flank normal 45 deg off x
        return dict(Fx=2.0 / r, Fy=2.0, Fz=2 * math.sqrt(2) * mu,
                    Mx=LC / 1000.0 / 3, My=LC / 1000.0 / (1.5 * r), Mz=2 * math.sqrt(2) * mu * R_PIPE / 1000.0)
    R = R_DONUT / 1000.0
    s_mean = (math.cos(A0) - math.cos(A1)) / (A1 - A0)       # mean |sin| over the contact arc
    a_m = math.degrees(math.asin(s_mean))
    # the arc contact a_m off the jaw line has its normal 90 - a_m off the finger axis: a steep wedge
    return dict(Fx=2.0 / wedge(90.0 - a_m, mu), Fy=2.0, Fz=2 * mu, Mx=2 * mu * R, My=2 * mu * R * s_mean, Mz=2 * mu * R)


def demand(g):
    """per-component peak while the object is carried (the sim leaves out samples with field contact)."""
    rows = list(g["tcp_wrench_by_phase"].values())
    return [max(abs(r[i]) for r in rows) for i in range(6)]


def check(obj, load, jaw, mu):
    cap = capacities(obj, mu)
    comp = dict(zip(("Fx", "Fy", "Fz", "Mx", "My", "Mz"), demand(load)))
    need = {k: comp[k] / cap[k] for k in comp}
    f_req = sum(need.values())
    f_rated, t_sp = clamp(jaw, SV["rated_Nm"])
    f_stall, _ = clamp(jaw, SV["stall_Nm"])
    return dict(obj=obj, jaw=jaw, mu=mu, load=comp, need_N=need, F_req=f_req, F_rated=f_rated, F_stall=f_stall,
                spring_Nm=t_sp, sf_rated=f_rated / f_req if f_req else float("inf"),
                sf_stall=f_stall / f_req if f_req else float("inf"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mu", type=float, default=MU_DESIGN)
    a = ap.parse_args()
    run = os.path.join(os.path.dirname(CAD), "sim", "arc_arm_%s" % params.grip().lower(), "task_run.json")
    G = json.load(open(run, encoding="utf-8"))["actuation"]["grasp_loads"]
    if "tcp_wrench_by_phase" not in G["donut"]:
        print("task_run.json has no TCP-frame grasp loads: re-run cad/sim/tasks.py --no-viewer")
        return 2
    out = ["Grip hold check (tools/grip_hold.py): sim grasp wrench at the TCP vs clamp capacity; design MU %.2f, "
           "pass SF >= %.1f at RATED servo torque and >= %.1f at STALL" % (a.mu, SF_RATED, SF_STALL),
           "source: %s (per-phase peaks after the %.2f s attach transient; field-contact samples excluded)" % (os.path.relpath(run, os.path.dirname(CAD)),
                                                                    G["donut"]["settle_s"]), ""]
    rows, ok = [], True
    for obj, jaw in (("donut", 100.0), ("pipe", 2 * O_PIPE)):
        for mu in (a.mu, 0.3):
            r = check(obj, G[obj], jaw, mu)
            rows.append(r)
            if mu == a.mu:
                ok &= r["sf_rated"] >= SF_RATED and r["sf_stall"] >= SF_STALL
    for r in rows:
        tag = "design" if r["mu"] == a.mu else "low-friction case"
        out.append("%s, jaw %.1f, MU %.2f (%s)" % (r["obj"], r["jaw"], r["mu"], tag))
        out.append("  load at TCP: " + ", ".join("%s %.3f" % (k, v) for k, v in r["load"].items()) + "  (N, N*m)")
        out.append("  clamp needed per jaw: " + ", ".join("%s %.2f" % (k, v) for k, v in r["need_N"].items() if v)
                   + "  -> total %.2f N" % r["F_req"])
        out.append("  clamp available: %.1f N at rated (%.2f N*m, spring takes %.3f), %.1f N at stall -> SF %.2f rated, %.2f stall"
                   % (r["F_rated"], SV["rated_Nm"], r["spring_Nm"], r["F_stall"], r["sf_rated"], r["sf_stall"]))
    t_open = SP["rate_Nm_per_deg"] * SP["preload_deg"]
    wind = SP["preload_deg"] + math.degrees(theta(112.0) - theta(2 * O_PIPE))   # tightest grip: the pipe
    spring_ok = wind <= 90.0 + 1e-6 and SP["rate_Nm_per_deg"] * wind <= SP["max_torque_Nm"] + 1e-9
    out += ["", "opening spring %s: %.3f N*m at full open (must beat the unpowered servo back-drive: bench-measure it); "
            "wound %.0f deg at the pipe grip (limit 90 deg, %.3f N*m): %s"
            % (SP["pn"], t_open, wind, SP["max_torque_Nm"], "ok" if spring_ok else "OVER-WOUND")]
    ok &= spring_ok
    txt = "\n".join(out) + "\n"
    path = os.path.join(params.out_dir(), "grip_hold.txt")
    open(path, "w", encoding="utf-8").write(txt)
    js = os.path.join(params.out_dir(), "grip_hold.json")
    json.dump(rows, open(js, "w", encoding="utf-8"), indent=1)
    print(txt)
    d = [r for r in rows if r["mu"] == a.mu]
    # PASS: margin within the servo's continuous rating. WARN: the margin needs short-duty torque above rated (still
    # >= SF_STALL x the need at stall): a thermal bench test. FAIL: not even the stall torque gives SF_STALL.
    status = "PASS" if ok else ("WARN" if spring_ok and all(r["sf_stall"] >= SF_STALL and r["sf_rated"] >= 1.0 for r in d)
                                else "FAIL")
    params.record("grip_hold", status, [path, js, run], "; ".join(
        "%s SF %.1f rated / %.1f stall" % (r["obj"], r["sf_rated"], r["sf_stall"]) for r in d) + " (MU %.2f)" % a.mu)
    print("GRIP HOLD:", status)
    return 1 if status == "FAIL" else 0


if __name__ == "__main__":
    sys.exit(main())
