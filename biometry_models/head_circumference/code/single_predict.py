"""
Single image prediction for fetal head biometry.

"""
import sys
import torch
import cv2
import numpy as np
from pathlib import Path
from modules import CSM, mcc_edge, ellip_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from project_paths import Paths

def single_predict(image_path, device='cuda'):
    # Load the trained model
    net_dict_file = Paths.MODEL_TEST
    net = CSM()
    net.load_state_dict(torch.load(net_dict_file))
    net.to(device)
    net.eval()
    
    # Load and preprocess image
    img = cv2.imread(image_path, 0)
    if img is None:
        print(f"Error: Cannot load image from {image_path}")
        return
    
    # Resize factor (same as predict.py)
    k1 = 4
    w = int(768 / k1)
    h = int(512 / k1)
    
    # Preprocess (same as predict.py)
    input_img = cv2.resize(img, (w, h), interpolation=cv2.INTER_AREA)
    input_img = input_img.astype('float32')
    input_img = input_img / 255.0
    
    # To torch.tensor (same as predict.py)
    input_img = torch.from_numpy(input_img)
    input_img = input_img.unsqueeze(0)
    input_img = input_img.unsqueeze(0)
    input_img = input_img.to(device)
    
    # Predict (same as predict.py)
    _, _, predict = net(input_img)
    predict = predict[0, 0, :, :]
    predict = predict.cpu().detach().numpy()
    predict = np.round(predict)
    predict = predict * 255
    predict = predict.astype('uint8')
    
    # Postprocess - extract edge (same as postprocess.py)
    edge_img = mcc_edge(predict)
    
    # Ellipse fitting (same as ellip_fit.py)
    xc, yc, theta, a, b = ellip_fit(edge_img)
    
    # Calculate head circumference (same as ellip_fit.py)
    u = 16  # upsample factor
    
    # 1. Restore Center Coordinates
    xc = (xc + 0.5) * u - 0.5
    yc = (yc + 0.5) * u - 0.5
    
    # 2. CALIBRATION: Subtract offset
    offset = 0.05
    a = (a - offset) * u
    b = (b - offset) * u
    
    # 3. RAMANUJAN'S FORMULA for head circumference
    h = ((a - b) ** 2) / ((a + b) ** 2)
    hc = np.pi * (a + b) * (1 + (3 * h) / (10 + np.sqrt(4 - 3 * h)))
    
    # Display results
    print(f"\n=== Fetal Head Circumference Measurement ===")
    print(f"Image: {image_path}")
    print(f"Head Circumference: {hc:.2f} pixels")
    print(f"Center: ({xc:.2f}, {yc:.2f}) pixels")
    print(f"Semi-axes: a={a:.2f}, b={b:.2f} pixels")
    print(f"Angle: {theta:.4f} radians")
    
    # Return measurement data
    return {
        'hc_pixels': hc,
        'center': (xc, yc),
        'axes': (a, b),
        'angle': theta,
        'image_path': image_path
    }

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python single_predict.py path/to/image.png")
        sys.exit(1)
    
    image_path = sys.argv[1]
    single_predict(image_path)