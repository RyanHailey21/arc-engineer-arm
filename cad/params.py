# -*- coding: utf-8 -*-
"""
Parameter files (cad/params/*.toml) and data files (cad/data/*.toml).

    import params
    P = params.load("arm")          # dict; TOML arrays come back as tuples (hashable, like the old literals)
    params.grip()                   # active gripper variant: $GRIP, else params/variant.toml
    params.base_drive()             # active J1/J2 base drive: $BASE_DRIVE, else params/variant.toml (GEARED | DIRECT)
    params.variant()                # output/evidence key: grip(), plus "_DIRECT" for the direct-drive base

Edit the TOML, not the code: each value carries its unit and the reason for it.  After an intended change,
run cad/tools/quick_check.py, then re-record the fingerprint (cad/tools/fingerprint.py FP_MODE=record).
"""
import os
import tomllib

CAD = os.path.dirname(os.path.abspath(__file__))
_CACHE = {}


FACT_KEYS = {"value", "unit", "source", "status"}


def _tuples(v):
    """TOML arrays -> tuples; fact tables {value, unit, source[, status]} -> their value (the metadata stays in the
    file for people and tools/validate_data.py)."""
    if isinstance(v, list):
        return tuple(_tuples(x) for x in v)
    if isinstance(v, dict):
        if "value" in v and set(v) <= FACT_KEYS:
            return _tuples(v["value"])
        return {k: _tuples(x) for k, x in v.items()}
    return v


def load(name, folder="params"):
    key = (folder, name)
    if key not in _CACHE:
        with open(os.path.join(CAD, folder, name + ".toml"), "rb") as f:
            _CACHE[key] = _tuples(tomllib.load(f))
    return _CACHE[key]


def data(name):
    return load(name, "data")


def grip():
    return (os.environ.get("GRIP") or load("variant")["grip"]).upper()


BASE_DRIVES = ("GEARED", "DIRECT")


def base_drive():
    """J1/J2 base drive: GEARED (STS3215 + 3:1 spur stage, rev B) or DIRECT (DM-J4340 on the hubs, the Fusion rev A)."""
    b = (os.environ.get("BASE_DRIVE") or load("variant")["base_drive"]).upper()
    if b not in BASE_DRIVES:
        raise ValueError("BASE_DRIVE=%s: expected one of %s" % (b, ", ".join(BASE_DRIVES)))
    return b


def variant():
    """Variant key for outputs, evidence and fingerprints: the gripper (FOURBAR, SCREW), with "_DIRECT" appended
    when the base drive is not the default GEARED one (so the GEARED folders and baselines keep their names)."""
    return grip() if base_drive() == "GEARED" else "%s_%s" % (grip(), base_drive())


# ------------------------------------------------------------------ outputs, evidence, release guard
import datetime    # noqa: E402
import glob        # noqa: E402
import hashlib     # noqa: E402
import json        # noqa: E402

INPUT_GLOBS = ("arm/*.py", "arm/grippers/*.py", "arm_model.py", "hardware.py", "iface.py", "params.py", "field.py",
               "params/*.toml", "data/*.toml", "interfaces/*.toml", "envelopes/*.toml", "vendor/*")


def release_variant():
    return load("variant")["release"].upper()


def release_base_drive():
    return load("variant")["release_base_drive"].upper()


def out_dir(*sub):
    """cad/out/<variant>/<sub...> (created): every check's results for the active variant."""
    d = os.path.join(CAD, "out", variant().lower(), *sub)
    os.makedirs(d, exist_ok=True)
    return d


def inputs_hash():
    """Hash of everything that defines the geometry (model code, parameters, interfaces, envelopes, vendor CAD)."""
    h = hashlib.sha256()
    for g in INPUT_GLOBS:
        for f in sorted(glob.glob(os.path.join(CAD, g))):
            if os.path.isfile(f):
                h.update(os.path.relpath(f, CAD).replace("\\", "/").encode())
                h.update(bytes.fromhex(input_sha(f)))
    return h.hexdigest()[:16]


TEXT_INPUTS = (".py", ".toml", ".json", ".md")   # hashed EOL-neutral, like cad/sim/gz_check.py's urdf sha


def input_sha(path):
    """SHA-256 of a design input.  Text inputs hash with CRLF -> LF, so a checkout with core.autocrlf=true (a git
    worktree, a fresh clone) gets the same inputs hash as one whose files were written LF (TI-024).  Other inputs
    (vendor STEP/STL) hash raw."""
    with open(path, "rb") as fh:
        data = fh.read()
    if path.lower().endswith(TEXT_INPUTS):
        data = data.replace(b"\r\n", b"\n")
    return hashlib.sha256(data).hexdigest()


def _sha(path):
    """Raw-byte SHA-256 for evidence artifacts and the input snapshot (verify_report re-hashes those files as-is)."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def input_files():
    return sorted({f for g in INPUT_GLOBS for f in glob.glob(os.path.join(CAD, g)) if os.path.isfile(f)})


EVIDENCE_STATUS = {"PASS": "pass", "WARN": "pass", "FAIL": "fail"}   # cad-evidence/1: pass | fail | unknown | unsupported


def record(check, status, files=(), note="", implementation=None):
    """Write a cad-evidence/1 report for a check run and index it in the variant's manifest.

    cad/out/<variant>/<check>.evidence.json          {"status", "evidence": {schema cad-evidence/1, ...}}
    cad/out/<variant>/evidence/<check>.inputs.json   snapshot of every design input and its SHA-256
    cad/out/<variant>/manifest.json                  index: check -> time, raw status, inputs hash, report path
    Artifact and input paths are relative to the job directory (cad/out/<variant>/), so the folder can be copied and
    checked with mechanical-workflow-template evidence.verify_report.  Copies written outside the job directory
    (the release mirror in cad/fab/) are listed under extensions.external_copies, not as artifacts.
    WARN maps to pass (no requirement failed); anything unrecognised (a crash, a timeout) is unknown, never pass."""
    import platform
    import sys as _sys
    job = out_dir()
    now = datetime.datetime.now().isoformat(timespec="seconds")
    ins = input_files()
    snap_rel = "evidence/%s.inputs.json" % check
    snap = os.path.join(job, *snap_rel.split("/"))
    os.makedirs(os.path.dirname(snap), exist_ok=True)
    cur = inputs_hash()
    json.dump(dict(inputs_hash=cur, files=[dict(path=os.path.relpath(f, CAD).replace("\\", "/"), sha256=input_sha(f)) for f in ins]),
              open(snap, "w"), indent=0)
    arts, ext = [], []
    for f in files:
        f = os.path.abspath(f)
        rel = os.path.relpath(f, job).replace("\\", "/")
        if rel.startswith("..") or os.path.isabs(rel):
            ext.append(os.path.relpath(f, CAD).replace("\\", "/"))
        elif os.path.exists(f):
            arts.append(dict(id=os.path.basename(f), path=rel, sha256=_sha(f)))
    if implementation is None:
        implementation = _sys._getframe(1).f_code.co_filename
    vers = {"python": platform.python_version(), "platform": platform.system()}
    try:
        import FreeCAD
        vers["freecad"] = ".".join(FreeCAD.Version()[:3])
    except Exception:
        pass
    st = EVIDENCE_STATUS.get(str(status).upper(), "unknown")
    ev = {"schema": "cad-evidence/1", "producer": "light_weight_arm/cad/tools", "operation": check,
          "status": st, "reason": str(status) + ((": " + note) if note else ""), "scope": note or check,
          "versions": vers,
          "implementation_sha256": _sha(implementation) if os.path.isfile(implementation) else "unknown",
          "inputs": [dict(id="design-inputs", path=snap_rel, sha256=_sha(snap))],
          "artifacts": arts,
          "extensions": {"variant": variant(), "time": now, "inputs_hash": cur, "external_copies": ext}}
    rep = os.path.join(job, check + ".evidence.json")
    json.dump({"status": st, "evidence": ev}, open(rep, "w"), indent=1)
    p = os.path.join(job, "manifest.json")
    try:
        man = json.load(open(p))
    except Exception:
        man = {}
    man[check] = dict(time=now, inputs_hash=cur, status=status, evidence=os.path.basename(rep), note=note,
                      files=[a["path"] for a in arts] + ext)
    json.dump(man, open(p, "w"), indent=1, sort_keys=True)
    return ev


def evidence():
    """[(check, status, time, FRESH|STALE)] for the active variant's manifest against the current inputs."""
    p = os.path.join(CAD, "out", variant().lower(), "manifest.json")
    try:
        man = json.load(open(p))
    except Exception:
        return []
    cur = inputs_hash()
    return [(k, v["status"], v["time"], "FRESH" if v["inputs_hash"] == cur else "STALE") for k, v in sorted(man.items())]


def use_release_variant(script):
    """Release generators: build the released variant.  An explicit GRIP for another variant is refused, so a
    concept can't overwrite the released fab/drawings/FEA/render outputs."""
    rel = release_variant()
    g = os.environ.get("GRIP")
    if g and g.upper() != rel:
        raise RuntimeError("%s writes the released (%s) package; GRIP=%s refused. Use the checks under "
                         "cad/out/<variant>/ for other variants." % (script, rel, g))
    if g is None:
        os.environ["GRIP"] = rel
        print("%s: building the release variant GRIP=%s" % (script, rel))
    rb, b = release_base_drive(), os.environ.get("BASE_DRIVE")
    if b and b.upper() != rb:
        raise RuntimeError("%s writes the released (%s) package; BASE_DRIVE=%s refused (the released base drive is %s). "
                           "Use tools/export_variant.py for another variant's STEP/BOM." % (script, rel, b, rb))
    if b is None:
        os.environ["BASE_DRIVE"] = rb
