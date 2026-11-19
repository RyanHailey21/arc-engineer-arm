import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))   # this checkout or worktree (TI-022)
import arm_model as M
t = time.time()
b = M.build_bodies()
print("build %.1fs, parts %d" % (time.time() - t, sum(len(v) for v in b.values())))
for k, v in b.items():
    print("  %-8s %3d parts" % (k, len(v)))
q, jaw = M.pose_q(os.environ.get("POSE", "STOW"))
sh = [x for x in M.placed(b, *q, jaw=jaw) if x[1].check]
t = time.time(); hits = []
for i in range(len(sh)):
    for j in range(i + 1, len(sh)):
        a, c = sh[i][2], sh[j][2]
        if a.BoundBox.intersect(c.BoundBox):
            try:
                v = a.common(c).Volume
            except Exception:
                v = -1
            if v > 0.5 or v < 0:
                hits.append((sh[i][0], sh[i][1].name, sh[j][0], sh[j][1].name, round(v, 1)))
print("static check %.1fs, %d overlaps" % (time.time() - t, len(hits)))
for h in hits:
    print("  %-8s %-34s x %-8s %-34s %8.1f" % h)
