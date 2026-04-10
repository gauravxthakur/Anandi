from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate

def generate_report():
    """Generate a sample PDF report"""
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH = styles['Heading1']
    story = []

    #add some flowables
    story.append(Paragraph("Patient & Scan Information",styleH))
    story.append(Paragraph("Patient ID: 12345 <br/> Date of Scan: 11 April 2026 <br/> Gestational Age (GA): 27.6–28.4 weeks (confidence range) <br/> Scan Quality: Acceptable <br/>",styleN))
    
    story.append(Paragraph("Ultrasound Image",styleH))
    story.append(Paragraph("Original ultrasound image with overlays (segmentation masks, fitted ellipses). <br/> Annotated boundaries for head, abdomen, and femur. <br/>",styleN))
    
    story.append(Paragraph("Measurements",styleH))
    story.append(Paragraph("Mean difference: -0.317475(mm)<br/>Mean absolute difference: 2.287290(mm)<br/>Mean dice: 0.969913<br/>Mean hausdorff distance between predict and label is: 1.964289(mm)",styleN))
    
    story.append(Paragraph("Growth & Trends",styleH))
    story.append(Paragraph("Growth Curve: Tracking along the 40-50th percentile.<br/>Trajectory: Stable, no deviation from expected growth.<br/>Risk Indicator: Low.",styleN))
    
    story.append(Paragraph("Confidence & Quality",styleH))
    story.append(Paragraph("Confidence Classification: High.<br/>Image Quality Warnings: None detected.<br/>Completeness Check: All anatomical boundaries captured.",styleN))
    
    story.append(Paragraph("Explainability & Transparency",styleH))
    story.append(Paragraph("AI Measurement Basis: Skull boundary detection for HC, abdominal contour for AC, femur shaft for FL.<br/>Model Version: AutoFB v2.1.<br/>Audit Metadata: Stored internally for medico-legal compliance.",styleN))
    
    story.append(Paragraph("Disclaimers",styleH))
    story.append(Paragraph("Medical Disclaimer:<br/>These results are generated using AI-assisted analysis. They may be inaccurate. Please consult a qualified doctor for clinical interpretation.<br/><br/>Regulatory Note:<br/>Adjusted using population-aware statistical models.",styleN))
    
    doc = SimpleDocTemplate('doc_report.pdf',pagesize = letter)
    doc.build(story)
    print("Report generated: doc_report.pdf")

if __name__ == "__main__":
    generate_report()
