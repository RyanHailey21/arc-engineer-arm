# -*- coding: utf-8 -*-
"""Data-file validator tests (plain Python, no FreeCAD):  python -I cad/tests/test_validate_data.py
Every real data file must validate; each deliberately broken copy must fail with a message that names the line,
the field and what to do."""
import os
import re
import sys

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(CAD, "tools"))
import validate_data as VD  # noqa: E402


def read(rel):
    return open(os.path.join(CAD, rel), encoding="utf-8").read()


def expect(kind, name, text, *patterns):
    errs = VD.validate_text(kind, name, text, name + ".toml")
    joined = "\n".join(errs)
    missing = [p for p in patterns if not re.search(p, joined)]
    assert errs and not missing, "expected %s in:\n%s" % (missing, joined or "(no errors)")
    return errs


CASES = []


def case(fn):
    CASES.append(fn)
    return fn


@case
def real_files_valid():
    bad = [e for f in VD.all_data_files() for e in VD.validate_file(f)[2]]
    assert not bad, "\n".join(bad)


@case
def param_typo_type():
    src = read("params/gripper_fourbar.toml")
    assert "L = 47.0" in src and "ZL0 = [23.5, 26.5]" in src, "test anchors gone from gripper_fourbar.toml"
    line = next(i for i, s in enumerate(src.splitlines(), 1) if s.startswith("ZL0 = [23.5, 26.5]"))  # TI-023
    t = src.replace("L = 47.0", 'L = "forty-seven"').replace("ZL0 = [23.5, 26.5]", "ZL0 = {a = {b = 1}}")
    errs = expect("params", "gripper_fourbar", t,
                  r":%d: FB\.ZL0: expected a fact table .* found a table with keys a" % line)
    assert len(errs) == 1, errs          # reported once, at the leaf - not as "FB is not a number"


@case
def param_fact_needs_unit_and_source():
    t = read("params/pads.toml").replace("PAD_R = 50.0", 'PAD_R = {value = 50.0, source = "ARC manual 3.2.4"}')
    expect("params", "pads", t, r"PAD_R\.unit: missing")


@case
def param_fact_ok():
    t = read("params/pads.toml").replace("PAD_R = 50.0", 'PAD_R = {value = 50.0, unit = "mm", source = "ARC manual 3.2.4", status = "documented"}')
    assert not VD.validate_text("params", "pads", t)


@case
def interface_bad_hole_and_unknown_key():
    t = read("interfaces/roll_hub__gripper_palm.toml").replace('hole = "clearance"', 'hole = "slot"').replace(
        "clearance_d = 3.3", "clearance_d = 3.3\nclearence = 3.4")
    expect("interface", "roll_hub__gripper_palm", t, r"side_b\.hole: 'slot' is not allowed; use one of 'tapped', 'clearance'",
           r"side_b\.clearence: unknown key; allowed here: .*clearance_d")


@case
def interface_name_and_normal():
    t = read("interfaces/roll_hub__gripper_palm.toml").replace("normal = [1.0, 0.0, 0.0]", "normal = [1.0, 1.0, 0.0]")
    expect("interface", "renamed_file__x", t, r"must equal the file name 'renamed_file__x'", r"frame\.normal: must be a unit vector")


@case
def interface_pattern_needs_sides():
    t = read("interfaces/roll_horn__roll_hub.toml")
    t = t[:t.index("[side_a]")]
    expect("interface", "roll_horn__roll_hub", t, r"side_a: missing: required because \[pattern\] is present")


@case
def envelope_bad_box_pose_and_frame():
    t = read("envelopes/field.toml")
    t = t.replace('poses = ["DONUT_PLACE"]', 'poses = ["DONUT_DROP"]', 1)
    t = re.sub(r'(?m)^frame = "gripper"', 'frame = "tool"', t, count=1)       # the key, not the header comment
    t = t.replace("min = [303.0, -600.0, 0.0]", "min = [1e4, -600.0, 0.0]")
    expect("envelope", "field", t, r"unknown pose 'DONUT_DROP'; poses in arm/kinematics.py: .*DONUT_PLACE",
           r"frame: 'tool' is not allowed", r"x: min 10000.0 must be < max 10000.0")


@case
def envelope_reason_required():
    t = read("envelopes/field.toml").replace('name = "scoring_platform"\nwhy = ', 'name = "scoring_platform"\nwhy_not = ')
    expect("envelope", "field", t, r"keepout\.\d+\.why: missing", r"keepout\.\d+\.why_not: unknown key")


@case
def catalogue_mass_numeric():
    t = read("data/catalogue.toml").replace("mass = 330", 'mass = "330 g"', 1)
    expect("catalogue", "catalogue", t, r"mass: expected number")


@case
def toml_syntax():
    expect("params", "pads", "PAD_R = = 50", r"TOML syntax error")


@case
def hook_mode_ignores_other_files():
    import io
    import json
    sys.stdin = io.StringIO(json.dumps({"tool_input": {"file_path": os.path.join(CAD, "arm", "core.py")}}))
    assert VD.main(["--hook"]) == 0


if __name__ == "__main__":
    fails = 0
    for fn in CASES:
        try:
            fn()
            print("PASS", fn.__name__)
        except AssertionError as e:
            fails += 1
            print("FAIL", fn.__name__, "\n ", str(e).replace("\n", "\n  "))
    print("TESTS: %d passed, %d failed" % (len(CASES) - fails, fails))
    sys.exit(1 if fails else 0)
