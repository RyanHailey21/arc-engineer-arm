# Ender-3 S1 Pro PLA Print Plates (ERB 335)

Plates 1 and 3 to 6 sliced 2026-11-26 via the `creality-slicer` MCP (OrcaSlicer): Creality Ender-3 S1 Pro 0.4 mm nozzle, `0.20mm Standard @Creality Ender3S1Pro`, `Creality Generic PLA`, 210 C first layer / 205 C after, 60 C Textured PEI Plate, 3 walls, 7 top / 5 bottom layers, 25% gyroid, no supports. Plate 2 and the test pieces are the earlier Bambu Studio slices with the same settings.

All arm STLs are rotated flat onto Z=0 (`X +90 deg`), except `J1_Output_Hub` at `X -90 deg` (flange down) and `Tower_Bracket_*` as exported. The forearm A halves also turn `Z 45 deg` to fit diagonally.

**2026-11-26 re-split:** the first PLA upper arms broke their 2 mm socket cheeks when fitted. `export_print.py` now leaves at least 4 mm of material round every dovetail socket and uses one centred dovetail per split. Upper arm 6.0 mm, forearm 4.5, Rod AB / Rod 1 4.5, Rod 2 5.0 mm (column `note` in `print_list.csv`). Halves from the old plate 1 / old plate 3 do not mate with the new ones: reprint both halves of a part.

Each plate's `*_preview/` folder holds the slicer's first-layer, top and isometric views.

| File | Parts | Layers / Max Z | Time | Filament | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_pieces_S1Pro_PLA.gcode` | `Test_Dovetail`, `Test_Fit_Large`, `Test_Fit_Small` | 35 / 7.0 mm | 3h 45m | 34.5 g | Printed on `saed` (fits verified; dovetail 0.15 mm unchanged) |
| `plate1_upper_rods_S1Pro_PLA.gcode` | `Upper_Arm_L_CF3_A/B`, `Upper_Arm_R_CF3_A/B`, `Rod_1_CF3_A/B` (6) | 15 / 3.0 mm | 5h 35m | 62.6 g | **Re-sliced 11-26 (4 mm sockets)**: reprint |
| `plate2_gears_crank_rocker_S1Pro_PLA.gcode` | `Drive_Gear_m2_54T_J1/J2`, `Pinion_m2_18T_J1/J2`, `Crank_CF3`, `Level_Rocker_CF3` (6) | 45 / 9.0 mm | 14h 37m | 122.4 g | Unchanged (no split parts) |
| `plate3_forearmB_rod2_S1Pro_PLA.gcode` | `Forearm_L_CF3_B`, `Forearm_R_CF3_B`, `Rod_2_CF4_A/B` (4) | 20 / 4.0 mm | 3h 42m | 41.3 g | **New 11-26** (replaces old plate 3 with the forearm A halves) |
| `plate4_hubs_clevises_rodab_S1Pro_PLA.gcode` | `Rod_AB_CF3_A/B`, `Wrist_Level_Member_CF3`, `Clevis_L/R_CF3`, `J1_Output_Hub`, `Level_Hub_Elbow/Wrist`, `Wrist_Shaft_Coupler`, `Tower_Bracket_L0/L1/R0/R1` (13) | 135 / 27.0 mm | 6h 33m | 70.1 g | **Re-sliced 11-26** (Rod AB re-split) |
| `plate5_forearmL_A_S1Pro_PLA.gcode` | `Forearm_L_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | **New 11-26** |
| `plate6_forearmR_A_S1Pro_PLA.gcode` | `Forearm_R_CF3_A` (266 mm, diagonal) | 15 / 3.0 mm | 1h 27m | 17.3 g | **New 11-26** |

## Remaining Arm Parts (Next Batches)
- Large flat plates: `Base_Plate_AL5`, `Tower_L_CF3`, `Tower_R_CF3`
- Supported structural parts: `Drive_Frame_L`, `Drive_Frame_R`, `Roll_Housing`, `Wrist_Servo_Cradle`, `J2_Output_Hub_Journal`
- Shafts, standoffs, spacers/shims, and gripper sub-assembly
