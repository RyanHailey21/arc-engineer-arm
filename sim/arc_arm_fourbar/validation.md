# Validation - arc_arm_fourbar

- **urdf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "ok": true}`
- **mjcf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "max_equality_residual": 0.0, "ok": true, "nq": 17, "nu": 5, "neq": 12, "ngeom": 116}`
- **mjcf_hold_stow**: `{"seconds": 3.0, "nan": false, "max_equality_drift": 0.000121, "max_track_err_deg": 0.479, "actuator_torque_Nm": {"shoulder": -3.097, "elbow": 2.36, "wrist_pitch": 0.435, "wrist_roll": 0.035, "gripper": -0.418}, "ok": true}`
- **mjcf_power_off_release**: `{"start_gap_mm": 13.8, "end_gap_mm": 112.1, "t_open_10mm_s": 0.043000000000000003, "t_90pct_open_s": 0.14200000000000002, "ok": true, "note": "ARC rule: release within 1 s of power loss. Servo back-drive is modelled only as 0.05 N*m friction + 0.002 kg*m^2 armature on the gripper joint - an estimate until bench-measured; the result is only as good as that estimate"}`
- **scene**: `{"compiles": true, "nbody": 21, "ngeom": 121}`
- **urdf_in_mujoco**: `{"compiles": true, "nbody": 18, "note": "MuJoCo's URDF importer ignores <mimic>"}`
- **ok**: `true`
- **gazebo_package**: `{"parses": true, "mesh_uris": 116, "missing_meshes": [], "name_clashes": [], "mimic_joints": 12, "actuated": ["shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper"], "plugins": 6, "ok": true, "note": "structure only; the gz-sim run test is gazebo_run (cad/sim/gz_check.py)"}`
- **gazebo_run**: `{"ok": false, "status": "STALE", "gz_version": "8.10.0", "world": "sim/arc_arm_fourbar/worlds/arc_arm.sdf", "poses": 7, "max_track_err_deg": 0.004, "max_mimic_err_deg": 0.342, "max_tcp_err_mm": 2.238, "tolerances": {"track_deg": 1.5, "mimic_deg": 1.0, "tcp_mm": 3.0}, "power_off_release": {"t_open_10mm_s": 0.545, "t_90pct_open_s": 2.517, "end_gap_mm": 82.8, "ok": true}}`
