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

    def points(self):
        """Every hole centre as (x, y, z) in the interface's body frame: a [pattern] bolt circle (x-normal, at frame_x)
        or a [stations] row (y-normal, points_xz at the frame origin's y)."""
        if "pattern" in self:
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
