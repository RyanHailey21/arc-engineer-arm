# -*- coding: utf-8 -*-
"""
arm_model.py - facade over the cad/arm package: complete, buildable model of the ARC Season 2 Engineer arm
adapted from Wang et al., Actuators 2025, 14, 71.

Every part carries two shapes:  vis (detailed / vendor geometry, for the
assembly and renders) and chk (simplified solid used by the interference sweep).
Rigid bodies are built in local frames and placed by placements(); the same
frames are used by build_assembly.py to create Assembly-workbench joints.

Frame: X forward from chassis front bumper, Y left, Z up from Battlefield floor.

Y stack (centre planes, 3 mm CF plates):
    J1 DM-J4340 stator  -52.5 .. -105     |  J2 DM-J4340 stator +52.5 .. +105
    tower L  -51.0  (motor bolts on PCD50)|  tower R  +51.0
    J1 hub   -51.5 .. -47.0               |  J2 hub   +47.0 .. +51.5, journal D12
    upper L  -45.5                        |  upper R  +45.5  (6701 on J2 journal)
    rod 1    -42.0                        |
    rocker / level member -37.5 (+GT2 30T pulley -36..-25.5, 9 mm belt -35.25..-26.25)
                                          |  crank   +34.5
                                          |  rod AB  +29.0
    clevis L -23.5 (wrist)                |  clevis R +23.5
    forearm L -18.0                       |  forearm R +18.0
    servo (wrist, outboard)  -45 .. -86

Compatibility layer: the model now lives in cad/arm/ (one module per subassembly, see arm/__init__.py).
This module re-exports the whole namespace so `import arm_model as M` keeps working everywhere.
"""
from arm.core import *          # noqa: F401,F403
from arm.core import _hull2, _convex_hull, _vprism  # noqa: F401
from arm.base import *          # noqa: F401,F403
from arm.base import _DM        # noqa: F401
from arm.upper_arm import *     # noqa: F401,F403
from arm.forearm import *       # noqa: F401,F403
from arm.wrist import *         # noqa: F401,F403
from arm.wrist import _to_roll_axis, _xscrew, _servo_rot  # noqa: F401
from arm.grippers.screw import *    # noqa: F401,F403
from arm.grippers.fourbar import *  # noqa: F401,F403
from arm.grippers.fourbar import _pad_shape  # noqa: F401
from arm.bodies import *        # noqa: F401,F403
from arm.bodies import _BODIES  # noqa: F401
from arm.kinematics import *    # noqa: F401,F403
from arm.kinematics import _pl  # noqa: F401
