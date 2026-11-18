"""Gazebo task-sequence demo: cad/sim/demo.py with the Gazebo backend (kept for the documented command line).

Start the world first:
    GZ_SIM_RESOURCE_PATH=<repo>/sim gz sim -r <repo>/sim/arc_arm_fourbar/worlds/arc_arm_free.sdf
then:
    python cad/sim/gz_demo.py [variant] [--seq donut|pipe|both] [--loops N] [--rate 100] [--speed 0.5]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo import main  # noqa: E402

if __name__ == "__main__":
    main(default_backend="gazebo")
