"""Build the MuJoCo task scene sim/arc_arm_<variant>/tasks.xml from the generated arm (arc_arm.xml) and the CAD field
export (task_field.json, written by cad/sim/export_robot.py).

  - The arm rides on a CHASSIS body with two slide joints (base_x, base_y) and position actuators: an abstraction
    of the drivetrain (holonomic strafe/drive, no yaw), enough for the CAD tasks: drive between stations, strafe
    along the pole during the donut lift (field.donut_lift_path), drive the pipe 300 mm into the chute.
  - Four field STATIONS side by side along world y, each laid out in the robot frame the CAD checks used:
    pick (lower tier + zigzag pole + donut), place (scoring platform), bucket (bucket + pipes), chute (wall + chute).
  - Objects (donut, target pipe) are free bodies. KINEMATIC GRASP: a weld equality per object (head <-> object),
    inactive until the task runner confirms a grasp; held objects do not collide with the arm (contype 4 /
    conaffinity 5), but do collide with the field and the chassis.
  - Field geometry is primitives (boxes, capsules, cylinders), so contacts are exact rather than mesh convex hulls.

Usage (simenv: mujoco):  python cad/sim/build_tasks.py [variant]
"""
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

VAR = (sys.argv[1] if len(sys.argv) > 1 else "fourbar").lower()
REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ROOT = os.path.join(REPO, "sim", "arc_arm_%s" % VAR)
MM = 0.001
LANES = dict(pick=0.0, place=1.6, bucket=-1.6, chute=-3.2)   # world y of each station's robot frame (m)
TCP_IN_HEAD = (0.151, 0.0, -0.015)                            # TCP (151, 0, -20) in HEAD = head link frame + (0,0,5)


def f(*v):
    return " ".join("%.6g" % x for x in v)


def box_geom(parent, name, lo, hi, dy, rgba="0.55 0.45 0.33 1", cls="field"):
    c = [(a + b) / 2 * MM for a, b in zip(lo, hi)]
    h = [(b - a) / 2 * MM for a, b in zip(lo, hi)]
    ET.SubElement(parent, "geom", {"class": cls, "name": name, "type": "box", "pos": f(c[0], c[1] + dy, c[2]),
                                   "size": f(*h), "rgba": rgba})


def capsule(parent, name, p, q, r, rgba, cls="field", dy=0.0):
    ET.SubElement(parent, "geom", {"class": cls, "name": name, "type": "capsule", "size": f(r * MM),
                                   "fromto": f(p[0] * MM, p[1] * MM + dy, p[2] * MM, q[0] * MM, q[1] * MM + dy, q[2] * MM),
                                   "rgba": rgba})


def main():
    F = json.load(open(os.path.join(ROOT, "task_field.json"), encoding="utf-8"))
    t = ET.parse(os.path.join(ROOT, "arc_arm.xml"))
    r = t.getroot()
    r.set("model", "arc_arm_%s_tasks" % VAR)
    for k in r.findall("keyframe"):                       # keyframes index the old qpos layout
        r.remove(k)
    stat = ET.Element("statistic", center="0 -0.8 0.4", extent="3.0")
    r.insert(1, stat)
    vis = ET.Element("visual")
    ET.SubElement(vis, "headlight", diffuse="0.6 0.6 0.6", ambient="0.3 0.3 0.3")
    ET.SubElement(vis, "global", azimuth="-120", elevation="-25")
    r.insert(2, vis)
    asset = r.find("asset")
    ET.SubElement(asset, "texture", type="2d", name="grid", builtin="checker", rgb1="0.2 0.3 0.4", rgb2="0.1 0.2 0.3",
                  width="300", height="300", mark="edge", markrgb="0.2 0.3 0.4")
    ET.SubElement(asset, "material", name="grid", texture="grid", texrepeat="8 8", reflectance="0.1")
    d = r.find("default")
    fld = ET.SubElement(d, "default", {"class": "field"})
    ET.SubElement(fld, "geom", contype="1", conaffinity="3", condim="3", friction="0.8 0.02 0.002")
    obj = ET.SubElement(d, "default", {"class": "object"})
    ET.SubElement(obj, "geom", contype="4", conaffinity="5", condim="4", friction="0.8 0.02 0.002")

    wb = r.find("worldbody")
    base = wb.find("body[@name='base_link']")
    wb.remove(base)
    ET.SubElement(wb, "light", pos="0.5 -1 3", dir="-0.2 0.4 -1", directional="true")
    ET.SubElement(wb, "geom", {"class": "field", "name": "floor", "type": "plane", "size": "0 0 0.05", "material": "grid"})
    # chassis: slide x/y (the drivetrain abstraction); deck placeholder as before (top at 120 mm under the arm base)
    ch = ET.SubElement(wb, "body", name="chassis")
    ET.SubElement(ch, "joint", name="base_x", type="slide", axis="1 0 0", damping="200", armature="1")
    ET.SubElement(ch, "joint", name="base_y", type="slide", axis="0 1 0", damping="200", armature="1")
    ET.SubElement(ch, "inertial", pos="-0.29 0 0.08", mass="12", diaginertia="0.3 0.4 0.6")
    ET.SubElement(ch, "geom", {"class": "field", "name": "chassis_deck", "type": "box", "pos": "-0.29 0 0.08",
                               "size": "0.29 0.24 0.04", "rgba": "0.15 0.16 0.17 1", "mass": "0"})
    ch.append(base)
    tcp = base.find(".//body[@name='head']/site[@name='tcp']")
    assert tcp is not None and [float(v) for v in tcp.get("pos").split()] == list(TCP_IN_HEAD), "TCP site moved"

    S = F["stations"]
    # --- pick station: lower tier, pole base plate, zigzag pole (capsule chain), donut threaded on it
    dy = LANES["pick"]
    for b in S["pick"]["boxes"]:
        box_geom(wb, b["name"], b["lo"], b["hi"], dy, "0.55 0.45 0.33 1" if b["name"] == "lower_tier" else "0.4 0.4 0.4 1")
    cl = S["pick"]["pole"]["centreline"]
    for i in range(len(cl) - 1):
        capsule(wb, "pole_%02d" % i, cl[i], cl[i + 1], S["pick"]["pole"]["r"], "0.35 0.35 0.38 1", dy=dy)
    D = F["donut"]
    db = ET.SubElement(wb, "body", name="donut", pos=f(D["start"][0] * MM, D["start"][1] * MM + dy, D["start"][2] * MM))
    ET.SubElement(db, "freejoint", name="donut_free")
    ET.SubElement(db, "inertial", pos="0 0 0", mass="%.3f" % (D["mass_g"] / 1000), diaginertia="2.40e-4 2.40e-4 4.57e-4")
    n = 16
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        p = [D["R"] * math.cos(a0), D["R"] * math.sin(a0), 0]
        q = [D["R"] * math.cos(a1), D["R"] * math.sin(a1), 0]
        capsule(db, "donut_%02d" % k, p, q, D["r"], "0.92 0.66 0.05 1", cls="object")
    for g in db.findall("geom"):
        g.set("mass", "0")
    # --- place station: scoring platform
    for b in S["place"]["boxes"]:
        box_geom(wb, b["name"], b["lo"], b["hi"], LANES["place"], "0.3 0.5 0.3 1")
    # --- bucket station: bucket shell (24 staves + floor), the target pipe (free), six leaning pipes (static)
    dy = LANES["bucket"]
    B = S["bucket"]["bucket"]
    for k in range(24):
        a = 2 * math.pi * k / 24
        cx, cy = B["c"][0] + (B["R"] - 2) * math.cos(a), B["c"][1] + (B["R"] - 2) * math.sin(a)
        ET.SubElement(wb, "geom", {"class": "field", "name": "bucket_%02d" % k, "type": "box",
                                   "pos": f(cx * MM, cy * MM + dy, B["h"] / 2 * MM), "size": f(0.002, 0.0135, B["h"] / 2 * MM),
                                   "euler": f(0, 0, a), "rgba": "0.2 0.4 0.8 1"})
    ET.SubElement(wb, "geom", {"class": "field", "name": "bucket_floor", "type": "cylinder",
                               "pos": f(B["c"][0] * MM, B["c"][1] * MM + dy, 0.001), "size": f(B["R"] * MM, 0.001), "rgba": "0.2 0.4 0.8 1"})
    P = F["pipe"]
    for i, lp in enumerate(S["bucket"]["leaning_pipes"]):
        dn = math.sqrt(sum(c * c for c in lp["d"]))
        q = [lp["p"][k] + lp["d"][k] / dn * P["L"] for k in range(3)]
        capsule(wb, "lean_pipe_%d" % i, lp["p"], q, P["r"], "0.8 0.15 0.15 1" if i % 2 else "0.15 0.25 0.8 1", dy=dy)
    tp = S["bucket"]["target_pipe"]
    pb = ET.SubElement(wb, "body", name="pipe", pos=f(tp["p"][0] * MM, tp["p"][1] * MM + dy, (tp["p"][2] + P["L"] / 2) * MM))
    ET.SubElement(pb, "freejoint", name="pipe_free")
    ET.SubElement(pb, "inertial", pos="0 0 0", mass="%.3f" % (P["mass_g"] / 1000), diaginertia="3.45e-3 3.45e-3 2.37e-5")
    ET.SubElement(pb, "geom", {"class": "object", "name": "pipe_geom", "type": "cylinder",
                               "size": f(P["r"] * MM, P["L"] / 2 * MM), "rgba": "0.8 0.15 0.15 1", "mass": "0"})
    # --- chute station: perimeter wall + chute block with a square opening (side = hole diameter) at the hole height
    dy = LANES["chute"]
    for b in S["chute"]["boxes"]:
        box_geom(wb, b["name"], b["lo"], b["hi"], dy, "0.55 0.45 0.33 1")
    C = S["chute"]["chute"]
    lo, hi, hr, hz = C["lo"], C["hi"], C["hole_r"], C["hole_z"]
    for name, l, h in (("chute_below", [lo[0], lo[1], lo[2]], [hi[0], hi[1], hz - hr]),
                       ("chute_above", [lo[0], lo[1], hz + hr], [hi[0], hi[1], hi[2]]),
                       ("chute_left", [lo[0], hr, hz - hr], [hi[0], hi[1], hz + hr]),
                       ("chute_right", [lo[0], lo[1], hz - hr], [hi[0], -hr, hz + hr])):
        box_geom(wb, name, l, h, dy, "0.4 0.4 0.4 1")

    # --- kinematic-grasp welds (relpose written by the task runner when a grasp is confirmed)
    eq = r.find("equality")
    ET.SubElement(eq, "weld", name="grasp_donut", body1="head", body2="donut", active="false", solref="0.004 1")
    ET.SubElement(eq, "weld", name="grasp_pipe", body1="head", body2="pipe", active="false", solref="0.004 1")
    # --- chassis actuators (position servos on the slide joints)
    act = r.find("actuator")
    for j in ("base_x", "base_y"):
        ET.SubElement(act, "position", name=j, joint=j, kp="20000", kv="2000", ctrlrange="-5 5", forcerange="-800 800")
    ET.indent(r)
    out = os.path.join(ROOT, "tasks.xml")
    t.write(out, encoding="utf-8", xml_declaration=False)
    import mujoco
    m = mujoco.MjModel.from_xml_path(out)
    print("tasks.xml: nq %d, nu %d, ngeom %d, neq %d, nbody %d -> %s" % (m.nq, m.nu, m.ngeom, m.neq, m.nbody, out))


if __name__ == "__main__":
    main()
