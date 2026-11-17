# -*- coding: utf-8 -*-
"""Shape provider for the FreeCAD MCP checking tools (interference_check, hole_edge_check).

    source = {"python": r"C:\\Users\\ryanh\\light_weight_arm\\cad\\tools\\mcp_provider.py",
              "function": "shapes", "poses_function": "poses", "args": {"which": "chk"}}

shapes(pose) returns every part in its rigid-body frame plus that body's
placement, so the MCP cache recognises unchanged relative poses.
pose: a pose name from arm_model.POSES ("STOW", ...), or {"q": [th1, th2, pitch, roll], "jaw": mm}.
"""
import os
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if CAD not in sys.path:
    sys.path.insert(0, CAD)
import arm_model as M  # noqa: E402

_BODIES = {}


def _bodies():
    if "b" not in _BODIES:
        _BODIES["b"] = M.build_bodies()
    return _BODIES["b"]


def poses():
    return list(M.POSES)


def shapes(pose="STOW", which="chk", skip_cat=False, checked_only=True):
    if pose is None:
        pose = "STOW"
    if isinstance(pose, str):
        q, jaw = M.pose_q(pose)
    else:
        q, jaw = tuple(pose["q"]), pose.get("jaw", 2 * M.O_REF)
    plc = M.placements(*q, jaw=jaw)
    out = []
    for bname, parts in _bodies().items():
        for p in parts:
            if checked_only and not p.check:
                continue
            if skip_cat and p.kind == "CAT":
                continue
            s = p.chk if which == "chk" else p.vis
            if s is None or s.isNull():
                continue
            out.append({"name": p.name, "shape": s, "placement": plc[bname], "group": bname})
    return out
