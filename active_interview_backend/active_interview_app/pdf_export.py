"""
PDF Export Utility for Interview Reports

This module provides functionality to generate professional PDF reports
from ExportableReport data structures.
"""

from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, Image, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas


def _create_styles():
    """
    Create and return custom PDF styles.

    Returns:
        tuple: (title_style, heading_style, normal_style)
    """
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=30,
        alignment=TA_CENTER,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#1a73e8'),
        spaceAfter=12,
        spaceBefore=12,
    )
    normal_style = styles['BodyText']
    normal_style.fontSize = 11
    normal_style.leading = 14

    return title_style, heading_style, normal_style


def _create_metadata_section(exportable_report, heading_style):
    """
    Create the interview metadata section.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use

    Returns:
        list: List of flowable elements for the metadata section
    """
    elements = []
    chat = exportable_report.chat

    elements.append(Paragraph("Interview Details", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1,
                              color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    metadata_data = [
        ['Interview Type:', chat.get_type_display()],
        ['Difficulty Level:', f"{chat.difficulty}/10"],
        ['Date Completed:', chat.modified_date.strftime('%B %d, %Y')],
        ['Report Generated:', exportable_report.generated_at.strftime('%B %d, %Y at %I:%M %p')],
    ]

    if chat.job_listing:
        metadata_data.append(['Job Position:', chat.job_listing.title or 'N/A'])

    if chat.resume:
        metadata_data.append(['Resume:', chat.resume.title or 'N/A'])

    metadata_table = Table(metadata_data, colWidths=[2 * inch, 4.5 * inch])
    metadata_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#000000')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(metadata_table)
    elements.append(Spacer(1, 0.3 * inch))

    return elements


def _create_performance_scores_section(exportable_report, heading_style, normal_style):
    """
    Create the performance assessment section.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use
        normal_style: The normal text style to use

    Returns:
        list: List of flowable elements for the performance scores section
    """
    elements = []

    elements.append(Paragraph("Performance Assessment", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1,
                              color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    if exportable_report.overall_score is not None:
        scores_data = [
            ['Category', 'Score', 'Rating'],
            ['Professionalism',
             f"{exportable_report.professionalism_score or 0}/100",
             get_score_rating(exportable_report.professionalism_score)],
            ['Subject Knowledge',
             f"{exportable_report.subject_knowledge_score or 0}/100",
             get_score_rating(exportable_report.subject_knowledge_score)],
            ['Clarity',
             f"{exportable_report.clarity_score or 0}/100",
             get_score_rating(exportable_report.clarity_score)],
            ['Overall Score',
             f"{exportable_report.overall_score or 0}/100",
             get_score_rating(exportable_report.overall_score)],
        ]

        scores_table = Table(scores_data, colWidths=[2.5 * inch, 1.5 * inch, 2.5 * inch])
        scores_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a73e8')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

            # Data rows
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 11),
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),

            # Overall row highlight
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8f0fe')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),

            # Grid
            ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        elements.append(scores_table)
        elements.append(Spacer(1, 0.2 * inch))
    else:
        elements.append(Paragraph(
            "No performance scores available for this interview.",
            normal_style
        ))
        elements.append(Spacer(1, 0.2 * inch))

    return elements


def _create_feedback_section(exportable_report, heading_style, normal_style):
    """
    Create the AI feedback section.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use
        normal_style: The normal text style to use

    Returns:
        list: List of flowable elements for the feedback section
    """
    elements = []

    if exportable_report.feedback_text:
        elements.append(Paragraph("AI Feedback", heading_style))
        elements.append(HRFlowable(width="100%", thickness=1,
                                  color=colors.HexColor('#1a73e8')))
        elements.append(Spacer(1, 0.1 * inch))

        feedback_lines = exportable_report.feedback_text.split('\n')
        for line in feedback_lines:
            if line.strip():
                elements.append(Paragraph(line, normal_style))
                elements.append(Spacer(1, 0.05 * inch))
        elements.append(Spacer(1, 0.2 * inch))

    return elements


def _create_question_responses_section(exportable_report, heading_style):
    """
    Create the question responses section.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use

    Returns:
        list: List of flowable elements for the question responses section
    """
    elements = []

    if exportable_report.question_responses:
        elements.append(PageBreak())
        elements.append(Paragraph("Interview Questions and Responses", heading_style))
        elements.append(HRFlowable(width="100%", thickness=1,
                                  color=colors.HexColor('#1a73e8')))
        elements.append(Spacer(1, 0.2 * inch))

        styles = getSampleStyleSheet()
        for idx, qa in enumerate(exportable_report.question_responses, 1):
            # Question
            question_style = ParagraphStyle(
                'Question',
                parent=styles['BodyText'],
                fontSize=11,
                textColor=colors.HexColor('#1a73e8'),
                fontName='Helvetica-Bold',
                spaceAfter=6,
            )
            elements.append(Paragraph(f"Q{idx}: {qa.get('question', 'N/A')}",
                                     question_style))

            # Answer
            answer_style = ParagraphStyle(
                'Answer',
                parent=styles['BodyText'],
                fontSize=10,
                leftIndent=20,
                spaceAfter=6,
            )
            answer_text = qa.get('answer', 'No response')
            elements.append(Paragraph(f"<b>Answer:</b> {answer_text}",
                                     answer_style))

            # Score and Feedback if available
            if 'score' in qa or 'feedback' in qa:
                feedback_data = []
                if 'score' in qa:
                    feedback_data.append(['Score:', f"{qa['score']}/10"])
                if 'feedback' in qa:
                    feedback_data.append(['Feedback:', qa['feedback']])

                feedback_table = Table(feedback_data,
                                      colWidths=[1 * inch, 5 * inch])
                feedback_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
                    ('LEFTPADDING', (0, 0), (-1, -1), 20),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                elements.append(feedback_table)

            elements.append(Spacer(1, 0.15 * inch))
            elements.append(HRFlowable(width="80%", thickness=0.5,
                                      color=colors.HexColor('#cccccc'),
                                      spaceAfter=0.15 * inch))

    return elements


def _create_statistics_section(exportable_report, heading_style):
    """
    Create the statistics section.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use

    Returns:
        list: List of flowable elements for the statistics section
    """
    elements = []

    elements.append(PageBreak())
    elements.append(Paragraph("Interview Statistics", heading_style))
    elements.append(HRFlowable(width="100%", thickness=1,
                              color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    stats_data = [
        ['Total Questions Asked:', str(exportable_report.total_questions_asked)],
        ['Total Responses Given:', str(exportable_report.total_responses_given)],
    ]

    if exportable_report.interview_duration_minutes:
        stats_data.append(['Interview Duration:',
                          f"{exportable_report.interview_duration_minutes} minutes"])

    stats_table = Table(stats_data, colWidths=[2.5 * inch, 4 * inch])
    stats_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#555555')),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    elements.append(stats_table)

    return elements


def _create_footer():
    """
    Create the footer section.

    Returns:
        list: List of flowable elements for the footer
    """
    elements = []

    styles = getSampleStyleSheet()
    elements.append(Spacer(1, 0.5 * inch))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.grey,
        alignment=TA_CENTER,
    )
    footer_text = (
        f"This report was automatically generated by the Active Interview System on "
        f"{datetime.now().strftime('%B %d, %Y at %I:%M %p')}."
    )
    elements.append(Paragraph(footer_text, footer_style))

    return elements


def generate_pdf_report(exportable_report):
    """
    Generate a PDF report from an ExportableReport instance.

    Args:
        exportable_report: An ExportableReport model instance

    Returns:
        BytesIO: A file-like object containing the generated PDF
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=18,
    )

    # Container for the 'Flowable' objects
    elements = []

    # Create styles
    title_style, heading_style, normal_style = _create_styles()

    # Add title
    chat = exportable_report.chat
    title_text = f"Interview Report: {chat.title}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.2 * inch))

    # Add sections
    elements.extend(_create_metadata_section(exportable_report, heading_style))
    elements.extend(_create_performance_scores_section(exportable_report, heading_style, normal_style))
    elements.extend(_create_feedback_section(exportable_report, heading_style, normal_style))
    elements.extend(_create_question_responses_section(exportable_report, heading_style))
    elements.extend(_create_statistics_section(exportable_report, heading_style))
    elements.extend(_create_footer())

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer and return it
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def get_score_rating(score):
    """
    Convert a numeric score (0-100) to a text rating.

    Args:
        score: Integer score from 0-100

    Returns:
        str: Text rating (Excellent, Good, Fair, Needs Improvement)
    """
    if score is None:
        return "N/A"

    if score >= 90:
        return "Excellent"
    elif score >= 75:
        return "Good"
    elif score >= 60:
        return "Fair"
    else:
        return "Needs Improvement"
