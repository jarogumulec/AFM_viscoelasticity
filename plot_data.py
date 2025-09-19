import matplotlib.pyplot as plt
import numpy as np
import afmformats as af
import seaborn as sns
import pandas as pd
from scipy.ndimage import gaussian_filter1d

file_name = 'PC-3-2029-bleb-25-dish1-data-2025.09.05-10.47.17.093.jpk-force-map'
ind = 45
SEG_NAMES = {0: "approach", 1: "hold", 2: "retract"}



afm_group = af.AFMGroup(file_name)


metadata = afm_group[0].metadata
n_x = metadata['grid shape x']
n_y = metadata['grid shape y']
spring_constant = metadata['spring constant']
light_lever_sensitivity = metadata['sensitivity']
invOLS = 1 / light_lever_sensitivity

curve = afm_group[ind]
# curve.columns = ['force', 'height (measured)', 'height (piezo)', 'segment', 'time']

df = pd.DataFrame()
for col in curve.columns:
    df[col] = curve[col]



df['segment'] = [SEG_NAMES[x] for x in df['segment']]





df['deflection'] = df['force'] / spring_constant
# height (piezo) - height (measured) = deflection
#  height (measured) = height (piezo) - deflection


df['force_filtered'] = gaussian_filter1d(df['force'], sigma=50)



#sns.lineplot(df, x='time', y='force', hue='segment', palette='tab10')
#plt.show()

# sns.lineplot(df, x='time', y='deflection', hue='segment', palette='tab10')
# plt.show()

#sns.lineplot(df, x='time', y='height (piezo)', hue='segment', palette='tab10')
#plt.show()

#sns.lineplot(df, x='time', y='height (measured)', hue='segment', palette='tab10')
#plt.show()


#sns.lineplot(df, x='height (measured)', y='force', hue='segment', palette='tab10')
#plt.show()



# sns.lineplot(df, x='time', y='force_filtered', hue='segment', palette='tab10')
# plt.show()


# --- hold-only dual Y: compact version using pandas plotting (secondary_y) ---
hold = df[df['segment'] == 'hold']
if not hold.empty:
    ax = hold.plot(x='time', y=['force', 'height (measured)'], secondary_y='height (measured)',
                   color=['tab:blue', 'tab:orange'], figsize=(8, 4.5))
    ax.set_xlabel('time [s]')
    ax.set_ylabel('force [N]')
    ax.right_ax.set_ylabel('height (measured) [m]')
    ax.set_title(f"Hold (segment==1) — curve idx={ind}")
    ax.grid(True, alpha=0.3)
    fig = ax.get_figure()
    fig.tight_layout()
    fig.savefig(f"Figure_hold_dualy_idx{ind:03d}.png", dpi=200)
    plt.show()
else:
    print("No rows with segment == 'hold' found; skipping hold-only dual-Y plot.")