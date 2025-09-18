import matplotlib.pyplot as plt
import numpy as np
import afmformats as af
import seaborn as sns
import pandas as pd


file_name = '/data/2025-09-05/PC-3-2029-bleb-25-dish1-data-2025.09.05-10.47.17.093.jpk-force-map'
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



# sns.lineplot(df, x='time', y='height (measured)', hue='segment', palette='tab10')
# plt.show()

# sns.lineplot(df, x='time', y='height (piezo)', hue='segment', palette='tab10')
# plt.show()

# sns.lineplot(df, x='time', y='force', hue='segment', palette='tab10')
# plt.show()


df['deflection'] = df['force'] / spring_constant
# height (piezo) - height (measured) = deflection


contact_index = df[df['segment'] == 'hold'].index[0]


z_c = df.at[contact_index, 'height (piezo)']
d_c = df.at[contact_index, 'deflection']



df['my height (measured)'] = df['height (piezo)'] - df['deflection']
df['height / deflection'] = df['height (piezo)'] / df['deflection']

df['height (piezo) - height (measured)']  = df['height (piezo)'] - df['my height (measured)']
df['delta'] = (df['height (piezo)'] - z_c) + (df['deflection'] - d_c)


# sns.lineplot(df, x='time', y='delta', hue='segment', palette='tab10')
# plt.show()


# sns.lineplot(df, x='time', y='deflection', hue='segment', palette='tab10')
# plt.show()


# sns.lineplot(df, x='time', y='deflection', hue='segment', palette='tab10')
# sns.lineplot(df, x='time', y='height (piezo)', hue='segment', palette='tab10', linestyle='--')
# plt.show()






sns.lineplot(df, x='time', y='height (piezo) - height (measured)', hue='segment', palette='tab10')
plt.show()

sns.lineplot(df, x='time', y='deflection', hue='segment', palette='tab10')
plt.show()