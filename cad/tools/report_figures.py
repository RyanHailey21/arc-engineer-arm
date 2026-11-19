"""CAD figures for cad/docs/compliance_report.md (the gripper head before/after the top-and-bottom jaw support).

Two steps, because the "before" head is built from an older commit's code:
  1. headless, in any checkout (this one, or a worktree of the old commit):
         python -I cad/tools/run.py --grip FOURBAR cad/tools/report_figures.py <out.FCStd> [POSE]
     writes the gripper head (head, jaws, links) at POSE (default DONUT_PICK) plus <out>.json with each part's colour.
  2. in the FreeCAD GUI (view providers and the 3D view exist only there):
         exec(open(r"<repo>/cad/tools/report_figures.py").read()); render(r"<out.FCStd>", r"<png stem>")
     colours the parts and saves <stem>_iso.png, <stem>_low.png (from below), <stem>_front.png (looking at the pads), <stem>_side.png.
The report's images live in cad/docs/figures/ (regenerate after a gripper change).
"""
import json
import os
import sys

HEAD_GROUPS = ("HEAD", "JAW_L", "JAW_R", "LK_LD", "LK_LI", "LK_RD", "LK_RI")
RGB = {"cf": (0.15, 0.15, 0.17), "pla": (0.90, 0.32, 0.06), "alu": (0.80, 0.81, 0.84), "steel": (0.55, 0.56, 0.60),
       "motor": (0.10, 0.10, 0.11), "pad": (0.12, 0.40, 0.90), "brass": (0.85, 0.65, 0.30), "pcb": (0.05, 0.30, 0.10),
       "pom": (0.92, 0.91, 0.86)}


def export(out, pose="DONUT_PICK"):
    cad = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, cad)
    import FreeCAD as App
    import arm_model as M
    doc = App.newDocument("head")
    colours = {}
    q, jaw = M.pose_q(pose)
    from arm.kinematics import placements
    to_head = placements(*q, jaw=jaw)["HEAD"].inverse()     # draw in the gripper frame: x along the roll axis, z up
    for bname, p, s in M.placed(M.build_bodies(), *q, jaw=jaw, which="vis"):
        if bname not in HEAD_GROUPS or s.isNull():
            continue
        s.Placement = to_head.multiply(s.Placement)
        o = doc.addObject("Part::Feature", p.name.replace("-", "_"))
        o.Shape = s
        colours[o.Name] = p.color
    doc.recompute()
    doc.saveAs(out)
    json.dump(dict(pose=pose, grip=M.GRIP, colours=colours), open(os.path.splitext(out)[0] + ".json", "w"), indent=1)
    print("head (%s, %s): %d parts -> %s" % (M.GRIP, pose, len(colours), out))


def render(fcstd, stem, w=1600, h=1200):
    import FreeCAD as App
    import FreeCADGui as Gui
    meta = json.load(open(os.path.splitext(fcstd)[0] + ".json"))
    doc = App.openDocument(fcstd)
    for o in doc.Objects:
        vo = o.ViewObject
        vo.Visibility = True                    # documents saved headless store their objects hidden
        vo.ShapeColor = RGB.get(meta["colours"].get(o.Name), (0.5, 0.5, 0.5))
        vo.LineColor = (0.05, 0.05, 0.05)
        vo.LineWidth = 1.0
    App.setActiveDocument(doc.Name)
    gd = Gui.getDocument(doc.Name)
    Gui.ActiveDocument = gd
    v = gd.activeView() or gd.mdiViewsOfType("Gui::View3DInventor")[0]
    Gui.updateGui()
    Gui.runCommand("Std_OrthographicCamera")
    v.setAnimationEnabled(False)                # else saveImage catches the camera mid-turn between views
    from PIL import Image, ImageChops
    views = (("iso", lambda: v.viewIsometric()),
             ("low", lambda: v.setViewDirection((-1.0, -1.0, 0.7))),     # from front-left, below: the bottom links
             ("front", lambda: v.viewRight()),                          # looking along -x at the pads
             ("side", lambda: v.viewFront()))
    for name, setter in views:
        setter()
        v.fitAll()
        png = "%s_%s.png" % (stem, name)
        v.saveImage(png, w, h, "#FFFFFF")
        im = Image.open(png).convert("RGB")                             # crop to the part, 24 px margin
        box = ImageChops.difference(im, Image.new("RGB", im.size, (255, 255, 255))).getbbox()
        if box:
            im.crop((max(0, box[0] - 24), max(0, box[1] - 24), min(im.width, box[2] + 24),
                     min(im.height, box[3] + 24))).save(png)
    App.closeDocument(doc.Name)


if __name__ == "__main__":
    export(sys.argv[1], *(sys.argv[2:3] or []))


def compose(src_dir, out_png):
    """Before/after panel for the report: rows = top-held (before) / top+bottom (after), columns = iso, side, low."""
    from PIL import Image, ImageDraw, ImageFont
    cols, rows = ("iso", "side", "low"), (("old", "Before: each jaw held by the links at its top only"),
                                         ("new", "After: links hold each jaw at its top and its bottom"))
    cw, ch, head = 900, 620, 70
    try:
        font, small = ImageFont.truetype("arialbd.ttf", 34), ImageFont.truetype("arial.ttf", 26)
    except OSError:
        font = small = ImageFont.load_default()
    names = {"iso": "isometric", "side": "side (links' plane)", "low": "from below"}
    out = Image.new("RGB", (cw * len(cols), (ch + head) * len(rows)), "white")
    d = ImageDraw.Draw(out)
    for i, (tag, title) in enumerate(rows):
        y0 = i * (ch + head)
        d.text((20, y0 + 16), title, font=font, fill=(11, 11, 11))
        for j, c in enumerate(cols):
            im = Image.open(os.path.join(src_dir, "head_%s_%s.png" % (tag, c))).convert("RGB")
            im.thumbnail((cw - 40, ch - 50))
            x = j * cw + (cw - im.width) // 2
            out.paste(im, (x, y0 + head + (ch - 40 - im.height) // 2))
            d.text((j * cw + 20, y0 + head + ch - 40), names[c], font=small, fill=(82, 81, 78))
        if i:
            d.line((0, y0 - 2, out.width, y0 - 2), fill=(200, 200, 200), width=3)
    out.save(out_png)
