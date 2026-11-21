# -*- coding: utf-8 -*-
"""
Validate the project data files against cad/schemas/*.schema.json, plus cross-checks a schema can't express.
Pure Python 3.11+ (tomllib), no FreeCAD and no third-party packages, so hooks can run it in well under a second.

    python -I cad/tools/validate_data.py                  # every params/, interfaces/, envelopes/, data/ file
    python -I cad/tools/validate_data.py <file> [...]     # just these files
    python -I cad/tools/validate_data.py --hook           # Claude Code PostToolUse hook: reads the hook JSON on stdin,
                                                          # validates the edited file if it is a data file
Exit 0 = valid, 1 = errors (2 in --hook mode, so Claude Code feeds stderr back to the agent).
Errors name the file, line, field, what was expected and what was found.
"""
import ast
import json
import math
import os
import re
import sys
import tomllib

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMAS = os.path.join(CAD, "schemas")
KINDS = {"params": "params", "interfaces": "interface", "envelopes": "envelope", "data": None}
DATA_SCHEMA = {"catalogue": "catalogue"}
TYPES = {"object": dict, "array": list, "string": str, "boolean": bool}


# ------------------------------------------------------------------ minimal JSON-Schema subset
def _type_ok(v, t):
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    return isinstance(v, TYPES[t])


def _tname(v):
    return {dict: "table", list: "array", str: "string", bool: "boolean", int: "integer", float: "number"}.get(type(v), type(v).__name__)


def check(v, s, root, path=()):
    """-> list of (path, message). Supports the subset the project schemas use."""
    if "$ref" in s:
        ref = s["$ref"]
        node = root
        for part in ref.lstrip("#/").split("/"):
            node = node[part]
        return check(v, node, root, path)
    errs = []
    if "not" in s:
        if not check(v, s["not"], root, path):
            return [(path, s.get("description", "matches a form that is not allowed here"))]
    if "anyOf" in s:
        branches = [check(v, b, root, path) for b in s["anyOf"]]
        if all(branches):
            # report the branch whose shape fits (no type mismatch at this level), so a bad leaf deep in a table
            # is reported at that leaf rather than as "this table is not a number"
            fit = [b for b in branches if not any(p == path and m.startswith("expected ") for p, m in b)]
            if fit:
                best = min(fit, key=len)
                if isinstance(v, dict) and "value" not in v and any(p == path + ("value",) for p, _m in best):
                    return [(path, "expected a fact table {value, unit, source} (tables nest at most two levels), "
                                   "found a table with keys %s" % ", ".join(sorted(v)))]
                return best
            kinds = sorted({m.split(", found")[0][len("expected "):] for b in branches for p, m in b if p == path and m.startswith("expected ")})
            return [(path, "expected %s, found %s" % (" or ".join(kinds), _tname(v)))]
        # a branch matched: fall through, so the schema's own type/properties/enum beside the anyOf still apply
    t = s.get("type")
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_type_ok(v, x) for x in ts):
            return [(path, "expected %s, found %s %r" % (" or ".join(ts), _tname(v), v if not isinstance(v, (dict, list)) else "..."))]
    if "enum" in s and v not in s["enum"]:
        errs.append((path, "%r is not allowed; use one of %s" % (v, ", ".join(repr(e) for e in s["enum"]))))
    if isinstance(v, str):
        if len(v) < s.get("minLength", 0):
            errs.append((path, "too short (%d chars, need >= %d)" % (len(v), s["minLength"])))
        if "pattern" in s and not re.search(s["pattern"], v):
            errs.append((path, "%r does not match pattern %s" % (v, s["pattern"])))
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if "minimum" in s and v < s["minimum"]:
            errs.append((path, "%s is below the minimum %s" % (v, s["minimum"])))
        if "exclusiveMinimum" in s and v <= s["exclusiveMinimum"]:
            errs.append((path, "%s must be greater than %s" % (v, s["exclusiveMinimum"])))
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0):
            errs.append((path, "needs at least %d items, found %d" % (s["minItems"], len(v))))
        if "maxItems" in s and len(v) > s["maxItems"]:
            errs.append((path, "allows at most %d items, found %d" % (s["maxItems"], len(v))))
        if "items" in s:
            for i, x in enumerate(v):
                errs += check(x, s["items"], root, path + (i,))
    if isinstance(v, dict):
        if len(v) < s.get("minProperties", 0):
            errs.append((path, "table is empty"))
        for k in s.get("required", []):
            if k not in v:
                errs.append((path + (k,), "missing (required in %s)" % (".".join(map(str, path)) or "the file")))
        for k, deps in s.get("dependentRequired", {}).items():
            if k in v:
                for d in deps:
                    if d not in v:
                        errs.append((path + (d,), "missing: required because [%s] is present" % k))
        props = s.get("properties", {})
        extra = s.get("additionalProperties", True)
        for k, x in v.items():
            if k in props:
                errs += check(x, props[k], root, path + (k,))
            elif extra is False:
                allowed = ", ".join(sorted(props)) or "(none)"
                errs.append((path + (k,), "unknown key; allowed here: %s" % allowed))
            elif isinstance(extra, dict):
                errs += check(x, extra, root, path + (k,))
    return errs


# ------------------------------------------------------------------ cross-checks
def model_poses():
    """POSES keys parsed from arm/kinematics.py without importing FreeCAD."""
    src = open(os.path.join(CAD, "arm", "kinematics.py"), encoding="utf-8").read()
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "POSES" for t in node.targets):
            return {k.value for k in node.value.keys if isinstance(k, ast.Constant)}
    return set()


def cross_checks(kind, name, data):
    errs = []
    if kind == "interface":
        if data.get("interface", {}).get("name") not in (None, name):
            errs.append((("interface", "name"), "%r must equal the file name %r" % (data["interface"]["name"], name)))
        n = data.get("frame", {}).get("normal")
        if isinstance(n, list) and len(n) == 3 and all(isinstance(x, (int, float)) for x in n):
            if abs(math.sqrt(sum(x * x for x in n)) - 1.0) > 1e-6:
                errs.append((("frame", "normal"), "must be a unit vector, length is %.4f" % math.sqrt(sum(x * x for x in n))))
        for sk in ("side_a", "side_b"):
            sd = data.get(sk, {})
            if sd.get("hole") == "clearance" and "clearance_d" not in sd:
                errs.append(((sk, "clearance_d"), "missing: a clearance hole needs clearance_d"))
    if kind == "envelope":
        poses = model_poses()
        seen = set()
        for i, kz in enumerate(data.get("keepout", [])):
            nm = kz.get("name", "#%d" % i)
            if nm in seen:
                errs.append((("keepout", i, "name"), "duplicate keep-out name %r" % nm))
            seen.add(nm)
            mn, mx = kz.get("min"), kz.get("max")
            if isinstance(mn, list) and isinstance(mx, list) and len(mn) == len(mx) == 3:
                for ax, a, b in zip("xyz", mn, mx):
                    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not a < b:
                        errs.append((("keepout", i, "min"), "%s: min %s must be < max %s" % (ax, a, b)))
            for p in kz.get("poses", []):
                if poses and p not in poses:
                    errs.append((("keepout", i, "poses"), "unknown pose %r; poses in arm/kinematics.py: %s" % (p, ", ".join(sorted(poses)))))
    return errs


# ------------------------------------------------------------------ reporting
def line_of(text, path, data):
    """Best-effort 1-based line for an error path (key = ..., [table] or the keep-out entry's name)."""
    lines = text.split("\n")
    if path and path[0] == "keepout" and len(path) > 1 and isinstance(path[1], int):
        try:
            nm = data["keepout"][path[1]]["name"]
            for i, ln in enumerate(lines):
                if re.match(r'\s*name\s*=\s*"%s"' % re.escape(nm), ln):
                    start = i
                    if len(path) > 2:
                        for j in range(i, min(i + 40, len(lines))):
                            if re.match(r"\s*%s\s*=" % re.escape(str(path[2])), lines[j]):
                                return j + 1
                    return start + 1
        except (KeyError, IndexError, TypeError):
            pass
    for key in reversed([p for p in path if isinstance(p, str)]):
        for i, ln in enumerate(lines):
            if re.match(r"\s*%s\s*=" % re.escape(key), ln) or re.match(r"\s*\[+%s\]+" % re.escape(key), ln):
                return i + 1
    return 1


def kind_of(path):
    rel = os.path.relpath(os.path.abspath(path), CAD).replace("\\", "/")
    parts = rel.split("/")
    if len(parts) != 2 or not parts[1].endswith(".toml") or parts[0] not in KINDS:
        return None, rel
    k = KINDS[parts[0]] if parts[0] != "data" else DATA_SCHEMA.get(parts[1][:-5])
    return k, rel


def validate_file(path):
    kind, rel = kind_of(path)
    if kind is None:
        return rel, None, []
    text = open(path, encoding="utf-8").read()
    return rel, kind, validate_text(kind, os.path.basename(path)[:-5], text, rel)


def validate_text(kind, name, text, rel="<text>"):
    """Validate TOML text as a data file of this kind ('params', 'interface', 'envelope', 'catalogue')."""
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError as e:
        return ["%s: TOML syntax error: %s" % (rel, e)]
    schema = json.load(open(os.path.join(SCHEMAS, kind + ".schema.json"), encoding="utf-8"))
    errs = check(data, schema, schema) + cross_checks(kind, name, data)
    return ["%s:%d: %s: %s" % (rel, line_of(text, p, data), ".".join(map(str, p)) or "(file)", m) for p, m in errs]


def all_data_files():
    out = []
    for d in KINDS:
        folder = os.path.join(CAD, d)
        if os.path.isdir(folder):
            out += [os.path.join(folder, f) for f in sorted(os.listdir(folder)) if f.endswith(".toml")]
    return out


def main(argv):
    if "--hook" in argv:
        try:
            ev = json.load(sys.stdin)
        except Exception:
            return 0
        fp = (ev.get("tool_input") or {}).get("file_path") or ""
        if not fp or kind_of(fp)[0] is None or not os.path.exists(fp):
            return 0
        rel, kind, errs = validate_file(fp)
        if errs:
            print("Data file %s fails its schema (cad/schemas/%s.schema.json):\n  " % (rel, kind) + "\n  ".join(errs), file=sys.stderr)
            return 2
        print("%s valid. Geometry inputs changed: run cad/tools/quick_check.py before finishing." % rel, file=sys.stderr)
        return 0
    files = [a for a in argv if not a.startswith("-")] or all_data_files()
    n_err, n_ok = 0, 0
    for f in files:
        rel, kind, errs = validate_file(f)
        if kind is None:
            print("skip %s (not a params/interfaces/envelopes/data TOML file)" % rel)
            continue
        if errs:
            n_err += len(errs)
            print("\n".join(errs))
        else:
            n_ok += 1
    print("VALIDATE: %d file(s) valid, %d error(s)" % (n_ok, n_err))
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
