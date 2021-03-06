# For each RCT, computes mean, variance, and entropy of test and train data separately

import __init__
import numpy as np
import rasterio
from zipfile import ZipFile
import sys
import os
import scipy.special as sc
from scipy.stats import entropy

sys.path.append('../../')
from CPR.configs import data_path

# Version numbers
print('Python Version:', sys.version)

# ======================================================================================================================
# Performance metrics vs. image metadata (dry/flood pixels, image size)
pctls = [10, 30, 50, 70, 90]

# To get list of all folders (images) in directory
img_list = os.listdir(data_path / 'images')
removed = {'4115_LC08_021033_20131227_test'}
img_list = [x for x in img_list if x not in removed]

feat_list_new = ['GSW_maxExtent', 'GSW_distExtent', 'aspect', 'curve', 'developed', 'elevation', 'forest',
                 'hand', 'other_landcover', 'planted', 'slope', 'spi', 'twi', 'wetlands', 'GSW_perm', 'flooded']

batch = 'RCTs'
trials = ['trial1', 'trial2', 'trial3', 'trial4', 'trial5', 'trial6', 'trial7', 'trial8', 'trial9', 'trial10']
exp_path = data_path / batch / 'results'
try:
    (data_path / batch).mkdir(parents=True)
except FileExistsError:
    pass
try:
    exp_path.mkdir(parents=True)
except FileExistsError:
    pass

dtypes = ['float32', 'float32', 'float32', 'float32', 'int', 'float32', 'int', 'float32', 'int', 'int', 'float32',
          'float32', 'float32', 'int', 'int', 'int']

# ======================================================================================================================


def preprocessing_random_clouds(data_path, img, pctl, trial, test):
    """
    Preprocessing but gets cloud image from random cloud file directories
    """
    img_path = data_path / 'images' / img
    stack_path = img_path / 'stack' / 'stack.tif'
    clouds_dir = data_path / 'clouds' / 'random' / trial

    # Check for any features that have all zeros/same value and remove. For both train and test sets.
    # Get local image
    with rasterio.open(str(stack_path), 'r') as ds:
        data = ds.read()
        data = data.transpose((1, -1, 0))  # Not sure why the rasterio.read output is originally (D, W, H)
        data[data == -999999] = np.nan
        data[np.isneginf(data)] = np.nan

    # Convert -999999 and -Inf to Nans
    data[data == -999999] = np.nan
    data[np.isneginf(data)] = np.nan
    # Now remove NaNs (real clouds, ice, missing data, etc). from cloudmask
    clouds = np.load(clouds_dir / '{0}'.format(img + '_clouds.npy'))
    clouds[np.isnan(data[:, :, 0])] = np.nan
    if test:
        cloudmask = np.greater(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))
    if not test:
        cloudmask = np.less(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))

    # And mask clouds
    data[cloudmask] = -999999
    data[data == -999999] = np.nan

    # Get indices of non-nan values. These are the indices of the original image array
    nans = np.sum(data, axis=2)
    data_ind = np.where(~np.isnan(nans))

    # Reshape into a 2D array, where rows = pixels and cols = features
    data_vector = data.reshape([data.shape[0] * data.shape[1], data.shape[2]])
    shape = data_vector.shape

    # Remove NaNs
    data_vector = data_vector[~np.isnan(data_vector).any(axis=1)]

    # Make sure NaNs are in the same position element-wise in image
    mask = np.sum(data, axis=2)
    data[np.isnan(mask)] = np.nan

    return data, data_vector, data_ind

# ======================================================================================================================
# Getting image-wide mean, variance, entropy of each variable in each trial

# Extract cloud files
clouds_dir = data_path / 'clouds'
for trial in trials:
    trial_clouds_dir = clouds_dir / 'random' / trial
    if not os.path.isdir(trial_clouds_dir):
        trial_clouds_dir.mkdir(parents=True)
        trial_clouds_zip = clouds_dir / 'random' / '{}'.format(trial + '.zip')
        with ZipFile(trial_clouds_zip, 'r') as src:
            src.extractall(trial_clouds_dir)

def binary_variance(x):
    p = np.sum(x) / x.shape[0]
    bin_var = p*(1-p)
    return bin_var

def binary_entropy(x):
    return -np.sum(sc.xlogy(x, x) + sc.xlog1py(1 - x, -x))/np.log(2)

for img in img_list:
    print('Getting train means for', img)
    means_train = []
    variances_train = []
    entropies_train = []
    for trial in trials:
        print(trial)
        for pctl in pctls:
            print(pctl)
            data_train, data_vector_train, data_ind_train = preprocessing_random_clouds(data_path, img, pctl, trial, test=False)
            perm_index = feat_list_new.index('GSW_perm')
            p = sc.softmax(data_vector_train, axis=1)
            for i, feat in enumerate(feat_list_new):
                index = feat_list_new.index(feat)
                x = data_vector_train[:, index]
                px = p[:, index]
                means_train.append(np.mean(x))
                if dtypes[i] is 'int':
                    variances_train.append(binary_variance(x))
                    entropies_train.append(binary_entropy(px))
                if dtypes[i] is 'float32':
                    variances_train.append(np.var(x))
                    entropies_train.append(entropy(px[px != 0]))
    with open(exp_path / 'means_train.csv', 'ab') as f:
        np.savetxt(f, np.array(means_train), delimiter=',')
    with open(exp_path / 'variances_train.csv', 'ab') as f:
        np.savetxt(f, np.array(variances_train), delimiter=',')
    with open(exp_path / 'entropies_train.csv', 'ab') as f:
        np.savetxt(f, np.array(entropies_train), delimiter=',')

for img in img_list:
    print('Getting test means for', img)
    means_test = []
    variances_test = []
    entropies_test = []
    for trial in trials:
        print(trial)
        for pctl in pctls:
            print(pctl)
            data_test, data_vector_test, data_ind_test = preprocessing_random_clouds(data_path, img, pctl, trial, test=True)
            perm_index = feat_list_new.index('GSW_perm')
            p = sc.softmax(data_vector_test, axis=1)
            for i, feat in enumerate(feat_list_new):
                index = feat_list_new.index(feat)
                x = data_vector_test[:, index]
                px = p[:, index]
                means_test.append(np.mean(x))
                if dtypes[i] is 'int':
                    variances_test.append(binary_variance(x))
                    entropies_test.append(binary_entropy(px))
                if dtypes[i] is 'float32':
                    variances_test.append(np.var(x))
                    entropies_test.append(entropy(px[px != 0]))
    with open(exp_path / 'means_test.csv', 'ab') as f:
        np.savetxt(f, np.array(means_test), delimiter=',')
    with open(exp_path / 'variances_test.csv', 'ab') as f:
        np.savetxt(f, np.array(variances_test), delimiter=',')
    with open(exp_path / 'entropies_test.csv', 'ab') as f:
        np.savetxt(f, np.array(entropies_test), delimiter=',')


# ======================================================================================================================


def preprocessing_random_clouds_standard(data_path, img, pctl, trial, test):
    """
    Preprocessing but gets cloud image from random cloud file directories
    Does standardize features; any feature with original std=0 becomes the average standardized value
    """
    img_path = data_path / 'images' / img
    stack_path = img_path / 'stack' / 'stack.tif'
    clouds_dir = data_path / 'clouds' / 'random' / trial

    # Check for any features that have all zeros/same value and remove. For both train and test sets.
    # Get local image
    with rasterio.open(str(stack_path), 'r') as ds:
        data = ds.read()
        data = data.transpose((1, -1, 0))  # Not sure why the rasterio.read output is originally (D, W, H)
        data[data == -999999] = np.nan
        data[np.isneginf(data)] = np.nan

        # Getting std of train dataset
        # Remove NaNs (real clouds, ice, missing data, etc). from cloudmask
        clouds = np.load(clouds_dir / '{0}'.format(img + '_clouds.npy'))
        clouds[np.isnan(data[:, :, 0])] = np.nan
        cloudmask = np.less(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))
        data[cloudmask] = -999999
        data[data == -999999] = np.nan
        data_vector = data.reshape([data.shape[0] * data.shape[1], data.shape[2]])
        data_vector = data_vector[~np.isnan(data_vector).any(axis=1)]
        train_std = data_vector[:, 0:data_vector.shape[1] - 2].std(0)

        # Getting std of test dataset
        # Remove NaNs (real clouds, ice, missing data, etc). from cloudmask
        data = ds.read()
        data = data.transpose((1, -1, 0))  # Not sure why the rasterio.read output is originally (D, W, H)
        data[data == -999999] = np.nan
        data[np.isneginf(data)] = np.nan
        clouds = np.load(clouds_dir / '{0}'.format(img + '_clouds.npy'))
        clouds[np.isnan(data[:, :, 0])] = np.nan
        cloudmask = np.greater(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))
        data[cloudmask] = -999999
        data[data == -999999] = np.nan
        data_vector = data.reshape([data.shape[0] * data.shape[1], data.shape[2]])
        data_vector = data_vector[~np.isnan(data_vector).any(axis=1)]
        test_std = data_vector[:, 0:data_vector.shape[1] - 2].std(0)

    # Now adjust feat_list_new to account for a possible removed feature because of std=0
    feat_keep = feat_list_new.copy()
    with rasterio.open(str(stack_path), 'r') as ds:
        data = ds.read()
        data = data.transpose((1, -1, 0))  # Not sure why the rasterio.read output is originally (D, W, H)

    if 0 in train_std.tolist():
        print('Removing', feat_keep[train_std.tolist().index(0)], 'because std=0 in training data')
        zero_feat_ind = train_std.tolist().index(0)
        data = np.delete(data, zero_feat_ind, axis=2)
        removed_feat = data[:, :, zero_feat_ind]
        feat_keep.pop(zero_feat_ind)

    # Now checking stds of test data if not already removed because of train data
    if 0 in test_std.tolist():
        zero_feat_ind = test_std.tolist().index(0)
        zero_feat = feat_list_new[zero_feat_ind]
        try:
            zero_feat_ind = feat_keep.index(zero_feat)
            feat_keep.pop(feat_list_new.index(zero_feat))
            removed_feat = data[:, :, zero_feat_ind]
            data = np.delete(data, zero_feat_ind, axis=2)
        except ValueError:
            pass

    # Convert -999999 and -Inf to Nans
    data[data == -999999] = np.nan
    data[np.isneginf(data)] = np.nan
    # Now remove NaNs (real clouds, ice, missing data, etc). from cloudmask
    clouds = np.load(clouds_dir / '{0}'.format(img + '_clouds.npy'))
    clouds[np.isnan(data[:, :, 0])] = np.nan
    if test:
        cloudmask = np.greater(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))
    if not test:
        cloudmask = np.less(clouds, np.nanpercentile(clouds, pctl), where=~np.isnan(clouds))

    # And mask clouds
    data[cloudmask] = -999999
    data[data == -999999] = np.nan

    # Get indices of non-nan values. These are the indices of the original image array
    nans = np.sum(data, axis=2)
    data_ind = np.where(~np.isnan(nans))

    # Reshape into a 2D array, where rows = pixels and cols = features
    data_vector = data.reshape([data.shape[0] * data.shape[1], data.shape[2]])
    shape = data_vector.shape

    # Remove NaNs
    data_vector = data_vector[~np.isnan(data_vector).any(axis=1)]

    data_mean = data_vector[:, 0:shape[1] - 2].mean(0)
    data_std = data_vector[:, 0:shape[1] - 2].std(0)

    # Normalize data - only the non-binary variables
    data_vector[:, 0:shape[1] - 2] = (data_vector[:, 0:shape[1] - 2] - data_mean) / data_std

    # Add back removed feature with 0 (mean of standardized values)
    if 0 in test_std.tolist() or 0 in train_std.tolist():
        removed_feat = removed_feat * 0
        data = np.insert(data, zero_feat_ind, removed_feat, axis=2)
        removed_feat_vector = removed_feat.reshape([removed_feat.shape[0] * removed_feat.shape[1], ])
        removed_feat_vector = removed_feat_vector[~np.isnan(removed_feat_vector)]
        data_vector = np.insert(data_vector, zero_feat_ind, removed_feat_vector, axis=1)

    # Make sure NaNs are in the same position element-wise in image
    mask = np.sum(data, axis=2)
    data[np.isnan(mask)] = np.nan

    return data, data_vector, data_ind


# ======================================================================================================================
# With standardized data
exp_path = data_path / batch / 'results' / 'standardized'
try:
    (data_path / batch).mkdir(parents=True)
except FileExistsError:
    pass
try:
    exp_path.mkdir(parents=True)
except FileExistsError:
    pass

# Extract cloud files
clouds_dir = data_path / 'clouds'
for trial in trials:
    trial_clouds_dir = clouds_dir / 'random' / trial
    if os.path.isdir(trial_clouds_dir):
        try:
            trial_clouds_dir.mkdir(parents=True)
        except FileExistsError:
            pass
    trial_clouds_zip = clouds_dir / 'random' / '{}'.format(trial + '.zip')
    with ZipFile(trial_clouds_zip, 'r') as src:
        src.extractall(trial_clouds_dir)
#
for img in img_list:
    print('Getting train means for', img)
    means_train = []
    variances_train = []
    entropies_train = []
    for trial in trials:
        print(trial)
        for pctl in pctls:
            print(pctl)
            data_train, data_vector_train, data_ind_train = preprocessing_random_clouds_standard(data_path, img, pctl, trial, test=False)
            perm_index = feat_list_new.index('GSW_perm')
            p = sc.softmax(data_vector_train, axis=1)
            for feat in feat_list_new:
                index = feat_list_new.index(feat)
                means_train.append(np.mean(data_vector_train[:, index]))
                variances_train.append(np.var(data_vector_train[:, index]))
                p_feat = p[:, index]
                entropies_train.append(entropy(p_feat[p_feat != 0]))
    with open(exp_path / 'means_train.csv', 'ab') as f:
        np.savetxt(f, np.array(means_train), delimiter=',')
    with open(exp_path / 'variances_train.csv', 'ab') as f:
        np.savetxt(f, np.array(variances_train), delimiter=',')
    with open(exp_path / 'entropies_train.csv', 'ab') as f:
        np.savetxt(f, np.array(entropies_train), delimiter=',')


for img in img_list:
    print('Getting test means for', img)
    means_test = []
    variances_test = []
    entropies_test = []
    for trial in trials:
        print(trial)
        for pctl in pctls:
            print(pctl)
            data_test, data_vector_test, data_ind_test = preprocessing_random_clouds_standard(data_path, img, pctl, trial, test=True)
            perm_index = feat_list_new.index('GSW_perm')
            p = sc.softmax(data_vector_test, axis=1)
            for feat in feat_list_new:
                index = feat_list_new.index(feat)
                means_test.append(np.mean(data_vector_test[:, index]))
                variances_test.append(np.var(data_vector_test[:, index]))
                p_feat = p[:, index]
                entropies_test.append(entropy(p_feat[p_feat != 0]))
    with open(exp_path / 'means_test.csv', 'ab') as f:
        np.savetxt(f, np.array(means_test), delimiter=',')
    with open(exp_path / 'variances_test.csv', 'ab') as f:
        np.savetxt(f, np.array(variances_test), delimiter=',')
    with open(exp_path / 'entropies_test.csv', 'ab') as f:
        np.savetxt(f, np.array(entropies_test), delimiter=',')
