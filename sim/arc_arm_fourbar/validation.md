# Validation - arc_arm_fourbar

- **urdf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "ok": true}`
- **mjcf_fk**: `{"poses": 7, "max_pos_err_mm": 0.0004, "max_rot_err_deg": 0.0, "max_equality_residual": 0.0, "ok": true, "nq": 16, "nu": 5, "neq": 11, "ngeom": 106}`
- **mjcf_hold_stow**: `{"seconds": 3.0, "nan": false, "max_equality_drift": 0.000115, "max_track_err_deg": 0.479, "actuator_torque_Nm": {"shoulder": -2.767, "elbow": 2.056, "wrist_pitch": 0.339, "wrist_roll": 0.036, "gripper": -0.418}, "ok": true}`
- **mjcf_power_off_release**: `{"start_gap_mm": 13.8, "end_gap_mm": 112.1, "t_open_10mm_s": 0.041, "t_90pct_open_s": 0.137, "ok": true, "note": "ARC rule: release within 1 s of power loss. Servo back-drive is modelled only as 0.05 N*m friction + 0.002 kg*m^2 armature on the gripper joint - an estimate until bench-measured; the result is only as good as that estimate"}`
- **scene**: `{"compiles": true, "nbody": 20, "ngeom": 111}`
- **urdf_in_mujoco**: `{"compiles": true, "nbody": 17, "note": "MuJoCo's URDF importer ignores <mimic>"}`
- **ok**: `true`
- **gazebo_package**: `{"parses": true, "mesh_uris": 106, "missing_meshes": [], "mimic_joints": 11, "actuated": ["shoulder", "elbow", "wrist_pitch", "wrist_roll", "gripper"], "plugins": 6, "ok": true, "note": "structure only - not yet loaded in Gazebo (gz-sim not installed on this machine)"}`
