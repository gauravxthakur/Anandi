"""
Visualize results by drawing ellipses on original images.

Requires ellip_fit.py to be executed first so ellipse parameters exist.
"""
import pandas as pd
import os
from modules import draw_ellip
import cv2
import shutil

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from project_paths import Paths, ensure_results_dirs

ensure_results_dirs()

# Valitation images folder
img_folder = Paths.VALIDATION_IMAGES_DIR

# Folder to save visualization results
visual_folder = Paths.VISUALIZATIONS_DIR
if os.path.isdir(visual_folder):
    shutil.rmtree(visual_folder)
os.makedirs(visual_folder)

# Prediction ellipse parameters file
predict_ellip_params_file = Paths.ELLIP_PARAMS_CSV

params_data = pd.read_csv(predict_ellip_params_file)
v = params_data.values

for i in range(len(params_data)):
    print("Image processing: %d / %d" % (i+1, len(params_data)))
    img_name = v[i, 0]
    xc = v[i, 1]
    yc = v[i, 2]
    a = v[i, 3]
    b = v[i, 4]
    theta = v[i, 6]

    img_path = os.path.join(img_folder, img_name)
    img = cv2.imread(img_path,0)

    # Draw ellipse on the original image using predicted ellipse parameters
    visual_img = draw_ellip(xc, yc, a, b, theta, img, 'r')

    # Save
    visual_path = os.path.join(visual_folder, img_name)
    cv2.imwrite(visual_path, visual_img)

