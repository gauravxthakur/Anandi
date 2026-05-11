"""
Calculate evaluation metrics for the model.

Computes mean difference, mean absolute difference, mean dice coefficient, 
and mean hausdorff distance. Requires prediction results and ellipse fitting results.
"""
import numpy as np
from modules import dice_folder, hausdorff_folder
import pandas as pd

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project_paths import Paths

# True and predict params of fetal head
params_label_file = Paths.VALIDATION_CSV
params_predict_file = Paths.ELLIP_PARAMS_CSV

# Calculate mean difference and mean abs difference
params_label = pd.read_csv(params_label_file)
params_predict = pd.read_csv(params_predict_file)

label_fn = params_label['filename'].values
label_ps = params_label['pixel size(mm)'].values
label_hc = params_label['head circumference (mm)'].values

predict_fn = params_predict['filename'].values
predict_hc = params_predict['HC(pixel)'].values

label_ps_series = pd.Series(label_ps,label_fn)
label_hc_series = pd.Series(label_hc,label_fn)

predict_hc_series = pd.Series(predict_hc,predict_fn)

eval_results = pd.DataFrame({'pixel size(mm)':label_ps_series, 'HC_truth(mm)':label_hc_series,
                             'HC_predict(pixel)': predict_hc_series})

eval_results['HC_predict(mm)'] = eval_results['HC_predict(pixel)'] * eval_results['pixel size(mm)']
eval_results['Difference(mm)'] = eval_results['HC_predict(mm)'] - eval_results['HC_truth(mm)']
eval_results['Abs_Difference(mm)'] = abs(eval_results['Difference(mm)'])

ave_adf = np.average(eval_results['Abs_Difference(mm)'].values)
ave_df = np.average(eval_results['Difference(mm)'].values)

print("Mean difference: %f(mm)" % (ave_df))
print("Mean absolulate difference: %f(mm)" % (ave_adf))

# label and prediction folder
label_folder = Paths.VALIDATION_LABELS_DIR
predict_folder = Paths.PREDICTIONS_DIR

# Calculate mean dice cofficience
dice = dice_folder(label_folder,predict_folder)
eval_results['Dice'] = dice
ave_dice = np.average(dice.values)
print('Mean dice: %f' % ave_dice)

# Calculate hausdorff distance
hd = hausdorff_folder(label_folder,predict_folder,label_ps_series)
eval_results['Hausdorff distance(mm)'] = hd
ave_hd = np.average(hd.values)
print('Mean hausdorff distance between predict and label is: %f(mm)' % ave_hd)

# save evaluation results
save_path = Paths.EVAL_RESULTS_CSV
eval_results.to_csv(save_path)