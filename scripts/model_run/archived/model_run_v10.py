from models import get_nn_bn3 as model_func
import tensorflow as tf
import os
from training import training3, SGDRScheduler, LrRangeFinder
from prediction import prediction
from results_viz import VizFuncs
import sys

sys.path.append('../../')
from CPR.configs import data_path

# Version numbers
print('Tensorflow version:', tf.__version__)
print('Python Version:', sys.version)

# ==================================================================================
# Examining batch size effects on testing results. Keeping % cloud cover equal and testing on different images
# However, v9 uses two neural layers and v10 uses three
# Batch size = 16385
# ==================================================================================
# Parameters

uncertainty = False
batch = 'v10'
pctls = [50]
BATCH_SIZE = 2**14
EPOCHS = 100
DROPOUT_RATE = 0.3  # Dropout rate for MCD
HOLDOUT = 0.3  # Validation data size

try:
    (data_path / batch).mkdir()
except FileExistsError:
    pass

# To get list of all folders (images) in directory
# img_list = os.listdir(data_path / 'images')

# img_list = ['4115_LC08_021033_20131227_test']
img_list = ['4444_LC08_044033_20170222_2',
            '4101_LC08_027038_20131103_1',
#             '4101_LC08_027038_20131103_2',
#             '4101_LC08_027039_20131103_1',
            '4115_LC08_021033_20131227_1',
            '4115_LC08_021033_20131227_2',
#             '4337_LC08_026038_20160325_1',
#             '4444_LC08_043034_20170303_1',
            '4444_LC08_043035_20170303_1',
            '4444_LC08_044032_20170222_1',
            '4444_LC08_044033_20170222_1',
#             '4444_LC08_044033_20170222_3',
#             '4444_LC08_044033_20170222_4',
#             '4444_LC08_044034_20170222_1',
            '4444_LC08_045032_20170301_1',
            '4468_LC08_022035_20170503_1',
            '4468_LC08_024036_20170501_1',
#             '4468_LC08_024036_20170501_2',
#             '4469_LC08_015035_20170502_1',
#             '4469_LC08_015036_20170502_1',
            '4477_LC08_022033_20170519_1',
            '4514_LC08_027033_20170826_1']

# Order in which features should be stacked to create stacked tif
feat_list_new = ['GSW_maxExtent', 'GSW_distExtent', 'aspect', 'curve', 'developed', 'elevation', 'forest',
                 'hand', 'other_landcover', 'planted', 'slope', 'spi', 'twi', 'wetlands', 'GSW_perm', 'flooded']

model_params = {'batch_size': BATCH_SIZE,
                'epochs': EPOCHS,
                'verbose': 2,
                'use_multiprocessing': True}

viz_params = {'img_list': img_list,
              'pctls': pctls,
              'data_path': data_path,
              'uncertainty': uncertainty,
              'batch': batch,
              'feat_list_new': feat_list_new}

# ==================================================================================
# Training and prediction

training3(img_list, pctls, model_func, feat_list_new, uncertainty,
          data_path, batch, DROPOUT_RATE, HOLDOUT, **model_params)

prediction(img_list, pctls, feat_list_new, data_path, batch, remove_perm=True, **model_params)

viz = VizFuncs(viz_params)
viz.metric_plots()
viz.time_plot()
viz.metric_plots_multi()
viz.false_map()
viz.time_size()

# Because all of the batch size tests were with the same cloud cover %, have to make a special average plot
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns


batches = ['v4', 'v5', 'v6', 'v7', 'v8', 'v9', 'v10']
batch_sizes = [256, 512, 1024, 4096, 8192, 16384, 16384]


metrics_all = pd.DataFrame(columns=['cloud_cover', 'precision', 'recall', 'f1', 'batch_size'])
for i, batch in enumerate(batches):
    if uncertainty:
        metrics_path = data_path / batch / 'metrics' / 'testing_nn_mcd'
        plot_path = data_path / batch / 'plots' / 'nn_mcd'
    else:
        metrics_path = data_path / batch / 'metrics' / 'testing'
        plot_path = data_path / batch / 'plots'

    file_list = [metrics_path / img / 'metrics.csv' for img in img_list]
    df_concat = pd.concat(pd.read_csv(file) for file in file_list)
    batch_df = pd.DataFrame(np.column_stack([np.tile(batch_sizes[i], len(df_concat)),
                                             np.tile(batches[i], len(df_concat))]), columns=['batch_size', 'batches'])
    batch_df.index = list(range(len(batch_df)))
    df_concat.index = list(range(len(df_concat)))
    df_concat = pd.concat([df_concat, batch_df], axis=1)
    metrics_all = metrics_all.append(df_concat)
mean_plot = metrics_all.groupby('batch_size').mean().plot(y=['recall', 'precision', 'f1', 'accuracy'], ylim=(0, 1))
plt.show()

# -------------------------------------
# Boxplots
fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(6, 10))
ax1, ax2, ax3, ax4 = axes.flatten()
accuracy_box = sns.boxplot(x='batches', y='accuracy', data=metrics_all, ax=ax1)
recall_box = sns.boxplot(x='batches', y='recall', data=metrics_all, ax=ax2)
precision_box = sns.boxplot(x='batches', y='precision', data=metrics_all, ax=ax3)
f1_box = sns.boxplot(x='batches', y='f1', data=metrics_all, ax=ax4)
ax1.set_ylim(0, 1)
ax2.set_ylim(0, 1)
ax3.set_ylim(0, 1)
ax4.set_ylim(0, 1)
