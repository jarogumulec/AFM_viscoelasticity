import os
from glob import glob
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import afmformats as af
from skimage import io as skio
import matplotlib.pyplot as plt
import seaborn as sns

# Minimal configuration
folder = '/data/2025-09-05'
pattern = '*.jpk-force-map'
masks_dir = '/data/2025-09-05_masks'
out_dir = 'plots'

SEG_HOLD = 1


def find_mask_for(base: str) -> str | None:
    candidates = [
        os.path.join(masks_dir, f'{base}.png'),
        os.path.join(masks_dir, f'{base}_mask.png'),
        os.path.join(masks_dir, f'{base}.jpg'),
        os.path.join(masks_dir, f'{base}.jpeg'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    globs = glob(os.path.join(masks_dir, f'{base}*.png'))
    return globs[0] if globs else None


def rgb_red_mask(mask_img: np.ndarray) -> np.ndarray:
    if mask_img.ndim == 2:
        return mask_img > 0
    if mask_img.ndim == 3 and mask_img.shape[2] >= 3:
        r = mask_img[..., 0]
        g = mask_img[..., 1]
        b = mask_img[..., 2]
        max_val = 255.0 if mask_img.dtype not in (np.float32, np.float64) else 1.0
        thr_r = 0.7 * max_val
        thr_gb = 0.2 * max_val
        return (r >= thr_r) & (g <= thr_gb) & (b <= thr_gb)
    return np.zeros(mask_img.shape[:2], dtype=bool)


def file_group_from_name(name: str) -> str:
    s = name.lower()
    cond = 'ctrl' if 'ctrl' in s else ('bleb' if 'bleb' in s else 'unknown')
    dish = 'dish1' if 'dish1' in s else ('dish2' if 'dish2' in s else 'unknown')
    return f'{cond}-{dish}'


def curve_grid_xy(i: int, curve, n_x: int, n_y: int) -> Tuple[int, int]:
    md = getattr(curve, 'metadata', {}) or {}
    gx = md.get('grid index x')
    gy = md.get('grid index y')
    if gx is None or gy is None:
        gy = i // n_x
        gx = i % n_x
    return int(gx), int(gy)


def compute_hold_steepness(df: pd.DataFrame) -> float | None:
    # Steepness: linear slope of height(measured) vs time over the second half of hold
    seg = df['segment']
    hold_mask = (seg == SEG_HOLD)
    if not np.any(hold_mask):
        return None
    idxs = np.flatnonzero(hold_mask)
    if idxs.size < 4:
        return None
    start = idxs[0]
    end = idxs[-1]
    mid = start + (end - start) // 2
    use = np.arange(mid, end + 1)

    t = np.asarray(df['time'])[use]
    h = np.asarray(df['height (measured)'])[use]
    # require finite
    finite = np.isfinite(t) & np.isfinite(h)
    if finite.sum() < 3:
        return None
    t = t[finite]
    h = h[finite]
    # Normalize time to avoid scale issues (optional)
    t0 = t[0]
    t = t - t0
    # Linear least squares slope
    # slope units: meters per second
    A = np.vstack([t, np.ones_like(t)]).T
    try:
        slope, _ = np.linalg.lstsq(A, h, rcond=None)[0]
        return float(slope)
    except Exception:
        return None


def process_file(path: str) -> List[Tuple[str, float]]:
    base = os.path.splitext(os.path.basename(path))[0]
    mask_path = find_mask_for(base)
    if mask_path is None:
        print(f'Skip {base}: mask not found')
        return []

    try:
        group = af.AFMGroup(path)
    except Exception as e:
        print(f'Skip {base}: cannot open ({e})')
        return []

    md0 = group[0].metadata
    n_x = int(md0['grid shape x'])
    n_y = int(md0['grid shape y'])

    try:
        mask_img = skio.imread(mask_path)
    except Exception as e:
        print(f'Skip {base}: cannot read mask ({e})')
        return []

    mask2d = rgb_red_mask(mask_img)
    if mask2d.shape != (n_y, n_x):
        print(f'Skip {base}: mask shape {mask2d.shape} != grid shape {(n_y, n_x)}')
        return []

    results: List[Tuple[str, float]] = []
    for i, curve in enumerate(group):
        gx, gy = curve_grid_xy(i, curve, n_x, n_y)
        if gx < 0 or gx >= n_x or gy < 0 or gy >= n_y:
            continue
        if not mask2d[gy, gx]:
            continue
        df = pd.DataFrame()
        for col in curve.columns:
            df[col] = curve[col]
        slope = compute_hold_steepness(df)
        if slope is not None and np.isfinite(slope):
            results.append((base, slope))
    return results


def main():
    os.makedirs(out_dir, exist_ok=True)
    files = sorted(glob(os.path.join(folder, pattern)))
    if not files:
        print(f'No files found in {folder} matching {pattern}')
        return

    rows = []
    for path in files:
        base = os.path.splitext(os.path.basename(path))[0]
        grp = file_group_from_name(base)
        for _, slope in process_file(path):
            rows.append({
                'file': base,
                'group': grp,
                'slope_m_per_s': slope,
                'slope_um_per_s': slope * 1e6,
            })

    if not rows:
        print('No slopes computed; nothing to plot')
        return

    df = pd.DataFrame(rows)
    # Boxplot by group in µm/s
    plt.figure(figsize=(8, 4), dpi=150)
    sns.boxplot(data=df, x='group', y='slope_um_per_s', color='lightgray')
    sns.stripplot(data=df, x='group', y='slope_um_per_s', color='k', alpha=0.6, jitter=0.2)
    plt.ylabel('hold steepness (µm/s)')
    plt.xlabel('group')
    plt.title('Hold segment steepness — second half (masked curves)')
    plt.tight_layout()
    out_png = os.path.join(out_dir, 'hold_steepness_boxplot.png')
    plt.savefig(out_png, dpi=150)
    plt.close()
    print(f'Saved boxplot: {out_png}')


if __name__ == '__main__':
    main()
