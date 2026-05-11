"""
Prediction on validation set.
"""
import torch
import os
import shutil
from modules import CSM, predict

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project_paths import Paths, ensure_results_dirs

ensure_results_dirs()

# Clear results folder
data_folder = Paths.RESULTS_DIR
dirs = os.listdir(data_folder)
for f in dirs:
    f_path = os.path.join(data_folder, f)
    if os.path.isdir(f_path):
        shutil.rmtree(f_path)
    else:
        os.remove(f_path)

# Validation images folder
input_folder = Paths.VALIDATION_IMAGES_DIR

# Prediction folder for results saving
predict_folder = Paths.PREDICTIONS_DIR
if os.path.isdir(predict_folder):
    shutil.rmtree(predict_folder)
os.makedirs(predict_folder)

# Load the network
net_dict_file = Paths.MODEL_TEST
net = CSM()
net.load_state_dict(torch.load(net_dict_file))

# Predict
predict(net,input_folder,predict_folder,device='cuda')









