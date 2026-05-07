"""
Single image prediction for fetal head biometry.

"""
import sys
import time
import torch
import cv2
import numpy as np
from pathlib import Path
from modules import CSM, mcc_edge, ellip_fit

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from project_paths import Paths

def single_predict(image_path, device='cuda'):
    # CUDA sanity check
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"Using device: {torch.cuda.get_device_name(0)}")
    else:
        print(f"WARNING: CUDA not available, falling back to CPU")
        device = 'cpu'
    
    # Start total timer
    total_start = time.time()
    
    # Load the trained model
    load_start = time.time()
    net_dict_file = Paths.MODEL_TEST
    net = CSM()
    net.load_state_dict(torch.load(net_dict_file))
    net.to(device)
    net.eval()
    load_end = time.time()
    
    # Load and preprocess image
    preprocess_start = time.time()
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
    preprocess_end = time.time()
    
    # Predict (same as predict.py)
    forward_start = time.time()
    _, _, predict = net(input_img)
    predict = predict[0, 0, :, :]
    predict = predict.cpu().detach().numpy()
    predict = np.round(predict)
    predict = predict * 255
    predict = predict.astype('uint8')
    forward_end = time.time()
    
    # Postprocess - extract edge (same as postprocess.py)
    postprocess_start = time.time()
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
    postprocess_end = time.time()
    
    # End total timer
    total_end = time.time()
    
    # Print timing breakdown
    print(f"\n=== Timing Breakdown ===")
    print(f"Model load time: {(load_end - load_start)*1000:.2f} ms")
    print(f"Preprocess time: {(preprocess_end - preprocess_start)*1000:.2f} ms")
    print(f"Forward pass time: {(forward_end - forward_start)*1000:.2f} ms")
    print(f"Postprocess + ellipse time: {(postprocess_end - postprocess_start)*1000:.2f} ms")
    print(f"Total time: {(total_end - total_start)*1000:.2f} ms")
    
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