# Logistic Regression with perm water kept in

from models import get_nn_bn2 as model_func
import tensorflow as tf
import os
from training import training3
from prediction import prediction
from results_viz import VizFuncs
import numpy as np
import pandas as pd
import time
import pickle
from sklearn.linear_model import LogisticRegression
import joblib
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import h5py
from CPR.utils import tif_stacker, cloud_generator, preprocessing, timer
import sys
sys.path.append('../')
from CPR.configs import data_path

# Version numbers
print('Tensorflow version:', tf.__version__)
print('Python Version:', sys.version)

# ==================================================================================
# Training on half of images WITH validation data. Compare with v24
# Batch size = 8192
# ==================================================================================
# Parameters

uncertainty = False  # Should be True if running with MCD
batch = 'v36'
pctls = [10, 30, 50, 70, 90]
NUM_PARALLEL_EXEC_UNITS = 4

try:
    (data_path / batch).mkdir()
except FileExistsError:
    pass

# To get list of all folders (images) in directory
# img_list = os.listdir(data_path / 'images')

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

viz_params = {'img_list': img_list,
              'pctls': pctls,
              'data_path': data_path,
              'uncertainty': uncertainty,
              'batch': batch,
              'feat_list_new': feat_list_new}

# Set some optimized config parameters
tf.config.threading.set_intra_op_parallelism_threads(NUM_PARALLEL_EXEC_UNITS)
tf.config.threading.set_inter_op_parallelism_threads(2)
tf.config.set_soft_device_placement(True)
# tf.config.experimental.set_visible_devices(NUM_PARALLEL_EXEC_UNITS, 'CPU')
os.environ["OMP_NUM_THREADS"] = str(NUM_PARALLEL_EXEC_UNITS)
os.environ["KMP_BLOCKTIME"] = "30"
os.environ["KMP_SETTINGS"] = "1"
os.environ["KMP_AFFINITY"] = "granularity=fine,verbose,compact,1,0"

# ======================================================================================================================


def log_reg_training(img_list, pctls, feat_list_new, data_path, batch):
    for j, img in enumerate(img_list):
        print(img + ': stacking tif, generating clouds')
        times = []
        tif_stacker(data_path, img, feat_list_new, features=True, overwrite=False)
        cloud_generator(img, data_path, overwrite=False)

        for i, pctl in enumerate(pctls):
            print(img, pctl, '% CLOUD COVER')
            print('Preprocessing')
            tf.keras.backend.clear_session()
            data_train, data_vector_train, data_ind_train, feat_keep = preprocessing(data_path, img, pctl, feat_list_new,
                                                                                     test=False)
            perm_index = feat_keep.index('GSW_perm')
            # flood_index = feat_keep.index('flooded')
            # data_vector_train[
            #     data_vector_train[:, perm_index] == 1, flood_index] = 0  # Remove flood water that is perm water
            data_vector_train = np.delete(data_vector_train, perm_index, axis=1)  # Remove perm water column
            shape = data_vector_train.shape
            X_train, y_train = data_vector_train[:, 0:shape[1] - 1], data_vector_train[:, shape[1] - 1]

            model_path = data_path / batch / 'models' / img
            metrics_path = data_path / batch / 'metrics' / 'training' / img / '{}'.format(
                img + '_clouds_' + str(pctl))

            if not model_path.exists():
                model_path.mkdir(parents=True)
            if not metrics_path.exists():
                metrics_path.mkdir(parents=True)

            model_path = model_path / '{}'.format(img + '_clouds_' + str(pctl) + '.sav')

            print('Training')
            start_time = time.time()
            logreg = LogisticRegression(n_jobs=-1, solver='sag')
            logreg.fit(X_train, y_train)
            end_time = time.time()
            times.append(timer(start_time, end_time, False))
            joblib.dump(logreg, model_path)

        metrics_path = metrics_path.parent
        times = [float(i) for i in times]
        times = np.column_stack([pctls, times])
        times_df = pd.DataFrame(times, columns=['cloud_cover', 'training_time'])
        times_df.to_csv(metrics_path / 'training_times.csv', index=False)



def prediction(img_list, pctls, feat_list_new, data_path, batch, remove_perm):
    for j, img in enumerate(img_list):
        times = []
        accuracy, precision, recall, f1 = [], [], [], []
        preds_path = data_path / batch / 'predictions' / img
        bin_file = preds_path / 'predictions.h5'
        metrics_path = data_path / batch / 'metrics' / 'testing' / img

        try:
            metrics_path.mkdir(parents=True)
        except FileExistsError:
            print('Metrics directory already exists')

        for i, pctl in enumerate(pctls):
            print('Preprocessing', img, pctl, '% cloud cover')
            data_test, data_vector_test, data_ind_test, feat_keep = preprocessing(data_path, img, pctl, feat_list_new,
                                                                                  test=True)
            perm_index = feat_keep.index('GSW_perm')
            flood_index = feat_keep.index('flooded')
            if remove_perm:
                data_vector_test[data_vector_test[:, perm_index] == 1, flood_index] = 0  # Remove flood water that is perm water
            data_vector_test = np.delete(data_vector_test, perm_index, axis=1)  # Remove GSW_perm column
            data_shape = data_vector_test.shape
            X_test, y_test = data_vector_test[:, 0:data_shape[1]-1], data_vector_test[:, data_shape[1]-1]

            print('Predicting for {} at {}% cloud cover'.format(img, pctl))
            # There is a problem loading keras models: https://github.com/keras-team/keras/issues/10417
            # Workaround is to use load_model: https://github.com/keras-team/keras-tuner/issues/75
            start_time = time.time()
            model_path = data_path / batch / 'models' / img / '{}'.format(img + '_clouds_' + str(pctl) + '.sav')
            trained_model = joblib.load(model_path)
            preds = trained_model.predict(X_test)

            try:
                preds_path.mkdir(parents=True)
            except FileExistsError:
                pass

            with h5py.File(bin_file, 'a') as f:
                if str(pctl) in f:
                    print('Deleting earlier mean predictions')
                    del f[str(pctl)]
                f.create_dataset(str(pctl), data=preds)

            times.append(timer(start_time, time.time(), False))  # Elapsed time for MC simulations

            print('Evaluating predictions')
            accuracy.append(accuracy_score(y_test, preds))
            precision.append(precision_score(y_test, preds))
            recall.append(recall_score(y_test, preds))
            f1.append(f1_score(y_test, preds))

            del preds, X_test, y_test, trained_model, data_test, data_vector_test, data_ind_test

        metrics = pd.DataFrame(np.column_stack([pctls, accuracy, precision, recall, f1]),
                               columns=['cloud_cover', 'accuracy', 'precision', 'recall', 'f1'])
        metrics.to_csv(metrics_path / 'metrics.csv', index=False)
        times = [float(i) for i in times]  # Convert time objects to float, otherwise valMetrics will be non-numeric
        times_df = pd.DataFrame(np.column_stack([pctls, times]),
                                columns=['cloud_cover', 'testing_time'])
        times_df.to_csv(metrics_path / 'testing_times.csv', index=False)


import pandas as pd
import sys
import rasterio
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from CPR.utils import preprocessing, tif_stacker
from PIL import Image, ImageEnhance
import h5py
sys.path.append('../')
from CPR.configs import data_path
import seaborn as sns
# ==================================================================================


class VizFuncs:

    def __init__(self, atts):
        self.img_list = None
        self.pctls = None
        self.data_path = None
        self.uncertainty = False
        self.batch = None
        self.feat_list_new = None
        for k, v in atts.items():
            setattr(self, k, v)

    def metric_plots(self):
        """
        Creates plot of performance metrics vs. cloud cover for a single image
        """
        plt.ioff()
        for i, img in enumerate(self.img_list):
            print('Making metric plots for {}'.format(img))
            metrics_path = data_path / self.batch / 'metrics' / 'testing' / img
            plot_path = data_path / self.batch / 'plots' / img

            try:
                plot_path.mkdir(parents=True)
            except FileExistsError:
                pass

            metrics = pd.read_csv(metrics_path / 'metrics.csv')
            if len(self.pctls) > 1:
                metrics_plot = metrics.plot(x='cloud_cover', y=['recall', 'precision', 'f1', 'accuracy'],
                                                   ylim=(0, 1))
            else:
                metrics_plot = sns.scatterplot(data=pd.melt(metrics, id_vars='cloud_cover'), x='cloud_cover', y='value',
                                     hue='variable')
                metrics_plot.set(ylim=(0, 1))

            metrics_fig = metrics_plot.get_figure()
            metrics_fig.savefig(plot_path / 'metrics_plot.png', dpi=300)



            plt.close('all')

    def time_plot(self):
        """
        Creates plot of training time vs. cloud cover
        """
        plt.ioff()
        for i, img in enumerate(self.img_list):
            print('Making time plots for {}'.format(img))
            metrics_path = data_path / self.batch / 'metrics' / 'training' / img
            plot_path = data_path / self.batch / 'plots' / img

            try:
                plot_path.mkdir(parents=True)
            except FileExistsError:
                pass

            times = pd.read_csv(metrics_path / 'training_times.csv')
            if len(self.pctls) > 1:
                time_plot = times.plot(x='cloud_cover', y=['training_time'])
            else:
                time_plot = times.plot.scatter(x='cloud_cover', y=['training_time'])

            time_plot = time_plot.get_figure()
            time_plot.savefig(plot_path / 'training_times.png', dpi=300)
            plt.close('all')

    def cir_image(self):
        """
        Creates CIR image
        """
        plt.ioff()
        data_path = self.data_path
        for i, img in enumerate(self.img_list):
            print('Creating FN/FP map for {}'.format(img))
            plot_path = data_path / self.batch / 'plots' / img
            bin_file = data_path / self.batch / 'predictions' / img / 'predictions.h5'

            stack_path = data_path / 'images' / img / 'stack' / 'stack.tif'

            # Get RGB image
            print('Stacking image')
            band_list = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
            tif_stacker(data_path, img, band_list, features=False, overwrite=False)
            spectra_stack_path = data_path / 'images' / img / 'stack' / 'spectra_stack.tif'

            # Function to normalize the grid values
            def normalize(array):
                """Normalizes numpy arrays into scale 0.0 - 1.0"""
                array_min, array_max = np.nanmin(array), np.nanmax(array)
                return ((array - array_min) / (array_max - array_min))

            print('Processing CIR image')
            with rasterio.open(spectra_stack_path, 'r') as f:
                nir, red, green = f.read(5), f.read(4), f.read(3)
                nir[nir == -999999] = np.nan
                red[red == -999999] = np.nan
                green[green == -999999] = np.nan
                nirn = normalize(nir)
                redn = normalize(red)
                greenn = normalize(green)
                cir = np.dstack((nirn, redn, greenn))

            # Convert to PIL image, enhance, and save
            cir_img = Image.fromarray((cir * 255).astype(np.uint8()))
            cir_img = ImageEnhance.Contrast(cir_img).enhance(1.5)
            cir_img = ImageEnhance.Sharpness(cir_img).enhance(2)
            cir_img = ImageEnhance.Brightness(cir_img).enhance(2)

            print('Saving CIR image')
            cir_file = plot_path / '{}'.format('cir_img' + '.png')
            cir_img.save(cir_file, dpi=(300, 300))

    def false_map(self):
        """
        Creates map of FP/FNs overlaid on RGB image
        """
        plt.ioff()
        data_path = self.data_path
        for i, img in enumerate(self.img_list):
            print('Creating FN/FP map for {}'.format(img))
            plot_path = data_path / self.batch / 'plots' / img
            bin_file = data_path / self.batch / 'predictions' / img / 'predictions.h5'

            stack_path = data_path / 'images' / img / 'stack' / 'stack.tif'

            # Get RGB image
            print('Stacking RGB image')
            band_list = ['B1', 'B2', 'B3', 'B4', 'B5', 'B6', 'B7']
            tif_stacker(data_path, img, band_list, features=False, overwrite=False)
            spectra_stack_path = data_path / 'images' / img / 'stack' / 'spectra_stack.tif'

            # Function to normalize the grid values
            def normalize(array):
                """Normalizes numpy arrays into scale 0.0 - 1.0"""
                array_min, array_max = np.nanmin(array), np.nanmax(array)
                return ((array - array_min) / (array_max - array_min))

            print('Processing RGB image')
            with rasterio.open(spectra_stack_path, 'r') as f:
                red, green, blue = f.read(4), f.read(3), f.read(2)
                red[red == -999999] = np.nan
                green[green == -999999] = np.nan
                blue[blue == -999999] = np.nan
                redn = normalize(red)
                greenn = normalize(green)
                bluen = normalize(blue)
                rgb = np.dstack((redn, greenn, bluen))

            # Convert to PIL image, enhance, and save
            rgb_img = Image.fromarray((rgb * 255).astype(np.uint8()))
            rgb_img = ImageEnhance.Contrast(rgb_img).enhance(1.5)
            rgb_img = ImageEnhance.Sharpness(rgb_img).enhance(2)
            rgb_img = ImageEnhance.Brightness(rgb_img).enhance(2)

            print('Saving RGB image')
            rgb_file = plot_path / '{}'.format('rgb_img' + '.png')
            rgb_img.save(rgb_file, dpi=(300, 300))

            # Reshape predicted values back into image band
            with rasterio.open(stack_path, 'r') as ds:
                shape = ds.read(1).shape  # Shape of full original image

            for j, pctl in enumerate(self.pctls):
                print('Fetching flood predictions for', str(pctl)+'{}'.format('%'))
                # Read predictions
                with h5py.File(bin_file, 'r') as f:
                    predictions = f[str(pctl)]
                    predictions = np.array(predictions)  # Copy h5 dataset to array

                data_test, data_vector_test, data_ind_test, feat_keep = preprocessing(data_path, img, pctl,
                                                                                      self.feat_list_new, test=True)

                # Add predicted values to cloud-covered pixel positions
                prediction_img = np.zeros(shape)
                prediction_img[:] = np.nan
                rows, cols = zip(data_ind_test)
                prediction_img[rows, cols] = predictions

                # Remove perm water from predictions and actual
                perm_index = feat_keep.index('GSW_perm')
                flood_index = feat_keep.index('flooded')
                # data_vector_test[data_vector_test[:, perm_index] == 1, flood_index] = 0  # Remove flood water that is perm water
                data_shape = data_vector_test.shape
                with rasterio.open(stack_path, 'r') as ds:
                    perm_feat = ds.read(perm_index+1)
                    prediction_img[perm_feat == 1] = 0

                # Add actual flood values to cloud-covered pixel positions
                flooded_img = np.zeros(shape)
                flooded_img[:] = np.nan
                flooded_img[rows, cols] = data_vector_test[:, data_shape[1] - 1]

                # Visualizing FNs/FPs
                ones = np.ones(shape=shape)
                red_actual = np.where(ones, flooded_img, 0.5)  # Actual
                blue_preds = np.where(ones, prediction_img, 0.5)  # Predictions
                green_combo = np.minimum(red_actual, blue_preds)

                # Saving FN/FP comparison image
                comparison_img = np.dstack((red_actual, green_combo, blue_preds))
                comparison_img_file = plot_path / '{}'.format('false_map' + str(pctl) + '.png')
                print('Saving FN/FP image for', str(pctl) + '{}'.format('%'))
                matplotlib.image.imsave(comparison_img_file, comparison_img, dpi=300)

                # Load comparison image
                flood_overlay = Image.open(comparison_img_file)

                # Convert black pixels to transparent in comparison image so it can overlay RGB
                datas = flood_overlay.getdata()
                newData = []
                for item in datas:
                    if item[0] == 0 and item[1] == 0 and item[2] == 0:
                        newData.append((255, 255, 255, 0))
                    else:
                        newData.append(item)
                flood_overlay.putdata(newData)

                # Superimpose comparison image and RGB image, then save and close
                rgb_img.paste(flood_overlay, (0, 0), flood_overlay)
                plt.imshow(rgb_img)
                print('Saving overlay image for', str(pctl) + '{}'.format('%'))
                rgb_img.save(plot_path / '{}'.format('false_map_overlay' + str(pctl) + '.png'), dpi=(300,300))
                plt.close('all')

    def metric_plots_multi(self):
        """
        Creates plot of average performance metrics of all images vs. cloud cover
        """
        plt.ioff()
        data_path = self.data_path
        metrics_path = data_path / self.batch / 'metrics' / 'testing'
        plot_path = data_path / self.batch / 'plots'

        try:
            plot_path.mkdir(parents=True)
        except FileExistsError:
            pass

        file_list = [metrics_path / img / 'metrics.csv' for img in self.img_list]
        df_concat = pd.concat(pd.read_csv(file) for file in file_list)

        # Average of metric values together in one plot
        if len(self.pctls) > 1:
            mean_plot = df_concat.groupby('cloud_cover').mean().plot(ylim=(0, 1))
        else:
            mean_plot = sns.scatterplot(data=pd.melt(df_concat.groupby('cloud_cover').mean().reset_index(),
                                                        id_vars='cloud_cover'),
                                           x='cloud_cover', y='value',
                                           hue='variable')
            mean_plot.set(ylim=(0, 1))

        metrics_fig = mean_plot.get_figure()
        metrics_fig.savefig(plot_path / 'mean_metrics.png', dpi=300)

        # Scatter of cloud_cover vs. metric for each metric, with all image metrics represented as a point
        for j, val in enumerate(df_concat.columns):
            name = val + 's.png'
            all_metric = df_concat.plot.scatter(x='cloud_cover', y=val, ylim=(0, 1))
            all_metric_fig = all_metric.get_figure()
            all_metric_fig.savefig(plot_path / name, dpi=300)

        plt.close('all')

    def time_size(self):
        """
        Creates plot of training time vs. number of pixels for each image in a scatterplot
        """
        plt.ioff()
        data_path = self.data_path
        metrics_path = data_path / self.batch / 'metrics' / 'training'
        plot_path = data_path / self.batch / 'plots'

        stack_list = [data_path / 'images' / img / 'stack' / 'stack.tif' for img in self.img_list]
        pixel_counts = []
        for j, stack in enumerate(stack_list):
            print('Getting pixel count of', self.img_list[j])
            with rasterio.open(stack, 'r') as ds:
                img = ds.read(1)
                img[img == -999999] = np.nan
                img[np.isneginf(img)] = np.nan
                cloud_mask_dir = data_path / 'clouds'
                cloud_mask = np.load(cloud_mask_dir / '{0}'.format(self.img_list[j] + '_clouds.npy'))
                for k, pctl in enumerate(self.pctls):
                    cloud_mask = cloud_mask < np.percentile(cloud_mask, pctl)
                    img_pixels = np.count_nonzero(~np.isnan(img))
                    img[cloud_mask] = np.nan
                    pixel_count = np.count_nonzero(~np.isnan(img))
                    pixel_counts.append(pixel_count)

        # pixel_counts = np.tile(pixel_counts, len(self.pctls))
        times_sizes = np.column_stack([np.tile(self.pctls, len(self.img_list)),
                                       # np.repeat(img_list, len(pctls)),
                                       pixel_counts])
        # times_sizes[:, 1] = times_sizes[:, 1].astype(np.int) / times_sizes[:, 0].astype(np.int)

        print('Fetching training times')
        file_list = [metrics_path / img / 'training_times.csv' for img in self.img_list]
        times = pd.concat(pd.read_csv(file) for file in file_list)
        times_sizes = np.column_stack([times_sizes, np.array(times['training_time'])])
        times_sizes = pd.DataFrame(times_sizes, columns=['cloud_cover', 'pixels', 'training_time'])

        print('Creating and saving plots')
        cover_times = times_sizes.plot.scatter(x='cloud_cover', y='training_time')
        cover_times_fig = cover_times.get_figure()
        cover_times_fig.savefig(plot_path / 'cloud_cover_times.png', dpi=300)

        pixel_times = times_sizes.plot.scatter(x='pixels', y='training_time')
        pixel_times_fig = pixel_times.get_figure()
        pixel_times_fig.savefig(plot_path / 'size_times.png', dpi=300)

        plt.close('all')


# ======================================================================================================================

log_reg_training(img_list, pctls, feat_list_new, data_path, batch)
prediction(img_list, pctls, feat_list_new, data_path, batch, remove_perm=True)

viz = VizFuncs(viz_params)
viz.metric_plots()
viz.cir_image()
viz.time_plot()
viz.false_map()
viz.metric_plots_multi()
# viz.time_size()



