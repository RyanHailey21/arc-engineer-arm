# Four-bar gripper - FEA and hand checks

Actuator-bounded loads x 1.25 (servo stall 2.94 N*m is a hard ceiling); gravity + pipe moment x 2.5. Required SF >= 1.5.

| Case | Part | Material | Method | Load | Max stress (MPa) | Allowable (MPa) | SF | Max disp (mm) | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| fb_drive_link | Link_LD_lo_CF3 | CF plate quasi-isotropic | FEA (gmsh 2nd-order tets + CalculiX) | servo stall 2.94 N*m reacted at the coupler pin: 63 N x 1.25 = 78 N | 111.2 | 200 | 1.8 | 0.294 | PASS |
| fb_jaw_block | Jaw_Block_L | PETG-CF (FDM) | FEA (gmsh 2nd-order tets + CalculiX) | stall clamp reaction 29.5 N x 1.25 = 37 N on the pad standoffs (all on the top finger; jaw held at top and bottom pin bores) | 2.5 | 40 | 16.1 | 0.040 | PASS |
| fb_palm | Gripper_Palm | PETG-CF (FDM) | FEA (gmsh 2nd-order tets + CalculiX) | head 0.35 kg + 165 g pipe + 0.5 N*m pipe moment: 0.79 N*m x 2.5 at the mount -> 117 N on the pivot bores | 18.7 | 40 | 2.1 | 0.638 | PASS |
| fb_sector_tooth | Sector_m1_77T | Acetal (POM) | Lewis bending (hand calc) | half stall torque through the mesh: Ft 38.2 N x 1.25 | 22.0 | 60 | 2.7 | - | PASS |
| fb_pivot_pin | Dowel D4 (91595A158/167/179) | 52100 steel, HRC 52+ | single shear (hand calc) | coupler/ground pin force 63 N x 1.25 | 6.2 | 1000 | 160.7 | - | PASS |
| fb_link_bearing | Link CF3 pivot bore | CF plate (bearing allowable 200 MPa) | projected-area bearing (hand calc) | 78 N on a 4 x 3 mm bore | 6.5 | 200 | 30.7 | - | PASS |
