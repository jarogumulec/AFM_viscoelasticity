import os
from glob import glob
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import afmformats as af
from skimage import io as skio
from skimage.measure import label as cc_label
import matplotlib.pyplot as plt

# Minimal configuration
folder = '/data/2025-09-05'
pattern = '*.jpk-force-map'
masks_dir = '/data/2025-09-05/masky'
out_dir = '/data/2025-09-05_curves'
### jeden file je naprd - ma kratke hold krivky - tak mu vymazat krivky před dalším krokem!!!!


# Segment names (no resampling/normalization; we only use HOLD)
SEG_NAMES = {0: 'approach', 1: 'hold', 2: 'retract'}


def find_mask_for(base: str) -> str | None:
    candidates = [
        os.path.join(masks_dir, f'{base}.tif'),
        # os.path.join(masks_dir, f'{base}.png'),
        # os.path.join(masks_dir, f'{base}_mask.png'),
        # os.path.join(masks_dir, f'{base}.jpg'),
        # os.path.join(masks_dir, f'{base}.jpeg'),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    globs = glob(os.path.join(masks_dir, f'{base}*.tif'))
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
    # kept for potential future use; not used in this script version
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


# No resampling: keep original time axis per curve


def find_time_column(df: pd.DataFrame) -> str | None:
    """Heuristically find a time column in seconds in curve DataFrame."""
    candidates = [
        'time (s)', 'Time (s)', 'time_s', 'timestamp (s)', 'timestamp_s', 'time'
    ]
    cols_lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        lc = cand.lower()
        if lc in cols_lower:
            return cols_lower[lc]
    # fuzzy: any column containing 'time'
    for c in df.columns:
        if 'time' in c.lower():
            return c
    return None


def process_file(path: str) -> None:
    base = os.path.splitext(os.path.basename(path))[0]
    mask_path = find_mask_for(base)
    if mask_path is None:
        print(f'Skip {base}: mask not found')
        return

    try:
        group = af.AFMGroup(path)
    except Exception as e:
        print(f'Skip {base}: cannot open ({e})')
        return

    md0 = group[0].metadata
    n_x = int(md0['grid shape x'])
    n_y = int(md0['grid shape y'])

    try:
        mask_img = skio.imread(mask_path)
    except Exception as e:
        print(f'Skip {base}: cannot read mask ({e})')
        return

    mask2d = rgb_red_mask(mask_img)
    if mask2d.shape != (n_y, n_x):
        print(f'Skip {base}: mask shape {mask2d.shape} != grid shape {(n_y, n_x)}')
        return

    # Connected components (cells) from mask
    labels = cc_label(mask2d.astype(np.uint8), connectivity=1)
    n_components = labels.max()
    if n_components == 0:
        print(f'Skip {base}: mask has no connected components')
        return

    """
    We will build, for each connected component, a list of raw hold-segment curves as
    (time_from_start_s, height_um). Later we'll interpolate onto a common time grid
    to produce a per-component mean±std in time units. Only the averaged CSV+PNG are saved.
    """
    comp_hold_times_raw: Dict[int, List[np.ndarray]] = {comp_id: [] for comp_id in range(1, n_components + 1)}
    comp_hold_heights_um_raw: Dict[int, List[np.ndarray]] = {comp_id: [] for comp_id in range(1, n_components + 1)}

    for i, curve in enumerate(group):
        gx, gy = curve_grid_xy(i, curve, n_x, n_y)
        if gx < 0 or gx >= n_x or gy < 0 or gy >= n_y:
            continue
        comp_id = int(labels[gy, gx])
        if comp_id == 0:
            continue

        # Build DataFrame for the curve
        df = pd.DataFrame()
        for col in curve.columns:
            df[col] = curve[col]

        seg = df['segment']
        h = df['height (measured)']

        # Only process HOLD segment (s == 1). No resampling.
        seg_mask = (seg == 1).to_numpy() if hasattr(seg, 'to_numpy') else (np.asarray(seg) == 1)
        idxs = np.flatnonzero(seg_mask)
        if idxs.size >= 2:
            t_col = find_time_column(df)
            if t_col is not None:
                try:
                    t = np.asarray(df[t_col], dtype=float)
                    # Save ORIGINAL time and height arrays for this curve's HOLD segment
                    time_orig = t[idxs]
                    height_um = np.asarray(h, dtype=float)[idxs] * 1e6
                    if time_orig.size >= 2 and height_um.size == time_orig.size:
                        # shift time to start at 0 for this curve
                        t0 = float(time_orig[0])
                        comp_hold_times_raw[comp_id].append(time_orig - t0)
                        comp_hold_heights_um_raw[comp_id].append(height_um)
                except Exception:
                    pass
    # Output per-component HOLD average curves (time domain): save CSV and plot
    base_out_dir = os.path.join(out_dir, base)
    os.makedirs(base_out_dir, exist_ok=True)

    components_with_data = 0
    for comp_id in range(1, n_components + 1):
        # Build averaged curve if we have any raw curves
        t_list = comp_hold_times_raw.get(comp_id, [])
        y_list = comp_hold_heights_um_raw.get(comp_id, [])
        if not t_list or not y_list:
            continue

        # Determine common time domain: 0 .. min(max time among curves)
        try:
            t_max_common = min(float(np.max(t)) for t in t_list if t.size > 1)
        except ValueError:
            t_max_common = 0.0
        if not np.isfinite(t_max_common) or t_max_common <= 0:
            continue
        # Simple uniform grid in seconds
        n_points = 200
        t_grid = np.linspace(0.0, t_max_common, n_points)

        mats: List[np.ndarray] = []
        for t, y in zip(t_list, y_list):
            if t.size < 2 or y.size != t.size:
                continue
            msk = np.isfinite(t) & np.isfinite(y)
            t2 = t[msk]
            y2 = y[msk]
            if t2.size < 2:
                continue
            try:
                y_grid = np.interp(t_grid, t2, y2)
                mats.append(y_grid)
            except Exception:
                continue
        if not mats:
            continue
        A = np.vstack(mats)
        mean_um = np.nanmean(A, axis=0)
        std_um = np.nanstd(A, axis=0)
        n_curves = A.shape[0]

        # Save CSV and PNG
        df_out = pd.DataFrame({
            'file': [base] * n_points,
            'component_id': [comp_id] * n_points,
            'time_s': t_grid,
            'height_um_mean': mean_um,
            'height_um_std': std_um,
            'n_curves': [n_curves] * n_points,
        })
        csv_path = os.path.join(base_out_dir, f'{base}_comp{comp_id:03d}_hold_avg_time.csv')
        df_out.to_csv(csv_path, index=False)

        fig, ax = plt.subplots(figsize=(6, 4), dpi=150)
        ax.plot(t_grid, mean_um, color='k', label='mean')
        ax.fill_between(t_grid, mean_um - std_um, mean_um + std_um, color='k', alpha=0.15, linewidth=0)
        ax.set_title(f'{base} — comp {comp_id} — hold (n={n_curves})')
        ax.set_xlabel('time (s)')
        ax.set_ylabel('height (µm)')
        fig.tight_layout()
        png_path = os.path.join(base_out_dir, f'{base}_comp{comp_id:03d}_hold_avg_time.png')
        fig.savefig(png_path, dpi=150)
        plt.close(fig)
        print(f'Saved: {csv_path} and {png_path}')
        components_with_data += 1

    if components_with_data == 0:
        print(f'Skip {base}: no curves selected by components in mask')
        return


def main():
    files = sorted(glob(os.path.join(folder, pattern)))
    if not files:
        print(f'No files found in {folder} matching {pattern}')
        return

    # Process each file independently, generating per-component outputs
    for path in files:
        process_file(path)


if __name__ == '__main__':
    main()
