# FEA evidence - load-critical custom parts

FreeCAD 1.1 FEM: gmsh 2nd-order tets + CalculiX linear static. Load factor 2.5 on worst static case. Required SF >= 1.5 on factored load. All 8 cases run on the final model geometry (2026-11-15).

| Case | Part | Material | Load | Max von Mises (MPa) | Allowable (MPa) | SF | Max disp (mm) | Nodes | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| upper_arm | Upper_Arm_L_CF3 | CF plate quasi-isotropic | elbow reaction 23.3 N per plate (1.9 kg distal mass x g x 2.5) | 27.8 | 200 | 7.2 | 0.977 | 45446 | PASS |
| clevis | Clevis_L_CF3 | CF plate quasi-isotropic | head weight 12.3 N per plate at the roll-housing screws (1.0 kg x g x 2.5) | 4.3 | 200 | 46.2 | 0.003 | 47807 | PASS |
| j2_hub | J2_Output_Hub_Journal | Aluminium-6061-T6 | crank reaction 62 N on the D12 journal (J2 10.0 N*m incl. x2.5) | 7.6 | 276 | 36.3 | 0.001 | 40224 | PASS |
| jaw_bracket | Jaw_Bracket_L | Aluminium-6061-T6 | grip/lead-screw reaction 100 N on the nut upright (M2006 current-limited grip) | 39.4 | 276 | 7.0 | 0.056 | 120986 | PASS |
| finger | Finger_L_top_CF3 | CF plate quasi-isotropic | grip reaction 50 N per finger plate (100 N jaw force over 2 plates) | 12.6 | 200 | 15.9 | 0.015 | 59843 | PASS |
| roll_housing | Roll_Housing | PETG-CF (FDM) | head + payload 24.5 N through the 6805 seat (1.0 kg x g x 2.5) | 0.6 | 40 | 62.5 | 0.005 | 62435 | PASS |
| end_block | Screw_End_Block_R | Aluminium-6061-T6 | lead-screw axial reaction 100 N on the 688 bearing seat | 4.0 | 276 | 69.4 | 0.001 | 68676 | PASS |
| forearm | Forearm_L_CF3 | CF plate quasi-isotropic | wrist load 14.7 N per plate (1.2 kg head+payload x g x 2.5) | 21.1 | 200 | 9.5 | 0.810 | 63824 | PASS |
