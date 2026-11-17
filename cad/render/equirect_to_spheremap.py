"""Convert the Poly Haven equirectangular studio image to OpenGL sphere maps
(for Coin SoTextureCoordinateEnvironment), at several reflection strengths."""
import os
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
src = Image.open(os.path.join(HERE, "assets", "polyhaven", "studio_small_03_tonemapped.jpg")).convert("RGB")
E = np.asarray(src).astype(np.float32) / 255.0
H, W, _ = E.shape
n = 1024
y, x = np.mgrid[0:n, 0:n]
s = (x + 0.5) / n * 2 - 1
t = 1 - (y + 0.5) / n * 2
r2 = s * s + t * t
inside = r2 <= 1
nz = np.sqrt(np.clip(1 - r2, 0, 1))
# sphere-map normal (s, t, nz); reflection of view dir (0,0,-1) about normal
rx, ry, rz = 2 * nz * s, 2 * nz * t, 2 * nz * nz - 1
lon = np.arctan2(rx, -rz)
lat = np.arcsin(np.clip(ry, -1, 1))
u = ((lon / (2 * np.pi)) + 0.5) * (W - 1)
v = (0.5 - lat / np.pi) * (H - 1)
img = E[v.astype(int), u.astype(int)]
img[~inside] = 0
for name, k in (("env_full", 1.0), ("env_metal", 0.75), ("env_dark", 0.35), ("env_coat", 0.22)):
    out = np.clip(img * k * 255, 0, 255).astype(np.uint8)
    Image.fromarray(out).save(os.path.join(HERE, "assets", name + ".png"))
    print("wrote", name)
