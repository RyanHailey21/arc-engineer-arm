# -*- coding: utf-8 -*-
"""
Bloat / redundancy report: dead code, duplicates and orphaned project data, for a cleanup agent to act on.
Plain Python (no FreeCAD, no model build); a few seconds.  Informational: always exits 0.

    python -I cad/tools/bloat_report.py            full report -> cad/out/bloat_report.md + .json, evidence record
    python -I cad/tools/bloat_report.py --counts   one count line, writes nothing (git pre-commit hook, quick_check)

Findings (each has a stable id `kind:path:name`, so a later run can diff against cad/out/bloat_report.json):
  unused-import     an imported name the module never uses (skips `# noqa`, try/except imports, __init__.py)
  unused-variable   a local assigned once and never read (single-name targets only, not `_x`, like ruff F841)
  dead-def          a top-level function/class whose name appears nowhere else in the scanned code: not as a name,
                    attribute or word inside a string literal (so BODY_FUNCS-style dict lookups and getattr strings
                    count as uses; docstrings and comments do not)
  duplicate         >= DUP_MIN (6) identical consecutive code lines (comments, blank, trivial lines dropped) in
                    two places, or >= NEAR_MIN (8) once names/numbers/strings are blanked (id near-*)
  orphan-param      a params/*.toml key that no code reads (no string literal or attribute with its name)
  orphan-catalogue  a data/catalogue.toml key no code names (parts use catalogue keys as their `src` string)
  orphan-interface  an interfaces/*.toml file that no builder (arm/, hardware.py) loads by name
  orphan-envelope   an envelopes/*.toml file with no keep-out boxes
  out-unindexed     a file in cad/out/<variant>/ that manifest.json does not index and no tool names
  scratch           a local leftover: *.bak*, *.FCBak, *.orig, *.tmp, *~ (git-ignored, so only on this machine)

Scanned code: every git-tracked *.py (cad/, sim/, analysis/) plus untracked, not-ignored *.py.
Anything matching tools/bloat_keep.toml is reported as "kept" with its reason, never as bloat; the rev A package
(fab/, drawings/out, fea/out, render/) and the release generators are on it.
Limits: a name built at run time (getattr(H, "gt2_" + x)) is invisible, so check a dead-def before deleting it;
a TOML key read by iterating its table (for k, v in T.items()) shows as an orphan unless kept.
"""
import ast
import fnmatch
import hashlib
import json
import keyword
import os
import re
import subprocess
import sys
import time
import tomllib
from collections import Counter, defaultdict

T0 = time.time()
CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) if "__file__" in globals() else \
    r"C:\Users\ryanh\light_weight_arm\cad"
ROOT = os.path.dirname(CAD)
KEEP_FILE = os.path.join(CAD, "tools", "bloat_keep.toml")
OUT_MD = os.path.join(CAD, "out", "bloat_report.md")
OUT_JSON = os.path.join(CAD, "out", "bloat_report.json")
DUP_MIN = 6                       # identical significant lines before a block counts as a duplicate
NEAR_MIN = 8                      # lines identical after renaming (names -> N, numbers -> 0, strings -> S)
WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
SCRATCH = ("*.bak", "*.bak[0-9]*", "*.FCBak", "*.orig", "*.tmp", "*~")
# .claude/ holds Claude Code settings and other sessions' git worktrees (.claude/worktrees/<name>/, full copies of
# the repo): scanning them would report every file twice and their scratch as ours (TI-022).
SKIP_DIRS = {"__pycache__", ".git", ".cache", "node_modules", ".venv", ".claude"}
SKIP_PREFIX = ("tools/blender-", ".claude/")      # the downloaded Blender install; Claude Code worktrees
SELF = {"cad/tools/bloat_report.py", "cad/tests/test_bloat_report.py"}   # name findings in strings: not uses
KINDS = ("unused-import", "unused-variable", "dead-def", "duplicate", "orphan-param", "orphan-catalogue",
         "orphan-interface", "orphan-envelope", "out-unindexed", "scratch")


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def _git(*args):
    try:
        r = subprocess.run(["git", "-C", ROOT] + list(args), capture_output=True, text=True, timeout=20)
        return r.stdout.splitlines() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def py_files():
    tracked = _git("ls-files", "--cached", "--others", "--exclude-standard", "--", "*.py")
    if tracked is None:                           # no git: walk the tree
        tracked = []
        for d, dirs, fs in os.walk(ROOT):
            dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith("blender-")]
            tracked += [rel(os.path.join(d, f)) for f in fs if f.endswith(".py")]
    return sorted(f for f in set(tracked) if not f.startswith(SKIP_PREFIX) and f not in SELF
                  and os.path.isfile(os.path.join(ROOT, f)))


# ------------------------------------------------------------------ parsing
class Module:
    """One parsed file: its names, attributes and string-literal words, with docstrings left out."""

    def __init__(self, path, src=None):
        self.path = path
        self.src = src if src is not None else open(os.path.join(ROOT, path), encoding="utf-8", errors="replace").read()
        self.lines = self.src.splitlines()
        try:
            self.tree = ast.parse(self.src)
        except SyntaxError:
            self.tree = None
        self.words = Counter()          # every identifier use: Name, Attribute, import alias, words in strings
        self.strings = set()            # whole string constants (catalogue keys, file names, format patterns)
        self.attrs = set()
        if self.tree is None:
            return
        docs = set()
        for n in ast.walk(self.tree):
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and n.body:
                b = n.body[0]
                if isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and isinstance(b.value.value, str):
                    docs.add(id(b.value))
        for n in ast.walk(self.tree):
            if isinstance(n, ast.Name):
                self.words[n.id] += 1
            elif isinstance(n, ast.Attribute):
                self.words[n.attr] += 1
                self.attrs.add(n.attr)
            elif isinstance(n, ast.alias):
                for w in (n.name.split(".") + ([n.asname] if n.asname else [])):
                    self.words[w] += 1
            elif isinstance(n, ast.keyword) and n.arg:
                self.words[n.arg] += 1
            elif isinstance(n, ast.Constant) and isinstance(n.value, str) and id(n) not in docs:
                self.strings.add(n.value)
                for w in WORD.findall(n.value):
                    self.words[w] += 1

    def noqa(self, line):
        return 0 < line <= len(self.lines) and "noqa" in self.lines[line - 1]


def unused_imports(m):
    if m.tree is None or m.path.endswith("__init__.py"):
        return []
    in_try = set()
    for n in ast.walk(m.tree):
        if isinstance(n, ast.Try):
            for b in n.body:
                for x in ast.walk(b):
                    in_try.add(id(x))
    used = Counter()
    for n in ast.walk(m.tree):
        if isinstance(n, ast.Name):
            used[n.id] += 1
        elif isinstance(n, ast.Constant) and isinstance(n.value, str):
            for w in WORD.findall(n.value):            # __all__ entries, names in strings
                used[w] += 1
    out = []
    for n in ast.walk(m.tree):
        if not isinstance(n, (ast.Import, ast.ImportFrom)) or id(n) in in_try or m.noqa(n.lineno):
            continue
        if isinstance(n, ast.ImportFrom) and n.module == "__future__":
            continue
        for a in n.names:
            if a.name == "*":
                continue
            bound = a.asname or a.name.split(".")[0]
            if not used[bound]:
                out.append(("unused-import", m.path, n.lineno, bound, "`%s` imported, never used" % bound))
    return out


def unused_variables(m):
    if m.tree is None:
        return []
    out = []
    for fn in ast.walk(m.tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        loads, stores, escape = Counter(), {}, False
        for n in ast.walk(fn):
            if isinstance(n, ast.Name):
                if isinstance(n.ctx, ast.Load):
                    loads[n.id] += 1
                    if n.id in ("locals", "vars", "eval", "exec"):
                        escape = True
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                for x in n.names:
                    loads[x] += 1
            elif isinstance(n, (ast.Assign, ast.AnnAssign)):
                tg = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in tg:
                    if isinstance(t, ast.Name):
                        stores.setdefault(t.id, n.lineno)
            elif isinstance(n, ast.AugAssign) and isinstance(n.target, ast.Name):
                loads[n.target.id] += 1
        if escape:
            continue
        for name, line in stores.items():
            if not loads[name] and not name.startswith("_") and not m.noqa(line):
                out.append(("unused-variable", m.path, line, "%s.%s" % (fn.name, name),
                            "`%s` assigned in %s(), never read" % (name, fn.name)))
    return out


FROZEN_GLOBS = []                  # keep-list [[path]] globs, set by scan(): rev A package and release generators


def frozen(path):
    return any(fnmatch.fnmatch(path, g) for g in FROZEN_GLOBS)


def _only_frozen(users):
    """Kept-reason for a name that only frozen code (rev A package, release generators) uses, else None."""
    return ("used only by frozen/release code: %s" % ", ".join(sorted(users)[:3])) if users else None


def dead_defs(mods):
    total, by_frozen = Counter(), defaultdict(set)
    for m in mods.values():
        if frozen(m.path):
            for w in m.words:
                by_frozen[w].add(m.path)
        else:
            total.update(m.words)
    out = []
    for m in mods.values():
        if m.tree is None or frozen(m.path):         # frozen code's own helpers are its business
            continue
        is_test = "/tests/" in m.path or os.path.basename(m.path).startswith("test_")
        for n in m.tree.body:
            if not isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                continue
            nm = n.name
            if nm == "main" or nm.startswith("__") or (is_test and nm.startswith("test")) or n.decorator_list:
                continue
            if total[nm] == 0:                        # the def itself is not a Name node; recursion counts as use
                out.append(("dead-def", m.path, n.lineno, nm, "%s `%s` is never referenced" % (
                    "class" if isinstance(n, ast.ClassDef) else "function", nm), None, _only_frozen(by_frozen[nm])))
    return out


TRIVIAL = re.compile(r"^(\)|\]|\}|\),?|\],?|\}\)?,?|else:|try:|finally:|pass|return|break|continue|"
                     r"except.*:|@\w+|import .*|from .* import .*|if __name__.*)$")


KEYWORDS = set(keyword.kwlist)


def _normalise(s):
    s = re.sub(r"\"[^\"]*\"|'[^']*'", "S", s)
    s = re.sub(r"\b\d+(\.\d*)?\b", "0", s)
    return WORD.sub(lambda w: w.group() if w.group() in KEYWORDS else "N", s)


def duplicates(mods, min_n=None, near=False):
    """Runs of >= min_n identical significant lines (stripped; comments, blank and trivial lines dropped).
    near=True compares the lines after _normalise(): same shape, different names or numbers (copy-paste-edit)."""
    min_n = min_n or (NEAR_MIN if near else DUP_MIN)
    DUP = min_n
    seqs = {}
    for m in mods.values():
        sig = []
        for i, ln in enumerate(m.lines, 1):
            s = ln.split("#", 1)[0].strip() if not ln.strip().startswith(("'", '"')) else ln.strip()
            if len(s) < 6 or TRIVIAL.match(s):
                continue
            sig.append((i, _normalise(s) if near else s))
        seqs[m.path] = sig
    index = defaultdict(list)
    for p, sig in seqs.items():
        for k in range(len(sig) - DUP + 1):
            h = hashlib.sha1("\n".join(s for _i, s in sig[k:k + DUP]).encode()).hexdigest()
            index[h].append((p, k))
    pairs = {}                                         # (pathA, kA, pathB, kB) -> run length, extended greedily
    seen = set()
    for h, locs in index.items():
        if len(locs) < 2:
            continue
        a = locs[0]
        for b in locs[1:]:
            if (a, b) in seen:
                continue
            pa, ka = a
            pb, kb = b
            if pa == pb and abs(ka - kb) < DUP:
                continue
            n = DUP
            sa, sb = seqs[pa], seqs[pb]
            while ka + n < len(sa) and kb + n < len(sb) and sa[ka + n][1] == sb[kb + n][1]:
                n += 1
            for j in range(n - DUP + 1):
                seen.add(((pa, ka + j), (pb, kb + j)))
            pairs[(pa, ka, pb, kb)] = n
    out = []
    for (pa, ka, pb, kb), n in sorted(pairs.items()):
        if any(((pa, ka), (pb, kb)) != ((qa, qka), (qb, qkb)) and pa == qa and pb == qb and
               qka <= ka < qka + m_ and qkb <= kb < qkb + m_ for (qa, qka, qb, qkb), m_ in pairs.items()):
            continue                                   # inside a longer run already reported
        sa, sb = seqs[pa], seqs[pb]
        la, lb = sa[ka][0], sb[kb][0]
        digest = hashlib.sha1("\n".join(s for _i, s in sa[ka:ka + n]).encode()).hexdigest()[:10]
        out.append(("duplicate", pa, la, ("near-" if near else "") + digest, "%d %s lines also at %s:%d" % (
            n, "near-identical (renamed)" if near else "identical", pb, lb), pb))
    return out


# ------------------------------------------------------------------ project data
def _leaves(d, prefix=()):
    for k, v in d.items():
        if isinstance(v, dict) and not ("value" in v and set(v) <= {"value", "unit", "source", "status"}):
            yield from _leaves(v, prefix + (k,))
        else:
            yield prefix + (k,), v


def _toml_line(path, key):
    try:
        for i, ln in enumerate(open(path, encoding="utf-8"), 1):
            if re.match(r"\s*\"?%s\"?\s*=" % re.escape(key), ln) or ln.strip().startswith("[%s" % key) or \
                    ln.strip() == '["%s"]' % key:
                return i
    except OSError:
        pass
    return 1


def orphan_params(mods, d=None):
    words, by_frozen = Counter(), defaultdict(set)
    for m in mods.values():
        ws = [w for s in m.strings for w in WORD.findall(s)] + list(m.attrs)
        if frozen(m.path):
            for w in ws:
                by_frozen[w].add(m.path)
        else:
            words.update(ws)
    out = []
    d = d or os.path.join(CAD, "params")
    for fn in sorted(os.listdir(d)):
        if not fn.endswith(".toml"):
            continue
        p = os.path.join(d, fn)
        stem = fn[:-5]
        data = tomllib.load(open(p, "rb"))
        for path, _v in _leaves(data):
            leaf = path[-1]
            if not words[leaf]:
                out.append(("orphan-param", rel(p), _toml_line(p, leaf), ".".join(path),
                            "params/%s.toml key `%s` is read by no code" % (stem, ".".join(path)), None,
                            _only_frozen(by_frozen[leaf])))
    return out


def orphan_catalogue(mods):
    strings, by_frozen = set(), defaultdict(set)
    for m in mods.values():
        if m.path.endswith("tools/validate_data.py"):
            continue
        if frozen(m.path):
            for x in m.strings:
                by_frozen[x].add(m.path)
        else:
            strings |= m.strings
    strings |= set(part_map_srcs())          # src built at run time ("GEAR-M1-%dT" % n): the model's own part list
    p = os.path.join(CAD, "data", "catalogue.toml")
    out = []
    for k in tomllib.load(open(p, "rb")):
        if k not in strings:
            out.append(("orphan-catalogue", rel(p), _toml_line(p, k), k,
                        "catalogue key `%s`: no part uses it as its src" % k, None, _only_frozen(by_frozen[k])))
    return out


MAP_NOTES = []                     # set by part_map_srcs(): stale part maps (they would hide an orphan key)


def part_map_srcs():
    """Catalogue keys used by CAT parts, from cad/out/<variant>/map_parts.md (tools/make_map.py, built from the
    model).  Notes a map older than the newest model input: rerun make_map.py for an exact catalogue check."""
    keys, newest = set(), 0.0
    try:
        sys.path.insert(0, CAD)
        import params as _p
        newest = max(os.path.getmtime(f) for f in _p.input_files())
    except Exception:
        pass
    MAP_NOTES[:] = []
    od = os.path.join(CAD, "out")
    for var in sorted(os.listdir(od)) if os.path.isdir(od) else []:
        mp = os.path.join(od, var, "map_parts.md")
        if not os.path.isdir(os.path.join(od, var)) or var == "evidencetest":
            continue
        if not os.path.isfile(mp):
            MAP_NOTES.append("%s: no map_parts.md (run tools/make_map.py)" % var)
            continue
        if os.path.getmtime(mp) < newest:
            MAP_NOTES.append("%s/map_parts.md is older than the model inputs (rerun tools/make_map.py)" % var)
        for ln in open(mp, encoding="utf-8"):
            c = [x.strip() for x in ln.split("|")]
            if len(c) > 5 and c[3] == "CAT":
                keys.add(c[4])
    return keys


def orphan_interfaces(mods):
    builders = set()
    for m in mods.values():
        if m.path.startswith("cad/arm/") or m.path in ("cad/hardware.py", "cad/arm_model.py"):
            builders |= m.strings
    out = []
    d = os.path.join(CAD, "interfaces")
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".toml") and fn[:-5] not in builders:
            out.append(("orphan-interface", rel(os.path.join(d, fn)), 1, fn[:-5],
                        "no builder loads interfaces/%s (iface.load(\"%s\"))" % (fn, fn[:-5])))
    d = os.path.join(CAD, "envelopes")
    for fn in sorted(os.listdir(d)):
        if fn.endswith(".toml") and not tomllib.load(open(os.path.join(d, fn), "rb")).get("keepout"):
            out.append(("orphan-envelope", rel(os.path.join(d, fn)), 1, fn[:-5], "envelopes/%s has no keep-out box" % fn))
    return out


def _pattern(s):
    """A string constant used to build file names ("%s_report.txt", "{v}.json") -> regex, or None."""
    if not re.search(r"%[-0-9.]*[sdf]|\{[^}]*\}", s):
        return None
    parts = re.split(r"%[-0-9.]*[sdf]|\{[^}]*\}", s)
    if sum(len(x) for x in parts) < 4:
        return None
    return re.compile("^" + ".+".join(re.escape(x) for x in parts) + "$")


def out_unindexed(mods):
    names, pats = set(), []
    for m in mods.values():
        for s in m.strings:
            if len(s) > 200 or "\n" in s:
                continue
            b = os.path.basename(s.replace("\\", "/"))
            if b:
                names.add(b)
            r = _pattern(b)
            if r:
                pats.append(r)
    out = []
    od = os.path.join(CAD, "out")
    for var in sorted(os.listdir(od)):
        vd = os.path.join(od, var)
        if not os.path.isdir(vd):
            continue
        indexed = {"manifest.json"}
        try:
            for k, e in json.load(open(os.path.join(vd, "manifest.json"))).items():
                indexed.add(e.get("evidence") or "")
                indexed |= {os.path.basename(f) for f in e.get("files", [])}
        except (OSError, ValueError):
            pass
        for d, dirs, fs in os.walk(vd):
            dirs[:] = [x for x in dirs if x not in ("evidence",) and not x.startswith("ccx_")]
            for f in fs:
                if any(fnmatch.fnmatch(f, g) for g in SCRATCH) or f.endswith((".vtu",)):
                    continue                           # scratch is its own kind; .vtu are ignored FEA results
                if f in indexed or f in names or any(r.match(f) for r in pats):
                    continue
                p = os.path.join(d, f)
                out.append(("out-unindexed", rel(p), 1, rel(p),
                            "not in %s/manifest.json and no tool writes a file of this name" % var))
    ign = set(_git_ignored([o[1] for o in out]))
    return [o if o[1] not in ign else o + (None, "git-ignored solver/tool output (regenerable, never committed)")
            for o in out]


def _git_ignored(paths):
    if not paths:
        return []
    try:
        r = subprocess.run(["git", "-C", ROOT, "check-ignore", "--"] + list(paths), capture_output=True,
                           text=True, timeout=20)       # (not --stdin: Windows text mode would send "\r\n")
        return [x.strip().replace("\\", "/") for x in r.stdout.splitlines()]
    except (OSError, subprocess.SubprocessError):
        return []


def scratch():
    out = []
    for d, dirs, fs in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS and not x.startswith("blender-")]
        for f in fs:
            if any(fnmatch.fnmatch(f, g) for g in SCRATCH):
                p = os.path.join(d, f)
                out.append(("scratch", rel(p), 1, rel(p), "local leftover (%.0f kB)" % (os.path.getsize(p) / 1024)))
    return out


# ------------------------------------------------------------------ keep-list, ids, report
def load_keep(path=KEEP_FILE):
    try:
        k = tomllib.load(open(path, "rb"))
    except OSError:
        return [], []
    return k.get("path", []), k.get("item", [])


def keep_reason(f, keep):
    kind, path, _line, name = f["kind"], f["path"], f["line"], f["name"]
    paths, items = keep
    for e in paths:
        if fnmatch.fnmatch(path, e["glob"]) or path.startswith(e["glob"].rstrip("*").rstrip("/") + "/") \
                and e["glob"].endswith("/**"):
            e["_hit"] = True
            return e["reason"]
    for e in items:
        if e.get("kind") not in (kind, "*"):
            continue
        if not fnmatch.fnmatchcase(name.split(".")[-1] if kind in ("orphan-param", "unused-variable") else name,
                                   e.get("name", "*")) and not fnmatch.fnmatchcase(name, e.get("name", "*")):
            continue
        if "path" in e and not fnmatch.fnmatch(path, e["path"]):
            continue
        e["_hit"] = True
        return e["reason"]
    return None


def scan(files=None, keep=None, extra_sources=None, params_dir=None):
    """-> dict(findings=[...], kept=[...], counts={kind: n}, scanned=n, ...).
    Tests: extra_sources {path: source} adds planted modules; params_dir scans another params folder."""
    files = py_files() if files is None else files
    mods = {p: Module(p) for p in files}
    for p, s in (extra_sources or {}).items():
        mods[p] = Module(p, s)
    keep = load_keep() if keep is None else keep
    FROZEN_GLOBS[:] = [e["glob"] for e in keep[0]]
    raw = []
    for m in mods.values():
        raw += unused_imports(m) + unused_variables(m)
    live = {p: m for p, m in mods.items() if not frozen(p)}       # duplicates inside frozen code are not bloat
    exact = duplicates(live)
    near = [d for d in duplicates(live, near=True) if not any(
        d[1] == e[1] and d[5] == e[5] and abs(d[2] - e[2]) < 15 for e in exact)]
    raw += dead_defs(mods) + exact + near + orphan_params(mods, params_dir) + orphan_catalogue(mods)
    raw += orphan_interfaces(mods) + out_unindexed(mods) + scratch()
    findings, kept = [], []
    for r in raw:
        f = dict(kind=r[0], path=r[1], line=r[2], name=r[3], detail=r[4], id="%s:%s:%s" % (r[0], r[1], r[3]))
        if len(r) > 5 and r[5]:
            f["other"] = r[5]
        why = (r[6] if len(r) > 6 else None) or keep_reason(f, keep) or \
            (keep_reason(dict(f, path=f["other"]), keep) if "other" in f else None)
        if why:
            f["kept"] = why
            kept.append(f)
        else:
            findings.append(f)
    findings.sort(key=lambda f: (KINDS.index(f["kind"]), f["id"]))
    kept.sort(key=lambda f: (KINDS.index(f["kind"]), f["id"]))
    counts = {k: sum(1 for f in findings if f["kind"] == k) for k in KINDS}
    stale = [dict(e.get("glob") and {"glob": e["glob"]} or {k: e[k] for k in ("kind", "name", "path") if k in e},
                  reason=e["reason"]) for e in keep[1] if not e.get("_hit") and not e.get("guard")]
    return dict(findings=findings, kept=kept, counts=counts, scanned=len(mods), stale_keep=stale, notes=list(MAP_NOTES))


def counts_line(res):
    c = res["counts"]
    return "BLOAT %d findings (%s), %d kept" % (
        sum(c.values()), ", ".join("%s %d" % (k, n) for k, n in c.items() if n) or "none", len(res["kept"]))


def write(res, elapsed):
    prev = set()
    try:
        prev = {f["id"] for f in json.load(open(OUT_JSON))["findings"]}
    except (OSError, ValueError, KeyError):
        pass
    cur = {f["id"] for f in res["findings"]}
    res = dict(res, new=sorted(cur - prev) if prev else [], resolved=sorted(prev - cur),
               keep_file=rel(KEEP_FILE))
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    json.dump(res, open(OUT_JSON, "w", encoding="utf-8"), indent=1)
    L = ["# Bloat report", "",
         "Generated by `cad/tools/bloat_report.py` (%d Python files). Informational; nothing was changed." % (
             res["scanned"]),
         "Keep-list: `%s`. Ids are stable (`kind:path:name`); `bloat_report.json` holds the same data." % rel(KEEP_FILE),
         "", "**%s**" % counts_line(res), ""]
    if prev:
        L += ["Since the last run: %d new, %d resolved." % (len(res["new"]), len(res["resolved"])), ""]
    L += ["Note: %s." % n for n in res.get("notes", [])] + ([""] if res.get("notes") else [])
    L += ["Before deleting a `dead-def`, grep for names built at run time; before removing an `orphan-param`, check "
          "for code that iterates its table. Never touch anything under **Kept**.", ""]
    for k in KINDS:
        fs = [f for f in res["findings"] if f["kind"] == k]
        if not fs:
            continue
        L += ["## %s (%d)" % (k, len(fs)), "", "| where | what | id |", "|---|---|---|"]
        L += ["| `%s:%d` | %s | `%s` |" % (f["path"], f["line"], f["detail"].replace("|", "\\|"), f["id"]) for f in fs]
        L.append("")
    if res.get("stale_keep"):
        L += ["## Keep-list entries that matched nothing (%d)" % len(res["stale_keep"]), "",
              "Remove them from the keep-list if what they protected is gone.", ""]
        L += ["- `%s`: %s" % (json.dumps({k: v for k, v in e.items() if k != "reason"}), e["reason"])
              for e in res["stale_keep"]]
        L.append("")
    L += ["## Kept (%d)" % len(res["kept"]), "", "| where | what | why kept |", "|---|---|---|"]
    ks = [f for f in res["kept"] if not (f["kind"] == "scratch" and frozen(f["path"]))]
    L += ["| `%s:%d` | %s | %s |" % (f["path"], f["line"], f["detail"].replace("|", "\\|"), f["kept"]) for f in ks]
    if len(ks) < len(res["kept"]):
        L += ["", "Plus %d FreeCAD backup files inside frozen rev A folders (listed in the JSON)." % (
            len(res["kept"]) - len(ks))]
    open(OUT_MD, "w", encoding="utf-8").write("\n".join(L) + "\n")
    return res


def main(argv):
    res = scan()
    if "--counts" in argv:
        print(counts_line(res))
        return 0
    res = write(res, time.time() - T0)
    print(counts_line(res))
    if res.get("new") or res.get("resolved"):
        print("  since last run: %d new, %d resolved" % (len(res["new"]), len(res["resolved"])))
    print("  -> %s, %s  (%.1f s)" % (rel(OUT_MD), rel(OUT_JSON), time.time() - T0))
    try:
        sys.path.insert(0, CAD)
        import params
        n = sum(res["counts"].values())
        params.record("bloat", "WARN" if n else "PASS", [OUT_MD, OUT_JSON], counts_line(res))
    except Exception as e:                            # evidence is best-effort; the report is the product
        print("  (evidence record skipped: %s)" % e)
    return 0


if __name__ == "__main__" and not os.environ.get("QC_IMPORT"):
    try:
        main(sys.argv[1:])
    except Exception as e:                            # informational tool: never block a commit or a check
        print("BLOAT report failed: %s: %s" % (type(e).__name__, e))
    sys.exit(0)
