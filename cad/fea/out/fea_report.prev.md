# FEA evidence - load-critical custom parts

FreeCAD 1.1 FEM: gmsh 2nd-order tets + CalculiX linear static. Load factor 2.5 on worst static case. Required SF >= 1.5 on factored load.

| Case | Part | Material | Load | Max von Mises (MPa) | Allowable (MPa) | SF | Max disp (mm) | Nodes | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| clevis | Clevis_L_CF3 | CF plate quasi-isotropic | head weight 12.3 N per plate at the roll-housing screws (1.0 kg x g x 2.5) | 4.0 | 200 | 49.8 | 0.004 | 48592 | PASS |
| j2_hub | J2_Output_Hub_Journal | Aluminium-6061-T6 | crank reaction 62 N on the D12 journal (J2 10.0 N*m incl. x2.5) | 7.6 | 276 | 36.3 | 0.001 | 40273 | PASS |
