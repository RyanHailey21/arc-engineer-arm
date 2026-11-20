# -*- coding: utf-8 -*-
"""
Interface files (cad/interfaces/*.toml): one file per mating interface, read by both mating parts.

    import iface
    I = iface.load("roll_hub__gripper_palm")
    I.points_yz()      -> [(y, z), ...] hole centres in the interface plane (gripper frame)
    I.frame_x          -> x of the interface plane
    I["side_b"]["clearance_d"]

Keep geometry decisions that two parts must agree on here, not in either part's build code.
"""
import math
import os
import tomllib

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "interfaces")
_CACHE = {}


class Interface(dict):
    @property
    def name(self):
        return self["interface"]["name"]

    @property
    def origin(self):
        return tuple(self["frame"]["origin"])

    @property
    def frame_x(self):
        return self["frame"]["origin"][0]

    def points_yz(self):
        """Bolt-pattern hole centres (y, z) around the frame origin, for an x-normal interface."""
        pat = self["pattern"]
        y0, z0 = self["frame"]["origin"][1], self["frame"]["origin"][2]
        return [(y0 + pat["radius"] * math.cos(math.radians(a)), z0 + pat["radius"] * math.sin(math.radians(a)))
                for a in pat["angles_deg"]]

    def stations_x(self):
        """[stations] interface: station x positions (for a y-normal row of holes along a link)."""
        return [p[0] for p in self["stations"]["points_xz"]]

    def points_xz(self):
        """Bolt-pattern hole centres (x, z) around the frame origin, for a y-normal interface (angles atan2(z, x))."""
        pat = self["pattern"]
        x0, z0 = self["frame"]["origin"][0], self["frame"]["origin"][2]
        return [(x0 + pat["radius"] * math.cos(math.radians(a)), z0 + pat["radius"] * math.sin(math.radians(a)))
                for a in pat["angles_deg"]]

    def sides(self):
        """[(key, side table, [(body, part), ...])] for side_a, side_b, side_c ... ; a side names one part
        (body + part) or several (parts = [[body, part], ...], e.g. the mirrored J1/J2 motor mounts)."""
        out = []
        for k in sorted(k for k in self if k.startswith("side_")):
            s = self[k]
            out.append((k, s, [tuple(bp) for bp in s["parts"]] if "parts" in s else [(s["body"], s["part"])]))
        return out

    def points(self):
        """Every hole centre as (x, y, z) in the interface's body frame: a [pattern] bolt circle (x-normal at frame_x,
        or y-normal at the frame origin's y) or a [stations] row (y-normal, points_xz at the frame origin's y)."""
        if "pattern" in self:
            if abs(self["frame"]["normal"][1]) > 0.5:
                return [(x, self["frame"]["origin"][1], z) for (x, z) in self.points_xz()]
            return [(self.frame_x, y, z) for (y, z) in self.points_yz()]
        y0 = self["frame"]["origin"][1]
        return [(x, y0, z) for (x, z) in self["stations"]["points_xz"]]


def load(name):
    if name not in _CACHE:
        with open(os.path.join(DIR, name + ".toml"), "rb") as f:
            _CACHE[name] = Interface(tomllib.load(f))
    return _CACHE[name]


def all_interfaces():
    return [load(f[:-5]) for f in sorted(os.listdir(DIR)) if f.endswith(".toml")]
