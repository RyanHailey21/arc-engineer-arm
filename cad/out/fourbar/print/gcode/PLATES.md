# Ender-3 S1 Pro PLA Print Plates (ERB 335)

Sliced via `creality-slicer` (Creality Ender-3 S1 Pro 0.4 mm nozzle, `0.20mm Standard @Creality Ender3S1Pro`, Generic PLA, 210 C first layer / 205 C subsequent, 60 C Textured PEI Plate, 3 walls, 25% gyroid infill, no supports, Marlin-sanitized).

All arm STLs are rotated flat onto Z=0 (`X +90 deg`, except `J1_Output_Hub` at `X -90 deg` flange-down and `Tower_Bracket_*` as-exported).

| File | Parts | Layers / Max Z | Time | Filament | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `test_pieces_S1Pro_PLA.gcode` | `Test_Dovetail`, `Test_Fit_Large`, `Test_Fit_Small` | 35 / 7.0 mm | 3h 45m | 34.5 g | Printed on `saed` (fits verified) |
| `plate1_upper_rods_S1Pro_PLA.gcode` | `Upper_Arm_L_CF3_A/B`, `Upper_Arm_R_CF3_A/B`, `Rod_1_CF3_A/B` (6) | 15 / 3.0 mm | 6h 31m | 60.6 g | Printing on `steve` |
| `plate2_gears_crank_rocker_S1Pro_PLA.gcode` | `Drive_Gear_m2_54T_J1/J2`, `Pinion_m2_18T_J1/J2`, `Crank_CF3`, `Level_Rocker_CF3` (6) | 45 / 9.0 mm | 14h 37m | 122.4 g | Printing on `kate` |
| `plate3_forearmA_rod2_S1Pro_PLA.gcode` | `Forearm_L_CF3_A`, `Forearm_R_CF3_A`, `Rod_2_CF4_A/B` (4) | 20 / 4.0 mm | 4h 28m | 48.0 g | Ready to print |
| `plate4_hubs_clevises_rodab_S1Pro_PLA.gcode` | `Rod_AB_CF3_A/B`, `Wrist_Level_Member_CF3`, `Clevis_L/R_CF3`, `J1_Output_Hub`, `Level_Hub_Elbow/Wrist`, `Wrist_Shaft_Coupler`, `Tower_Bracket_L0/L1/R0/R1` (13) | 135 / 27.0 mm | 7h 40m | 70.6 g | Ready to print |

## Remaining Arm Parts (Next Batches)
- Diagonal singles (245.5 mm): `Forearm_L_CF3_B`, `Forearm_R_CF3_B` (~1h 24m / 14.1 g each)
- Large flat plates: `Base_Plate_AL5`, `Tower_L_CF3`, `Tower_R_CF3`
- Supported structural parts: `Drive_Frame_L`, `Drive_Frame_R`, `Roll_Housing`, `Wrist_Servo_Cradle`, `J2_Output_Hub_Journal`
- Shafts, standoffs, spacers/shims, and gripper sub-assembly
