# Model map (generated - do not edit)

Regenerate with `cad/tools/make_map.py` (once per variant).  Search here first: every part links to the
file:line that builds it; parameters, interfaces and keep-outs are data files.  Active variant comes from
`params/variant.toml` (override with GRIP and BASE_DRIVE).  Inputs hash at generation: `9cf67eeedebaa998`.

## Model modules (`cad/arm/`)

| Module | What it holds | Builders and key functions |
|---|---|---|
| [arm/base.py](arm/base.py) | Base: GROUND body (chassis deck, towers, J1/J2 drives) and the J1/J2 output hubs (motor_hub, joint_drive_parts). Two base drives (params/variant.toml base_drive, $BASE_DRIVE): GEARED (rev B): STS3215 servo + printed m2 18T/54T spur stage on a printed drive frame per tower; the hubs carry the 54T gears. Mates: interfaces/drive_frame__tower.toml, base_hub__drive.toml, sts3215__cradle.toml; sizes from params/base_drive.toml. DIRECT (Fusion "Rev A"): a Damiao DM-J4340-2EC per tower, stator bolted to the tower's outboard face, output flange bolted to the hub flange. Mates: interfaces/dm_j4340__tower.toml, dm_j4340__output_hub.toml. | `drive_layout` :13, `drive_frame` :26, `body_ground` :56, `motor_hub` :168, `joint_drive_parts` :206, `drive_gear_parts` :212, `dm_split` :247, `dm_hub` :294, `dm_output_parts` :315 |
| [arm/bodies.py](arm/bodies.py) | Body registry: the arm bodies plus the active gripper variant's bodies (GRIPPERS[GRIP]), and build_bodies(). | `build_bodies` :33 |
| [arm/core.py](arm/core.py) | Shared core of the arm model: frames and global parameters (K, Y, T), jaw/pad geometry shared by every gripper, actuators (STS_R, BASE_R) and base-drive interfaces, purchased-part catalogue (CAT), materials (MAT), the Part_ record and the geometry helpers (box, ycyl, plate, at, to_z, ...). Every other arm module star-imports this one. | `u` :82, `add` :87, `ycyl` :91, `ring` :96, `box` :100, `hexhole` :105, `plate` :134, `link_pockets` :189, `fillet_z` :208, `at` :217, `to_z` :226, `P` :237, `mirror_y` :241, `csk` :250, `sts_place` :274, `sts_xz` :286, `sts_pocket` :294, `sts_case_screws` :310 |
| [arm/forearm.py](arm/forearm.py) | Forearm: FOREARM, ROCKER, ROD2 and the level-keeping hubs. | `level_hub` :15, `v2_pin` :25, `body_rod2` :44, `body_forearm` :58, `body_rocker` :93 |
| [arm/grippers/fourbar.py](arm/grippers/fourbar.py) | Gripper variant FOURBAR (concept): gear-synchronised parallel four-bar, STS3215 direct drive, torsion-spring release. API: fourbar_bodies(), fb_placements(Hd, jaw). Parameters in FB. | `fb_theta` :21, `zc` :30, `zprism` :35, `zlink` :40, `stadium` :48, `fb_pivots` :62, `body_fb_palm` :70, `body_fb_link` :165, `body_fb_jaw` :227, `fb_placements` :341, `fourbar_bodies` :360 |
| [arm/kinematics.py](arm/kinematics.py) | Kinematics and poses: joints, ik, placements (arm + active gripper), placed, part_mass_g, static_torques, POSES / SEQUENCES / pose_q. | `joints` :11, `ik` :21, `placements` :41, `placed` :55, `part_mass_g` :67, `static_torques` :76, `torques_from_coms` :92, `pose_q` :139 |
| [arm/upper_arm.py](arm/upper_arm.py) | Upper arm: UPPER (J1-driven upper-arm plates), CRANK (J2-driven crank) and the parallel rods (body_rod). | `body_upper` :13, `body_crank` :49, `body_rod` :69 |
| [arm/wrist.py](arm/wrist.py) | Wrist: LEVEL (level member + J3 pitch STS3215 in its printed cradle), GRIPPER (pitch frame: shaft, clevis plates, roll housing with the J4 roll STS3215, 6805 bearing) and the roll hub shared by every gripper variant (roll_hub_parts, built from interfaces/roll_*.toml). Roll-stage constants: HX, ROLL_Z, ROLL_XS. | `j3_cradle` :26, `body_level` :46, `xcyl` :86, `roll_hub_parts` :106, `body_gripper` :126 |

## Parameters (`cad/params/`)

- [actuators.toml](params/actuators.toml): `STS3215` (rated_Nm, stall_Nm, hold_frac); `BASE` (ratio, efficiency); `DM_J4340` (rated_Nm, peak_Nm, hold_frac, rotor_share)
- [arm.toml](params/arm.toml): `T`; `K` (SX, SZ, L1, L2, L3, GRIP, DROP, V1_LEN, V1_ANG, V2_LEN, V2_ANG, DECK_Z); `Y` (FL, ROD2, ROCK, ROD1, UA, TW, RAB, CRANK); `level_keeping` (ROD2_T, ROD2_W); `j1_hub` (HUB_R, UA_HUB_SCREWS); `harness` (UA_CLIP_YZ); `base_plate` (x, half_width, thickness, corner_r, chassis_holes, window, clips_x)
- [base_drive.toml](params/base_drive.toml): `GEAR` (module, z_gear, z_pinion, face, y0, pinion_angle, lightening); `FRAME` (lip, lip_d, boss_r, leg_d)
- [gripper_fourbar.toml](params/gripper_fourbar.toml): `FB` (XG, YG, L, S, E, TEETH, XMAX, PIN_R, ZL0, ZL1, ZG, ZSEC, ZPAD, ZFT, ZFB, WALL_GAP, WALL_INSERTS, ZLB, ZGB, SEAT_Z, Y_OUT, ZLUG); `SPRING` (pn, od, wire, length, arbor_d, max_torque_Nm, rate_Nm_per_deg, preload_deg)
- [materials.toml](params/materials.toml): `CF`; `PRINT`; `AL`; `STEEL`; `TPU`; `BRASS`; `SHIM`; `PTFE`
- [pads.toml](params/pads.toml): `PAD_R`; `NOTCH`; `WRAP`; `PIPE_OD`
- [variant.toml](params/variant.toml): `grip`; `base_drive`; `release`; `release_base_drive`
- [wrist.toml](params/wrist.toml): `SERVO_ANG`; `HX`; `ROLL_Z`; `ROLL_XS`

- [catalogue.toml](data/catalogue.toml): purchased parts (27 entries) - desc, mass, source, verify

## Interfaces (`cad/interfaces/`)

- [base_hub__drive.toml](interfaces/base_hub__drive.toml): Hub stub: D28 collar, 19 AF hex carrying the 54T gear, D20 journal in a 6804 bearing in the drive frame; an M5 end screw clamps the inner race
- [dm_j4340__output_hub.toml](interfaces/dm_j4340__output_hub.toml): Hub flange bolts to the DM-J4340 output flange: 6x M3 SHCS on PCD 27, counterbored from the hub's inboard side, + 3x D4 dowels on PCD 24 - parts: J1_Output_Hub / J2_Output_Hub_Journal / J1_Motor_DM-J4340_rotor / J2_Motor_DM-J4340_rotor
- [dm_j4340__tower.toml](interfaces/dm_j4340__tower.toml): DM-J4340 stator front face bolts to the tower's outboard face: 6x M3 BHCS on PCD 50 from inside the tower + 2x D3 dowels - parts: Tower_L_CF3 / Tower_R_CF3 / J1_Motor_DM-J4340_stator / J2_Motor_DM-J4340_stator
- [drive_frame__tower.toml](interfaces/drive_frame__tower.toml): Drive frame legs bolt to the tower's outboard face: 3x M3 BHCS from inside the tower into heat-set inserts in the legs - parts: Tower_L_CF3 / Tower_R_CF3 / Drive_Frame_L / Drive_Frame_R
- [level_member__j3_cradle.toml](interfaces/level_member__j3_cradle.toml): J3 cradle's four pillars bolt to the level member plate: 4x M3 countersunk from the plate's inboard face into heat-set inserts
- [roll_horn__roll_hub.toml](interfaces/roll_horn__roll_hub.toml): Roll hub rear wall screws to the 25T aluminium disc horn on the J4 roll servo with 4x M3 - parts: Servo_Horn_25T_roll / Roll_Hub
- [roll_hub__gripper_palm.toml](interfaces/roll_hub__gripper_palm.toml): Gripper palm bolts to the front face of the roll hub flange with 4x M3 - parts: Roll_Hub / Gripper_Palm
- [sts3215__cradle.toml](interfaces/sts3215__cradle.toml): STS3215 sits in a printed pocket, fixed by its 4 bottom-cap screws (PA2.0 x 12) through the cradle floor; output via the supplied horn
- [ua_plate__ua_standoff.toml](interfaces/ua_plate__ua_standoff.toml): Upper-arm plates L/R tied by D8 standoffs: M3 clearance holes in both plates, M3-tapped standoff ends, BHCS from outboard - parts: Upper_Arm_L_CF3 / Upper_Arm_R_CF3

## Envelopes (`cad/envelopes/`)

- [field.toml](envelopes/field.toml): `donut_plate_floor` @ DONUT_APPROACH, DONUT_PICK; `lower_tier` @ DONUT_APPROACH, DONUT_PICK, DONUT_LIFT; `pole_above_fingers` @ DONUT_LIFT; `pole_below_donut` @ DONUT_LIFT; `perimeter_wall_at_chute` @ PIPE_CHUTE, PIPE_CHUTE_ROLL90; `scoring_platform` @ DONUT_PLACE

## Checks and outputs

- `tools/quick_check.py` (~25-30 s, every edit) -> `out/<variant>/quick.json`
- `check_interference.py`, `tools/check_holes.py`, `tools/check_engagement.py` -> `out/<variant>/`; each run is logged in `out/<variant>/manifest.json` with the inputs hash
- `tools/fingerprint.py` -> regression guard against `tests/fingerprints/<variant>.json`
- release generators (export_fab, fea/run_fea, render/export_render) build the release variant (`params/variant.toml` release) into `fab/`, `fea/out/`, `render/`
- `docs/paper/make_paper.py` -> `docs/ARC_S2_Engineer_Arm.pdf`, the product summary (from the check results)

## Parts by variant

### Parts - variant FOURBAR (265 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 269.5 | [arm/base.py:73](arm/base.py#L73) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 68.8 | [arm/base.py:119](arm/base.py#L119) _tower |
| GROUND | Drive_Frame_L | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 81.0 | [arm/base.py:134](arm/base.py#L134) _geared_tower_side |
| GROUND | Pinion_m2_18T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:160](arm/base.py#L160) _geared_tower_side |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 64.3 | [arm/base.py:119](arm/base.py#L119) _tower |
| GROUND | Drive_Frame_R | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 81.0 | [arm/base.py:134](arm/base.py#L134) _geared_tower_side |
| GROUND | Pinion_m2_18T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:160](arm/base.py#L160) _geared_tower_side |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:96](arm/base.py#L96) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:76](arm/base.py#L76) body_ground |
| GROUND | Insert_M3_frame_L (x6) | CAT | INSERT | 1.8 | [arm/base.py:137](arm/base.py#L137) _geared_tower_side |
| GROUND | BHCS_M3x6_frame_L (x6) | CAT | BHCS | 6.0 | [arm/base.py:140](arm/base.py#L140) _geared_tower_side |
| GROUND | Brg_6804_J (x2) | CAT | 6804ZZ | 38.0 | [arm/base.py:143](arm/base.py#L143) _geared_tower_side |
| GROUND | J1_Servo_STS (x2) | CAT | STS3215 | 120.0 | [arm/base.py:146](arm/base.py#L146) _geared_tower_side |
| GROUND | Servo_Horn_STS_J (x2) | CAT | HORN-25T | 6.0 | [arm/base.py:149](arm/base.py#L149) _geared_tower_side |
| GROUND | PAN_M2x12_J (x8) | CAT | PAN-M2x12 | 2.4 | [arm/core.py:319](arm/core.py#L319) sts_case_screws |
| GROUND | BHCS_M3x8_pinion_J (x8) | CAT | BHCS | 8.0 | [arm/base.py:163](arm/base.py#L163) _geared_tower_side |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:91](arm/base.py#L91) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:93](arm/base.py#L93) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:97](arm/base.py#L97) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:98](arm/base.py#L98) body_ground |
| GROUND | Cable_Clip_Base (x2) | CAT | CLIP | 2.0 | [arm/base.py:100](arm/base.py#L100) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 32.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.4 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + milled hex | 33.6 | [arm/base.py:186](arm/base.py#L186) motor_hub |
| UPPER | Drive_Gear_m2_54T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:224](arm/base.py#L224) drive_gear_parts |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:28](arm/upper_arm.py#L28) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:29](arm/upper_arm.py#L29) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:30](arm/upper_arm.py#L30) body_upper |
| UPPER | Washer_M5_hub_J1 | CAT | WASHER | 0.3 | [arm/base.py:227](arm/base.py#L227) drive_gear_parts |
| UPPER | SHCS_M5x10_hub_J1 | CAT | SHCS | 1.0 | [arm/base.py:228](arm/base.py#L228) drive_gear_parts |
| UPPER | BHCS_M3x6_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:35](arm/upper_arm.py#L35) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:44](arm/upper_arm.py#L44) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + milled hex | 37.0 | [arm/base.py:186](arm/base.py#L186) motor_hub |
| CRANK | Drive_Gear_m2_54T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:224](arm/base.py#L224) drive_gear_parts |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| CRANK | Washer_M5_hub_J2 | CAT | WASHER | 0.3 | [arm/base.py:227](arm/base.py#L227) drive_gear_parts |
| CRANK | SHCS_M5x10_hub_J2 | CAT | SHCS | 1.0 | [arm/base.py:228](arm/base.py#L228) drive_gear_parts |
| CRANK | Washer_M4_crank | CAT | WASHER | 0.3 | [arm/upper_arm.py:59](arm/upper_arm.py#L59) body_crank |
| CRANK | SHCS_M4x8_crank | CAT | SHCS | 1.0 | [arm/upper_arm.py:60](arm/upper_arm.py#L60) body_crank |
| CRANK | SB5x8_A | CAT | SB5 | 4.0 | [arm/upper_arm.py:64](arm/upper_arm.py#L64) body_crank |
| CRANK | Nyloc_M4_A | CAT | NYLOC | 0.5 | [arm/upper_arm.py:65](arm/upper_arm.py#L65) body_crank |
| ROD_AB | Rod_AB_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:73](arm/upper_arm.py#L73) body_rod |
| ROD_AB | Brg_MR105_Rod_AB (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:75](arm/upper_arm.py#L75) body_rod |
| ROD1 | Rod_1_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:73](arm/upper_arm.py#L73) body_rod |
| ROD1 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:75](arm/upper_arm.py#L75) body_rod |
| FOREARM | Forearm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Forearm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Elbow_Shaft_D10x101 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, ground e-clip grooves | 61.7 | [arm/forearm.py:73](arm/forearm.py#L73) body_forearm |
| FOREARM | FA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:82](arm/forearm.py#L82) body_forearm |
| FOREARM | FA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:82](arm/forearm.py#L82) body_forearm |
| FOREARM | Spacer_B | AL | custom: D9/D5.2 x 8 alu | 0.9 | [arm/forearm.py:87](arm/forearm.py#L87) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_L | CAT | 6700ZZ | 2.0 | [arm/forearm.py:68](arm/forearm.py#L68) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_R | CAT | 6700ZZ | 2.0 | [arm/forearm.py:69](arm/forearm.py#L69) body_forearm |
| FOREARM | Elbow_Clamp_Collar_L (x2) | CAT | COLLAR10 | 50.0 | [arm/forearm.py:79](arm/forearm.py#L79) body_forearm |
| FOREARM | Eclip_D10_elbow_L (x2) | CAT | ECLIP | 0.6 | [arm/forearm.py:80](arm/forearm.py#L80) body_forearm |
| FOREARM | BHCS_M3x6_FA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/forearm.py:84](arm/forearm.py#L84) body_forearm |
| FOREARM | SB5x12_B | CAT | SB5 | 4.0 | [arm/forearm.py:88](arm/forearm.py#L88) body_forearm |
| FOREARM | Nyloc_M4_B | CAT | NYLOC | 0.5 | [arm/forearm.py:89](arm/forearm.py#L89) body_forearm |
| ROCKER | Level_Rocker_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 16.0 | [arm/forearm.py:102](arm/forearm.py#L102) body_rocker |
| ROCKER | Level_Hub_Elbow | AL | custom: 6061 turned hub, hex key af19, 6700 seat | 3.1 | [arm/forearm.py:21](arm/forearm.py#L21) level_hub |
| ROCKER | Washer_Ev2_head | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:31](arm/forearm.py#L31) v2_pin |
| ROCKER | Washer_PTFE_Ev2 | PTFE | custom: PTFE sheet 1.0, laser cut | 0.1 | [arm/forearm.py:33](arm/forearm.py#L33) v2_pin |
| ROCKER | Sleeve_E_outer | AL | custom: D13/D10 sleeve | 0.7 | [arm/forearm.py:105](arm/forearm.py#L105) body_rocker |
| ROCKER | Washer_PTFE_E | PTFE | custom: PTFE rod D13, turned thrust sleeve | 0.7 | [arm/forearm.py:107](arm/forearm.py#L107) body_rocker |
| ROCKER | Shim_Ev1 | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:108](arm/forearm.py#L108) body_rocker |
| ROCKER | Level_Hub_Elbow_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| ROCKER | SB5x8_Ev2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| ROCKER | Nyloc_M4_Ev2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| ROCKER | SB5x4_Ev1 | CAT | SB5 | 4.0 | [arm/forearm.py:110](arm/forearm.py#L110) body_rocker |
| ROCKER | Nyloc_M4_Ev1 | CAT | NYLOC | 0.5 | [arm/forearm.py:111](arm/forearm.py#L111) body_rocker |
| ROD2 | Rod_2_CF4 | CF | custom: 4 mm CF plate (DXF) | 33.1 | [arm/forearm.py:52](arm/forearm.py#L52) body_rod2 |
| ROD2 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/forearm.py:54](arm/forearm.py#L54) body_rod2 |
| LEVEL | Wrist_Level_Member_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 13.3 | [arm/wrist.py:55](arm/wrist.py#L55) body_level |
| LEVEL | Level_Hub_Wrist | AL | custom: 6061 turned hub, hex key af19, 6700 seat | 3.1 | [arm/forearm.py:21](arm/forearm.py#L21) level_hub |
| LEVEL | Washer_Dv2_head | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:31](arm/forearm.py#L31) v2_pin |
| LEVEL | Washer_PTFE_Dv2 | PTFE | custom: PTFE sheet 1.0, laser cut | 0.1 | [arm/forearm.py:33](arm/forearm.py#L33) v2_pin |
| LEVEL | Wrist_Servo_Cradle | PRINT | custom: PETG-CF print, 4x M3 heat-set inserts | 17.5 | [arm/wrist.py:62](arm/wrist.py#L62) body_level |
| LEVEL | Level_Hub_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| LEVEL | SB5x8_Dv2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| LEVEL | Nyloc_M4_Dv2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| LEVEL | J3_Wrist_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:59](arm/wrist.py#L59) body_level |
| LEVEL | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/core.py:319](arm/core.py#L319) sts_case_screws |
| LEVEL | Insert_M3_j3cradle (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:67](arm/wrist.py#L67) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:69](arm/wrist.py#L69) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:136](arm/wrist.py#L136) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 35.0 | [arm/wrist.py:185](arm/wrist.py#L185) body_gripper |
| GRIPPER | Eclip_D10_wrist | CAT | ECLIP | 0.3 | [arm/wrist.py:138](arm/wrist.py#L138) body_gripper |
| GRIPPER | Servo_Horn_25T_pitch | CAT | HORN-25T | 3.0 | [arm/wrist.py:139](arm/wrist.py#L139) body_gripper |
| GRIPPER | BHCS_M3x5_horn (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:148](arm/wrist.py#L148) body_gripper |
| GRIPPER | CSK_M3x6_clevis_L (x4) | CAT | CSK | 4.0 | [arm/wrist.py:163](arm/wrist.py#L163) body_gripper |
| GRIPPER | Insert_M3_clevis_L (x8) | CAT | INSERT | 2.4 | [arm/wrist.py:167](arm/wrist.py#L167) body_gripper |
| GRIPPER | BHCS_M3x6_clevis_R (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:165](arm/wrist.py#L165) body_gripper |
| GRIPPER | J4_Roll_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:187](arm/wrist.py#L187) body_gripper |
| GRIPPER | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/wrist.py:190](arm/wrist.py#L190) body_gripper |
| GRIPPER | Brg_6805_Roll | CAT | 6805ZZ | 18.0 | [arm/wrist.py:195](arm/wrist.py#L195) body_gripper |
| HEAD | Roll_Hub | AL | custom: 6061 turned, D25 journal in 6805 | 11.5 | [arm/wrist.py:119](arm/wrist.py#L119) roll_hub_parts |
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print (concept) | 66.0 | [arm/grippers/fourbar.py:143](arm/grippers/fourbar.py#L143) body_fb_palm |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:109](arm/wrist.py#L109) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:99](arm/wrist.py#L99) _xscrew |
| HEAD | Grip_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/grippers/fourbar.py:83](arm/grippers/fourbar.py#L83) body_fb_palm |
| HEAD | Pin_D4x14_ground_LI (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:153](arm/grippers/fourbar.py#L153) body_fb_palm |
| HEAD | Pin_D4x30_ground_RD | CAT | PIN-D4x30 | 3.0 | [arm/grippers/fourbar.py:153](arm/grippers/fourbar.py#L153) body_fb_palm |
| HEAD | Pin_D4x8_ground_bot_LD (x4) | CAT | PIN-D4x8 | 3.2 | [arm/grippers/fourbar.py:157](arm/grippers/fourbar.py#L157) body_fb_palm |
| HEAD | Torsion_Spring_Open | CAT | 9271K56 | 3.5 | [arm/grippers/fourbar.py:160](arm/grippers/fourbar.py#L160) body_fb_palm |
| JAW_L | Jaw_Block_L | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:306](arm/grippers/fourbar.py#L306) body_fb_jaw |
| JAW_L | Finger_L_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:314](arm/grippers/fourbar.py#L314) body_fb_jaw |
| JAW_L | Pad_L_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:323](arm/grippers/fourbar.py#L323) body_fb_jaw |
| JAW_L | Standoff_D6_L0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_L | Standoff_D6_L1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_L | Insert_M3_wall_L (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:316](arm/grippers/fourbar.py#L316) body_fb_jaw |
| JAW_L | BHCS_M3x6_wall_L (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:318](arm/grippers/fourbar.py#L318) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingtopL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingbotL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:329](arm/grippers/fourbar.py#L329) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:333](arm/grippers/fourbar.py#L333) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_bot_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:336](arm/grippers/fourbar.py#L336) body_fb_jaw |
| JAW_R | Jaw_Block_R | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:306](arm/grippers/fourbar.py#L306) body_fb_jaw |
| JAW_R | Finger_R_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:314](arm/grippers/fourbar.py#L314) body_fb_jaw |
| JAW_R | Pad_R_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:323](arm/grippers/fourbar.py#L323) body_fb_jaw |
| JAW_R | Standoff_D6_R0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_R | Standoff_D6_R1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_R | Insert_M3_wall_R (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:316](arm/grippers/fourbar.py#L316) body_fb_jaw |
| JAW_R | BHCS_M3x6_wall_R (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:318](arm/grippers/fourbar.py#L318) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingtopR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingbotR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:329](arm/grippers/fourbar.py#L329) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:333](arm/grippers/fourbar.py#L333) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_bot_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:336](arm/grippers/fourbar.py#L336) body_fb_jaw |
| LK_LD | Link_LD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Link_LD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Link_LD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Sector_m1_77T_L | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:191](arm/grippers/fourbar.py#L191) body_fb_link |
| LK_LD | Washer_LD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:194](arm/grippers/fourbar.py#L194) body_fb_link |
| LK_LD | Servo_Horn_STS_disc | CAT | HORN-25T | 3.0 | [arm/grippers/fourbar.py:200](arm/grippers/fourbar.py#L200) body_fb_link |
| LK_LD | Pin_D4x20_ground_LD | CAT | PIN-D4x20 | 2.0 | [arm/grippers/fourbar.py:202](arm/grippers/fourbar.py#L202) body_fb_link |
| LK_LI | Link_LI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LI | Link_LI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LI | Link_LI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Sector_m1_77T_R | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:191](arm/grippers/fourbar.py#L191) body_fb_link |
| LK_RD | Washer_RD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:194](arm/grippers/fourbar.py#L194) body_fb_link |
| LK_RI | Link_RI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RI | Link_RI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RI | Link_RI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |

### Parts - variant FOURBAR_DIRECT (259 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 269.5 | [arm/base.py:73](arm/base.py#L73) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 49.9 | [arm/base.py:119](arm/base.py#L119) _tower |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 39.5 | [arm/base.py:119](arm/base.py#L119) _tower |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:88](arm/base.py#L88) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:96](arm/base.py#L96) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:76](arm/base.py#L76) body_ground |
| GROUND | J1_Motor_DM-J4340_stator (x2) | CAT | DM-J4340-2EC | 462.0 | [arm/base.py:283](arm/base.py#L283) _dm_tower_side |
| GROUND | BHCS_M3x6_motorL (x12) | CAT | BHCS | 12.0 | [arm/base.py:286](arm/base.py#L286) _dm_tower_side |
| GROUND | Dowel_3x7_motorL (x4) | CAT | DOWEL | 4.0 | [arm/base.py:289](arm/base.py#L289) _dm_tower_side |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:91](arm/base.py#L91) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:93](arm/base.py#L93) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:97](arm/base.py#L97) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:98](arm/base.py#L98) body_ground |
| GROUND | Cable_Clip_Base (x2) | CAT | CLIP | 2.0 | [arm/base.py:100](arm/base.py#L100) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 32.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.4 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + drilled | 13.0 | [arm/base.py:311](arm/base.py#L311) dm_hub |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:28](arm/upper_arm.py#L28) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:29](arm/upper_arm.py#L29) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:30](arm/upper_arm.py#L30) body_upper |
| UPPER | J1_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:330](arm/base.py#L330) dm_output_parts |
| UPPER | SHCS_M3x6_hub_J (x6) | CAT | SHCS | 6.0 | [arm/base.py:335](arm/base.py#L335) dm_output_parts |
| UPPER | Dowel_4x5_hub_J (x3) | CAT | DOWEL | 3.0 | [arm/base.py:339](arm/base.py#L339) dm_output_parts |
| UPPER | BHCS_M3x6_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:35](arm/upper_arm.py#L35) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:44](arm/upper_arm.py#L44) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + drilled | 16.5 | [arm/base.py:311](arm/base.py#L311) dm_hub |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| CRANK | J2_Motor_DM-J4340_rotor | CAT | DM-J4340-2EC | 99.0 | [arm/base.py:330](arm/base.py#L330) dm_output_parts |
| CRANK | SHCS_M3x6_hub_J (x6) | CAT | SHCS | 6.0 | [arm/base.py:335](arm/base.py#L335) dm_output_parts |
| CRANK | Dowel_4x5_hub_J (x3) | CAT | DOWEL | 3.0 | [arm/base.py:339](arm/base.py#L339) dm_output_parts |
| CRANK | Washer_M4_crank | CAT | WASHER | 0.3 | [arm/upper_arm.py:59](arm/upper_arm.py#L59) body_crank |
| CRANK | SHCS_M4x8_crank | CAT | SHCS | 1.0 | [arm/upper_arm.py:60](arm/upper_arm.py#L60) body_crank |
| CRANK | SB5x8_A | CAT | SB5 | 4.0 | [arm/upper_arm.py:64](arm/upper_arm.py#L64) body_crank |
| CRANK | Nyloc_M4_A | CAT | NYLOC | 0.5 | [arm/upper_arm.py:65](arm/upper_arm.py#L65) body_crank |
| ROD_AB | Rod_AB_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:73](arm/upper_arm.py#L73) body_rod |
| ROD_AB | Brg_MR105_Rod_AB (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:75](arm/upper_arm.py#L75) body_rod |
| ROD1 | Rod_1_CF3 | CF | custom: 3 mm CF plate (DXF) | 17.3 | [arm/upper_arm.py:73](arm/upper_arm.py#L73) body_rod |
| ROD1 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/upper_arm.py:75](arm/upper_arm.py#L75) body_rod |
| FOREARM | Forearm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Forearm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 37.8 | [arm/forearm.py:67](arm/forearm.py#L67) body_forearm |
| FOREARM | Elbow_Shaft_D10x101 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, ground e-clip grooves | 61.7 | [arm/forearm.py:73](arm/forearm.py#L73) body_forearm |
| FOREARM | FA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:82](arm/forearm.py#L82) body_forearm |
| FOREARM | FA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 4.0 | [arm/forearm.py:82](arm/forearm.py#L82) body_forearm |
| FOREARM | Spacer_B | AL | custom: D9/D5.2 x 8 alu | 0.9 | [arm/forearm.py:87](arm/forearm.py#L87) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_L | CAT | 6700ZZ | 2.0 | [arm/forearm.py:68](arm/forearm.py#L68) body_forearm |
| FOREARM | Brg_6700_Wrist_FA_R | CAT | 6700ZZ | 2.0 | [arm/forearm.py:69](arm/forearm.py#L69) body_forearm |
| FOREARM | Elbow_Clamp_Collar_L (x2) | CAT | COLLAR10 | 50.0 | [arm/forearm.py:79](arm/forearm.py#L79) body_forearm |
| FOREARM | Eclip_D10_elbow_L (x2) | CAT | ECLIP | 0.6 | [arm/forearm.py:80](arm/forearm.py#L80) body_forearm |
| FOREARM | BHCS_M3x6_FA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/forearm.py:84](arm/forearm.py#L84) body_forearm |
| FOREARM | SB5x12_B | CAT | SB5 | 4.0 | [arm/forearm.py:88](arm/forearm.py#L88) body_forearm |
| FOREARM | Nyloc_M4_B | CAT | NYLOC | 0.5 | [arm/forearm.py:89](arm/forearm.py#L89) body_forearm |
| ROCKER | Level_Rocker_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 16.0 | [arm/forearm.py:102](arm/forearm.py#L102) body_rocker |
| ROCKER | Level_Hub_Elbow | AL | custom: 6061 turned hub, hex key af19, 6700 seat | 3.1 | [arm/forearm.py:21](arm/forearm.py#L21) level_hub |
| ROCKER | Washer_Ev2_head | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:31](arm/forearm.py#L31) v2_pin |
| ROCKER | Washer_PTFE_Ev2 | PTFE | custom: PTFE sheet 1.0, laser cut | 0.1 | [arm/forearm.py:33](arm/forearm.py#L33) v2_pin |
| ROCKER | Sleeve_E_outer | AL | custom: D13/D10 sleeve | 0.7 | [arm/forearm.py:105](arm/forearm.py#L105) body_rocker |
| ROCKER | Washer_PTFE_E | PTFE | custom: PTFE rod D13, turned thrust sleeve | 0.7 | [arm/forearm.py:107](arm/forearm.py#L107) body_rocker |
| ROCKER | Shim_Ev1 | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:108](arm/forearm.py#L108) body_rocker |
| ROCKER | Level_Hub_Elbow_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| ROCKER | SB5x8_Ev2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| ROCKER | Nyloc_M4_Ev2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| ROCKER | SB5x4_Ev1 | CAT | SB5 | 4.0 | [arm/forearm.py:110](arm/forearm.py#L110) body_rocker |
| ROCKER | Nyloc_M4_Ev1 | CAT | NYLOC | 0.5 | [arm/forearm.py:111](arm/forearm.py#L111) body_rocker |
| ROD2 | Rod_2_CF4 | CF | custom: 4 mm CF plate (DXF) | 33.1 | [arm/forearm.py:52](arm/forearm.py#L52) body_rod2 |
| ROD2 | Brg_MR105_Rod (x2) | CAT | MR105ZZ | 2.4 | [arm/forearm.py:54](arm/forearm.py#L54) body_rod2 |
| LEVEL | Wrist_Level_Member_CF3 | CF | custom: 3 mm CF plate (DXF), hex af19 | 13.3 | [arm/wrist.py:55](arm/wrist.py#L55) body_level |
| LEVEL | Level_Hub_Wrist | AL | custom: 6061 turned hub, hex key af19, 6700 seat | 3.1 | [arm/forearm.py:21](arm/forearm.py#L21) level_hub |
| LEVEL | Washer_Dv2_head | SHIM | custom: 301 SS shim stock 0.5, laser cut | 0.1 | [arm/forearm.py:31](arm/forearm.py#L31) v2_pin |
| LEVEL | Washer_PTFE_Dv2 | PTFE | custom: PTFE sheet 1.0, laser cut | 0.1 | [arm/forearm.py:33](arm/forearm.py#L33) v2_pin |
| LEVEL | Wrist_Servo_Cradle | PRINT | custom: PETG-CF print, 4x M3 heat-set inserts | 17.5 | [arm/wrist.py:62](arm/wrist.py#L62) body_level |
| LEVEL | Level_Hub_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| LEVEL | SB5x8_Dv2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| LEVEL | Nyloc_M4_Dv2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| LEVEL | J3_Wrist_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:59](arm/wrist.py#L59) body_level |
| LEVEL | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/core.py:319](arm/core.py#L319) sts_case_screws |
| LEVEL | Insert_M3_j3cradle (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:67](arm/wrist.py#L67) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:69](arm/wrist.py#L69) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:136](arm/wrist.py#L136) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 35.0 | [arm/wrist.py:185](arm/wrist.py#L185) body_gripper |
| GRIPPER | Eclip_D10_wrist | CAT | ECLIP | 0.3 | [arm/wrist.py:138](arm/wrist.py#L138) body_gripper |
| GRIPPER | Servo_Horn_25T_pitch | CAT | HORN-25T | 3.0 | [arm/wrist.py:139](arm/wrist.py#L139) body_gripper |
| GRIPPER | BHCS_M3x5_horn (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:148](arm/wrist.py#L148) body_gripper |
| GRIPPER | CSK_M3x6_clevis_L (x4) | CAT | CSK | 4.0 | [arm/wrist.py:163](arm/wrist.py#L163) body_gripper |
| GRIPPER | Insert_M3_clevis_L (x8) | CAT | INSERT | 2.4 | [arm/wrist.py:167](arm/wrist.py#L167) body_gripper |
| GRIPPER | BHCS_M3x6_clevis_R (x4) | CAT | BHCS | 4.0 | [arm/wrist.py:165](arm/wrist.py#L165) body_gripper |
| GRIPPER | J4_Roll_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:187](arm/wrist.py#L187) body_gripper |
| GRIPPER | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/wrist.py:190](arm/wrist.py#L190) body_gripper |
| GRIPPER | Brg_6805_Roll | CAT | 6805ZZ | 18.0 | [arm/wrist.py:195](arm/wrist.py#L195) body_gripper |
| HEAD | Roll_Hub | AL | custom: 6061 turned, D25 journal in 6805 | 11.5 | [arm/wrist.py:119](arm/wrist.py#L119) roll_hub_parts |
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print (concept) | 66.0 | [arm/grippers/fourbar.py:143](arm/grippers/fourbar.py#L143) body_fb_palm |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:109](arm/wrist.py#L109) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:99](arm/wrist.py#L99) _xscrew |
| HEAD | Grip_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/grippers/fourbar.py:83](arm/grippers/fourbar.py#L83) body_fb_palm |
| HEAD | Pin_D4x14_ground_LI (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:153](arm/grippers/fourbar.py#L153) body_fb_palm |
| HEAD | Pin_D4x30_ground_RD | CAT | PIN-D4x30 | 3.0 | [arm/grippers/fourbar.py:153](arm/grippers/fourbar.py#L153) body_fb_palm |
| HEAD | Pin_D4x8_ground_bot_LD (x4) | CAT | PIN-D4x8 | 3.2 | [arm/grippers/fourbar.py:157](arm/grippers/fourbar.py#L157) body_fb_palm |
| HEAD | Torsion_Spring_Open | CAT | 9271K56 | 3.5 | [arm/grippers/fourbar.py:160](arm/grippers/fourbar.py#L160) body_fb_palm |
| JAW_L | Jaw_Block_L | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:306](arm/grippers/fourbar.py#L306) body_fb_jaw |
| JAW_L | Finger_L_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:314](arm/grippers/fourbar.py#L314) body_fb_jaw |
| JAW_L | Pad_L_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:323](arm/grippers/fourbar.py#L323) body_fb_jaw |
| JAW_L | Standoff_D6_L0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_L | Standoff_D6_L1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_L | Insert_M3_wall_L (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:316](arm/grippers/fourbar.py#L316) body_fb_jaw |
| JAW_L | BHCS_M3x6_wall_L (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:318](arm/grippers/fourbar.py#L318) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingtopL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingbotL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:329](arm/grippers/fourbar.py#L329) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:333](arm/grippers/fourbar.py#L333) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_bot_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:336](arm/grippers/fourbar.py#L336) body_fb_jaw |
| JAW_R | Jaw_Block_R | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:306](arm/grippers/fourbar.py#L306) body_fb_jaw |
| JAW_R | Finger_R_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:314](arm/grippers/fourbar.py#L314) body_fb_jaw |
| JAW_R | Pad_R_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:323](arm/grippers/fourbar.py#L323) body_fb_jaw |
| JAW_R | Standoff_D6_R0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_R | Standoff_D6_R1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:326](arm/grippers/fourbar.py#L326) body_fb_jaw |
| JAW_R | Insert_M3_wall_R (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:316](arm/grippers/fourbar.py#L316) body_fb_jaw |
| JAW_R | BHCS_M3x6_wall_R (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:318](arm/grippers/fourbar.py#L318) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingtopR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingbotR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:329](arm/grippers/fourbar.py#L329) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:333](arm/grippers/fourbar.py#L333) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_bot_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:336](arm/grippers/fourbar.py#L336) body_fb_jaw |
| LK_LD | Link_LD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Link_LD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Link_LD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LD | Sector_m1_77T_L | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:191](arm/grippers/fourbar.py#L191) body_fb_link |
| LK_LD | Washer_LD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:194](arm/grippers/fourbar.py#L194) body_fb_link |
| LK_LD | Servo_Horn_STS_disc | CAT | HORN-25T | 3.0 | [arm/grippers/fourbar.py:200](arm/grippers/fourbar.py#L200) body_fb_link |
| LK_LD | Pin_D4x20_ground_LD | CAT | PIN-D4x20 | 2.0 | [arm/grippers/fourbar.py:202](arm/grippers/fourbar.py#L202) body_fb_link |
| LK_LI | Link_LI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LI | Link_LI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_LI | Link_LI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Link_RD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RD | Sector_m1_77T_R | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:191](arm/grippers/fourbar.py#L191) body_fb_link |
| LK_RD | Washer_RD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:194](arm/grippers/fourbar.py#L194) body_fb_link |
| LK_RI | Link_RI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RI | Link_RI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |
| LK_RI | Link_RI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:174](arm/grippers/fourbar.py#L174) body_fb_link |

