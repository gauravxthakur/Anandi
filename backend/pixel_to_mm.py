"""
Convert pixel measurements to millimeters for fetal biometry.
"""
import numpy as np

def convert_pixels_to_mm(pixels, pixel_spacing_mm=0.1):
    """
    Convert pixel measurements to millimeters.
    
    Args:
        pixels: Measurement in pixels
        pixel_spacing_mm: Pixel spacing in mm/pixel (default: 0.1mm/pixel)
    
    Returns:
        float: Measurement in millimeters
    """
    return pixels * pixel_spacing_mm

def convert_hc_to_mm(hc_pixels, pixel_spacing_mm=0.1):
    """
    Convert head circumference from pixels to millimeters.
    
    Args:
        hc_pixels: Head circumference in pixels
        pixel_spacing_mm: Pixel spacing in mm/pixel
    
    Returns:
        float: Head circumference in millimeters
    """
    return hc_pixels * pixel_spacing_mm

def get_default_pixel_spacing():
    """
    Get default pixel spacing for fetal ultrasound images.
    
    Returns:
        float: Default pixel spacing in mm/pixel
    """
    return 0.1  # 0.1mm per pixel for typical fetal ultrasound

def validate_pixel_spacing(pixel_spacing_mm):
    """
    Validate pixel spacing value is reasonable for fetal ultrasound.
    
    Args:
        pixel_spacing_mm: Pixel spacing in mm/pixel
    
    Returns:
        bool: True if valid, False otherwise
    """
    return 0.01 <= pixel_spacing_mm <= 1.0

def get_pixel_spacing_from_dicom(dicom_path):
    """
    Extract pixel spacing from existing DICOM file.
    
    Args:
        dicom_path: Path to DICOM file
    
    Returns:
        float: Pixel spacing in mm/pixel, or default if not found
    """
    try:
        import pydicom
        ds = pydicom.dcmread(dicom_path)
        
        # Try to get pixel spacing from DICOM metadata
        if hasattr(ds, 'PixelSpacing'):
            return float(ds.PixelSpacing[0])
        elif hasattr(ds, 'ImagerPixelSpacing'):
            return float(ds.ImagerPixelSpacing[0])
        else:
            return get_default_pixel_spacing()
    except:
        return get_default_pixel_spacing()

if __name__ == "__main__":
    # Test conversion
    test_pixels = 1500
    pixel_spacing = 0.1
    hc_mm = convert_hc_to_mm(test_pixels, pixel_spacing)
    print(f"HC: {test_pixels} pixels = {hc_mm:.2f} mm (spacing: {pixel_spacing} mm/pixel)")
