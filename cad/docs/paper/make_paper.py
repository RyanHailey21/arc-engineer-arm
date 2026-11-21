"""Build the ARC S2 Engineer arm product summary (arXiv-style PDF) from the check results in the repository.

    python -I cad/docs/paper/make_paper.py            (any Python with numpy + matplotlib; pdflatex on PATH)

It reads the current evidence and never types numbers by hand. Its inputs:
  - cad/out/fourbar/quick.json and cad/out/fourbar_direct/quick.json: masses, static torques, quick checks;
  - cad/out/fourbar/grip_hold.json: clamp margins;
  - cad/out/fourbar/fea/fea_results.json and cad/fea/out/fea_results.json: safety factors;
  - cad/out/fourbar/level_keeping.txt and the interference reports;
  - sim/arc_arm_fourbar/task_run.json and task_log.npz: MuJoCo task run;
  - cad/params/actuators.toml: actuator ratings.
It writes:
  - fig/*.pdf (vector plots in Computer Modern);
  - numbers.tex (one macro per reported value);
  - ../ARC_S2_Engineer_Arm.pdf, the paper itself.
The pictures in fig/ (renders and sim snapshots) come from cad/render and cad/sim. See paper.tex, which lists the
command for each picture.
"""
import json
import os
import re
import shutil
import subprocess
import tomllib

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CAD = os.path.dirname(os.path.dirname(HERE))
REPO = os.path.dirname(CAD)
FIG = os.path.join(HERE, "fig")
os.makedirs(FIG, exist_ok=True)


def load(*p):
    with open(os.path.join(REPO, *p), encoding="utf-8") as f:
        return json.load(f)


# ---- style: Computer Modern so the figures match the LaTeX body ------------------------------------------------
INK, INK2, GRID = "#111111", "#555555", "#dddddd"
C1, C2, C3, C4, C5 = "#1f5fa8", "#c8501e", "#2e8b57", "#b8860b", "#6a3d9a"
plt.rcParams.update({
    "font.family": "serif", "font.serif": ["cmr10"], "mathtext.fontset": "cm", "axes.formatter.use_mathtext": True,
    "font.size": 9, "axes.titlesize": 9, "axes.labelsize": 9, "legend.fontsize": 8, "xtick.labelsize": 8,
    "ytick.labelsize": 8, "axes.edgecolor": INK2, "axes.linewidth": 0.6, "axes.grid": True, "grid.color": GRID,
    "grid.linewidth": 0.5, "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "legend.frameon": False, "lines.linewidth": 1.1, "savefig.bbox": "tight", "pdf.fonttype": 42,
    "axes.unicode_minus": False})
W1, W2 = 3.3, 6.8     # one-column and full-width figure widths (in)


def save(fig, name):
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)


# ---- data ----------------------------------------------------------------------------------------------------
ACT = tomllib.load(open(os.path.join(CAD, "params", "actuators.toml"), "rb"))
STS = ACT["STS3215"]
RATIO = ACT["BASE"]["ratio"] * ACT["BASE"]["efficiency"]     # torque gain of the 3:1 spur stage at the joint
DM = ACT["DM_J4340"]
GEARED = load("cad", "out", "fourbar", "quick.json")
DIRECT = load("cad", "out", "fourbar_direct", "quick.json")
GRIP = load("cad", "out", "fourbar", "grip_hold.json")
FEA = load("cad", "out", "fourbar", "fea", "fea_results.json") + load("cad", "fea", "out", "fea_results.json")
RUN = load("sim", "arc_arm_fourbar", "task_run.json")
VAL = load("sim", "arc_arm_fourbar", "validation.json")

hold_sts_joint = STS["stall_Nm"] * RATIO * STS["hold_frac"]     # J1/J2 geared holding limit at the joint
hold_sts_wrist = STS["stall_Nm"] * STS["hold_frac"]
hold_dm = DM["rated_Nm"] * DM["hold_frac"]


def fig_static_torque():
    mt = GEARED["mass_torque"]
    poses = [p["pose"].replace("_", " ").title() for p in mt["poses"]]
    tau = np.abs(np.array([p["tau"] for p in mt["poses"]]))
    x = np.arange(len(poses))
    fig, axs = plt.subplots(1, 3, figsize=(W2, 2.3), sharey=False)
    for ax, j, lim, title in ((axs[0], 0, None, "J1 shoulder"), (axs[1], 1, None, "J2 elbow"),
                              (axs[2], 2, hold_sts_wrist, "J3 wrist pitch")):
        ax.bar(x, tau[:, j], color=C1, width=0.7, label="static torque")
        if lim is None:
            ax.axhline(hold_sts_joint, color=C2, ls="--", lw=1, label="geared STS3215 hold limit")
            ax.axhline(hold_dm, color=C3, ls="-.", lw=1, label="direct DM-J4340 rated")
            ax.set_ylim(0, hold_dm * 1.08)
        else:
            ax.axhline(lim, color=C2, ls="--", lw=1, label="STS3215 hold limit")
        ax.set_title(title)
        ax.set_xticks(x, poses, rotation=90, fontsize=6.5)
        ax.grid(axis="x", visible=False)
    axs[0].set_ylabel("torque at the joint (N m)")
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=3, bbox_to_anchor=(0.5, 1.08))
    save(fig, "static_torque.pdf")


def fig_grip_margin():
    rows = [(r["obj"], r["mu"], r["sf_rated"], r["sf_stall"]) for r in GRIP]
    labels = ["%s\n$\\mu=%.1f$" % (o.title(), mu) for o, mu, _, _ in rows]
    x = np.arange(len(rows))
    fig, ax = plt.subplots(figsize=(W1, 2.2))
    ax.bar(x - 0.18, [r[2] for r in rows], 0.36, color=C1, label="at rated torque")
    ax.bar(x + 0.18, [r[3] for r in rows], 0.36, color=C4, label="at stall")
    ax.axhline(1.5, color=C2, ls="--", lw=1, label="required margin (1.5)")
    ax.axhline(1.0, color=INK2, ls=":", lw=0.8)
    ax.set_xticks(x, labels)
    ax.set_ylabel("clamp margin")
    ax.grid(axis="x", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    save(fig, "grip_margin.pdf")


def fig_sim_torque():
    d = np.load(os.path.join(REPO, "sim", "arc_arm_fourbar", "task_log.npz"))
    t, tau = d["t"], d["tau"]
    joints = [str(j) for j in d["joints"]]
    lims = {"shoulder": (STS["rated_Nm"] * RATIO, STS["stall_Nm"] * RATIO), "elbow": (STS["rated_Nm"] * RATIO, STS["stall_Nm"] * RATIO),
            "wrist_pitch": (STS["rated_Nm"], STS["stall_Nm"]), "wrist_roll": (STS["rated_Nm"], STS["stall_Nm"]),
            "gripper": (STS["rated_Nm"], STS["stall_Nm"])}
    names = {"shoulder": "J1 shoulder", "elbow": "J2 elbow", "wrist_pitch": "J3 wrist pitch",
             "wrist_roll": "J4 wrist roll", "gripper": "gripper"}
    show = [j for j in ("shoulder", "elbow", "wrist_pitch", "gripper") if j in joints]
    fig, axs = plt.subplots(len(show), 1, figsize=(W2, 0.95 * len(show) + 0.4), sharex=True)
    for ax, j in zip(axs, show):
        k = joints.index(j)
        ax.plot(t, np.abs(tau[:, k]), color=C1, lw=0.7)
        cont, stall = lims[j]
        ax.axhline(cont, color=C2, ls="--", lw=0.9)
        ax.axhline(stall, color=INK2, ls=":", lw=0.9)
        ax.set_ylim(0, stall * 1.1)
        ax.set_ylabel("N m")
        ax.set_title(names[j], loc="left", fontsize=8, pad=2)
    axs[-1].set_xlabel("time (s), donut task then pipe task")
    axs[0].legend([plt.Line2D([], [], color=C1), plt.Line2D([], [], color=C2, ls="--"),
                   plt.Line2D([], [], color=INK2, ls=":")], ["torque (magnitude)", "continuous rating", "stall"],
                  loc="lower right", bbox_to_anchor=(1.0, 1.12), ncol=3)
    save(fig, "sim_torque.pdf")


def fig_fea():
    rows = sorted(((r.get("part", r["case"]).replace("_", " "), r["safety_factor"]) for r in FEA
                   if isinstance(r.get("safety_factor"), (int, float))), key=lambda r: r[1])
    fig, ax = plt.subplots(figsize=(W1, 0.22 * len(rows) + 0.5))
    y = np.arange(len(rows))
    ax.barh(y, [r[1] for r in rows], color=C1, height=0.6)
    for yi, (_, sf) in zip(y, rows):
        ax.text(sf * 1.08, yi, ("%.1f" % sf) if sf < 100 else "%.0f" % sf, va="center", fontsize=7)
    ax.axvline(1.5, color=C2, ls="--", lw=1)
    ax.set_yticks(y, [r[0] for r in rows], fontsize=7)
    ax.set_xscale("log")
    ax.set_xlim(1, 250)
    ax.set_xlabel("safety factor on factored loads (log)")
    ax.grid(axis="y", visible=False)
    save(fig, "fea_sf.pdf")
    return rows


# ---- numbers: one macro per reported value ---------------------------------------------------------------------
def macros(fea_rows):
    mt, md = GEARED["mass_torque"], DIRECT["mass_torque"]
    g = {(r["obj"], r["mu"]): r for r in GRIP}
    act = RUN["actuation"]["joints"]
    lk = open(os.path.join(CAD, "out", "fourbar", "level_keeping.txt"), encoding="utf-8").read()
    dead = re.search(r"dead-point margin: min ([\d.]+) deg", lk)
    full = open(os.path.join(CAD, "out", "fourbar", "interference_report.txt"), encoding="utf-8").read()
    overlaps = "0" if re.search(r"\b0 (overlap|interfer)", full) else "see report"
    peak_frac = max(act[j]["tau_peak_Nm"] / (STS["stall_Nm"] * (RATIO if j in ("shoulder", "elbow") else 1))
                    for j in act)
    rms_frac = max(act[j]["tau_rms_Nm"] / (STS["rated_Nm"] * (RATIO if j in ("shoulder", "elbow") else 1))
                   for j in act)
    v = {
        "ArmMass": "%.0f" % mt["arm_g"], "ArmMassDirect": "%.0f" % md["arm_g"],
        "PastWrist": "%.0f" % mt["past_wrist_g"], "HeadMass": "%.0f" % mt["head_g"],
        "JOneTau": "%.2f" % mt["worst_static_Nm"]["J1"], "JTwoTau": "%.2f" % mt["worst_static_Nm"]["J2"],
        "JThreeTau": "%.2f" % mt["worst_static_Nm"]["J3"],
        "JOneUtilG": "%.0f" % (100 * mt["rated_utilisation"]["J1"]), "JTwoUtilG": "%.0f" % (100 * mt["rated_utilisation"]["J2"]),
        "JOneUtilD": "%.0f" % (100 * md["rated_utilisation"]["J1"]), "JTwoUtilD": "%.0f" % (100 * md["rated_utilisation"]["J2"]),
        "JThreeUtil": "%.0f" % (100 * mt["rated_utilisation"]["J3"]),
        "HoldSTS": "%.2f" % hold_sts_joint, "HoldDM": "%.1f" % hold_dm, "Ratio": "%.0f" % ACT["BASE"]["ratio"],
        "DonutRated": "%.2f" % g[("donut", 0.5)]["sf_rated"], "DonutStall": "%.1f" % g[("donut", 0.5)]["sf_stall"],
        "PipeRated": "%.2f" % g[("pipe", 0.5)]["sf_rated"], "PipeStall": "%.1f" % g[("pipe", 0.5)]["sf_stall"],
        "MinSF": "%.1f" % fea_rows[0][1], "MinSFPart": fea_rows[0][0],
        "SimTime": "%.1f" % RUN["sim_time_s"], "PeakFrac": "%.0f" % (100 * peak_frac), "RmsFrac": "%.0f" % (100 * rms_frac),
        "DeadPoint": dead.group(1) if dead else "?", "Overlaps": overlaps,
        "PipeDepth": "%.0f" % RUN["pipe"]["pipe_tip_past_wall_face_mm"],
        "ReleaseTime": "%.2f" % VAL["mjcf_power_off_release"]["t_open_10mm_s"],
        "DirectExtra": "%.0f" % (md["arm_g"] - mt["arm_g"]),
        "JOneOverRated": "%.0f" % (100 * (mt["worst_static_Nm"]["J1"] / (STS["rated_Nm"] * RATIO) - 1)),
    }
    with open(os.path.join(HERE, "numbers.tex"), "w", encoding="utf-8") as f:
        f.write("% generated by make_paper.py from the check results; do not edit\n")
        for k, val in v.items():
            f.write("\\newcommand{\\%s}{%s}\n" % (k, val))
    return v


def build_pdf():
    tex = shutil.which("pdflatex")
    if not tex:
        raise SystemExit("pdflatex not found (install MiKTeX or TeX Live)")
    for _ in range(2):    # twice for references
        r = subprocess.run([tex, "-interaction=nonstopmode", "-halt-on-error", "paper.tex"], cwd=HERE,
                           capture_output=True, text=True)
        if r.returncode:
            print(r.stdout[-3000:])
            raise SystemExit("pdflatex failed")
    dst = os.path.join(os.path.dirname(HERE), "ARC_S2_Engineer_Arm.pdf")
    shutil.copyfile(os.path.join(HERE, "paper.pdf"), dst)
    print("wrote", dst)


def copy_renders():
    """The hero stills from cad/render/out, shrunk to JPEG for the paper (Blender PNGs are 2-3 MB each)."""
    from PIL import Image
    src = os.path.join(CAD, "render", "out")
    for still, name in (("hero_stow", "render_stow"), ("hero_donut_lift", "render_donut_lift"),
                        ("hero_pipe_chute", "render_pipe_chute")):
        p = os.path.join(src, still + ".png")
        if os.path.exists(p):
            im = Image.open(p).convert("RGB")
            im.thumbnail((1400, 1400))
            im.save(os.path.join(FIG, name + ".jpg"), quality=88)


if __name__ == "__main__":
    copy_renders()
    fig_static_torque()
    fig_grip_margin()
    fig_sim_torque()
    rows = fig_fea()
    print(json.dumps(macros(rows), indent=1))
    if os.environ.get("NO_PDF") != "1":
        build_pdf()
