# Prepare MakeHuman CC0 textures for the channel guy: remove the MakeHuman logo from the tee, dye the tee
# orange (channel colour), drop the corner watermark, downsize, write to project/assets/guy/.
# usage: .venv\Scripts\python.exe -I -X utf8 jobs\20261109-zdf-sivrisinek\scripts\prep_textures.py
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

JOB = Path(__file__).resolve().parents[1]
SRC = JOB / '_dl' / 'mh_cc0' / 'x'
OUT = JOB / 'project' / 'assets' / 'guy'
OUT.mkdir(parents=True, exist_ok=True)


def save(img, name, size=None, q=92):
    if size: img = img.resize((size, size), Image.LANCZOS)
    p = OUT / name
    if name.endswith('.jpg'): img.convert('RGB').save(p, quality=q)
    else: img.save(p, optimize=True)
    print(name, img.size, p.stat().st_size // 1024, 'KB')


# ---- clothes: tee + jeans
d = np.asarray(Image.open(SRC / 'clothes/male_casualsuit06/male_casualsuit06_diffuse.png').convert('RGB')).astype(np.float32) / 255
H, W, _ = d.shape
tee = np.zeros((H, W), bool); tee[: int(0.42 * H), :] = True
# logo = saturated orange or mid-grey letters inside the tee area -> replace by the blurred local white
hsv_s = d.max(2) - d.min(2); lum = d.mean(2)
logo = tee & ((hsv_s > 0.12) | (lum < 0.72))
logo_img = Image.fromarray((logo * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))
logo = np.asarray(logo_img) > 0
clean = d.copy()
fill = np.asarray(Image.fromarray((d * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(40))).astype(np.float32) / 255
# blur from non-logo pixels only (normalised convolution)
m = (~logo & tee).astype(np.float32)
num = np.asarray(Image.fromarray((d * m[..., None] * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30))).astype(np.float32) / 255
den = np.asarray(Image.fromarray((m * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(30))).astype(np.float32)[..., None] / 255
fill = num / np.maximum(den, 1e-3)
clean[logo] = fill[logo]
# dye: keep the fabric shading (luminance) of the white tee, colour it orange
L = clean.mean(2, keepdims=True)
orange = np.array([0.86, 0.30, 0.06], np.float32)
dyed = np.clip(orange * (L / 0.82) ** 1.15, 0, 1)
out = clean.copy(); out[tee] = dyed[tee]
# corner watermark (bottom-right) -> background grey
out[int(0.96 * H):, int(0.82 * W):] = out[int(0.9 * H), int(0.95 * W)]
save(Image.fromarray((out * 255).astype(np.uint8)), 'clothes_diffuse.jpg', 2048)
save(Image.open(SRC / 'clothes/male_casualsuit06/male_casualsuit06_normal.png').convert('RGB'), 'clothes_normal.jpg', 2048, 95)
save(Image.open(SRC / 'clothes/male_casualsuit06/male_casualsuit06_ao.png').convert('L'), 'clothes_ao.jpg', 1024)

# ---- skin, hair, brows, lashes, eyes
save(Image.open(SRC / 'skins/young_caucasian_male/young_lightskinned_male_diffuse.png').convert('RGB'), 'skin_diffuse.jpg', 2048, 94)
save(Image.open(SRC / 'hair/short02/short02_diffuse.png').convert('RGBA'), 'hair_diffuse.png', 1024)
save(Image.open(SRC / 'hair/short02/short02_normal.png').convert('RGB'), 'hair_normal.jpg', 1024)
save(Image.open(SRC / 'eyebrows/eyebrow001/eyebrow001.png').convert('RGBA'), 'eyebrow.png')
save(Image.open(SRC / 'eyelashes/eyelashes01/eyelashes01.png').convert('RGBA'), 'eyelashes.png')
save(Image.open(SRC / 'eyes/materials/brown_eye.png').convert('RGB'), 'eye_brown.jpg', 512)
