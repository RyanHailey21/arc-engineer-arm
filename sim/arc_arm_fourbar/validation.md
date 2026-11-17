# Validation - arc_arm_fourbar

- **urdf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "ok": true}`
- **mjcf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "max_equality_residual": 0.0, "ok": true, "nq": 16, "nu": 5, "neq": 11, "ngeom": 107}`
- **mjcf_hold_stow**: `{"seconds": 3.0, "nan": false, "max_equality_drift": 0.000115, "max_track_err_deg": 0.479, "actuator_torque_Nm": {"shoulder": -2.784, "elbow": 2.065, "wrist_pitch": 0.339, "wrist_roll": 0.036, "gripper": -0.418}, "ok": true}`
- **mjcf_power_off_release**: `{"start_gap_mm": 13.8, "end_gap_mm": 112.1, "t_open_10mm_s": 0.041, "t_90pct_open_s": 0.137, "ok": true, "note": "ARC rule: release within 1 s of power loss. Servo back-drive is modelled only as 0.05 N*m friction + 0.002 kg*m^2 armature on the gripper joint - an estimate until bench-measured; the result is only as good as that estimate"}`
- **scene**: `{"compiles": true, "nbody": 20, "ngeom": 112}`
- **urdf_in_mujoco**: `{"compiles": true, "nbody": 17, "note": "MuJoCo's URDF importer ignores <mimic>"}`
- **ok**: `true`
- **gazebo_package**: `{"parses": true, "mesh_uris": 107, "missing_meshes": [], "name_clashes": [], "mimic_joints": 11, "actuated": ["shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper"], "plugins": 6, "ok": true, "note": "structure only; the gz-sim run test is gazebo_run (cad/sim/gz_check.py)"}`
- **gazebo_run**: `{"ok": true, "status": "FRESH", "gz_version": "8.10.0", "world": "sim/arc_arm_fourbar/worlds/arc_arm.sdf", "poses": 7, "max_track_err_deg": 0.005, "max_mimic_err_deg": 0.4081, "max_tcp_err_mm": 2.434, "tolerances": {"track_deg": 1.5, "mimic_deg": 1.0, "tcp_mm": 3.0}}`
