# -*- coding: utf-8 -*-
"""Body registry: the arm bodies plus the active gripper variant's bodies (GRIPPERS[GRIP]), and build_bodies().
"""
from arm.core import *  # noqa: F401,F403
from arm.base import *  # noqa: F401,F403
from arm.upper_arm import *  # noqa: F401,F403
from arm.forearm import *  # noqa: F401,F403
from arm.wrist import *  # noqa: F401,F403


from arm.grippers.fourbar import fourbar_bodies, fb_placements

# gripper variants: each provides bodies() -> {body name: builder} (HEAD + its moving bodies, built in the
# gripper frame) and placements(Hd, jaw) -> {body name: placement} relative to the roll head Hd
GRIPPERS = {
    "FOURBAR": dict(bodies=fourbar_bodies, placements=fb_placements,
                    summary="gear-synchronised parallel four-bar, STS3215 direct, torsion-spring release"),
}

ARM_BODY_FUNCS = dict(GROUND=body_ground, UPPER=body_upper, CRANK=body_crank,
                      ROD_AB=lambda: body_rod("Rod_AB", K["L2"], Y["RAB"]),
                      ROD1=lambda: body_rod("Rod_1", K["L2"], Y["ROD1"]),
                      FOREARM=body_forearm, ROCKER=body_rocker, ROD2=body_rod2, LEVEL=body_level,
                      GRIPPER=body_gripper)
BODY_FUNCS = dict(ARM_BODY_FUNCS)
if GRIP not in GRIPPERS:
    raise SystemExit("GRIP=%s: unknown gripper variant; one of %s (params/variant.toml)" % (GRIP, ", ".join(GRIPPERS)))
BODY_FUNCS.update(GRIPPERS[GRIP]["bodies"]())

_BODIES = {}


def build_bodies(jaw_open=None):
    """Bodies are jaw-independent now (jaws move by placement)."""
    if not _BODIES:
        for k, f in BODY_FUNCS.items():
            _BODIES[k] = f()
    return _BODIES
