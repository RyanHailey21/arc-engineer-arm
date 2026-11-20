"""Plots for cad/docs/compliance_report.md, from the check results already in the repo.

    "%LOCALAPPDATA%/Programs/FreeCAD 1.1/bin/python.exe" -I cad/docs/make_plots.py      (any Python with numpy + matplotlib)

Inputs:  cad/out/fourbar/quick.json (static torques), cad/out/fourbar/grip_hold.json (clamp margins),
         sim/arc_arm_fourbar/task_log.npz (from: <sim python> cad/sim/tasks.py --no-viewer --log sim/arc_arm_fourbar/task_log.npz)
Outputs: cad/docs/figures/plot_*.png
"""
import json
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(REPO, "cad", "docs", "figures")
os.makedirs(OUT, exist_ok=True)

# reference light palette (dataviz skill): categorical slots in fixed order, text inks, recessive grid
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID,
                     "grid.linewidth": 0.8, "axes.axisbelow": True, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.facecolor": SURF, "axes.facecolor": SURF,
                     "savefig.facecolor": SURF, "legend.frameon": False, "lines.linewidth": 1.4})

# actuator ratings (report section 2/3): (label, continuous or 50 %-of-stall limit, peak/stall)
RATING = {"shoulder": ("J1 shoulder, STS3215 x3", 2.79, 8.38), "elbow": ("J2 elbow, STS3215 x3", 2.79, 8.38),
          "wrist_pitch": ("J3 wrist pitch, STS3215", 0.98, 2.94), "wrist_roll": ("J4 wrist roll, STS3215", 0.98, 2.94),
          "gripper": ("Gripper, STS3215", 0.98, 2.94)}


def save(fig, name):
    fig.savefig(os.path.join(OUT, name), dpi=150, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def static_torque():
    q = json.load(open(os.path.join(REPO, "cad", "out", "fourbar", "quick.json")))["mass_torque"]
    poses = [p["pose"] for p in q["poses"]]
    tau = np.abs(np.array([p["tau"] for p in q["poses"]]))
    lim = np.array([8.38, 8.38, 2.94, 2.94])               # stall at the joint (J1/J2 through the 3:1 stage)
    util = 100 * tau / lim
    fig, ax = plt.subplots(figsize=(10, 4.2))
    x = np.arange(len(poses))
    w = 0.2
    names = ("J1 shoulder (of 8.4 N·m stall)", "J2 elbow (of 8.4 N·m stall)", "J3 wrist pitch (of 2.94 N·m stall)",
             "J4 wrist roll (of 2.94 N·m stall)")
    for i, (c, n) in enumerate(zip((S1, S2, S3, S4), names)):
        ax.bar(x + (i - 1.5) * w, util[:, i], w * 0.9, color=c, label=n)
    ax.axhline(100, color=INK, lw=1.2)
    ax.text(len(poses) - 0.5, 101, "stall", ha="right", va="bottom", color=INK, fontsize=9)
    ax.axhline(50, color=INK2, lw=1.0, ls="--")
    ax.text(len(poses) - 0.5, 51, "servo limit: 50 % of stall", ha="right", va="bottom", color=INK2, fontsize=9)
    ax.set_xticks(x, [p.replace("_", " ") for p in poses], rotation=35, ha="right", fontsize=8.5)
    ax.set_ylabel("static torque, % of stall")
    ax.set_ylim(0, 135)
    ax.set_title("Static holding torque at every task pose (object in the jaws)", loc="left", color=INK)
    ax.legend(ncol=2, fontsize=8.5, loc="upper left")
    save(fig, "plot_static_torque.png")


def grip_margin():
    g = json.load(open(os.path.join(REPO, "cad", "out", "fourbar", "grip_hold.json")))
    fig, ax = plt.subplots(figsize=(8, 3.8))
    rows = [(r["obj"], r["mu"], r["sf_rated"], r["sf_stall"]) for r in g]
    labels = ["%s, friction %.1f" % (o, mu) for o, mu, _, _ in rows]
    y = np.arange(len(rows))[::-1]
    ax.barh(y + 0.18, [r[2] for r in rows], 0.34, color=S1, label="servo at its continuous rating (0.98 N·m)")
    ax.barh(y - 0.18, [r[3] for r in rows], 0.34, color=S2, label="servo at stall (2.94 N·m)")
    for yy, r in zip(y, rows):
        ax.text(r[2] + 0.08, yy + 0.18, "%.2f" % r[2], va="center", fontsize=8.5, color=INK)
        ax.text(r[3] + 0.08, yy - 0.18, "%.1f" % r[3], va="center", fontsize=8.5, color=INK)
    ax.axvline(1.0, color=INK, lw=1.2)
    ax.axvline(1.5, color=INK2, lw=1.0, ls="--")
    ax.text(1.0, len(rows) - 0.35, " holds", color=INK, fontsize=8.5, va="bottom")
    ax.text(1.5, len(rows) - 0.35, " target 1.5", color=INK2, fontsize=8.5, va="bottom")
    ax.set_yticks(y, labels)
    ax.set_xlabel("clamp margin = clamp available / clamp needed")
    ax.set_xlim(0, 6.6)
    ax.set_ylim(-0.6, len(rows) - 0.1)
    ax.set_title("Grip margin through the full task (MuJoCo grasp loads)", loc="left", color=INK)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, fontsize=8.5)
    save(fig, "plot_grip_margin.png")


def sim_series():
    d = np.load(os.path.join(REPO, "sim", "arc_arm_fourbar", "task_log.npz"))
    t, tau, qd = d["t"], d["tau"], d["qd"]
    joints = [str(j) for j in d["joints"]]
    phases = [str(p) for p in d["phases"]]
    ph = d["phase"]
    # peak/RMS from the sim's own per-physics-step statistics (the log is sampled per 10 ms tick)
    act = json.load(open(os.path.join(REPO, "sim", "arc_arm_fourbar", "task_run.json")))["actuation"]["joints"]
    # task spans: the donut task up to the first STOW, the pipe task after
    stow = [i for i, p in enumerate(phases) if p == "STOW"]
    t_split = t[np.argmax(ph == stow[0])] if stow else None
    fig, axs = plt.subplots(len(joints), 1, figsize=(10, 9), sharex=True)
    for ax, j, k in zip(axs, joints, range(len(joints))):
        lab, cont, peak = RATING[j]
        ax.plot(t, tau[:, k], color=S1, lw=1.0)
        ax.axhspan(-cont, cont, color=S3, alpha=0.10, lw=0)
        for s in (1, -1):
            ax.axhline(s * cont, color=S3, lw=1.0, ls="--")
            ax.axhline(s * peak, color=INK2, lw=1.0, ls=":")
        top = max(peak, np.abs(tau[:, k]).max()) * 1.15
        ax.set_ylim(-top, top)
        ax.set_ylabel("N·m", fontsize=8.5)
        ax.set_title("%s   peak %.2f N·m, RMS %.2f N·m" % (lab, act[j]["tau_peak_Nm"], act[j]["tau_rms_Nm"]),
                     loc="left", fontsize=9.5, color=INK)
        if t_split is not None:
            ax.axvline(t_split, color=INK2, lw=0.8)
    axs[0].text(2, axs[0].get_ylim()[1] * 0.92, "donut task", va="top", fontsize=9, color=INK2)
    if t_split is not None:
        axs[0].text(t_split + 2, axs[0].get_ylim()[1] * 0.92, "pipe task", va="top", fontsize=9, color=INK2)
    axs[-1].set_xlabel("simulated time, s")
    from matplotlib.lines import Line2D
    fig.legend([Line2D([], [], color=S1), Line2D([], [], color=S3, ls="--"), Line2D([], [], color=INK2, ls=":")],
               ["actuator torque", "continuous rating", "stall"],
               loc="upper center", ncol=3, fontsize=8.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    save(fig, "plot_sim_torque.png")

    # grasp loads while carried (gripper frame at the TCP)
    fig, axs = plt.subplots(1, 2, figsize=(10, 3.4))
    for ax, o, comps in ((axs[0], "donut", ((1, "across the jaws Fy", S1), (2, "vertical Fz", S2), (0, "along the fingers Fx", S3))),
                         (axs[1], "pipe", ((4, "tilt moment My (N·m)", S2),))):
        w = d["w_" + o]
        m = ~np.isnan(w[:, 0])
        for i, lab, c in comps:
            ax.plot(t[m], np.abs(w[m, i]), ".", ms=1.2, color=c, label=lab)
        ax.set_title("%s carried: grasp load at the TCP" % o.capitalize(), loc="left", fontsize=9.5, color=INK)
        ax.set_xlabel("simulated time, s")
        ax.set_ylabel("N" if o == "donut" else "N·m")
        ax.legend(fontsize=8, markerscale=8, loc="upper right")
    fig.tight_layout()
    save(fig, "plot_grasp_loads.png")


if __name__ == "__main__":
    static_torque()
    grip_margin()
    sim_series()
