## Medical Accuracy Metrics

The model achieves medical-grade accuracy on fetal head measurements:
- Mean difference: -0.317475(mm)
- Mean absolute difference: 2.287290(mm)
- Mean dice: 0.969913
- Mean hausdorff distance: 1.964289(mm)

## Performance Metrics

### Inference Speed (Desktop GPU)
- **Model forward pass:** ~9-20ms (microbenchmark validated)
- **GPU→CPU transfer:** 1-70ms
- **Postprocess + ellipse fitting:** 30-500ms
- **One-time warmup (cuDNN selection):** 7-12 seconds

### Production Deployment
- **First request:** 7-12 seconds (one-time warmup)
- **Subsequent requests:** 100-600ms typical per image

### Device Compatibility
- **Desktop GPU:** Optimized for CUDA-enabled GPUs
- **CPU fallback:** Supported (slower, for development/testing)