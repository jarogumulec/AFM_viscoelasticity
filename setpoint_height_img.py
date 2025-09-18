import matplotlib.pyplot as plt
import numpy as np
import afmformats as af
import pandas as pd
from skimage import io as skio

# Super-simple script similar to plot_data.py
# - Loads the AFM map
# - Extracts setpoint height from the approach segment (last sample)
# - Builds a 2D image and saves it as PNG

file_name = '/data/2025-09-05/PC-3-2029-bleb-25-dish1-data-2025.09.05-10.47.17.093.jpk-force-map'
out_png = 'setpoint_height.png'

afm_group = af.AFMGroup(file_name)

md0 = afm_group[0].metadata
n_x = int(md0['grid shape x'])
n_y = int(md0['grid shape y'])

img = np.full((n_y, n_x), np.nan, dtype=float)

for i, curve in enumerate(afm_group):
	# Convert curve to DataFrame
	df = pd.DataFrame()
	for col in curve.columns:
		df[col] = curve[col]

	# Approach segment = 0 (as in plot_data.py)
	seg = df['segment']
	approach_mask = seg == 0
	if not np.any(approach_mask):
		continue

	# Take the last sample of approach as the setpoint
	idx = np.flatnonzero(approach_mask)[-1]
	val = float(df['height (measured)'].iloc[idx])

	# Determine grid indices from metadata if present, else row-major fallback
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

# Determine scaling (ignore NaNs)
finite_mask = np.isfinite(img)
if np.any(finite_mask):
	vmin = float(np.nanmin(img))
	vmax = float(np.nanmax(img))
else:
	vmin, vmax = 0.0, 1.0

# Plot and save figure (using AFM-typical colormap)
plt.figure(figsize=(6, 5), dpi=150)
im = plt.imshow(img, origin='lower', cmap='afmhot', vmin=vmin, vmax=vmax)
plt.colorbar(im, label='setpoint height (height measured)')
plt.title('Setpoint height (approach)')
plt.xlabel('x index')
plt.ylabel('y index')
plt.tight_layout()
plt.savefig(out_png, dpi=150)
plt.close()
print(f'Saved figure: {out_png}')

# Save raw PNGs (not just the matplotlib figure)
# 1) Grayscale-normalized 8-bit image
den = (vmax - vmin) if (vmax > vmin) else 1.0
norm = (img - vmin) / den
norm = np.clip(norm, 0.0, 1.0)
norm[~finite_mask] = 0.0
gray_u8 = (norm * 255.0).astype(np.uint8)
raw_gray_png = f'{out_png}_raw.png'
skio.imsave(raw_gray_png, gray_u8)
print(f'Saved raw grayscale: {raw_gray_png}')

# 2) Color-mapped (afmhot) 8-bit RGB image
cmap = plt.get_cmap('afmhot')
rgba = cmap(norm)  # shape (H, W, 4)
rgb_u8 = (rgba[..., :3] * 255.0).astype(np.uint8)
raw_color_png = f'{out_png}_colormap.png'
skio.imsave(raw_color_png, rgb_u8)
print(f'Saved raw colormap: {raw_color_png}')




