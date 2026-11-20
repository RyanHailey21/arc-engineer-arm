# FEA evidence - load-critical custom parts

FreeCAD 1.1 FEM: gmsh 2nd-order tets + CalculiX linear static. Load factor 2.5 on worst static case. Required SF >= 1.5 on factored load.

| Case | Part | Material | Load | Max von Mises (MPa) | Allowable (MPa) | SF | Max disp (mm) | Nodes | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| upper_arm | Upper_Arm_L_CF3 | CF plate quasi-isotropic | elbow reaction 23.3 N per plate (1.9 kg distal mass x g x 2.5) | 50.9 | 200 | 3.9 | 1.595 | 46401 | PASS |
| forearm | Forearm_L_CF3 | CF plate quasi-isotropic | wrist load 14.7 N per plate (1.2 kg head+payload x g x 2.5) | 20.6 | 200 | 9.7 | 1.200 | 44735 | PASS |
| clevis | Clevis_L_CF3 | CF plate quasi-isotropic | head weight 12.3 N per plate at the roll-housing screws (1.0 kg x g x 2.5) | 4.3 | 200 | 46.2 | 0.003 | 47807 | PASS |
| j2_hub | J2_Output_Hub_Journal | Aluminium-6061-T6 | crank reaction 62 N on the D12 journal (J2 10.0 N*m incl. x2.5) | 3.9 | 276 | 70.1 | 0.001 | 65877 | PASS |
| roll_housing | Roll_Housing | PETG-CF (FDM) | head + payload 24.5 N through the 6805 seat (1.0 kg x g x 2.5) | 0.6 | 40 | 62.5 | 0.005 | 97087 | PASS |
