# -*- coding: utf-8 -*-
"""Encode FreeCAD-rendered PNG frames to H.264 MP4 using Blender's bundled FFmpeg
(Video Sequencer only - no rendering).
    blender -b -P cad/render/encode_frames.py -- <frames_dir> <out.mp4> [fps]
"""
import os
import sys

import bpy

args = sys.argv[sys.argv.index("--") + 1:]
src, out = args[0], args[1]
fps = int(args[2]) if len(args) > 2 else 24
files = sorted(f for f in os.listdir(src) if f.lower().endswith(".png"))
sc = bpy.context.scene
sc.sequence_editor_create()
seqs = sc.sequence_editor.strips if hasattr(sc.sequence_editor, "strips") else sc.sequence_editor.sequences
strip = seqs.new_image(name="frames", filepath=os.path.join(src, files[0]), channel=1, frame_start=1)
for f in files[1:]:
    strip.elements.append(f)
sc.frame_start, sc.frame_end = 1, len(files)
sc.render.fps = fps
try:
    img = bpy.data.images.load(os.path.join(src, files[0]))
    w, h = img.size
except Exception:
    w, h = 1280, 720
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, 100
try:
    sc.render.image_settings.media_type = "VIDEO"
except Exception:
    pass
sc.render.image_settings.file_format = "FFMPEG"
sc.render.ffmpeg.format = "MPEG4"
sc.render.ffmpeg.codec = "H264"
sc.render.ffmpeg.constant_rate_factor = "HIGH"
sc.render.filepath = out
bpy.ops.render.render(animation=True)
print("wrote", out, len(files), "frames")
