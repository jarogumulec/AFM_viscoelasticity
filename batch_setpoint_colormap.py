import os
from glob import glob

import numpy as np
import afmformats as af
import pandas as pd
import matplotlib.pyplot as plt
from skimage import io as skio

# Minimal batch script:
# - Set 'folder' to the directory containing AFM map files
# - For each file matching the pattern, compute the setpoint height image
#   (last sample of approach segment) and save a raw afmhot colormap PNG.

folder = '/data/2025-09-05'
pattern = '*.jpk-force-map'


def process_file(path: str) -> None:
    try:
        group = af.AFMGroup(path)
    except Exception as e:
        print(f"Skip {path}: cannot open ({e})")
        return

    md0 = group[0].metadata
    n_x = int(md0['grid shape x'])
    n_y = int(md0['grid shape y'])

    img = np.full((n_y, n_x), np.nan, dtype=float)

    for i, curve in enumerate(group):
        df = pd.DataFrame()
        for col in curve.columns:
            df[col] = curve[col]

        seg = df['segment']
        approach_mask = seg == 0
        if not np.any(approach_mask):
            continue

        idx = np.flatnonzero(approach_mask)[-1]
        val = float(df['height (measured)'].iloc[idx])

        md = getattr(curve, 'metadata', {}) or {}
        gx = md.get('grid index x')
        gy = md.get('grid index y')
        if gx is None or gy is None:
            gy = i // n_x
            gx = i % n_x

        gx = int(gx)
        gy = int(gy)
        if 0 <= gx < n_x and 0 <= gy < n_y:
            img[gy, gx] = val

    # Normalize and color-map
    finite_mask = np.isfinite(img)
    if np.any(finite_mask):
        vmin = float(np.nanmin(img))
        vmax = float(np.nanmax(img))
    else:
        vmin, vmax = 0.0, 1.0
    den = (vmax - vmin) if (vmax > vmin) else 1.0
    norm = (img - vmin) / den
    norm = np.clip(norm, 0.0, 1.0)
    norm[~finite_mask] = 0.0

    cmap = plt.get_cmap('afmhot')
    rgba = cmap(norm)
    rgb_u8 = (rgba[..., :3] * 255.0).astype(np.uint8)

    base = os.path.splitext(os.path.basename(path))[0]
    out_png = os.path.join(os.path.dirname(path), f"{base}_setpoint_height_afmhot.png")
    skio.imsave(out_png, rgb_u8)
    print(f"Saved {out_png}")


def main():
    files = sorted(glob(os.path.join(folder, pattern)))
    if not files:
        print(f"No files found in {folder} matching {pattern}")
        return
    for path in files:
        process_file(path)


if __name__ == '__main__':
    main()
