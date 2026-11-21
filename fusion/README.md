# Fusion as the design master: snapshots and checks (pilot)

The team designs in Autodesk Fusion. This folder keeps the design observable as code: each revision's Fusion state
is exported as **diffable text**, and checks run on that snapshot instead of on the FreeCAD builders.

## Take a snapshot

Run `snapshot_export.py` in Fusion. An agent sends it through the Fusion MCP; a teammate runs it as a Fusion script.
It **only reads**: it changes no design and saves nothing.

It makes one cloud open of the top assembly. Every part comes in through the assembly's references, so masses,
materials, placements and joints are read locally. One more open reads the parameter master. Rev B takes about 50 s.

| File in `snapshot/<rev>/` | What it holds | In git |
|---|---|---|
| `snapshot.json` | every occurrence: path, part, source document and version, world transform, bounding box, mass, centre of mass, volume, bodies and materials; every joint with its value and limits | yes |
| `params.toml` | the revision's master user parameters: value, unit, expression, comment | yes |
| `bom.csv` | unique parts: quantity, material, mass, source document and version | yes |
| `summary.json` | document version, counts, total mass, time | yes |
| `assembly.step` | the assembly at its saved pose, read by the checks | no (35 MB; regenerated) |

A commit of a new snapshot is the design diff: parameters, masses, versions and joint limits as text.

## Checks on a snapshot

| Check | Command | What it does |
|---|---|---|
| Mass and torque | `python -I cad/tools/run.py fusion/checks/mass_torque.py` | mass and COM per moving body vs the code-CAD; static J1-J3 torque at all 14 task poses by virtual work |
| Interference | `python -I cad/tools/run.py --timeout 1800 fusion/checks/interference.py` | every pair of solids in `assembly.step` at STOW, on the full Fusion geometry; volumes above 0.5 mm³ |

Results go to `checks/out/<rev>_*.json`. Set `SNAP_REV=rev_a` to check the other revision.

## Pilot findings (rev B, 2026-11-21)

- The custom parts' masses match the code-CAD within a few percent (forearm, upper arm, rods, links, jaws).
- The **purchased parts are wrong in Fusion.** The STS3215 vendor model's internal bodies (motor, case halves) were
  given *Steel*, so each servo weighs about 150 g instead of about 60 g. There is one each on the wrist (LEVEL),
  the gripper head and the base. That makes the J1/J2 static torques about 20-25 % higher than reality, and the
  bearings carry *Aluminum 6061*. Fix: set each purchased part's mass to its catalogue mass in Fusion, using a
  per-part material density.
- **Interference** (`checks/out/rev_b_interference.json`): 582 solids, 1,902 pairs; the run took **24 min**, which
  is the baseline for the faster checks. 151 overlaps above 0.5 mm³:
  - **85 are intended contacts:** 61 fasteners and pins in their holes, 24 heat-set inserts. These belong in an
    intended-contacts list.
  - **4 are real findings** that the code-CAD's simplified check shapes don't show:
    - **J2 gear mesh, 165 mm³:** `Drive_Gear_m2_54T_J2` vs `Pinion_m2_18T_J2`. The teeth are clocked into each
      other.
    - **The STS3215 vendor model overlaps the gripper palm,** up to 162 mm³, across 60 pairs. The real servo
      case is bigger than the pocket that was designed around the simplified servo.
    - **Duplicate horn, 554 mm³:** the `HORN-25T (placeholder)` sits inside the horn that the STS3215 vendor model
      already includes. Drop the placeholder.
    - **Opening spring 9271K56 vs `Gripper_Palm`, 32 mm³.**
