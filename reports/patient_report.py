from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate

def generate_patient_report():
    """Generate a patient-friendly baby growth report"""
    styles = getSampleStyleSheet()
    styleN = styles['Normal']
    styleH = styles['Heading1']
    story = []

    #add some flowables
    story.append(Paragraph("Baby Growth Report",styleH))
    
    story.append(Paragraph("About This Scan",styleH))
    story.append(Paragraph("Patient ID: 12345 <br/> Date of Scan: 11 April 2026<br/>Gestational Age: 27-28 weeks (AI-estimated from baby's size)<br/>Scan Quality: Good<br/>",styleN))
    
    story.append(Paragraph("Baby's Ultrasound Image",styleH))
    story.append(Paragraph("(Your baby's ultrasound picture with highlighted outlines of head, tummy, and leg bone)<br/>",styleN))
    
    story.append(Paragraph("Baby's Growth Measurements",styleH))
    story.append(Paragraph("Head Size: Normal for age<br/>Tummy Size: Normal for age<br/>Leg Bone Length: Normal for age<br/>Overall Growth: Tracking steadily along the 40-50th percentile (average range compared to other babies of the same age)",styleN))
    
    story.append(Paragraph("Growth Curve",styleH))
    story.append(Paragraph("Your baby's growth is following a steady curve, right around the middle of the expected range.<br/><br/>This means your baby is growing normally and proportionally.",styleN))
    
    story.append(Paragraph("Confidence & Safety",styleH))
    story.append(Paragraph("Confidence Level: High (AI is very sure about these measurements)<br/>Image Quality: Clear and complete<br/>Safety Note: If the scan quality had been poor, the system would have flagged it and recommended a re-scan.",styleN))
    
    story.append(Paragraph("Transparency",styleH))
    story.append(Paragraph("Measurements are based on baby's head, tummy, and leg bone outlines detected in the ultrasound image.<br/><br/>AI helps calculate size and growth, but doctors always confirm results.",styleN))
    
    story.append(Paragraph("Important Reminder",styleH))
    story.append(Paragraph("This report is for information only.<br/><br/>Please discuss these results with your doctor, who will provide full medical guidance.",styleN))
    
    doc = SimpleDocTemplate('patient_report.pdf',pagesize = letter)
    doc.build(story)
    print("Patient report generated: patient_report.pdf")

if __name__ == "__main__":
    generate_patient_report()
