from models import get_nn_bn2 as model_func
import tensorflow as tf
import os
from training import training4, SGDRScheduler, LrRangeFinder
from prediction import prediction
from evaluation import evaluation
from test_functions import cloud_generator_small
from results_viz import VizFuncs
import sys
import shutil

sys.path.append('../../')
from CPR.configs import data_path


# Version numbers
print('Tensorflow version:', tf.__version__)
print('Python Version:', sys.version)

# ==================================================================================
# Testing on all images using 2 layer nn with batch norm, training on smaller clouds.
# Batch size = 8192
# ==================================================================================
# Parameters

uncertainty = False
batch = 'v14'
pctls = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]
BATCH_SIZE = 8192
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
            '4101_LC08_027038_20131103_2',
            '4101_LC08_027039_20131103_1',
            '4115_LC08_021033_20131227_1',
            '4115_LC08_021033_20131227_2',
            '4337_LC08_026038_20160325_1',
            '4444_LC08_043034_20170303_1',
            '4444_LC08_043035_20170303_1',
            '4444_LC08_044032_20170222_1',
            '4444_LC08_044033_20170222_1',
            '4444_LC08_044033_20170222_3',
            '4444_LC08_044033_20170222_4',
            '4444_LC08_044034_20170222_1',
            '4444_LC08_045032_20170301_1',
            '4468_LC08_022035_20170503_1',
            '4468_LC08_024036_20170501_1',
            '4468_LC08_024036_20170501_2',
            '4469_LC08_015035_20170502_1',
            '4469_LC08_015036_20170502_1',
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

cloud_dir = data_path / 'clouds'

training4(img_list, pctls, model_func, feat_list_new, uncertainty,
          data_path, batch, DROPOUT_RATE, HOLDOUT, **model_params)

prediction(img_list, pctls, feat_list_new, data_path, batch, remove_perm=True, **model_params)

evaluation(img_list, pctls, feat_list_new, data_path, batch, remove_perm=True)

viz = VizFuncs(viz_params)
viz.metric_plots()
viz.time_plot()
viz.metric_plots_multi()
viz.false_map()
viz.time_size2()

# Move cloud files to another folder so they're not overwritten
for img in img_list:
    file_name = img + '_clouds.npy'
    cloud_src = cloud_dir / file_name
    cloud_dest_dir = cloud_dir / 'small'
    cloud_dest = cloud_dest_dir / file_name
    try:
        cloud_dest_dir.mkdir(parents=True)
    except FileExistsError:
        pass
    if not cloud_dest.exists():
        shutil.move(cloud_src, cloud_dest)
    else:
        print('Overwriting previous small clouds!')
        sys.exit()
