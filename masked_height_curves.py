import os
from glob import glob
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import afmformats as af
from skimage import io as skio
import matplotlib.pyplot as plt

# Minimal configuration
folder = '/data/2025-09-05'
pattern = '*.jpk-force-map'
masks_dir = '/data/2025-09-05_masks'
out_dir = 'plots'

# Resample sizes per segment (approach, hold, retract)
SEG_SIZES = {0: 200, 1: 60, 2: 200}
SEG_NAMES = {0: 'approach', 1: 'hold', 2: 'retract'}
GROUP_COLORS = {
    'ctrl-dish1': '#1f77b4',
    'ctrl-dish2': '#ff7f0e',
    'bleb-dish1': '#2ca02c',
    'bleb-dish2': '#d62728',
}


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


def resample_segment(values: np.ndarray, seg_mask: np.ndarray, size: int) -> np.ndarray | None:
    if size <= 1:
        return None
    idxs = np.flatnonzero(seg_mask)
    if idxs.size < 2:
        return None
    # Normalize by sample index position (0..1)
    t = (idxs - idxs[0]) / (idxs[-1] - idxs[0])
    xgrid = np.linspace(0.0, 1.0, size)
    try:
        # values might be pandas Series or numpy
        v = np.asarray(values)[idxs]
        # Handle NaNs by simple forward/backward fill before interp
        if np.isnan(v).any():
            # simple fill: replace NaNs with nearest non-NaN
            notnan = ~np.isnan(v)
            if not notnan.any():
                return None
            v = np.interp(np.arange(len(v)), np.flatnonzero(notnan), v[notnan])
        y = np.interp(xgrid, t, v)
        return y
    except Exception:
        return None


def process_file(path: str) -> Tuple[str, Dict[int, np.ndarray] | None, Dict[int, np.ndarray] | None]:
    base = os.path.splitext(os.path.basename(path))[0]
    mask_path = find_mask_for(base)
    if mask_path is None:
        print(f'Skip {base}: mask not found')
        return base, None, None

    try:
        group = af.AFMGroup(path)
    except Exception as e:
        print(f'Skip {base}: cannot open ({e})')
        return base, None, None

    md0 = group[0].metadata
    n_x = int(md0['grid shape x'])
    n_y = int(md0['grid shape y'])

    try:
        mask_img = skio.imread(mask_path)
    except Exception as e:
        print(f'Skip {base}: cannot read mask ({e})')
        return base, None, None

    mask2d = rgb_red_mask(mask_img)
    if mask2d.shape != (n_y, n_x):
        print(f'Skip {base}: mask shape {mask2d.shape} != grid shape {(n_y, n_x)}')
        return base, None, None

    # Collect resampled curves per segment
    seg_curves: Dict[int, List[np.ndarray]] = {0: [], 1: [], 2: []}

    for i, curve in enumerate(group):
        gx, gy = curve_grid_xy(i, curve, n_x, n_y)
        if gx < 0 or gx >= n_x or gy < 0 or gy >= n_y:
            continue
        if not mask2d[gy, gx]:
            continue

        # Build DataFrame for the curve
        df = pd.DataFrame()
        for col in curve.columns:
            df[col] = curve[col]

        seg = df['segment']
        h = df['height (measured)']

        for s, size in SEG_SIZES.items():
            seg_mask = (seg == s).to_numpy() if hasattr(seg, 'to_numpy') else (np.asarray(seg) == s)
            y = resample_segment(np.asarray(h), seg_mask, size)
            if y is not None and np.isfinite(y).any():
                seg_curves[s].append(y)

    if not any(len(v) > 0 for v in seg_curves.values()):
        print(f'Skip {base}: no curves selected by mask')
        return base, None, None

    # Compute per-file mean and std per segment
    seg_mean: Dict[int, np.ndarray] = {}
    seg_std: Dict[int, np.ndarray] = {}
    for s, arrs in seg_curves.items():
        if arrs:
            A = np.vstack(arrs)
            seg_mean[s] = np.nanmean(A, axis=0)
            seg_std[s] = np.nanstd(A, axis=0)

    # Plot per-file mean curve: HOLD only
    if 1 in seg_mean:
        os.makedirs(out_dir, exist_ok=True)
        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        x = np.linspace(0, 1, len(seg_mean[1]))
        ax.plot(x, seg_mean[1] * 1e6, color='k', label='mean')
        ax.fill_between(x, (seg_mean[1] - seg_std[1]) * 1e6, (seg_mean[1] + seg_std[1]) * 1e6,
                        color='k', alpha=0.15, linewidth=0)
        ax.set_title(f'{base} — hold (masked mean)')
        ax.set_xlabel('normalized progress')
        ax.set_ylabel('height (µm)')
        fig.tight_layout()
        out_path = os.path.join(out_dir, f'{base}_hold_masked_mean_height_curve.png')
        fig.savefig(out_path, dpi=150)
        plt.close(fig)
        print(f'Saved per-file hold curve: {out_path}')

    return base, seg_mean, seg_std


def main():
    files = sorted(glob(os.path.join(folder, pattern)))
    if not files:
        print(f'No files found in {folder} matching {pattern}')
        return

    # Accumulate per-group lists of per-file means
    groups_means: Dict[str, Dict[int, List[np.ndarray]]] = {}

    for path in files:
        base = os.path.splitext(os.path.basename(path))[0]
        grp = file_group_from_name(base)
        _, seg_mean, _ = process_file(path)
        if seg_mean is None:
            continue
        d = groups_means.setdefault(grp, {0: [], 1: [], 2: []})
        for s in [0, 1, 2]:
            if s in seg_mean:
                d[s].append(seg_mean[s])

    if not groups_means:
        print('No group data to plot')
        return

    # Plot merged group averages: HOLD only
    os.makedirs(out_dir, exist_ok=True)
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    for grp, seg_dict in groups_means.items():
        arrs = seg_dict.get(1, [])
        if not arrs:
            continue
        min_len = min(len(a) for a in arrs)
        A = np.vstack([a[:min_len] for a in arrs])
        mean = np.nanmean(A, axis=0)
        std = np.nanstd(A, axis=0)
        x = np.linspace(0, 1, min_len)
        color = GROUP_COLORS.get(grp, None)
        ax.plot(x, mean * 1e6, label=grp, color=color)
        ax.fill_between(x, (mean - std) * 1e6, (mean + std) * 1e6,
                        color=color, alpha=0.15, linewidth=0)
    ax.set_title('Hold — group masked mean height (measured)')
    ax.set_xlabel('normalized progress')
    ax.set_ylabel('height (µm)')
    ax.legend(loc='upper right')
    fig.tight_layout()
    out_group = os.path.join(out_dir, 'group_hold_masked_mean_height_curves.png')
    fig.savefig(out_group, dpi=150)
    plt.close(fig)
    print(f'Saved group hold curves: {out_group}')


if __name__ == '__main__':
    main()
