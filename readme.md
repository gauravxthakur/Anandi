## Medical Accuracy Metrics

The model achieves medical-grade accuracy on fetal head measurements:
- Mean difference: -0.317475(mm)
- Mean absolute difference: 2.287290(mm)
- Mean dice: 0.969913
- Mean hausdorff distance: 1.964289(mm)

# PC-PNDT Form F Workflow
<img width="1566" height="704" alt="gatha_example1" src="https://github.com/user-attachments/assets/8fe60fe3-8aeb-49a5-b67c-e7e4c08eaa7d" />

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
- **Desktop GPU:** Full pipeline after warmup
- **CPU fallback:** Supported (slower, for development/testing)

---

# PC-PNDT Form F Workflow
<img width="1566" height="704" alt="gatha_example1" src="https://github.com/user-attachments/assets/8fe60fe3-8aeb-49a5-b67c-e7e4c08eaa7d" />
