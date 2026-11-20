# -*- coding: utf-8 -*-
"""
Generate cad/MAP.md: a searchable index of the model - modules and their builders, parameter files, interfaces,
envelopes, and every part (body, kind, source, mass, and the file:line that builds it) for each gripper variant.

    set GRIP=SCREW   & freecadcmd cad/tools/make_map.py      (writes cad/out/screw/map_parts.md)
    set GRIP=FOURBAR & freecadcmd cad/tools/make_map.py      (writes cad/out/fourbar/map_parts.md, then MAP.md)
Each run refreshes its variant's part table and rebuilds MAP.md from every variant table on disk.
"""
import ast
import glob
import os
import sys
import tomllib

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else r"C:\Users\ryanh\light_weight_arm\cad"
sys.path.insert(0, CAD)
import arm_model as M      # noqa: E402
import params              # noqa: E402

REL = lambda p: os.path.relpath(p, CAD).replace("\\", "/")


def modules_section():
    out = ["## Model modules (`cad/arm/`)", "", "| Module | What it holds | Builders and key functions |", "|---|---|---|"]
    for f in sorted(glob.glob(os.path.join(CAD, "arm", "*.py")) + glob.glob(os.path.join(CAD, "arm", "grippers", "*.py"))):
        if f.endswith("__init__.py"):
            continue
        tree = ast.parse(open(f, encoding="utf-8").read())
        doc = " ".join((ast.get_docstring(tree) or "").strip().split("\n\n")[0].split())
        fns = ["`%s` :%d" % (n.name, n.lineno) for n in tree.body if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
        out.append("| [%s](%s) | %s | %s |" % (REL(f), REL(f), doc.replace("|", "/"), ", ".join(fns)))
    return out


def toml_section(title, folder, describe):
    out = ["## %s (`cad/%s/`)" % (title, folder), ""]
    for f in sorted(glob.glob(os.path.join(CAD, folder, "*.toml"))):
        d = tomllib.load(open(f, "rb"))
        out.append("- [%s](%s): %s" % (os.path.basename(f), REL(f), describe(d)))
    return out + [""]


def params_desc(d):
    keys = []
    for k, v in d.items():
        keys.append("`%s` (%s)" % (k, ", ".join(v)) if isinstance(v, dict) else "`%s`" % k)
    return "; ".join(keys)


def iface_desc(d):
    i = d.get("interface", {})
    sides = []
    for k in sorted(k for k in d if k.startswith("side_")):        # a side names one part or several (parts list)
        sides += [d[k]["part"]] if "part" in d[k] else [bp[1] for bp in d[k]["parts"]]
    return "%s%s" % (i.get("summary", ""), (" - parts: " + " / ".join(sides)) if sides else "")


def env_desc(d):
    return "; ".join("`%s` @ %s" % (k["name"], ", ".join(k["poses"])) for k in d.get("keepout", []))


def link(where):
    """'arm/wrist.py:97 roll_hub_parts' -> markdown link to that line."""
    try:
        loc, fn = where.split(" ", 1)
        path, ln = loc.split(":")
        return "[%s](%s#L%s) %s" % (loc, path, ln, fn)
    except ValueError:
        return where


def part_table():
    bodies = M.build_bodies()
    out = ["### Parts - variant %s (%d parts)" % (M.GRIP, sum(len(v) for v in bodies.values())), "",
           "| Body | Part | Kind | Source / note | Mass g | Built at |", "|---|---|---|---|---|---|"]
    for bn, ps in bodies.items():
        cat = {}
        for p in ps:
            m = M.part_mass_g(p)
            w = link(getattr(p, "where", "?"))
            if p.kind == "CAT":                          # group identical purchased items per builder line
                k = (p.src, w)
                c = cat.setdefault(k, [0, 0.0, p.name])
                c[0] += 1
                c[1] += m
                continue
            out.append("| %s | %s | %s | %s | %.1f | %s |" % (bn, p.name, p.kind, p.src.replace("|", "/")[:90], m, w))
        for (src, w), (n, m, first) in cat.items():
            nm = first if n == 1 else "%s (x%d)" % (first.rstrip("0123456789_"), n)
            out.append("| %s | %s | CAT | %s | %.1f | %s |" % (bn, nm, src, m, w))
    return out


def main():
    var = M.GRIP.lower()
    tbl = os.path.join(params.out_dir(), "map_parts.md")
    open(tbl, "w", encoding="utf-8").write("\n".join(part_table()) + "\n")
    doc = ["# Model map (generated - do not edit)", "",
           "Regenerate with `cad/tools/make_map.py` (once per variant).  Search here first: every part links to the",
           "file:line that builds it; parameters, interfaces and keep-outs are data files.  Active variant comes from",
           "`params/variant.toml` (override with GRIP).  Inputs hash at generation: `%s`." % params.inputs_hash(), ""]
    doc += modules_section() + [""]
    doc += toml_section("Parameters", "params", params_desc)
    doc += ["- [catalogue.toml](data/catalogue.toml): purchased parts (%d entries) - desc, mass, source, verify" % len(M.CAT), ""]
    doc += toml_section("Interfaces", "interfaces", iface_desc)
    doc += toml_section("Envelopes", "envelopes", env_desc)
    doc += ["## Checks and outputs", "",
            "- `tools/quick_check.py` (~25-30 s, every edit) -> `out/<variant>/quick.json`",
            "- `check_interference.py`, `tools/check_holes.py`, `tools/check_engagement.py`, `tools/projected_heights.py`"
            " -> `out/<variant>/`; each run is logged in `out/<variant>/manifest.json` with the inputs hash",
            "- `tools/fingerprint.py` -> regression guard against `tests/fingerprints/<variant>.json`",
            "- release generators (export_fab, fea/run_fea, drawings, build_assembly, render/export_render) build the"
            " release variant (`params/variant.toml` release) into `fab/`, `fea/out/`, `drawings/out/`, `render/`", ""]
    doc += ["## Parts by variant", ""]
    for t in sorted(glob.glob(os.path.join(CAD, "out", "*", "map_parts.md"))):
        doc += open(t, encoding="utf-8").read().rstrip("\n").split("\n") + [""]
    open(os.path.join(CAD, "MAP.md"), "w", encoding="utf-8").write("\n".join(doc) + "\n")
    print("MAP written: %s (variant %s table refreshed)" % (os.path.join(CAD, "MAP.md"), var))


main()
