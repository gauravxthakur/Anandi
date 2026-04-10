"""
This script is used for ellipse fitting from edge images.
Requirement: postprocess.py has been executed so edge images exist.
"""
import pandas as pd
import os
import cv2
from modules import ellip_fit
import numpy as np

# Postprocess results folder
edge_folder = '../results/predictions_edge/'

# To save ellipse parameters
results = []
name = ['filename', 'center_x(pixel)', 'center_y(pixel)', 'semi_axes_a(pixel)',
        'semi_axes_b(pixel)', 'HC(pixel)', 'angle(rad)']

# Filename of ellipse parameters file
save_ellip_para_file = '../results/ellip_params.csv'

# upsample factor
u = 16

# Ellipse fitting to obtain parameters
dirs = os.listdir(edge_folder)
for i in range(len(dirs)):
    print('Ellip fitting (Optimized): Image = %d / %d' % (i + 1, len(dirs)))
    img_name = dirs[i]
    img_path = edge_folder + img_name

    edge_img = cv2.imread(img_path, 0)
    xc, yc, theta, a, b = ellip_fit(edge_img)

    # 1. Restore Center Coordinates
    xc = (xc + 0.5) * u - 0.5
    yc = (yc + 0.5) * u - 0.5
    
    # 2. CALIBRATION: Subtract a tiny offset to move from 
    # the outer edge of the prediction to the center of the skull bone.
    offset = 0.05
    a = (a - offset) * u
    b = (b - offset) * u
    
    # 3. RAMANUJAN'S FORMULA: Much more accurate than 2*pi*b + 4(a-b)
    h = ((a - b) ** 2) / ((a + b) ** 2)
    hc = np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(4 - 3 * h)))

    results.append([img_name, xc, yc, a, b, hc, theta])

# Save
predict_results = pd.DataFrame(columns=name, data=results)
predict_results.to_csv(save_ellip_para_file, index=False)

