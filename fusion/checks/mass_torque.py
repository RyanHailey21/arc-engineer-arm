"""Mass and static-torque check on a Fusion snapshot, compared with the code-CAD model.

    python -I cad/tools/run.py fusion/checks/mass_torque.py        (FreeCAD, for the kinematics; rev from SNAP_REV)

Reads fusion/snapshot/<rev>/snapshot.json. Every occurrence with bodies is grouped into its moving body: the
top-level group name, or the body inside the shared "ARC Four-Bar Gripper" sub-assembly; the pinions count as
GROUND. Each body's mass and world centre of mass at the saved pose (STOW) are moved into that body's own frame
with the code-CAD placements at STOW. The static torques at every task pose then follow by virtual work, exactly as
cad/arm/kinematics.static_torques does, so the two can be compared directly.

Writes fusion/checks/out/<rev>_mass_torque.json and prints a comparison table.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
sys.path[:0] = [os.path.join(REPO, "cad"), os.path.join(REPO, "cad", "arm")]
import FreeCAD as App  # noqa: E402
import arm_model as M  # noqa: E402
import kinematics as K  # noqa: E402

REV = os.environ.get("SNAP_REV", "rev_b")
snap = json.load(open(os.path.join(REPO, "fusion", "snapshot", REV, "snapshot.json"), encoding="utf-8"))
ALIAS = {"J1 pinion": "GROUND", "J2 pinion": "GROUND"}


def body_of(path):
    seg = [s.split(":")[0] for s in path.split("+")]
    b = seg[1] if seg[0] == "ARC Four-Bar Gripper" and len(seg) > 1 else seg[0]
    return ALIAS.get(b, b)


# Fusion: mass and world COM per moving body
fus = {}
for o in snap["occurrences"]:
    if not o["bodies"] or o["mass_g"] <= 0:
        continue
    b = body_of(o["path"])
    m, c = fus.get(b, (0.0, App.Vector()))
    fus[b] = (m + o["mass_g"], c + App.Vector(*o["com_mm"]) * o["mass_g"])
fus = {b: (m, c / m) for b, (m, c) in fus.items()}

# code-CAD: the same per body
bodies = M.build_bodies()
names = set(bodies)
code = {}
for bn, parts in bodies.items():
    m_tot, c_tot = 0.0, App.Vector()
    for p in parts:
        m = K.part_mass_g(p)
        if m <= 0:
            continue
        try:
            c = p.chk.CenterOfMass
        except Exception:
            c = p.chk.BoundBox.Center
        m_tot += m
        c_tot += c * m
    if m_tot > 0:
        code[bn] = (m_tot, c_tot / m_tot)           # body frame

# torques by virtual work, from body masses + COMs (body frame)
q0, jaw0 = K.pose_q("STOW")
plc0 = K.placements(*q0, jaw=jaw0)


def torques(com_body, pose):
    """Arm-only static torques at a pose (no payload), with the code-CAD's own virtual-work routine."""
    q, jaw = K.pose_q(pose)
    q = list(q) + [0.0] * (4 - len(q))
    coms = {b: [(m / 1000.0, c)] for b, (m, c) in com_body.items()}
    return K.torques_from_coms(coms, *q, payload_g=0.0, jaw=jaw)


fus_body = {b: (m, plc0[b].inverse().multVec(c)) for b, (m, c) in fus.items() if b in plc0}
unmapped = sorted(set(fus) - set(plc0))
rows = []
print("%-8s %9s %9s %7s   %s" % ("body", "fusion g", "code g", "diff %", "COM offset mm (body frame)"))
for b in sorted(set(fus_body) | set(code), key=lambda b: -(code.get(b, (0,))[0])):
    mf, cf = fus_body.get(b, (0.0, App.Vector()))
    mc, cc = code.get(b, (0.0, App.Vector()))
    d = 100 * (mf - mc) / mc if mc else float("nan")
    off = (cf - cc).Length if b in fus_body and b in code else float("nan")
    rows.append(dict(body=b, fusion_g=round(mf, 1), code_g=round(mc, 1), diff_pct=round(d, 1), com_offset_mm=round(off, 2)))
    print("%-8s %9.1f %9.1f %7.1f   %.2f" % (b, mf, mc, d, off))
print("unmapped Fusion groups:", unmapped)

# static torques (arm only, no payload) at every pose: Fusion masses vs code masses
tq = []
print("\n%-20s %s" % ("pose", "J1 J2 J3 (N m): fusion / code"))
for pose in K.POSES:
    tf, tc = torques(fus_body, pose), torques(code, pose)
    tq.append(dict(pose=pose, fusion=[round(x, 3) for x in tf[:3]], code=[round(x, 3) for x in tc[:3]]))
    print("%-20s " % pose + "  ".join("%6.2f/%6.2f" % (a, c) for a, c in zip(tf[:3], tc[:3])))
os.makedirs(os.path.join(HERE, "out"), exist_ok=True)
json.dump(dict(revision=REV, snapshot=snap["summary"], bodies=rows, torques_no_payload=tq, unmapped=unmapped),
          open(os.path.join(HERE, "out", "%s_mass_torque.json" % REV), "w"), indent=1)
