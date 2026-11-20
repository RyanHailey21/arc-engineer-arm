# -*- coding: utf-8 -*-
"""
ARC S2 Engineer arm model, one module per subassembly (import the facade `arm_model` for the full namespace).

    core.py        frames + global parameters (K, Y, T), pad geometry, actuators + base-drive interfaces, catalogue CAT, helpers
    base.py        GROUND: chassis deck, towers + J1/J2 STS3215 drive frames, motor_hub + drive_gear_parts (J1/J2 output hubs)
    upper_arm.py   UPPER, CRANK, parallel rods (body_rod)
    forearm.py     FOREARM, ROCKER, GT2 level-keeping pulley
    wrist.py       LEVEL (J3 pitch), GRIPPER (pitch frame + J4 roll stage), roll_hub_parts (interfaces/roll_*.toml)
    grippers/      one module per gripper variant (GRIP env var): screw.py (rev A), fourbar.py (concept)
    bodies.py      body registry: arm bodies + GRIPPERS[GRIP]; build_bodies()
    kinematics.py  joints, ik, placements, placed, part_mass_g, static_torques, POSES, pose_q

Mating interfaces: cad/interfaces/*.toml.  Field keep-outs: cad/envelopes/*.toml.
Regression guard: cad/tools/fingerprint.py (a pure refactor must report MATCH for GRIP=SCREW and GRIP=FOURBAR).
"""

# dependency order, for importlib.reload in long-running FreeCAD sessions (reload these, then arm_model)
MODULES = ("arm.core", "arm.base", "arm.upper_arm", "arm.forearm", "arm.wrist", "arm.grippers.screw",
           "arm.grippers.fourbar", "arm.bodies", "arm.kinematics")


def reload_all():
    """Reload hardware, iface, params, every arm module and the arm_model facade, in dependency order."""
    import importlib
    import sys
    for m in ("hardware", "iface", "params") + MODULES + ("arm_model",):
        if m in sys.modules:
            importlib.reload(sys.modules[m])
