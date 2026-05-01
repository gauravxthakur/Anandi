"""
Extract edge images from prediction results.

Run predict.py first so prediction results exist.
"""
import os
import cv2
from modules import mcc_edge
import shutil

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project_paths import Paths, ensure_results_dirs

ensure_results_dirs()

# Folder of model predictions
input_folder = Paths.PREDICTIONS_DIR

#  Folder to save postprocess results
edge_folder = Paths.PREDICTIONS_EDGE_DIR
if os.path.isdir(edge_folder):
    shutil.rmtree(edge_folder)
os.makedirs(edge_folder)

# Extract fetal contour
dirs = os.listdir(input_folder)
for i in range(len(dirs)):
    print('Extracting max connect component edge: Image = %d / %d' % (i + 1, len(dirs)))
    img_name = dirs[i]
    img_path = os.path.join(input_folder, img_name)

    img = cv2.imread(img_path, 0)
    edge_img = mcc_edge(img)

    save_path = os.path.join(edge_folder, img_name)
    cv2.imwrite(save_path, edge_img)

