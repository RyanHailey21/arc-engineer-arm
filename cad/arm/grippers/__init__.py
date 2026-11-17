# -*- coding: utf-8 -*-
"""
Gripper variants.  Each module provides, in the gripper frame (x along the roll axis, TCP at (K['GRIP'], 0, -K['DROP'])):

    <name>_bodies()            -> {body name: builder}; must include HEAD (rotates with the roll stage) plus
                                  every moving body (jaws, links, screws ...), built at the pipe grip (jaw = PIPE_JAW)
    <name>_placements(Hd, jaw) -> {body name: placement} for every body except HEAD, given the roll-head
                                  placement Hd and the pad-arc gap 'jaw' (mm)

Register the pair in arm/bodies.py GRIPPERS.  Every variant mounts on interfaces/roll_hub__gripper_palm.toml.
"""
