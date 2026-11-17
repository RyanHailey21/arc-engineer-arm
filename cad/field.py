# -*- coding: utf-8 -*-
"""ARC Season 2 Battlefield items used for clearance checks (manual sec. 3.2).
Robot frame: X forward from the chassis front bumper, Z up from the floor."""
import math
import FreeCAD as App
import Part
from arm_model import K, box

V = App.Vector
PIPE_R, PIPE_RI = 13.35, 10.45          # 3/4" Sch40 PVC: OD 26.7, ID ~20.9
DONUT_R, DONUT_r = 37.5, 12.5           # OD 100 / ID 50 / thickness 25


def tube(p, d, L):
    return Part.makeCylinder(PIPE_R, L, p, d).cut(Part.makeCylinder(PIPE_RI, L, p, d))


def donut(x, z, local_frame=False):
    return Part.makeTorus(DONUT_R, DONUT_r, V(x, 0, z), V(0, 0, 1))


POLE_X, POLE_Z0, POLE_H = 130.0, 210.0, 456.0     # pole axis x (tier edge 30 + 100), tier top, tube height


def pole_lat(h, A=50.0, h0=40.0, h1=440.0):
    """Lateral (Y) offset of the pole centreline at height h above the tube start."""
    if h <= h0 or h >= h1:
        return 0.0
    t = (h - h0) / (h1 - h0)
    return A * math.sin(math.pi * t) ** 2 * math.sin(2 * math.pi * t) / 0.6495


def _path_slack(z_u, yc, th, roll_z, tcp_z):
    """Smallest clearance (mm) between the pole tube and the donut hole / finger gap,
    evaluated in the (rolled) head frame for one path sample."""
    zA = z_u + (roll_z - tcp_z)                      # roll axis height (robot frame, y=0)
    c, s_ = math.cos(-th), math.sin(-th)
    worst = 1e9
    for k in range(-60, 61):
        hz = POLE_Z0 + 6.0 + (zA - POLE_Z0 - 6.0) + 1.0 * k   # pole sample heights around the head
        h = hz - POLE_Z0 - 6.0
        if h < 0 or h > POLE_H:
            continue
        wy, wz = pole_lat(h) - yc, hz - zA
        yh, zh = c * wy - s_ * wz, s_ * wy + c * wz + roll_z
        dz = zh - tcp_z
        if abs(dz) < 12.5:                           # inside the donut ring: hole radius at this height
            allowed = 37.5 - math.sqrt(156.25 - dz * dz) - 12.5
        elif -12.0 <= zh - tcp_z <= 50.0 or -12.0 <= dz < 0:
            allowed = 52.0 - 13.0                    # between the finger plates / pads (donut grip)
        else:
            continue
        worst = min(worst, allowed - abs(yh))
    return worst


def donut_lift_path(z_from=228.5, z_to=720.0, n=32, roll_z=-5.0, tcp_z=-20.0):
    """Donut lift along the pole: [(arm_tcp_z, chassis_y, roll_deg)].
    The arm raises the donut (x on the pole axis, pitch 0); the wrist roll J4 tilts
    the donut so its axis follows the pole tangent (up to ~50 deg on this placeholder
    pole); the chassis strafes to keep the pole inside the donut hole, biased within
    the hole's play so the curving pole also stays clear of the fingers above/below.
    arm_tcp_z / chassis_y are corrected for the roll axis sitting above the TCP."""
    d = roll_z - tcp_z                                  # roll axis height above the TCP (15 mm)
    out = []
    for i in range(n + 1):
        z = z_from + (z_to - z_from) * i / n
        h = z - POLE_Z0 - 6.0
        slope = (pole_lat(h + 0.5) - pole_lat(h - 0.5))
        th = -math.atan(slope)
        z_u = z - d * (1 - math.cos(th))
        y0 = pole_lat(h) - d * math.sin(th)
        best = max((_path_slack(z_u, y0 + 0.5 * b, th, roll_z, tcp_z), -abs(b), y0 + 0.5 * b) for b in range(-24, 25))
        out.append((z_u, best[2], math.degrees(th)))
    return out


def zigzag_pole(bx, by, z0):
    """PLACEHOLDER: manual says pole details TBA. 456 tall, 250 sq base, ~D24 tube,
    lateral S of +/-50 mm in Y (worst case for the robot to follow by strafing)."""
    # Centreline: one analytic S-curve, y = A*sin^2(pi*t)*sin(2*pi*t) between 40 and 440 mm,
    # straight below/above. Sampled densely and interpolated into ONE B-spline, so the tube is a
    # single swept face. Min bend radius ~39 mm (> 12 mm tube radius, so no self-intersection).
    s = box(bx - 125, by - 125, z0, bx + 125, by + 125, z0 + 6)
    cps = [V(bx, by + pole_lat(h), z0 + 6 + h) for h in (456.0 * i / 60 for i in range(61))]
    bs = Part.BSplineCurve()
    bs.interpolate(Points=cps, InitialTangent=V(0, 0, 1), FinalTangent=V(0, 0, 1))
    prof = Part.Wire(Part.makeCircle(12, cps[0], V(0, 0, 1)))
    # corrected-Frenet (frenet=False): Frenet frames flip at inflections and pinch the tube
    tube = Part.Wire(bs.toShape()).makePipeShell([prof], True, False)
    return s.fuse(tube).fuse(Part.makeSphere(12, cps[-1])).removeSplitter()


def scene_items(scene):
    """-> list of (name, shape, color). Chassis placeholder always included."""
    items = []
    if scene.startswith("DONUT") and not scene.startswith("DONUT_PLACE"):
        edge = 30.0                                  # bumper 30 mm off the tier
        items.append(("Side_High_Ground_Lower_Tier", box(edge, -500, 0, edge + 1000, 500, 210), "wood"))
        items.append(("ZigZag_Pole_PLACEHOLDER", zigzag_pole(edge + 100, 0, 210), "field"))
        if scene.startswith(("DONUT_APPROACH", "DONUT_PICK")):
            items.append(("Objective_C_Donut", donut(edge + 100, 216 + DONUT_r), "donut"))
    if scene == "DONUT_PLACE":
        items.append(("Scoring_Area_Platform", box(60.8, -150, 0, 360.8, 150, 50), "field"))
    if scene.startswith("PIPE") and not scene.startswith("PIPE_CHUTE"):
        cx = 110.0                                   # bucket rim 10 mm off bumper
        items.append(("Objective_B_Bucket", Part.makeCylinder(100, 250, V(cx, 0, 0)).cut(
            Part.makeCylinder(98, 248, V(cx, 0, 2))), "field"))
        # remaining pipes rest against the far rim, leaning outward
        for i, ang in enumerate((-100, -60, -20, 20, 60, 100)):
            a = math.radians(ang)
            px, py = cx + 62 * math.cos(a), 62 * math.sin(a)
            d = V(0.12 * math.cos(a), 0.12 * math.sin(a), 1)
            items.append(("Objective_B_Pipe_%d" % i, tube(V(px, py, 2), d, 500), "red" if i % 2 else "blue"))
        if scene.startswith(("PIPE_APPROACH", "PIPE_GRASP")):
            items.append(("Objective_B_Pipe_Target", tube(V(40, 0, 2), V(0, 0, 1), 500), "red"))
    if scene.startswith("PIPE_CHUTE"):
        face = 150 + 453 - 300                       # 300 mm of pipe inside the chute
        items.append(("Perimeter_Wall", box(face, -600, 0, face + 40, 600, 500), "wood"))
        items.append(("Pipe_Chute_D52.5", box(face, -100, 500, face + 60, 100, 700).cut(
            Part.makeCylinder(26.25, 80, V(face - 10, 0, 600), V(1, 0, 0))), "field"))
    return items


def held_object(scene):
    """Object carried in the gripper, in GRIPPER local frame (TCP at (GRIP,0,-DROP))."""
    G, Dp = K["GRIP"], K["DROP"]
    if scene.startswith(("DONUT_LIFT", "DONUT_PLACE")):
        return ("Objective_C_Donut_Held", Part.makeTorus(DONUT_R, DONUT_r, V(G, 0, -Dp), V(0, 0, 1)), "donut")
    if scene.startswith(("PIPE_LIFT", "PIPE_CHUTE")):
        top = -Dp + 47.0                             # pipe top flush with pad top
        return ("Objective_B_Pipe_Held", tube(V(G, 0, top - 500), V(0, 0, 1), 500), "red")
    return None
