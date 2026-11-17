# Model map (generated - do not edit)

Regenerate with `cad/tools/make_map.py` (once per variant).  Search here first: every part links to the
file:line that builds it; parameters, interfaces and keep-outs are data files.  Active variant comes from
`params/variant.toml` (override with GRIP).  Inputs hash at generation: `48b9b3450fe5cb0a`.

## Model modules (`cad/arm/`)

| Module | What it holds | Builders and key functions |
|---|---|---|
| [arm/base.py](arm/base.py) | Base: GROUND body (chassis deck, towers, J1/J2 DM-J4340 stators) and the J1/J2 output hubs (motor_hub). | `body_ground` :7, `dm_split` :94, `dm_rotor_part` :106, `motor_hub` :115 |
| [arm/bodies.py](arm/bodies.py) | Body registry: the arm bodies plus the active gripper variant's bodies (GRIPPERS[GRIP]), and build_bodies(). | `build_bodies` :34 |
| [arm/core.py](arm/core.py) | Shared core of the arm model: frames and global parameters (K, Y, T), jaw/pad geometry shared by every gripper, motor interface (DM), purchased-part catalogue (CAT), materials (MAT), the Part_ record and the geometry helpers (box, ycyl, plate, at, to_z, ...). Every other arm module star-imports this one. | `u` :65, `add` :70, `ycyl` :74, `ring` :79, `box` :83, `hexhole` :88, `plate` :126, `link_pockets` :181, `fillet_z` :200, `fillet_y` :209, `at` :218, `to_z` :227, `to_x` :238, `clip_at` :249, `P` :260, `csk` :264 |
| [arm/forearm.py](arm/forearm.py) | Forearm: FOREARM, ROCKER and the GT2 level-keeping pulley. | `gt2_level_pulley` :10, `body_forearm` :23, `body_rocker` :76 |
| [arm/grippers/fourbar.py](arm/grippers/fourbar.py) | Gripper variant FOURBAR (concept): gear-synchronised parallel four-bar, STS3215 direct drive, torsion-spring release. API: fourbar_bodies(), fb_placements(Hd, jaw). Parameters in FB. | `fb_theta` :22, `zc` :31, `zprism` :36, `zlink` :41, `fb_pivots` :54, `body_fb_palm` :62, `body_fb_link` :109, `body_fb_jaw` :157, `fb_placements` :212, `fourbar_bodies` :231 |
| [arm/grippers/screw.py](arm/grippers/screw.py) | Gripper variant SCREW (rev A): Tr8x8 bidirectional lead screw, M2006 via 20T/32T, MGN9 rails, 6061 jaw brackets, constant-torque spring-motor release. API: screw_bodies(), screw_placements(Hd, jaw). | `body_head` :28, `zslot` :137, `body_screw` :145, `body_mgear` :169, `body_jaw` :180, `screw_bodies` :262, `screw_placements` :267 |
| [arm/kinematics.py](arm/kinematics.py) | Kinematics and poses: joints, ik, placements (arm + active gripper), placed, part_mass_g, static_torques, POSES / SEQUENCES / pose_q. | `joints` :11, `ik` :21, `placements` :41, `placed` :54, `part_mass_g` :69, `static_torques` :78, `pose_q` :138 |
| [arm/upper_arm.py](arm/upper_arm.py) | Upper arm: UPPER (J1-driven upper-arm plates), CRANK (J2-driven crank) and the parallel rods (body_rod). | `body_upper` :12, `body_crank` :46, `body_rod` :66 |
| [arm/wrist.py](arm/wrist.py) | Wrist: LEVEL (level member + J3 pitch servo), GRIPPER (pitch frame: shaft, clevis plates, roll housing, J4 roll servo, 6805 bearing) and the roll hub shared by every gripper variant (roll_hub_parts, built from interfaces/roll_*.toml). Roll-stage constants: HX, ROLL_Z, ROLL_XS. | `body_level` :23, `xcyl` :64, `roll_hub_parts` :84, `body_gripper` :104 |

## Parameters (`cad/params/`)

- [arm.toml](params/arm.toml): `T`; `K` (SX, SZ, L1, L2, L3, GRIP, DROP, V1_LEN, V1_ANG, DECK_Z); `Y` (FL, CL, BELT, ROCK, ROD1, UA, TW, RAB, CRANK); `level_keeping` (GT2_T); `j1_hub` (HUB_R, UA_HUB_SCREWS); `harness` (UA_CLIP_YZ)
- [gripper_fourbar.toml](params/gripper_fourbar.toml): `FB` (XG, YG, L, S, E, TEETH, XMAX, PIN_R, ZL0, ZL1, ZG, ZSEC, ZPAD, ZFT, ZFB); `SERVO` (rated_Nm, stall_Nm, speed_s_per_60deg); `SPRING` (pn, od, wire, length, arbor_d, max_torque_Nm, rate_Nm_per_deg, preload_deg, alt_pn); `GRIP_REQ` (donut, pipe, pipe_friction_only)
- [gripper_screw.toml](params/gripper_screw.toml): `LEAD`; `Z_SCREW_T`; `Z_MOTOR_T`; `HXJ_OFF`; `XR_OFF`; `ZS`; `ZM_OFF`; `ZTOP`; `YEB`; `RAIL_END`; `MOT_FACE`; `M2006_FRONT`; `GEAR_Y0`; `GEAR_Y1`; `M2006_HOLES` (pcd, ang)
- [materials.toml](params/materials.toml): `CF`; `PRINT`; `AL`; `STEEL`; `TPU`; `BRASS`; `SHIM`; `PTFE`
- [pads.toml](params/pads.toml): `PAD_R`; `NOTCH`; `WRAP`; `PIPE_OD`
- [variant.toml](params/variant.toml): `grip`; `release`
- [wrist.toml](params/wrist.toml): `SERVO_ANG`; `HX`; `ROLL_Z`; `ROLL_XS`

- [catalogue.toml](data/catalogue.toml): purchased parts (42 entries) - desc, mass, source, verify

## Interfaces (`cad/interfaces/`)

- [dm_j4340__hub_tower.toml](interfaces/dm_j4340__hub_tower.toml): DM-J4340 stator bolts to the CF tower (6x M3 PCD50 + 2 dowels); output flange drives the hub (6x M3 PCD27 + 3x D4 dowels PCD24)
- [roll_horn__roll_hub.toml](interfaces/roll_horn__roll_hub.toml): Roll hub rear wall screws to the 25T aluminium disc horn on the J4 roll servo with 4x M3 - parts: Servo_Horn_25T_roll / Roll_Hub
- [roll_hub__gripper_palm.toml](interfaces/roll_hub__gripper_palm.toml): Gripper palm bolts to the front face of the roll hub flange with 4x M3 - parts: Roll_Hub / Gripper_Palm

## Envelopes (`cad/envelopes/`)

- [field.toml](envelopes/field.toml): `donut_plate_floor` @ DONUT_APPROACH, DONUT_PICK; `lower_tier` @ DONUT_APPROACH, DONUT_PICK, DONUT_LIFT; `pole_above_fingers` @ DONUT_LIFT; `pole_below_donut` @ DONUT_LIFT; `perimeter_wall_at_chute` @ PIPE_CHUTE, PIPE_CHUTE_ROLL90; `scoring_platform` @ DONUT_PLACE

## Checks and outputs

- `tools/quick_check.py` (~25-30 s, every edit) -> `out/<variant>/quick.json`
- `check_interference.py`, `tools/check_holes.py`, `tools/check_engagement.py`, `tools/projected_heights.py` -> `out/<variant>/`; each run is logged in `out/<variant>/manifest.json` with the inputs hash
- `tools/fingerprint.py` -> regression guard against `tests/fingerprints/<variant>.json`
- release generators (export_fab, fea/run_fea, drawings, build_assembly, render/export_render) build the release variant (`params/variant.toml` release) into `fab/`, `fea/out/`, `drawings/out/`, `render/`

## Parts by variant

### Parts - variant FOURBAR (242 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 1041.0 | [arm/base.py:20](arm/base.py#L20) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 49.9 | [arm/base.py:42](arm/base.py#L42) body_ground |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 39.5 | [arm/base.py:42](arm/base.py#L42) body_ground |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:76](arm/base.py#L76) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:23](arm/base.py#L23) body_ground |
| GROUND | J1_Motor_DM-J4340_stator (x2) | CAT | DM-J4340-2EC | 462.0 | [arm/base.py:51](arm/base.py#L51) body_ground |
| GROUND | BHCS_M3x8_motorL (x12) | CAT | BHCS | 12.0 | [arm/base.py:54](arm/base.py#L54) body_ground |
| GROUND | Dowel_3x7_motorL (x4) | CAT | DOWEL | 4.0 | [arm/base.py:58](arm/base.py#L58) body_ground |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:69](arm/base.py#L69) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:71](arm/base.py#L71) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:73](arm/base.py#L73) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:77](arm/base.py#L77) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:78](arm/base.py#L78) body_ground |
| GROUND | Cable_Clip_Base (x3) | CAT | CLIP | 3.0 | [arm/base.py:80](arm/base.py#L80) body_ground |
| GROUND | ESC_C610 | CAT | C610 | 15.0 | [arm/base.py:85](arm/base.py#L85) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.3 | [arm/upper_arm.py:24](arm/upper_arm.py#L24) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 30.7 | [arm/upper_arm.py:24](arm/upper_arm.py#L24) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + drilled | 13.0 | [arm/base.py:142](arm/base.py#L142) motor_hub |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:34](arm/upper_arm.py#L34) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:34](arm/upper_arm.py#L34) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:25](arm/upper_arm.py#L25) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:26](arm/upper_arm.py#L26) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | SHCS_M3x6_J1_Output_Hub (x6) | CAT | SHCS | 6.0 | [arm/base.py:145](arm/base.py#L145) motor_hub |
| UPPER | Dowel_4x5_J1_Output_Hub (x3) | CAT | DOWEL | 3.0 | [arm/base.py:149](arm/base.py#L149) motor_hub |
| UPPER | J1_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:112](arm/base.py#L112) dm_rotor_part |
| UPPER | BHCS_M3x5_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:32](arm/upper_arm.py#L32) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:38](arm/upper_arm.py#L38) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:53](arm/upper_arm.py#L53) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + drilled | 16.5 | [arm/base.py:142](arm/base.py#L142) motor_hub |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:59](arm/upper_arm.py#L59) body_crank |
| CRANK | SHCS_M3x6_J2_Output_Hub_Journal (x6) | CAT | SHCS | 6.0 | [arm/base.py:145](arm/base.py#L145) motor_hub |
| CRANK | Dowel_4x5_J2_Output_Hub_Journal (x3) | CAT | DOWEL | 3.0 | [arm/base.py:149](arm/base.py#L149) motor_hub |
| CRANK | J2_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:112](arm/base.py#L112) dm_rotor_part |
| CRANK | Washer_M4_crank | CAT | WASHER | 0.3 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | SHCS_M4x8_crank | CAT | SHCS | 1.0 | [arm/upper_arm.py:57](arm/upper_arm.py#L57) body_crank |
| CRANK | SB5x8_A | CAT | SB5 | 4.0 | [arm/upper_arm.py:61](arm/upper_arm.py#L61) body_crank |
| CRANK | Nyloc_M4_A | CAT | NYLOC | 0.5 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| ROD_AB | Rod_AB_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:70](arm/upper_arm.py#L70) body_rod |
| ROD_AB | Brg_MR105_Rod_AB (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:72](arm/upper_arm.py#L72) body_rod |
| ROD1 | Rod_1_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:70](arm/upper_arm.py#L70) body_rod |
| ROD1 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:72](arm/upper_arm.py#L72) body_rod |
| FOREARM | Forearm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 46.8 | [arm/forearm.py:37](arm/forearm.py#L37) body_forearm |
| FOREARM | Forearm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:37](arm/forearm.py#L37) body_forearm |
| FOREARM | Elbow_Shaft_D10x101 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, ground e-clip grooves | 61.7 | [arm/forearm.py:43](arm/forearm.py#L43) body_forearm |
| FOREARM | FA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:52](arm/forearm.py#L52) body_forearm |
| FOREARM | FA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:52](arm/forearm.py#L52) body_forearm |
| FOREARM | Spacer_B | AL | custom: D9/D5.2 x 8 alu | 0.9 | [arm/forearm.py:57](arm/forearm.py#L57) body_forearm |
| FOREARM | Belt_Idler_Roller | PRINT | custom: printed roller | 0.6 | [arm/forearm.py:62](arm/forearm.py#L62) body_forearm |
| FOREARM | Belt_Idler_Spacer | AL | custom: D8/D4.2 x 6.5 | 0.6 | [arm/forearm.py:66](arm/forearm.py#L66) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_L | CAT | 6700ZZ | 2.0 | [arm/forearm.py:38](arm/forearm.py#L38) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_R | CAT | 6700ZZ | 2.0 | [arm/forearm.py:39](arm/forearm.py#L39) body_forearm |
| FOREARM | Elbow_Clamp_Collar_L (x2) | CAT | COLLAR10 | 50.0 | [arm/forearm.py:49](arm/forearm.py#L49) body_forearm |
| FOREARM | Eclip_D10_elbow_L (x2) | CAT | ECLIP | 0.6 | [arm/forearm.py:50](arm/forearm.py#L50) body_forearm |
| FOREARM | BHCS_M3x6_FA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/forearm.py:54](arm/forearm.py#L54) body_forearm |
| FOREARM | SB5x12_B | CAT | SB5 | 4.0 | [arm/forearm.py:58](arm/forearm.py#L58) body_forearm |
| FOREARM | Nyloc_M4_B | CAT | NYLOC | 0.5 | [arm/forearm.py:59](arm/forearm.py#L59) body_forearm |
| FOREARM | Belt_Idler_Brg_MR104 | CAT | MR104ZZ | 1.2 | [arm/forearm.py:64](arm/forearm.py#L64) body_forearm |
| FOREARM | Belt_Idler_Brg_MR104_b | CAT | MR104ZZ | 1.2 | [arm/forearm.py:65](arm/forearm.py#L65) body_forearm |
| FOREARM | SHCS_M4x30_idler | CAT | SHCS | 1.0 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Nyloc_M4_idler | CAT | NYLOC | 0.5 | [arm/forearm.py:68](arm/forearm.py#L68) body_forearm |
| FOREARM | GT2_Belt_9mm_Stage2 | CAT | GT2-BELT | 5.5 | [arm/forearm.py:72](arm/forearm.py#L72) body_forearm |
| ROCKER | Level_Rocker_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 8.3 | [arm/forearm.py:81](arm/forearm.py#L81) body_rocker |
| ROCKER | GT2_Pulley_Elbow | AL | custom: 6061 GT2 30T hobbed, hex key af19 | 6.4 | [arm/forearm.py:19](arm/forearm.py#L19) gt2_level_pulley |
| ROCKER | Sleeve_E_outer | AL | custom: D13/D10 sleeve | 0.7 | [arm/forearm.py:84](arm/forearm.py#L84) body_rocker |
| ROCKER | Washer_PTFE_E | PTFE | custom: PTFE rod D13, turned thrust sleeve | 0.7 | [arm/forearm.py:86](arm/forearm.py#L86) body_rocker |
| ROCKER | Shim_Ev1 | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:87](arm/forearm.py#L87) body_rocker |
| ROCKER | GT2_Pulley_Elbow_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:20](arm/forearm.py#L20) gt2_level_pulley |
| ROCKER | SB5x4_Ev1 | CAT | SB5 | 4.0 | [arm/forearm.py:89](arm/forearm.py#L89) body_rocker |
| ROCKER | Nyloc_M4_Ev1 | CAT | NYLOC | 0.5 | [arm/forearm.py:90](arm/forearm.py#L90) body_rocker |
| LEVEL | Wrist_Level_Member_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 5.2 | [arm/wrist.py:37](arm/wrist.py#L37) body_level |
| LEVEL | GT2_Pulley_Wrist | AL | custom: 6061 GT2 30T hobbed, hex key af19 | 6.4 | [arm/forearm.py:19](arm/forearm.py#L19) gt2_level_pulley |
| LEVEL | Servo_Standoff_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_2 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_3 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | GT2_Pulley_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:20](arm/forearm.py#L20) gt2_level_pulley |
| LEVEL | J3_Wrist_Servo_DS3225 | CAT | DS3225MG | 60.0 | [arm/wrist.py:42](arm/wrist.py#L42) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:46](arm/wrist.py#L46) body_level |
| LEVEL | BHCS_M3x6_servo (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:47](arm/wrist.py#L47) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:114](arm/wrist.py#L114) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:123](arm/wrist.py#L123) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:137](arm/wrist.py#L137) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:137](arm/wrist.py#L137) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 24.6 | [arm/wrist.py:161](arm/wrist.py#L161) body_gripper |
| GRIPPER | Eclip_D10_wrist | CAT | ECLIP | 0.3 | [arm/wrist.py:116](arm/wrist.py#L116) body_gripper |
| GRIPPER | Servo_Horn_25T_pitch | CAT | HORN-25T | 3.0 | [arm/wrist.py:117](arm/wrist.py#L117) body_gripper |
| GRIPPER | BHCS_M3x5_horn (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:126](arm/wrist.py#L126) body_gripper |
| GRIPPER | CSK_M3x6_clevis_L (x4) | CAT | CSK | 4.0 | [arm/wrist.py:141](arm/wrist.py#L141) body_gripper |
| GRIPPER | Insert_M3_clevis_L (x8) | CAT | INSERT | 2.4 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | BHCS_M3x6_clevis_R (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:143](arm/wrist.py#L143) body_gripper |
| GRIPPER | Insert_M3_rollear (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:164](arm/wrist.py#L164) body_gripper |
| GRIPPER | J4_Roll_Servo_DS3225 | CAT | DS3225MG | 60.0 | [arm/wrist.py:167](arm/wrist.py#L167) body_gripper |
| GRIPPER | BHCS_M3x6_rollservo (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:77](arm/wrist.py#L77) _xscrew |
| GRIPPER | Brg_6805_Roll | CAT | 6805ZZ | 18.0 | [arm/wrist.py:174](arm/wrist.py#L174) body_gripper |
| HEAD | Roll_Hub | AL | custom: 6061 turned, D25 journal in 6805 | 11.5 | [arm/wrist.py:97](arm/wrist.py#L97) roll_hub_parts |
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print (concept) | 58.1 | [arm/grippers/fourbar.py:91](arm/grippers/fourbar.py#L91) body_fb_palm |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:87](arm/wrist.py#L87) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:77](arm/wrist.py#L77) _xscrew |
| HEAD | Grip_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/grippers/fourbar.py:73](arm/grippers/fourbar.py#L73) body_fb_palm |
| HEAD | Pin_D4x14_ground_LI (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:101](arm/grippers/fourbar.py#L101) body_fb_palm |
| HEAD | Pin_D4x30_ground_RD | CAT | PIN-D4x30 | 3.0 | [arm/grippers/fourbar.py:101](arm/grippers/fourbar.py#L101) body_fb_palm |
| HEAD | Torsion_Spring_Open | CAT | 9271K56 | 3.5 | [arm/grippers/fourbar.py:104](arm/grippers/fourbar.py#L104) body_fb_palm |
| JAW_L | Jaw_Block_L | PRINT | custom: PETG-CF print (concept) | 5.5 | [arm/grippers/fourbar.py:186](arm/grippers/fourbar.py#L186) body_fb_jaw |
| JAW_L | Finger_L_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 5.8 | [arm/grippers/fourbar.py:188](arm/grippers/fourbar.py#L188) body_fb_jaw |
| JAW_L | Pad_L_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 20.4 | [arm/grippers/fourbar.py:192](arm/grippers/fourbar.py#L192) body_fb_jaw |
| JAW_L | Standoff_D6_L0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_L | Standoff_D6_L1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_L | Standoff_D6_L2 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingtopL (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:197](arm/grippers/fourbar.py#L197) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingbotL (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:198](arm/grippers/fourbar.py#L198) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:202](arm/grippers/fourbar.py#L202) body_fb_jaw |
| JAW_R | Jaw_Block_R | PRINT | custom: PETG-CF print (concept) | 5.5 | [arm/grippers/fourbar.py:186](arm/grippers/fourbar.py#L186) body_fb_jaw |
| JAW_R | Finger_R_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 5.8 | [arm/grippers/fourbar.py:188](arm/grippers/fourbar.py#L188) body_fb_jaw |
| JAW_R | Pad_R_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 20.4 | [arm/grippers/fourbar.py:192](arm/grippers/fourbar.py#L192) body_fb_jaw |
| JAW_R | Standoff_D6_R0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_R | Standoff_D6_R1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_R | Standoff_D6_R2 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:195](arm/grippers/fourbar.py#L195) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingtopR (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:197](arm/grippers/fourbar.py#L197) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingbotR (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:198](arm/grippers/fourbar.py#L198) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:202](arm/grippers/fourbar.py#L202) body_fb_jaw |
| LK_LD | Link_LD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_LD | Link_LD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_LD | Sector_m1_77T_L | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:135](arm/grippers/fourbar.py#L135) body_fb_link |
| LK_LD | Washer_LD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:138](arm/grippers/fourbar.py#L138) body_fb_link |
| LK_LD | Servo_Horn_STS_disc | CAT | HORN-25T | 3.0 | [arm/grippers/fourbar.py:141](arm/grippers/fourbar.py#L141) body_fb_link |
| LK_LD | Pin_D4x20_ground_LD | CAT | PIN-D4x20 | 2.0 | [arm/grippers/fourbar.py:143](arm/grippers/fourbar.py#L143) body_fb_link |
| LK_LI | Link_LI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_LI | Link_LI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_RD | Link_RD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_RD | Link_RD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_RD | Sector_m1_77T_R | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:135](arm/grippers/fourbar.py#L135) body_fb_link |
| LK_RD | Washer_RD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:138](arm/grippers/fourbar.py#L138) body_fb_link |
| LK_RI | Link_RI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |
| LK_RI | Link_RI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:118](arm/grippers/fourbar.py#L118) body_fb_link |

### Parts - variant SCREW (314 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 1041.0 | [arm/base.py:20](arm/base.py#L20) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 49.9 | [arm/base.py:42](arm/base.py#L42) body_ground |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 39.5 | [arm/base.py:42](arm/base.py#L42) body_ground |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:68](arm/base.py#L68) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:76](arm/base.py#L76) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:23](arm/base.py#L23) body_ground |
| GROUND | J1_Motor_DM-J4340_stator (x2) | CAT | DM-J4340-2EC | 462.0 | [arm/base.py:51](arm/base.py#L51) body_ground |
| GROUND | BHCS_M3x8_motorL (x12) | CAT | BHCS | 12.0 | [arm/base.py:54](arm/base.py#L54) body_ground |
| GROUND | Dowel_3x7_motorL (x4) | CAT | DOWEL | 4.0 | [arm/base.py:58](arm/base.py#L58) body_ground |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:69](arm/base.py#L69) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:71](arm/base.py#L71) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:73](arm/base.py#L73) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:77](arm/base.py#L77) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:78](arm/base.py#L78) body_ground |
| GROUND | Cable_Clip_Base (x3) | CAT | CLIP | 3.0 | [arm/base.py:80](arm/base.py#L80) body_ground |
| GROUND | ESC_C610 | CAT | C610 | 15.0 | [arm/base.py:85](arm/base.py#L85) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.3 | [arm/upper_arm.py:24](arm/upper_arm.py#L24) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 30.7 | [arm/upper_arm.py:24](arm/upper_arm.py#L24) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + drilled | 13.0 | [arm/base.py:142](arm/base.py#L142) motor_hub |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:34](arm/upper_arm.py#L34) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:34](arm/upper_arm.py#L34) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:25](arm/upper_arm.py#L25) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:26](arm/upper_arm.py#L26) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | SHCS_M3x6_J1_Output_Hub (x6) | CAT | SHCS | 6.0 | [arm/base.py:145](arm/base.py#L145) motor_hub |
| UPPER | Dowel_4x5_J1_Output_Hub (x3) | CAT | DOWEL | 3.0 | [arm/base.py:149](arm/base.py#L149) motor_hub |
| UPPER | J1_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:112](arm/base.py#L112) dm_rotor_part |
| UPPER | BHCS_M3x5_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:32](arm/upper_arm.py#L32) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:38](arm/upper_arm.py#L38) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:53](arm/upper_arm.py#L53) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + drilled | 16.5 | [arm/base.py:142](arm/base.py#L142) motor_hub |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:59](arm/upper_arm.py#L59) body_crank |
| CRANK | SHCS_M3x6_J2_Output_Hub_Journal (x6) | CAT | SHCS | 6.0 | [arm/base.py:145](arm/base.py#L145) motor_hub |
| CRANK | Dowel_4x5_J2_Output_Hub_Journal (x3) | CAT | DOWEL | 3.0 | [arm/base.py:149](arm/base.py#L149) motor_hub |
| CRANK | J2_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:112](arm/base.py#L112) dm_rotor_part |
| CRANK | Washer_M4_crank | CAT | WASHER | 0.3 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | SHCS_M4x8_crank | CAT | SHCS | 1.0 | [arm/upper_arm.py:57](arm/upper_arm.py#L57) body_crank |
| CRANK | SB5x8_A | CAT | SB5 | 4.0 | [arm/upper_arm.py:61](arm/upper_arm.py#L61) body_crank |
| CRANK | Nyloc_M4_A | CAT | NYLOC | 0.5 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| ROD_AB | Rod_AB_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:70](arm/upper_arm.py#L70) body_rod |
| ROD_AB | Brg_MR105_Rod_AB (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:72](arm/upper_arm.py#L72) body_rod |
| ROD1 | Rod_1_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:70](arm/upper_arm.py#L70) body_rod |
| ROD1 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:72](arm/upper_arm.py#L72) body_rod |
| FOREARM | Forearm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 46.8 | [arm/forearm.py:37](arm/forearm.py#L37) body_forearm |
| FOREARM | Forearm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:37](arm/forearm.py#L37) body_forearm |
| FOREARM | Elbow_Shaft_D10x101 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, ground e-clip grooves | 61.7 | [arm/forearm.py:43](arm/forearm.py#L43) body_forearm |
| FOREARM | FA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:52](arm/forearm.py#L52) body_forearm |
| FOREARM | FA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:52](arm/forearm.py#L52) body_forearm |
| FOREARM | Spacer_B | AL | custom: D9/D5.2 x 8 alu | 0.9 | [arm/forearm.py:57](arm/forearm.py#L57) body_forearm |
| FOREARM | Belt_Idler_Roller | PRINT | custom: printed roller | 0.6 | [arm/forearm.py:62](arm/forearm.py#L62) body_forearm |
| FOREARM | Belt_Idler_Spacer | AL | custom: D8/D4.2 x 6.5 | 0.6 | [arm/forearm.py:66](arm/forearm.py#L66) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_L | CAT | 6700ZZ | 2.0 | [arm/forearm.py:38](arm/forearm.py#L38) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_R | CAT | 6700ZZ | 2.0 | [arm/forearm.py:39](arm/forearm.py#L39) body_forearm |
| FOREARM | Elbow_Clamp_Collar_L (x2) | CAT | COLLAR10 | 50.0 | [arm/forearm.py:49](arm/forearm.py#L49) body_forearm |
| FOREARM | Eclip_D10_elbow_L (x2) | CAT | ECLIP | 0.6 | [arm/forearm.py:50](arm/forearm.py#L50) body_forearm |
| FOREARM | BHCS_M3x6_FA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/forearm.py:54](arm/forearm.py#L54) body_forearm |
| FOREARM | SB5x12_B | CAT | SB5 | 4.0 | [arm/forearm.py:58](arm/forearm.py#L58) body_forearm |
| FOREARM | Nyloc_M4_B | CAT | NYLOC | 0.5 | [arm/forearm.py:59](arm/forearm.py#L59) body_forearm |
| FOREARM | Belt_Idler_Brg_MR104 | CAT | MR104ZZ | 1.2 | [arm/forearm.py:64](arm/forearm.py#L64) body_forearm |
| FOREARM | Belt_Idler_Brg_MR104_b | CAT | MR104ZZ | 1.2 | [arm/forearm.py:65](arm/forearm.py#L65) body_forearm |
| FOREARM | SHCS_M4x30_idler | CAT | SHCS | 1.0 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Nyloc_M4_idler | CAT | NYLOC | 0.5 | [arm/forearm.py:68](arm/forearm.py#L68) body_forearm |
| FOREARM | GT2_Belt_9mm_Stage2 | CAT | GT2-BELT | 5.5 | [arm/forearm.py:72](arm/forearm.py#L72) body_forearm |
| ROCKER | Level_Rocker_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 8.3 | [arm/forearm.py:81](arm/forearm.py#L81) body_rocker |
| ROCKER | GT2_Pulley_Elbow | AL | custom: 6061 GT2 30T hobbed, hex key af19 | 6.4 | [arm/forearm.py:19](arm/forearm.py#L19) gt2_level_pulley |
| ROCKER | Sleeve_E_outer | AL | custom: D13/D10 sleeve | 0.7 | [arm/forearm.py:84](arm/forearm.py#L84) body_rocker |
| ROCKER | Washer_PTFE_E | PTFE | custom: PTFE rod D13, turned thrust sleeve | 0.7 | [arm/forearm.py:86](arm/forearm.py#L86) body_rocker |
| ROCKER | Shim_Ev1 | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:87](arm/forearm.py#L87) body_rocker |
| ROCKER | GT2_Pulley_Elbow_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:20](arm/forearm.py#L20) gt2_level_pulley |
| ROCKER | SB5x4_Ev1 | CAT | SB5 | 4.0 | [arm/forearm.py:89](arm/forearm.py#L89) body_rocker |
| ROCKER | Nyloc_M4_Ev1 | CAT | NYLOC | 0.5 | [arm/forearm.py:90](arm/forearm.py#L90) body_rocker |
| LEVEL | Wrist_Level_Member_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 5.2 | [arm/wrist.py:37](arm/wrist.py#L37) body_level |
| LEVEL | GT2_Pulley_Wrist | AL | custom: 6061 GT2 30T hobbed, hex key af19 | 6.4 | [arm/forearm.py:19](arm/forearm.py#L19) gt2_level_pulley |
| LEVEL | Servo_Standoff_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_2 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | Servo_Standoff_3 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 1.2 | [arm/wrist.py:44](arm/wrist.py#L44) body_level |
| LEVEL | GT2_Pulley_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:20](arm/forearm.py#L20) gt2_level_pulley |
| LEVEL | J3_Wrist_Servo_DS3225 | CAT | DS3225MG | 60.0 | [arm/wrist.py:42](arm/wrist.py#L42) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:46](arm/wrist.py#L46) body_level |
| LEVEL | BHCS_M3x6_servo (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:47](arm/wrist.py#L47) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:114](arm/wrist.py#L114) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:123](arm/wrist.py#L123) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:137](arm/wrist.py#L137) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:137](arm/wrist.py#L137) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 24.6 | [arm/wrist.py:161](arm/wrist.py#L161) body_gripper |
| GRIPPER | Eclip_D10_wrist | CAT | ECLIP | 0.3 | [arm/wrist.py:116](arm/wrist.py#L116) body_gripper |
| GRIPPER | Servo_Horn_25T_pitch | CAT | HORN-25T | 3.0 | [arm/wrist.py:117](arm/wrist.py#L117) body_gripper |
| GRIPPER | BHCS_M3x5_horn (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:126](arm/wrist.py#L126) body_gripper |
| GRIPPER | CSK_M3x6_clevis_L (x4) | CAT | CSK | 4.0 | [arm/wrist.py:141](arm/wrist.py#L141) body_gripper |
| GRIPPER | Insert_M3_clevis_L (x8) | CAT | INSERT | 2.4 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | BHCS_M3x6_clevis_R (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:143](arm/wrist.py#L143) body_gripper |
| GRIPPER | Insert_M3_rollear (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:164](arm/wrist.py#L164) body_gripper |
| GRIPPER | J4_Roll_Servo_DS3225 | CAT | DS3225MG | 60.0 | [arm/wrist.py:167](arm/wrist.py#L167) body_gripper |
| GRIPPER | BHCS_M3x6_rollservo (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:77](arm/wrist.py#L77) _xscrew |
| GRIPPER | Brg_6805_Roll | CAT | 6805ZZ | 18.0 | [arm/wrist.py:174](arm/wrist.py#L174) body_gripper |
| HEAD | Roll_Hub | AL | custom: 6061 turned, D25 journal in 6805 | 11.5 | [arm/wrist.py:97](arm/wrist.py#L97) roll_hub_parts |
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print, M3 inserts | 43.3 | [arm/grippers/screw.py:59](arm/grippers/screw.py#L59) body_head |
| HEAD | Screw_End_Block_L | AL | custom: 6061 machined, 688 seat, M3 tapped | 42.5 | [arm/grippers/screw.py:80](arm/grippers/screw.py#L80) body_head |
| HEAD | Screw_End_Block_R | AL | custom: 6061 machined, 688 seat, M3 tapped | 42.3 | [arm/grippers/screw.py:80](arm/grippers/screw.py#L80) body_head |
| HEAD | Spring_Housing | PRINT | custom: PETG-CF print, two-drum spring housing | 6.3 | [arm/grippers/screw.py:85](arm/grippers/screw.py#L85) body_head |
| HEAD | Spring_Output_Drum | AL | custom: 6061 turned, D20 drum on the D8 screw journal, M3 set screw | 12.0 | [arm/grippers/screw.py:87](arm/grippers/screw.py#L87) body_head |
| HEAD | Gripper_Bridge_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 22.0 | [arm/grippers/screw.py:111](arm/grippers/screw.py#L111) body_head |
| HEAD | Motor_Clamp_0 | PRINT | custom: PETG-CF print, M3 inserts, pinch slit | 4.5 | [arm/grippers/screw.py:127](arm/grippers/screw.py#L127) body_head |
| HEAD | Motor_Clamp_1 | PRINT | custom: PETG-CF print, M3 inserts, pinch slit | 4.5 | [arm/grippers/screw.py:127](arm/grippers/screw.py#L127) body_head |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:87](arm/wrist.py#L87) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:77](arm/wrist.py#L77) _xscrew |
| HEAD | MGN9_Rail_L (x2) | CAT | MGN9-RAIL | 54.0 | [arm/grippers/screw.py:51](arm/grippers/screw.py#L51) body_head |
| HEAD | SHCS_M3x8_rail (x8) | CAT | SHCS | 8.0 | [arm/grippers/screw.py:63](arm/grippers/screw.py#L63) body_head |
| HEAD | Insert_M3_rail (x8) | CAT | INSERT | 2.4 | [arm/grippers/screw.py:64](arm/grippers/screw.py#L64) body_head |
| HEAD | Brg_688_Screw_L (x2) | CAT | 688ZZ | 8.0 | [arm/grippers/screw.py:81](arm/grippers/screw.py#L81) body_head |
| HEAD | Dowel_3x20_spring | CAT | DOWEL | 1.0 | [arm/grippers/screw.py:89](arm/grippers/screw.py#L89) body_head |
| HEAD | SetScrew_M3x3_drum | CAT | SETSCREW | 0.3 | [arm/grippers/screw.py:90](arm/grippers/screw.py#L90) body_head |
| HEAD | Spring_Motor_Cassette | CAT | SPRING-MOTOR | 12.0 | [arm/grippers/screw.py:91](arm/grippers/screw.py#L91) body_head |
| HEAD | BHCS_M3x8_cassette (x2) | CAT | BHCS | 2.0 | [arm/grippers/screw.py:94](arm/grippers/screw.py#L94) body_head |
| HEAD | SHCS_M3x40_endblock (x4) | CAT | SHCS | 4.0 | [arm/grippers/screw.py:97](arm/grippers/screw.py#L97) body_head |
| HEAD | BHCS_M3x8_bridge (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:99](arm/grippers/screw.py#L99) body_head |
| HEAD | Grip_Motor_M2006 | CAT | M2006-P36 | 90.0 | [arm/grippers/screw.py:119](arm/grippers/screw.py#L119) body_head |
| HEAD | SHCS_M3x30_motorclamp (x2) | CAT | SHCS | 2.0 | [arm/wrist.py:77](arm/wrist.py#L77) _xscrew |
| HEAD | BHCS_M3x8_clamp (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:130](arm/grippers/screw.py#L130) body_head |
| HEAD | Insert_M3_clamp (x4) | CAT | INSERT | 1.2 | [arm/grippers/screw.py:132](arm/grippers/screw.py#L132) body_head |
| SCREW | Shim_8x10_L | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/grippers/screw.py:161](arm/grippers/screw.py#L161) body_screw |
| SCREW | Shim_8x10_R | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/grippers/screw.py:161](arm/grippers/screw.py#L161) body_screw |
| SCREW | Leadscrew_Tr8x8_bidir | CAT | TR8X8-BIDIR | 88.0 | [arm/grippers/screw.py:151](arm/grippers/screw.py#L151) body_screw |
| SCREW | Screw_Gear_m1_32T | CAT | GEAR-M1-32T | 10.0 | [arm/grippers/screw.py:157](arm/grippers/screw.py#L157) body_screw |
| SCREW | SetScrew_M3x3_screwgear | CAT | SETSCREW | 0.3 | [arm/grippers/screw.py:158](arm/grippers/screw.py#L158) body_screw |
| SCREW | Collar_D8_L | CAT | COLLAR8 | 8.0 | [arm/grippers/screw.py:164](arm/grippers/screw.py#L164) body_screw |
| MGEAR | Motor_Gear_m1_20T | CAT | GEAR-M1-20T | 6.0 | [arm/grippers/screw.py:175](arm/grippers/screw.py#L175) body_mgear |
| MGEAR | SetScrew_M3_motorgear | CAT | SETSCREW | 0.3 | [arm/grippers/screw.py:176](arm/grippers/screw.py#L176) body_mgear |
| JAW_L | Jaw_Bracket_L | AL | custom: 6061 machined, M3 tapped | 52.7 | [arm/grippers/screw.py:208](arm/grippers/screw.py#L208) body_jaw |
| JAW_L | Finger_L_top_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 9.9 | [arm/grippers/screw.py:230](arm/grippers/screw.py#L230) body_jaw |
| JAW_L | Finger_L_bot_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 9.9 | [arm/grippers/screw.py:230](arm/grippers/screw.py#L230) body_jaw |
| JAW_L | Pad_L_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V, bolted | 22.2 | [arm/grippers/screw.py:242](arm/grippers/screw.py#L242) body_jaw |
| JAW_L | Finger_Standoff_D6x50_L0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_L | Finger_Standoff_D6x50_L1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_L | Finger_Standoff_D6x50_L2 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_L | Finger_Standoff_D6x50_L3 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_L | MGN9H_Block_L | CAT | MGN9H | 26.0 | [arm/grippers/screw.py:192](arm/grippers/screw.py#L192) body_jaw |
| JAW_L | Nut_Tr8x8_RH | CAT | NUT-T8 | 12.0 | [arm/grippers/screw.py:210](arm/grippers/screw.py#L210) body_jaw |
| JAW_L | BHCS_M3x6_nutL (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:215](arm/grippers/screw.py#L215) body_jaw |
| JAW_L | BHCS_M3x6_jawL (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:217](arm/grippers/screw.py#L217) body_jaw |
| JAW_L | BHCS_M3x8_fingtopL (x6) | CAT | BHCS | 6.0 | [arm/grippers/screw.py:247](arm/grippers/screw.py#L247) body_jaw |
| JAW_L | BHCS_M3x8_fingbotL (x6) | CAT | BHCS | 6.0 | [arm/grippers/screw.py:249](arm/grippers/screw.py#L249) body_jaw |
| JAW_R | Jaw_Bracket_R | AL | custom: 6061 machined, M3 tapped | 52.7 | [arm/grippers/screw.py:208](arm/grippers/screw.py#L208) body_jaw |
| JAW_R | Nut_Tr8x8_LH | BRASS | custom: CW614N brass, Tr8x8(P2) LH 4-start thread-milled | 11.6 | [arm/grippers/screw.py:213](arm/grippers/screw.py#L213) body_jaw |
| JAW_R | Finger_R_top_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 9.9 | [arm/grippers/screw.py:230](arm/grippers/screw.py#L230) body_jaw |
| JAW_R | Finger_R_bot_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 9.9 | [arm/grippers/screw.py:230](arm/grippers/screw.py#L230) body_jaw |
| JAW_R | Pad_R_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V, bolted | 22.2 | [arm/grippers/screw.py:242](arm/grippers/screw.py#L242) body_jaw |
| JAW_R | Finger_Standoff_D6x50_R0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_R | Finger_Standoff_D6x50_R1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_R | Finger_Standoff_D6x50_R2 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_R | Finger_Standoff_D6x50_R3 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 3.1 | [arm/grippers/screw.py:244](arm/grippers/screw.py#L244) body_jaw |
| JAW_R | MGN9H_Block_R | CAT | MGN9H | 26.0 | [arm/grippers/screw.py:192](arm/grippers/screw.py#L192) body_jaw |
| JAW_R | BHCS_M3x6_nutR (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:215](arm/grippers/screw.py#L215) body_jaw |
| JAW_R | BHCS_M3x6_jawR (x4) | CAT | BHCS | 4.0 | [arm/grippers/screw.py:217](arm/grippers/screw.py#L217) body_jaw |
| JAW_R | BHCS_M3x8_fingtopR (x6) | CAT | BHCS | 6.0 | [arm/grippers/screw.py:247](arm/grippers/screw.py#L247) body_jaw |
| JAW_R | BHCS_M3x8_fingbotR (x6) | CAT | BHCS | 6.0 | [arm/grippers/screw.py:249](arm/grippers/screw.py#L249) body_jaw |

