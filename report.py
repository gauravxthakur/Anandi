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
    story.append(Paragraph("Auto Fetal Biometry Report",styleH))
    story.append(Paragraph("John Doe, 23, Male <br/><br/>",styleN))
    story.append(Paragraph("Mean difference: -0.317475(mm)<br/>Mean absolute difference: 2.287290(mm)<br/>Mean dice: 0.969913<br/>Mean hausdorff distance between predict and label is: 1.964289(mm)",styleN))
    doc = SimpleDocTemplate('mydoc.pdf',pagesize = letter)
    doc.build(story)
    print("Report generated: mydoc.pdf")

if __name__ == "__main__":
    generate_report()
