import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from datetime import datetime

def generate_offer_letter_pdf(offer_data: dict, output_path: str):
    """
    Generates a professional styled PDF offer letter using ReportLab.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Initialize document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Design colors
    primary_color = colors.HexColor('#3525cd')
    secondary_color = colors.HexColor('#f97316')
    text_dark = colors.HexColor('#0b1c30')
    border_color = colors.HexColor('#dce9ff')
    bg_light = colors.HexColor('#f8f9ff')
    bg_header = colors.HexColor('#eff4ff')
    
    # Text styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=14,
        textColor=secondary_color,
        spaceAfter=15
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=15,
        textColor=text_dark,
        spaceAfter=10
    )
    
    table_label_style = ParagraphStyle(
        'TableLabel',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#464555')
    )
    
    table_value_style = ParagraphStyle(
        'TableValue',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=text_dark
    )
    
    terms_title_style = ParagraphStyle(
        'TermsTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=13,
        textColor=primary_color,
        spaceAfter=6
    )
    
    # 1. Company Branded Header Banner
    company_name = offer_data.get('company_name', 'AIHire').upper()
    header_data = [
        [Paragraph(f"<font color='white'><b>{company_name}</b></font>", ParagraphStyle('HCol', fontName='Helvetica-Bold', fontSize=18, leading=22, alignment=1))]
    ]
    header_table = Table(header_data, colWidths=[7*inch])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), primary_color),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMPADDING', (0,0), (-1,-1), 12),
        ('BOTTOMMARGIN', (0,0), (-1,-1), 20)
    ]))
    story.append(header_table)
    story.append(Spacer(1, 15))
    
    # 2. Document Title and Revision Version
    version_no = offer_data.get('offer_version', 1)
    story.append(Paragraph("OFFER OF EMPLOYMENT", title_style))
    story.append(Paragraph(f"Official Job Offer Package &bull; Revision Version {version_no}", subtitle_style))
    
    # 3. Date and Reference
    ref_no = offer_data.get('offer_reference', 'AIH-OFFER-0001')
    current_date = datetime.now().strftime('%B %d, %Y')
    date_ref_data = [
        [Paragraph(f"<b>Date:</b> {current_date}", table_value_style), 
         Paragraph(f"<b>Reference:</b> {ref_no}", table_value_style)]
    ]
    date_ref_table = Table(date_ref_data, colWidths=[3.5*inch, 3.5*inch])
    date_ref_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
        ('TOPPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(date_ref_table)
    story.append(Spacer(1, 15))
    
    # 4. Salutation and Introduction
    cand_name = offer_data.get('candidate_name', 'Candidate')
    cand_code = offer_data.get('candidate_code', '')
    story.append(Paragraph(f"Dear <b>{cand_name}</b> (Candidate Code: {cand_code}),", body_style))
    story.append(Paragraph(
        "Following your successful completion of the selection assessments and interview panel rounds, "
        "we are extremely pleased to offer you employment with us. We were highly impressed by your skills, "
        "experience, and potential, and look forward to welcoming you aboard.",
        body_style
    ))
    story.append(Spacer(1, 10))
    
    # 5. Position and Details Table
    details_data = [
        [Paragraph("Position Title", table_label_style), Paragraph(offer_data.get('position_title', 'N/A'), table_value_style)],
        [Paragraph("Department", table_label_style), Paragraph(offer_data.get('department', 'N/A'), table_value_style)],
        [Paragraph("Employment Type", table_label_style), Paragraph(offer_data.get('employment_type', 'Full-time'), table_value_style)],
        [Paragraph("Compensation Package", table_label_style), Paragraph(offer_data.get('package_amount', 'N/A'), table_value_style)],
        [Paragraph("Expected Joining Date", table_label_style), Paragraph(str(offer_data.get('joining_date', 'N/A')), table_value_style)],
        [Paragraph("Work Location", table_label_style), Paragraph(offer_data.get('location', 'N/A'), table_value_style)],
        [Paragraph("Reporting Manager", table_label_style), Paragraph(offer_data.get('reporting_manager', 'N/A'), table_value_style)]
    ]
    
    details_table = Table(details_data, colWidths=[2.5*inch, 4.5*inch])
    details_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), bg_header),
        ('BACKGROUND', (1,0), (1,-1), bg_light),
        ('GRID', (0,0), (-1,-1), 0.5, border_color),
        ('PADDING', (0,0), (-1,-1), 8),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    story.append(details_table)
    story.append(Spacer(1, 15))
    
    # 6. Terms & Conditions
    expiry_date_str = str(offer_data.get('offer_expiry_date', 'the date specified on your dashboard'))
    story.append(Paragraph("Key Terms & Conditions of Employment", terms_title_style))
    terms_text = (
        f"1. <b>Validity & Expiry:</b> This offer letter is valid until <b>{expiry_date_str}</b>. Please complete your acceptance signature within this period.<br/>"
        "2. <b>Background Verification:</b> This offer is subject to verification of your academic credentials, references, and professional experience history.<br/>"
        "3. <b>Probationary Period:</b> You will undergo a three-month probation review period upon joining to assess mutual alignment."
    )
    story.append(Paragraph(terms_text, body_style))
    story.append(Spacer(1, 20))
    
    # 7. Signature blocks
    sig_data = [
        [Paragraph("Sincerely,", body_style), Paragraph("I accept the terms of this offer.", body_style)],
        [Spacer(1, 25), Spacer(1, 25)],
        [Paragraph("____________________________<br/><b>Authorized HR Representative</b><br/>AIHire Recruitment Team", body_style),
         Paragraph("____________________________<br/><b>Candidate Acceptance Signature</b><br/>" + cand_name, body_style)]
    ]
    sig_table = Table(sig_data, colWidths=[3.5*inch, 3.5*inch])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(sig_table)
    
    # Build Document
    doc.build(story)
