# Ender-3 S1 Pro PLA Print Plates (ERB 335)

Plates 1 and 3 to 6 sliced 2026-11-26 via the `creality-slicer` MCP (OrcaSlicer): Creality Ender-3 S1 Pro 0.4 mm nozzle, `0.20mm Standard @Creality Ender3S1Pro`, `Creality Generic PLA`, 210 C first layer / 205 C after, 60 C Textured PEI Plate, 3 walls, 7 top / 5 bottom layers, 25% gyroid, no supports. Plate 2 and the test pieces are the earlier Bambu Studio slices with the same settings.

All arm STLs are rotated flat onto Z=0 (`X +90 deg`), except `J1_Output_Hub` at `X -90 deg` (flange down) and `Tower_Bracket_*` as exported. The forearm A halves also turn `Z 45 deg` to fit diagonally.

**2026-11-26 re-split:** the first PLA upper arms broke their 2 mm socket cheeks when fitted. `export_print.py` now leaves at least 4 mm of material round every dovetail socket and uses one centred dovetail per split. Upper arm 6.0 mm, forearm 4.5, Rod AB / Rod 1 4.5, Rod 2 5.0 mm (column `note` in `print_list.csv`). Halves from the old plate 1 / old plate 3 do not mate with the new ones: reprint both halves of a part.

Each plate's `*_preview/` folder holds the slicer's first-layer, top and isometric views.

| File | Parts | Layers / Max Z | Time | Filament | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_pieces_S1Pro_PLA.gcode` | `Test_Dovetail`, `Test_Fit_Large`, `Test_Fit_Small` | 35 / 7.0 mm | 3h 45m | 34.5 g | **Printed** on `saed` (fits verified; dovetail 0.15 mm unchanged) |
| `plate1_upper_rods_S1Pro_PLA.gcode` | `Upper_Arm_L_CF3_A/B`, `Upper_Arm_R_CF3_A/B`, `Rod_1_CF3_A/B` (6) | 15 / 3.0 mm | 5h 35m | 62.6 g | **Printing** on `kate` (re-sliced 11-26, 4 mm sockets) |
| `plate2_gears_crank_rocker_S1Pro_PLA.gcode` | `Drive_Gear_m2_54T_J1/J2`, `Pinion_m2_18T_J1/J2`, `Crank_CF3`, `Level_Rocker_CF3` (6) | 45 / 9.0 mm | 14h 37m | 122.4 g | **Printed** on `kate` (unchanged) |
| `plate3_forearmB_rod2_S1Pro_PLA.gcode` | `Forearm_L_CF3_B`, `Forearm_R_CF3_B`, `Rod_2_CF4_A/B` (4) | 20 / 4.0 mm | 3h 42m | 41.3 g | **Printed** on `a1` (1h 13m, 34.7 g) |
| `plate4_hubs_clevises_rodab_S1Pro_PLA.gcode` | `Rod_AB_CF3_A/B`, `Wrist_Level_Member_CF3`, `Clevis_L/R_CF3`, `J1_Output_Hub`, `Level_Hub_Elbow/Wrist`, `Wrist_Shaft_Coupler`, `Tower_Bracket_L0/L1/R0/R1` (13) | 135 / 27.0 mm | 6h 33m | 70.1 g | **Printing** on `steve` (re-sliced 11-26) |
| `plate5_forearmL_A_S1Pro_PLA.gcode` | `Forearm_L_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | **Printing** on `a1` (27 min, 14.2 g, no brim) |
| `plate6_forearmR_A_S1Pro_PLA.gcode` | `Forearm_R_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | Queued next for `a1` (27 min, 14.2 g) |
| `plate7_gripper_links_K1SE_PLA.gcode` | `Link_LD/LI/RD/RI_bot/hi/lo_CF3` (12), `Finger_L/R_bot_CF3`, `Sector_m1_77T_L/R` (16) | 25 / 5.0 mm | 1h 33m | 41.2 g | **Printing** on `k1se-home` (retry with a 5 mm outer brim and glue on the textured PEI: the first run lifted off the bed at 35%; Generic PLA @K1 SE-all 220/60 C) |
| `plate8_drive_frame_L_spacers_K2_PETG.gcode` | `Drive_Frame_L` (reworked 11-26: no legs, prints face down), `Spacer_DF_L0-2`, `Spacer_DF_R0-2` (7) | 195 / 39.0 mm | 3h 03m | 87.2 g | **Printing** on `k2-home` (home K2, Generic PETG @K2-all 250/70 C, auto-orient, auto-brim) |
| `plate9_drive_frame_R_K2_PETG.gcode` | `Drive_Frame_R` (reworked) | 195 / 39.0 mm | 2h 43m | 81.9 g | Queued next on `k2-home` |

## Bambu Lab Plates (2026-11-26, PLA 220 C / 60-65 C Textured PEI, 3 walls, 25% gyroid)
- **Printing on `p1s-2`:** `Roll_Housing`, `Wrist_Servo_Cradle`, `J2_Output_Hub_Journal`, `Elbow_Shaft_D10x101`, `Wrist_Shaft_D10x70`, `FA_Standoff_D8_0/1`, `UA_Standoff_D8_0/1` (9 parts, tree auto supports, 3h 55m, 112.7 g)
- **Sliced & queued:** ~~`Drive_Frame_L/R` (P1S)~~ obsolete: the frames were reworked on 11-26 (no legs, separate spacers) and are plates 8 and 9 on the home K2, `Base_Plate_AL5` (A1, 2h 01m, 64.4 g), `Tower_L_CF3` (A1, 1h 06m, 37.8 g), `Tower_R_CF3` (A1, 1h 02m, 35.4 g)

## Remaining Un-Sliced Parts
- Shims, spacers, and PTFE washers (`Shim_A`, `Shim_Ev1`, `Spacer_B`, `Spacer_G1`, `Sleeve_E_outer`, `Washer_*`)
- Gripper sub-assembly (`Gripper_Palm`, `Roll_Hub`, `Jaw_Block_L/R`, `Pad_L/R_TPU`, `Standoff_D6_*`); links, fingers and sectors are plate 7
