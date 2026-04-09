import os
import datetime
import numpy as np
import random
from PIL import Image
from pydicom.dataset import Dataset, FileDataset
from pydicom.uid import ExplicitVRLittleEndian, generate_uid

def create_dicom_from_png(png_path, out_path, patient_name="ANONYMOUS", hc_value=None):
    """
    Converts PNG to DICOM by attaching OB-GYN metadata.
    hc_value: The Head Circumference measurement from your CV model (in mm).
    """
    
    # Generate randomized patient identifiers for test data
    if patient_name == "ANONYMOUS":
        names = ["John Doe", "Jane Smith", "Clark Kent", "Bruce Wayne", "Diana Prince", "Peter Parker", "Lois Lane", "Barry Allen"]
        patient_name = random.choice(names)
    
    # Generate random patient ID
    patient_id = f"{random.randint(100000, 999999)}"

    # 1. Load the PNG image
    plan_image = Image.open(png_path).convert('L') # Convert to grayscale
    pixel_data = np.array(plan_image)

    # 2. Create File Meta Information
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.6.1' # Ultrasound Image Storage
    file_meta.MediaStorageSOPInstanceUID = generate_uid()
    file_meta.ImplementationClassUID = generate_uid()
    file_meta.TransferSyntaxUID = ExplicitVRLittleEndian

    # 3. Create the DICOM Dataset
    ds = FileDataset(out_path, {}, file_meta=file_meta, preamble=b"\0" * 128)

    # --- Basic Patient/Study Metadata ---
    ds.PatientName = patient_name
    ds.PatientID = patient_id
    ds.ContentDate = datetime.datetime.now().strftime('%Y%m%d')
    ds.ContentTime = datetime.datetime.now().strftime('%H%M%S.%f')
    ds.Modality = "US" # Ultrasound
    ds.SeriesInstanceUID = generate_uid()
    ds.SOPInstanceUID = file_meta.MediaStorageSOPInstanceUID
    ds.SOPClassUID = file_meta.MediaStorageSOPClassUID

    # --- Image Pixel Data ---
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = pixel_data.shape[0]
    ds.Columns = pixel_data.shape[1]
    ds.BitsAllocated = 8
    ds.BitsStored = 8
    ds.HighBit = 7
    ds.PixelRepresentation = 0 # unsigned integer
    ds.PixelData = pixel_data.tobytes()

    # --- OB-GYN Ultrasound Metadata ---
    if hc_value:
        # Model validation metrics
        mean_difference = -0.317475  # mm
        mean_abs_diff = 2.287290     # mm
        mean_dice = 0.969913
        mean_hausdorff = 1.964289    # mm
        
        # HC measurement stored in ImageComments (DICOM SR preferred)
        ds.ImageComments = f"Fetal Head Circumference: {hc_value:.2f}±{mean_abs_diff:.2f}mm (Dice: {mean_dice:.4f})"
        
        # Algorithm identification
        ds.PerformedProcedureStepDescription = "Automated fetal HC measurement"
        ds.SoftwareVersions = "Auto-Fetal-Biometry v1.0"
        
        # Study classification
        ds.StudyDescription = "OB-GYN Ultrasound - AI Analysis"
        ds.BodyPartExamined = "ABDOMEN"
        
        # Private tags for detailed metrics
        ds.add_new((0x7777, 0x0001), 'LO', 'Auto-Fetal-Biometry')
        ds.add_new((0x7777, 0x0010), 'DS', str(mean_difference))  # Mean difference
        ds.add_new((0x7777, 0x0011), 'DS', str(mean_abs_diff))    # Mean absolute difference
        ds.add_new((0x7777, 0x0012), 'DS', str(mean_dice))        # Dice coefficient
        ds.add_new((0x7777, 0x0013), 'DS', str(mean_hausdorff))   # Hausdorff distance

    # Save the file
    ds.save_as(out_path)
    print(f"DICOM file saved to: {out_path}")

# Example usage:
if __name__ == "__main__":
    # Test image path
    test_png = "results/visualizations/test_sample_01.png"
    output_dcm = "results/dicom_outputs/test_sample_01.dcm"
    
    if not os.path.exists("results/dicom_outputs/"):
        os.makedirs("results/dicom_outputs/")

    # Test HC measurement value
    create_dicom_from_png(test_png, output_dcm, hc_value=150.5)