# Model map (generated - do not edit)

Regenerate with `cad/tools/make_map.py` (once per variant).  Search here first: every part links to the
file:line that builds it; parameters, interfaces and keep-outs are data files.  Active variant comes from
`params/variant.toml` (override with GRIP).  Inputs hash at generation: `a6a5f3405c32a209`.

## Model modules (`cad/arm/`)

| Module | What it holds | Builders and key functions |
|---|---|---|
| [arm/base.py](arm/base.py) | Base: GROUND body (chassis deck, towers, J1/J2 drives: STS3215 servo + printed m2 spur stage on a printed drive frame per tower) and the J1/J2 output hubs with their 54T gears (motor_hub, drive_gear_parts). The drive's mates come from interfaces/drive_frame__tower.toml, base_hub__drive.toml and sts3215__cradle.toml; its sizes from params/base_drive.toml. | `drive_layout` :10, `drive_frame` :23, `body_ground` :53, `motor_hub` :150, `drive_gear_parts` :178 |
| [arm/bodies.py](arm/bodies.py) | Body registry: the arm bodies plus the active gripper variant's bodies (GRIPPERS[GRIP]), and build_bodies(). | `build_bodies` :34 |
| [arm/core.py](arm/core.py) | Shared core of the arm model: frames and global parameters (K, Y, T), jaw/pad geometry shared by every gripper, actuators (STS_R, BASE_R) and base-drive interfaces, purchased-part catalogue (CAT), materials (MAT), the Part_ record and the geometry helpers (box, ycyl, plate, at, to_z, ...). Every other arm module star-imports this one. | `u` :78, `add` :83, `ycyl` :87, `ring` :92, `box` :96, `hexhole` :101, `plate` :139, `link_pockets` :194, `fillet_z` :213, `fillet_y` :222, `at` :231, `to_z` :240, `to_x` :251, `clip_at` :262, `P` :273, `csk` :277, `sts_place` :301, `sts_xz` :313, `sts_pocket` :321, `sts_case_screws` :337 |
| [arm/forearm.py](arm/forearm.py) | Forearm: FOREARM, ROCKER, ROD2 and the level-keeping hubs. | `level_hub` :15, `v2_pin` :25, `body_rod2` :44, `body_forearm` :58, `body_rocker` :93 |
| [arm/grippers/fourbar.py](arm/grippers/fourbar.py) | Gripper variant FOURBAR (concept): gear-synchronised parallel four-bar, STS3215 direct drive, torsion-spring release. API: fourbar_bodies(), fb_placements(Hd, jaw). Parameters in FB. | `fb_theta` :22, `zc` :31, `zprism` :36, `zlink` :41, `stadium` :54, `fb_pivots` :69, `body_fb_palm` :77, `body_fb_link` :167, `body_fb_jaw` :226, `fb_placements` :345, `fourbar_bodies` :364 |
| [arm/grippers/screw.py](arm/grippers/screw.py) | Gripper variant SCREW (rev A): Tr8x8 bidirectional lead screw, M2006 via 20T/32T, MGN9 rails, 6061 jaw brackets, constant-torque spring-motor release. API: screw_bodies(), screw_placements(Hd, jaw). | `body_head` :28, `zslot` :137, `body_screw` :145, `body_mgear` :169, `body_jaw` :180, `screw_bodies` :262, `screw_placements` :267 |
| [arm/kinematics.py](arm/kinematics.py) | Kinematics and poses: joints, ik, placements (arm + active gripper), placed, part_mass_g, static_torques, POSES / SEQUENCES / pose_q. | `joints` :11, `ik` :21, `placements` :41, `placed` :55, `part_mass_g` :67, `static_torques` :74, `pose_q` :132 |
| [arm/upper_arm.py](arm/upper_arm.py) | Upper arm: UPPER (J1-driven upper-arm plates), CRANK (J2-driven crank) and the parallel rods (body_rod). | `body_upper` :13, `body_crank` :49, `body_rod` :69 |
| [arm/wrist.py](arm/wrist.py) | Wrist: LEVEL (level member + J3 pitch STS3215 in its printed cradle), GRIPPER (pitch frame: shaft, clevis plates, roll housing with the J4 roll STS3215, 6805 bearing) and the roll hub shared by every gripper variant (roll_hub_parts, built from interfaces/roll_*.toml). Roll-stage constants: HX, ROLL_Z, ROLL_XS. | `j3_cradle` :26, `body_level` :46, `xcyl` :86, `roll_hub_parts` :106, `body_gripper` :126 |

## Parameters (`cad/params/`)

- [actuators.toml](params/actuators.toml): `STS3215` (rated_Nm, stall_Nm, speed_s_per_60deg, hold_frac); `BASE` (ratio, efficiency)
- [arm.toml](params/arm.toml): `T`; `K` (SX, SZ, L1, L2, L3, GRIP, DROP, V1_LEN, V1_ANG, V2_LEN, V2_ANG, DECK_Z); `Y` (FL, CL, ROD2, ROCK, ROD1, UA, TW, RAB, CRANK); `level_keeping` (ROD2_T, ROD2_W, GT2_T); `j1_hub` (HUB_R, UA_HUB_SCREWS); `harness` (UA_CLIP_YZ)
- [base_drive.toml](params/base_drive.toml): `GEAR` (module, z_gear, z_pinion, face, y0, pinion_angle, lightening); `FRAME` (lip, lip_d, boss_r, leg_d)
- [gripper_fourbar.toml](params/gripper_fourbar.toml): `FB` (XG, YG, L, S, E, TEETH, XMAX, PIN_R, ZL0, ZL1, ZG, ZSEC, ZPAD, ZFT, ZFB, WALL_GAP, WALL_INSERTS, ZLB, ZGB, ZLUG); `SERVO` (rated_Nm, stall_Nm, speed_s_per_60deg); `SPRING` (pn, od, wire, length, arbor_d, max_torque_Nm, rate_Nm_per_deg, preload_deg, alt_pn); `GRIP_REQ` (donut, pipe, pipe_friction_only)
- [gripper_screw.toml](params/gripper_screw.toml): `LEAD`; `Z_SCREW_T`; `Z_MOTOR_T`; `HXJ_OFF`; `XR_OFF`; `ZS`; `ZM_OFF`; `ZTOP`; `YEB`; `RAIL_END`; `MOT_FACE`; `M2006_FRONT`; `GEAR_Y0`; `GEAR_Y1`; `M2006_HOLES` (pcd, ang)
- [materials.toml](params/materials.toml): `CF`; `PRINT`; `AL`; `STEEL`; `TPU`; `BRASS`; `SHIM`; `PTFE`
- [pads.toml](params/pads.toml): `PAD_R`; `NOTCH`; `WRAP`; `PIPE_OD`
- [variant.toml](params/variant.toml): `grip`; `release`
- [wrist.toml](params/wrist.toml): `SERVO_ANG`; `HX`; `ROLL_Z`; `ROLL_XS`

- [catalogue.toml](data/catalogue.toml): purchased parts (44 entries) - desc, mass, source, verify

## Interfaces (`cad/interfaces/`)

- [base_hub__drive.toml](interfaces/base_hub__drive.toml): Hub stub: D24 collar, 19 AF hex carrying the 54T gear, D20 journal in a 6804 bearing in the drive frame; an M5 end screw clamps the inner race
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
- `check_interference.py`, `tools/check_holes.py`, `tools/check_engagement.py`, `tools/projected_heights.py` -> `out/<variant>/`; each run is logged in `out/<variant>/manifest.json` with the inputs hash
- `tools/fingerprint.py` -> regression guard against `tests/fingerprints/<variant>.json`
- release generators (export_fab, fea/run_fea, drawings, build_assembly, render/export_render) build the release variant (`params/variant.toml` release) into `fab/`, `fea/out/`, `drawings/out/`, `render/`

## Parts by variant

### Parts - variant FOURBAR (267 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 1041.0 | [arm/base.py:66](arm/base.py#L66) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 68.8 | [arm/base.py:87](arm/base.py#L87) body_ground |
| GROUND | Drive_Frame_L | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 80.8 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Pinion_m2_18T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:115](arm/base.py#L115) body_ground |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 64.3 | [arm/base.py:87](arm/base.py#L87) body_ground |
| GROUND | Drive_Frame_R | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 80.8 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Pinion_m2_18T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:115](arm/base.py#L115) body_ground |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:135](arm/base.py#L135) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:69](arm/base.py#L69) body_ground |
| GROUND | Insert_M3_frame_L (x6) | CAT | INSERT | 1.8 | [arm/base.py:92](arm/base.py#L92) body_ground |
| GROUND | BHCS_M3x6_frame_L (x6) | CAT | BHCS | 6.0 | [arm/base.py:95](arm/base.py#L95) body_ground |
| GROUND | Brg_6804_J (x2) | CAT | 6804ZZ | 38.0 | [arm/base.py:98](arm/base.py#L98) body_ground |
| GROUND | J1_Servo_STS (x2) | CAT | STS3215 | 120.0 | [arm/base.py:101](arm/base.py#L101) body_ground |
| GROUND | Servo_Horn_STS_J (x2) | CAT | HORN-25T | 6.0 | [arm/base.py:104](arm/base.py#L104) body_ground |
| GROUND | PAN_M2x12_J (x8) | CAT | PAN-M2x12 | 2.4 | [arm/core.py:345](arm/core.py#L345) sts_case_screws |
| GROUND | BHCS_M3x8_pinion_J (x8) | CAT | BHCS | 8.0 | [arm/base.py:118](arm/base.py#L118) body_ground |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:128](arm/base.py#L128) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:130](arm/base.py#L130) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:132](arm/base.py#L132) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:136](arm/base.py#L136) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:137](arm/base.py#L137) body_ground |
| GROUND | Cable_Clip_Base (x3) | CAT | CLIP | 3.0 | [arm/base.py:139](arm/base.py#L139) body_ground |
| GROUND | ESC_C610 | CAT | C610 | 15.0 | [arm/base.py:144](arm/base.py#L144) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 32.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.4 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + milled hex | 32.6 | [arm/base.py:174](arm/base.py#L174) motor_hub |
| UPPER | Drive_Gear_m2_54T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:190](arm/base.py#L190) drive_gear_parts |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:28](arm/upper_arm.py#L28) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:29](arm/upper_arm.py#L29) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:30](arm/upper_arm.py#L30) body_upper |
| UPPER | Washer_M5_hub_J1 | CAT | WASHER | 0.3 | [arm/base.py:193](arm/base.py#L193) drive_gear_parts |
| UPPER | SHCS_M5x10_hub_J1 | CAT | SHCS | 1.0 | [arm/base.py:194](arm/base.py#L194) drive_gear_parts |
| UPPER | BHCS_M3x6_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:35](arm/upper_arm.py#L35) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:44](arm/upper_arm.py#L44) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + milled hex | 36.0 | [arm/base.py:174](arm/base.py#L174) motor_hub |
| CRANK | Drive_Gear_m2_54T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:190](arm/base.py#L190) drive_gear_parts |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| CRANK | Washer_M5_hub_J2 | CAT | WASHER | 0.3 | [arm/base.py:193](arm/base.py#L193) drive_gear_parts |
| CRANK | SHCS_M5x10_hub_J2 | CAT | SHCS | 1.0 | [arm/base.py:194](arm/base.py#L194) drive_gear_parts |
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
| LEVEL | Wrist_Servo_Cradle | PRINT | custom: PETG-CF print, 4x M3 heat-set inserts | 17.3 | [arm/wrist.py:62](arm/wrist.py#L62) body_level |
| LEVEL | Level_Hub_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| LEVEL | SB5x8_Dv2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| LEVEL | Nyloc_M4_Dv2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| LEVEL | J3_Wrist_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:59](arm/wrist.py#L59) body_level |
| LEVEL | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/core.py:345](arm/core.py#L345) sts_case_screws |
| LEVEL | Insert_M3_j3cradle (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:67](arm/wrist.py#L67) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:69](arm/wrist.py#L69) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:136](arm/wrist.py#L136) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 34.9 | [arm/wrist.py:185](arm/wrist.py#L185) body_gripper |
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
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print (concept) | 62.8 | [arm/grippers/fourbar.py:145](arm/grippers/fourbar.py#L145) body_fb_palm |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:109](arm/wrist.py#L109) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:99](arm/wrist.py#L99) _xscrew |
| HEAD | Grip_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/grippers/fourbar.py:88](arm/grippers/fourbar.py#L88) body_fb_palm |
| HEAD | Pin_D4x14_ground_LI (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:155](arm/grippers/fourbar.py#L155) body_fb_palm |
| HEAD | Pin_D4x30_ground_RD | CAT | PIN-D4x30 | 3.0 | [arm/grippers/fourbar.py:155](arm/grippers/fourbar.py#L155) body_fb_palm |
| HEAD | Pin_D4x8_ground_bot_LD (x4) | CAT | PIN-D4x8 | 3.2 | [arm/grippers/fourbar.py:159](arm/grippers/fourbar.py#L159) body_fb_palm |
| HEAD | Torsion_Spring_Open | CAT | 9271K56 | 3.5 | [arm/grippers/fourbar.py:162](arm/grippers/fourbar.py#L162) body_fb_palm |
| JAW_L | Jaw_Block_L | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:305](arm/grippers/fourbar.py#L305) body_fb_jaw |
| JAW_L | Finger_L_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:313](arm/grippers/fourbar.py#L313) body_fb_jaw |
| JAW_L | Pad_L_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:322](arm/grippers/fourbar.py#L322) body_fb_jaw |
| JAW_L | Standoff_D6_L0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:325](arm/grippers/fourbar.py#L325) body_fb_jaw |
| JAW_L | Standoff_D6_L1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:325](arm/grippers/fourbar.py#L325) body_fb_jaw |
| JAW_L | Insert_M3_wall_L (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:315](arm/grippers/fourbar.py#L315) body_fb_jaw |
| JAW_L | BHCS_M3x6_wall_L (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:317](arm/grippers/fourbar.py#L317) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingtopL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:327](arm/grippers/fourbar.py#L327) body_fb_jaw |
| JAW_L | BHCS_M3x6_fingbotL (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:332](arm/grippers/fourbar.py#L332) body_fb_jaw |
| JAW_L | Pin_D4x14_coupler_bot_L (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:335](arm/grippers/fourbar.py#L335) body_fb_jaw |
| JAW_R | Jaw_Block_R | PRINT | custom: PETG-CF print (concept) | 30.7 | [arm/grippers/fourbar.py:305](arm/grippers/fourbar.py#L305) body_fb_jaw |
| JAW_R | Finger_R_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 6.9 | [arm/grippers/fourbar.py:313](arm/grippers/fourbar.py#L313) body_fb_jaw |
| JAW_R | Pad_R_TPU | TPU | custom: TPU 95A print, R50 arc + 90 deg V | 19.6 | [arm/grippers/fourbar.py:322](arm/grippers/fourbar.py#L322) body_fb_jaw |
| JAW_R | Standoff_D6_R0 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:325](arm/grippers/fourbar.py#L325) body_fb_jaw |
| JAW_R | Standoff_D6_R1 | AL | custom: 6061 D6 standoff, M3 both ends | 2.9 | [arm/grippers/fourbar.py:325](arm/grippers/fourbar.py#L325) body_fb_jaw |
| JAW_R | Insert_M3_wall_R (x3) | CAT | INSERT | 0.9 | [arm/grippers/fourbar.py:315](arm/grippers/fourbar.py#L315) body_fb_jaw |
| JAW_R | BHCS_M3x6_wall_R (x3) | CAT | BHCS | 3.0 | [arm/grippers/fourbar.py:317](arm/grippers/fourbar.py#L317) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingtopR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:327](arm/grippers/fourbar.py#L327) body_fb_jaw |
| JAW_R | BHCS_M3x6_fingbotR (x2) | CAT | BHCS | 2.0 | [arm/grippers/fourbar.py:328](arm/grippers/fourbar.py#L328) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:332](arm/grippers/fourbar.py#L332) body_fb_jaw |
| JAW_R | Pin_D4x14_coupler_bot_R (x2) | CAT | PIN-D4x14 | 2.8 | [arm/grippers/fourbar.py:335](arm/grippers/fourbar.py#L335) body_fb_jaw |
| LK_LD | Link_LD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_LD | Link_LD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_LD | Link_LD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_LD | Sector_m1_77T_L | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:193](arm/grippers/fourbar.py#L193) body_fb_link |
| LK_LD | Washer_LD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:196](arm/grippers/fourbar.py#L196) body_fb_link |
| LK_LD | Servo_Horn_STS_disc | CAT | HORN-25T | 3.0 | [arm/grippers/fourbar.py:199](arm/grippers/fourbar.py#L199) body_fb_link |
| LK_LD | Pin_D4x20_ground_LD | CAT | PIN-D4x20 | 2.0 | [arm/grippers/fourbar.py:201](arm/grippers/fourbar.py#L201) body_fb_link |
| LK_LI | Link_LI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_LI | Link_LI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_LI | Link_LI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RD | Link_RD_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RD | Link_RD_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RD | Link_RD_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RD | Sector_m1_77T_R | PRINT | custom: POM/PA12 sector gear m1 77T, 5 thick (concept) | 3.4 | [arm/grippers/fourbar.py:193](arm/grippers/fourbar.py#L193) body_fb_link |
| LK_RD | Washer_RD | CAT | WASHER-D4 | 0.3 | [arm/grippers/fourbar.py:196](arm/grippers/fourbar.py#L196) body_fb_link |
| LK_RI | Link_RI_lo_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RI | Link_RI_hi_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |
| LK_RI | Link_RI_bot_CF3 | CF | custom: 3 mm CF plate (concept) | 2.4 | [arm/grippers/fourbar.py:176](arm/grippers/fourbar.py#L176) body_fb_link |

### Parts - variant SCREW (321 parts)

| Body | Part | Kind | Source / note | Mass g | Built at |
|---|---|---|---|---|---|
| GROUND | Base_Plate_AL5 | AL | custom: 5 mm 6061, waterjet + tap | 1041.0 | [arm/base.py:66](arm/base.py#L66) body_ground |
| GROUND | Tower_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 68.8 | [arm/base.py:87](arm/base.py#L87) body_ground |
| GROUND | Drive_Frame_L | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 80.8 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Pinion_m2_18T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:115](arm/base.py#L115) body_ground |
| GROUND | Tower_Bracket_L0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_Bracket_L1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 64.3 | [arm/base.py:87](arm/base.py#L87) body_ground |
| GROUND | Drive_Frame_R | PRINT | custom: PETG-CF print, 3x M3 heat-set inserts | 80.8 | [arm/base.py:89](arm/base.py#L89) body_ground |
| GROUND | Pinion_m2_18T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 18T, 4x M3 cbore | 4.6 | [arm/base.py:115](arm/base.py#L115) body_ground |
| GROUND | Tower_Bracket_R0 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Tower_Bracket_R1 | PRINT | custom: PETG-CF print | 1.6 | [arm/base.py:127](arm/base.py#L127) body_ground |
| GROUND | Spacer_G1 | AL | custom: D9/D5.2 x 6 alu | 0.7 | [arm/base.py:135](arm/base.py#L135) body_ground |
| GROUND | SHCS_M4x12_base (x4) | CAT | SHCS | 4.0 | [arm/base.py:69](arm/base.py#L69) body_ground |
| GROUND | Insert_M3_frame_L (x6) | CAT | INSERT | 1.8 | [arm/base.py:92](arm/base.py#L92) body_ground |
| GROUND | BHCS_M3x6_frame_L (x6) | CAT | BHCS | 6.0 | [arm/base.py:95](arm/base.py#L95) body_ground |
| GROUND | Brg_6804_J (x2) | CAT | 6804ZZ | 38.0 | [arm/base.py:98](arm/base.py#L98) body_ground |
| GROUND | J1_Servo_STS (x2) | CAT | STS3215 | 120.0 | [arm/base.py:101](arm/base.py#L101) body_ground |
| GROUND | Servo_Horn_STS_J (x2) | CAT | HORN-25T | 6.0 | [arm/base.py:104](arm/base.py#L104) body_ground |
| GROUND | PAN_M2x12_J (x8) | CAT | PAN-M2x12 | 2.4 | [arm/core.py:345](arm/core.py#L345) sts_case_screws |
| GROUND | BHCS_M3x8_pinion_J (x8) | CAT | BHCS | 8.0 | [arm/base.py:118](arm/base.py#L118) body_ground |
| GROUND | BHCS_M3x10_bracket_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:128](arm/base.py#L128) body_ground |
| GROUND | Nyloc_M3_bracket_L (x4) | CAT | NYLOC | 2.0 | [arm/base.py:130](arm/base.py#L130) body_ground |
| GROUND | BHCS_M3x8_bracketbase_L (x4) | CAT | BHCS | 4.0 | [arm/base.py:132](arm/base.py#L132) body_ground |
| GROUND | SB5x10_G1 | CAT | SB5 | 4.0 | [arm/base.py:136](arm/base.py#L136) body_ground |
| GROUND | Nyloc_M4_G1 | CAT | NYLOC | 0.5 | [arm/base.py:137](arm/base.py#L137) body_ground |
| GROUND | Cable_Clip_Base (x3) | CAT | CLIP | 3.0 | [arm/base.py:139](arm/base.py#L139) body_ground |
| GROUND | ESC_C610 | CAT | C610 | 15.0 | [arm/base.py:144](arm/base.py#L144) body_ground |
| UPPER | Upper_Arm_L_CF3 | CF | custom: 3 mm CF plate (DXF) | 32.0 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | Upper_Arm_R_CF3 | CF | custom: 3 mm CF plate (DXF) | 31.4 | [arm/upper_arm.py:27](arm/upper_arm.py#L27) body_upper |
| UPPER | J1_Output_Hub | AL | custom: 6061 turned + milled hex | 32.6 | [arm/base.py:174](arm/base.py#L174) motor_hub |
| UPPER | Drive_Gear_m2_54T_J1 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:190](arm/base.py#L190) drive_gear_parts |
| UPPER | UA_Standoff_D8_0 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | UA_Standoff_D8_1 | AL | custom: 6061 D8/D6 rod, cut to length, D2.5 thru, M3 tapped both ends (spacer) | 10.7 | [arm/upper_arm.py:37](arm/upper_arm.py#L37) body_upper |
| UPPER | Brg_6700_Elbow_UA_L | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:28](arm/upper_arm.py#L28) body_upper |
| UPPER | Brg_6700_Elbow_UA_R | CAT | 6700ZZ | 2.0 | [arm/upper_arm.py:29](arm/upper_arm.py#L29) body_upper |
| UPPER | Brg_6701_Shoulder_UA_R | CAT | 6701ZZ | 3.0 | [arm/upper_arm.py:30](arm/upper_arm.py#L30) body_upper |
| UPPER | Washer_M5_hub_J1 | CAT | WASHER | 0.3 | [arm/base.py:193](arm/base.py#L193) drive_gear_parts |
| UPPER | SHCS_M5x10_hub_J1 | CAT | SHCS | 1.0 | [arm/base.py:194](arm/base.py#L194) drive_gear_parts |
| UPPER | BHCS_M3x6_UA_hub (x3) | CAT | BHCS | 3.0 | [arm/upper_arm.py:35](arm/upper_arm.py#L35) body_upper |
| UPPER | PClip_UA (x2) | CAT | PCLIP | 2.0 | [arm/upper_arm.py:41](arm/upper_arm.py#L41) body_upper |
| UPPER | BHCS_M3x8_UA_st_0L (x4) | CAT | BHCS | 4.0 | [arm/upper_arm.py:44](arm/upper_arm.py#L44) body_upper |
| CRANK | Crank_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore on journal flat | 7.6 | [arm/upper_arm.py:56](arm/upper_arm.py#L56) body_crank |
| CRANK | J2_Output_Hub_Journal | AL | custom: 6061 turned + milled hex | 36.0 | [arm/base.py:174](arm/base.py#L174) motor_hub |
| CRANK | Drive_Gear_m2_54T_J2 | PRINT | custom: PA12 / PETG-CF print, m2 54T, 19 AF hex bore | 43.8 | [arm/base.py:190](arm/base.py#L190) drive_gear_parts |
| CRANK | Shim_A | SHIM | custom: 301 SS shim stock 1.5, laser cut | 0.4 | [arm/upper_arm.py:62](arm/upper_arm.py#L62) body_crank |
| CRANK | Washer_M5_hub_J2 | CAT | WASHER | 0.3 | [arm/base.py:193](arm/base.py#L193) drive_gear_parts |
| CRANK | SHCS_M5x10_hub_J2 | CAT | SHCS | 1.0 | [arm/base.py:194](arm/base.py#L194) drive_gear_parts |
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
| LEVEL | Wrist_Servo_Cradle | PRINT | custom: PETG-CF print, 4x M3 heat-set inserts | 17.3 | [arm/wrist.py:62](arm/wrist.py#L62) body_level |
| LEVEL | Level_Hub_Wrist_Brg_6700 | CAT | 6700ZZ | 2.0 | [arm/forearm.py:22](arm/forearm.py#L22) level_hub |
| LEVEL | SB5x8_Dv2 | CAT | SB5 | 4.0 | [arm/forearm.py:39](arm/forearm.py#L39) v2_pin |
| LEVEL | Nyloc_M4_Dv2 | CAT | NYLOC | 0.5 | [arm/forearm.py:40](arm/forearm.py#L40) v2_pin |
| LEVEL | J3_Wrist_Servo_STS3215 | CAT | STS3215 | 60.0 | [arm/wrist.py:59](arm/wrist.py#L59) body_level |
| LEVEL | PAN_M2x12_J (x4) | CAT | PAN-M2x12 | 1.2 | [arm/core.py:345](arm/core.py#L345) sts_case_screws |
| LEVEL | Insert_M3_j3cradle (x4) | CAT | INSERT | 1.2 | [arm/wrist.py:67](arm/wrist.py#L67) body_level |
| LEVEL | CSK_M3x6_level (x4) | CAT | CSK | 4.0 | [arm/wrist.py:69](arm/wrist.py#L69) body_level |
| GRIPPER | Wrist_Shaft_D10x70 | STEEL | custom: cut from McMaster 6112K47 D10 h6 rod, D6x4 ground step, D-flats, e-clip groove | 41.2 | [arm/wrist.py:136](arm/wrist.py#L136) body_gripper |
| GRIPPER | Wrist_Shaft_Coupler | AL | custom: 6061, D6 D-bore on the shaft step, 4x M3 clearance (horn) | 2.1 | [arm/wrist.py:145](arm/wrist.py#L145) body_gripper |
| GRIPPER | Clevis_L_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore, 4x csk | 18.0 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Clevis_R_CF3 | CF | custom: 3 mm CF plate (DXF), D-bore | 18.1 | [arm/wrist.py:159](arm/wrist.py#L159) body_gripper |
| GRIPPER | Roll_Housing | PRINT | custom: PETG-CF print, M3 inserts | 34.9 | [arm/wrist.py:185](arm/wrist.py#L185) body_gripper |
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
| HEAD | Gripper_Palm | PRINT | custom: PETG-CF print, M3 inserts | 43.3 | [arm/grippers/screw.py:59](arm/grippers/screw.py#L59) body_head |
| HEAD | Screw_End_Block_L | AL | custom: 6061 machined, 688 seat, M3 tapped | 42.5 | [arm/grippers/screw.py:80](arm/grippers/screw.py#L80) body_head |
| HEAD | Screw_End_Block_R | AL | custom: 6061 machined, 688 seat, M3 tapped | 42.3 | [arm/grippers/screw.py:80](arm/grippers/screw.py#L80) body_head |
| HEAD | Spring_Housing | PRINT | custom: PETG-CF print, two-drum spring housing | 6.3 | [arm/grippers/screw.py:85](arm/grippers/screw.py#L85) body_head |
| HEAD | Spring_Output_Drum | AL | custom: 6061 turned, D20 drum on the D8 screw journal, M3 set screw | 12.0 | [arm/grippers/screw.py:87](arm/grippers/screw.py#L87) body_head |
| HEAD | Gripper_Bridge_CF3 | CF | custom: 3 mm CF plate (DXF, XY) | 22.0 | [arm/grippers/screw.py:111](arm/grippers/screw.py#L111) body_head |
| HEAD | Motor_Clamp_0 | PRINT | custom: PETG-CF print, M3 inserts, pinch slit | 4.5 | [arm/grippers/screw.py:127](arm/grippers/screw.py#L127) body_head |
| HEAD | Motor_Clamp_1 | PRINT | custom: PETG-CF print, M3 inserts, pinch slit | 4.5 | [arm/grippers/screw.py:127](arm/grippers/screw.py#L127) body_head |
| HEAD | Servo_Horn_25T_roll | CAT | HORN-25T | 3.0 | [arm/wrist.py:109](arm/wrist.py#L109) roll_hub_parts |
| HEAD | BHCS_M3x5_rollhorn (x8) | CAT | BHCS | 8.0 | [arm/wrist.py:99](arm/wrist.py#L99) _xscrew |
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
| HEAD | SHCS_M3x30_motorclamp (x2) | CAT | SHCS | 2.0 | [arm/wrist.py:99](arm/wrist.py#L99) _xscrew |
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

