# Ender-3 S1 Pro PLA Print Plates (ERB 335)

Plates 1 and 3 to 6 sliced 2026-11-26 via the `creality-slicer` MCP (OrcaSlicer): Creality Ender-3 S1 Pro 0.4 mm nozzle, `0.20mm Standard @Creality Ender3S1Pro`, `Creality Generic PLA`, 210 C first layer / 205 C after, 60 C Textured PEI Plate, 3 walls, 7 top / 5 bottom layers, 25% gyroid, no supports. Plate 2 and the test pieces are the earlier Bambu Studio slices with the same settings.

All arm STLs are rotated flat onto Z=0 (`X +90 deg`), except `J1_Output_Hub` at `X -90 deg` (flange down) and `Tower_Bracket_*` as exported. The forearm A halves also turn `Z 45 deg` to fit diagonally.

**2026-11-26 re-split:** the first PLA upper arms broke their 2 mm socket cheeks when fitted. `export_print.py` now leaves at least 4 mm of material round every dovetail socket and uses one centred dovetail per split. Upper arm 6.0 mm, forearm 4.5, Rod AB / Rod 1 4.5, Rod 2 5.0 mm (column `note` in `print_list.csv`). Halves from the old plate 1 / old plate 3 do not mate with the new ones: reprint both halves of a part.

Each plate's `*_preview/` folder holds the slicer's first-layer, top and isometric views.

| File | Parts | Layers / Max Z | Time | Filament | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_pieces_S1Pro_PLA.gcode` | `Test_Dovetail`, `Test_Fit_Large`, `Test_Fit_Small` | 35 / 7.0 mm | 3h 45m | 34.5 g | **Printed** on `saed` (fits verified; dovetail 0.15 mm unchanged) |
| `plate1_upper_rods_S1Pro_PLA.gcode` | `Upper_Arm_L_CF3_A/B`, `Upper_Arm_R_CF3_A/B`, `Rod_1_CF3_A/B` (6) | 15 / 3.0 mm | 5h 35m | 62.6 g | **Printed** on `kate` 11-26 (re-sliced, 4 mm sockets) |
| `plate2_gears_crank_rocker_S1Pro_PLA.gcode` | `Drive_Gear_m2_54T_J1/J2`, `Pinion_m2_18T_J1/J2`, `Crank_CF3`, `Level_Rocker_CF3` (6) | 45 / 9.0 mm | 14h 37m | 122.4 g | **Printed** on `kate` (unchanged) |
| `plate3_forearmB_rod2_S1Pro_PLA.gcode` | `Forearm_L_CF3_B`, `Forearm_R_CF3_B`, `Rod_2_CF4_A/B` (4) | 20 / 4.0 mm | 3h 42m | 41.3 g | **Printed** on `a1` 11-26 (1h 13m, 34.7 g) |
| `plate4_hubs_clevises_rodab_S1Pro_PLA.gcode` | `Rod_AB_CF3_A/B`, `Wrist_Level_Member_CF3`, `Clevis_L/R_CF3`, `J1_Output_Hub`, `Level_Hub_Elbow/Wrist`, `Wrist_Shaft_Coupler`, `Tower_Bracket_L0/L1/R0/R1` (13) | 135 / 27.0 mm | 6h 33m | 70.1 g | **Partial (10/13)** on `steve` 11-26; 3 failed: `Level_Hub_Elbow` & `Level_Hub_Wrist` (CAD floating shell: D14 OD inside D15 bore) and `J1_Output_Hub` (D39 flange overhang, needs supports) |
| `plate4b_hubs_S1Pro_PLA.gcode` | `Level_Hub_Elbow`, `Level_Hub_Wrist` (fixed 11-27: D15.2 x 0.6 shoulder joins the D14 neck to the 6700 seat, one solid), `J1_Output_Hub` (pilot down, as plate 4) (3) | 135 / 27.0 mm | 1h 55m | 14.3 g | **Printing** on `steve` 11-27 (tree(auto) supports: 2.5 mm ring under J1 flange + level hubs inner shoulder; replaces plate 4's three failed parts) |
| `plate5_forearmL_A_S1Pro_PLA.gcode` | `Forearm_L_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | **Printed** on `a1` 11-26 (27 min, 14.2 g, no brim) |
| `plate6_forearmR_A_S1Pro_PLA.gcode` | `Forearm_R_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | **Failed on `kate` 11-27** (lifted off bed with no brim; cancelled). **Re-queued next for `a1`** (27 min, 14.2 g; same setup as `Forearm_L_CF3_A`) |
| `plate7_gripper_links_K1SE_PLA.gcode` | `Link_LD/LI/RD/RI_bot/hi/lo_CF3` (12), `Finger_L/R_bot_CF3`, `Sector_m1_77T_L/R` (16) | 25 / 5.0 mm | 1h 33m | 41.2 g | **Printed** on `k1se-home` 11-27 (second run, with a 5 mm outer brim and glue on the textured PEI; the first run lifted off the bed at 35%; Generic PLA @K1 SE-all 220/60 C) |
| `plate8_drive_frame_L_spacers_K2_PETG.gcode` | `Drive_Frame_L` (reworked 11-26: no legs, prints face down), `Spacer_DF_L0-2`, `Spacer_DF_R0-2` (7) | 195 / 39.0 mm | 3h 03m | 87.2 g | **Printed** on `k2-home` 11-27 (home K2, Generic PETG @K2-all 250/70 C, auto-orient, auto-brim, no supports) |
| `plate9_drive_frame_R_K2_PETG.gcode` | `Drive_Frame_R` (reworked) | 195 / 39.0 mm | 3h 07m | 87.9 g | Superseded for prototype by `a1_plate7_drive_frame_R_spacers_PLA.gcode.3mf` (**Printing** on `a1` 11-27 with tree(auto) supports + 6x `Spacer_DF`, 3h 03m, 79.7 g) |
| `plate10_towerL_S1Pro_PLA.gcode` | `Tower_L_CF3` (152 x 141 x 3.0 mm, flat) | 15 / 3.0 mm | 3h 51m | 48.2 g | **Printing** on `saed` 11-27 |
| `plate11_towerR_S1Pro_PLA.gcode` | `Tower_R_CF3` (152 x 126 x 3.0 mm, flat) | 15 / 3.0 mm | 3h 37m | 45.1 g | **Printing** on `kate` 11-27 |

## Bambu Lab Plates (2026-11-26 / 2026-11-27, PLA 220 C / 60-65 C Textured PEI, 3 walls, 25% gyroid)
- **Printed on `p1s-2` (11-26):** `Roll_Housing`, `Wrist_Servo_Cradle`, `J2_Output_Hub_Journal`, `Elbow_Shaft_D10x101`, `Wrist_Shaft_D10x70`, `FA_Standoff_D8_0/1`, `UA_Standoff_D8_0/1` (9 parts, tree auto supports, 3h 55m, 112.7 g)
- **Printing on `a1` (11-27):** `a1_plate7_drive_frame_R_spacers_PLA.gcode.3mf` (`Drive_Frame_R` reworked + `Spacer_DF_L0-2` + `Spacer_DF_R0-2`, tree(auto) supports, 3h 03m, 79.7 g)
- **Queued next on `a1`:** `a1_plate4_base_plate_PLA.gcode.3mf` (`Base_Plate_AL5`, 2h 01m, 64.4 g, already uploaded on SD), `Forearm_R_CF3_A` (27 min, 14.2 g; failed on `kate` 11-27 with no brim, re-queued for `a1`)

## Remaining Un-Sliced Parts
- Shims, spacers, and PTFE washers (`Shim_A`, `Shim_Ev1`, `Spacer_B`, `Spacer_G1`, `Sleeve_E_outer`, `Washer_*`)
- Gripper sub-assembly (`Gripper_Palm`, `Roll_Hub`, `Jaw_Block_L/R`, `Pad_L/R_TPU`, `Standoff_D6_*`); links, fingers and sectors are plate 7
