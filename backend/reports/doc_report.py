from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import Paragraph, SimpleDocTemplate, Table, TableStyle, Spacer
from reportlab.lib.enums import TA_LEFT, TA_CENTER

def create_card_style():
    """Create custom styles for the report"""
    styles = getSampleStyleSheet()
    
    # Card title style
    card_title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#1e40af'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    # Field label style
    field_label_style = ParagraphStyle(
        'FieldLabel',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6b7280'),
        fontName='Helvetica-Oblique',
        spaceAfter=2
    )
    
    # Field value style
    field_value_style = ParagraphStyle(
        'FieldValue',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        fontName='Helvetica',
        spaceAfter=8
    )
    
    return styles, card_title_style, field_label_style, field_value_style

def create_card(title, fields, card_title_style, field_label_style, field_value_style):
    """Create a card with title and fields"""
    story = []
    
    # Card title
    story.append(Paragraph(title, card_title_style))
    
    # Card border and content
    card_data = []
    for label, value in fields:
        card_data.append([Paragraph(label, field_label_style), Paragraph(value, field_value_style)])
    
    # Create table for card content
    card_table = Table(card_data, colWidths=[2.5*inch, 4*inch])
    card_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f3f4f6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e5e7eb')),
    ]))
    
    story.append(card_table)
    story.append(Spacer(1, 0.2*inch))
    
    return story

def generate_report(
    # Card 1: Patient Identity
    full_name="",
    age="",
    husband_father_name="",
    contact_number="",
    postal_address="",
    
    # Card 2: Obstetric History
    total_living_children="",
    living_sons="",
    living_daughters="",
    lmp_or_weeks="",
    
    # Card 3: Referral Details
    referral_source="Self-Referral",
    referring_doctor="",
    
    # Card 4: Fetal Head Circumference Measurement
    image_name="",
    head_circumference="",
    center="",
    semi_axes="",
    angle="",
    
    # Card 5: Anandi Insights
    indication_ultrasound="",
    result_procedure="",
    indication_mtp="No",
    
    # Card 6: Digital Sign-off
    date_procedure="",
    patient_consent=False,
    doctor_confirmation=False,
    
    output_filename="doc_report.pdf"
):
    """Generate a PDF report with card-based layout"""
    styles, card_title_style, field_label_style, field_value_style = create_card_style()
    story = []
    
    # Add title
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a8a'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    story.append(Paragraph("ULTRASOUND REPORT", title_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Card 1: Patient Identity
    card1_fields = [
        ("Full Name:", full_name),
        ("Age:", age),
        ("Husband's / Father's Name:", husband_father_name),
        ("Contact Number:", contact_number),
        ("Full Postal Address:", postal_address)
    ]
    story.extend(create_card("Patient Identity", card1_fields, card_title_style, field_label_style, field_value_style))
    
    # Card 2: Obstetric History
    card2_fields = [
        ("Total Number of Living Children:", total_living_children),
        ("Number of Living Sons (with ages):", living_sons),
        ("Number of Living Daughters (with ages):", living_daughters),
        ("LMP / Current Weeks of Pregnancy:", lmp_or_weeks)
    ]
    story.extend(create_card("Obstetric History", card2_fields, card_title_style, field_label_style, field_value_style))
    
    # Card 3: Referral Details
    card3_fields = [
        ("Referral Source:", referral_source),
    ]
    if referral_source == "External Reference":
        card3_fields.append(("Referring Doctor Name/Address:", referring_doctor))
    story.extend(create_card("Referral Details", card3_fields, card_title_style, field_label_style, field_value_style))
    
    # Card 4: Fetal Head Circumference Measurement
    card4_fields = [
        ("Head Circumference:", head_circumference),
        ("Center:", center),
        ("Semi-axes:", semi_axes),
        ("Angle:", angle)
    ]
    story.extend(create_card("Fetal Head Circumference Measurement", card4_fields, card_title_style, field_label_style, field_value_style))
    
    # Card 5: Anandi Insights
    card5_fields = [
        ("Indication for Ultrasound:", indication_ultrasound),
        ("Result of Procedure:", result_procedure),
        ("Indication for MTP:", indication_mtp)
    ]
    story.extend(create_card("Anandi Insights", card5_fields, card_title_style, field_label_style, field_value_style))
    
    # Card 6: Digital Sign-off
    consent_text = "✓" if patient_consent else "✗"
    confirmation_text = "✓" if doctor_confirmation else "✗"
    
    card6_fields = [
        ("Date of Procedure:", date_procedure),
        ("Patient Consent (I do not want to know the sex of my fetus):", consent_text),
        ("Doctor Confirmation (I have not disclosed the sex):", confirmation_text)
    ]
    story.extend(create_card("Digital Sign-off", card6_fields, card_title_style, field_label_style, field_value_style))
    
    # Build the PDF
    doc = SimpleDocTemplate(output_filename, pagesize=letter, 
                          leftMargin=0.75*inch, rightMargin=0.75*inch,
                          topMargin=0.75*inch, bottomMargin=0.75*inch)
    doc.build(story)
    print(f"Report generated: {output_filename}")

if __name__ == "__main__":
    # Sample data for testing
    generate_report(
        full_name="Sample Patient Name",
        age="28",
        husband_father_name="John Doe",
        contact_number="+91 9876543210",
        postal_address="123, Street Name, City, State - 123456",
        
        total_living_children="2",
        living_sons="1 (5 years)",
        living_daughters="1 (3 years)",
        lmp_or_weeks="28 weeks",
        
        referral_source="Self-Referral",
        referring_doctor="",
        
        image_name="single_test_img.png",
        head_circumference="1336.84 mm",
        center="(255.02, 300.88) mm",
        semi_axes="a=235.60, b=188.63 mm",
        angle="1.6862 radians",
        
        indication_ultrasound="Estimation of gestational age",
        result_procedure="Normal fetal growth parameters observed. All measurements within expected range.",
        indication_mtp="No",
        
        date_procedure="09 May 2026",
        patient_consent=True,
        doctor_confirmation=True,
        
        output_filename="doc_report.pdf"
    )
