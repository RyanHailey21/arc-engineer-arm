# -*- coding: utf-8 -*-
"""Purchased-part mass vs the catalogue (TI-015).  Used by tools/quick_check.py (line `catalogue`) and by
tests/test_catalogue_mass.py.  Pure Python over already-built bodies: about 0.1 s.

  1. every CAT part's src is a data/catalogue.toml key (a missing key silently weighs 0 g in part_mass_g);
  2. sum(part_mass_g) per key == units x catalogue mass (within TOL), where units counts parts whose name has
     no "rotor" (the split-motor rule tools/bom.py uses for qty: stator part + rotor part = one motor);
  3. every "rotor" part has a "stator" sibling with the same stem (else the unit count is wrong).
"""
TOL = 0.005


def check(bodies, cat, part_mass_g):
    """Return (ok, data); data has keys, units, split, fails."""
    fails, rows, names = [], {}, set()
    for bn, parts in bodies.items():
        for p in parts:
            if p.kind != "CAT":
                continue
            names.add(p.name)
            if p.src not in cat:
                fails.append("%s/%s: src %r is not in data/catalogue.toml (weighs 0 g)" % (bn, p.name, p.src))
                continue
            e = rows.setdefault(p.src, dict(units=0, mass=0.0, parts=0))
            e["parts"] += 1
            e["units"] += 0 if "rotor" in p.name else 1
            e["mass"] += part_mass_g(p)
    for n in sorted(names):
        if "rotor" in n and n.replace("rotor", "stator") not in names:
            fails.append("%s: rotor part without a matching %s" % (n, n.replace("rotor", "stator")))
    for key, e in sorted(rows.items()):
        want = e["units"] * cat[key]["mass"]
        if (want or e["mass"]) and abs(e["mass"] - want) > TOL * max(want, 1e-9):
            fails.append("%s: modelled %.1f g over %d parts, expected %d unit(s) x %g g = %.1f g"
                         % (key, e["mass"], e["parts"], e["units"], cat[key]["mass"], want))
    split = {k: "%d parts = %d units" % (e["parts"], e["units"]) for k, e in rows.items() if e["parts"] != e["units"]}
    return not fails, dict(keys=len(rows), units=sum(e["units"] for e in rows.values()), split=split, fails=fails)
