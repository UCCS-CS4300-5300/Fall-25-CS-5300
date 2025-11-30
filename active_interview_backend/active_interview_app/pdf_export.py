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
    PageBreak, HRFlowable
)
from reportlab.lib.enums import TA_CENTER


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
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    metadata_data = [
        ['Interview Type:', chat.get_type_display()],
        ['Difficulty Level:', f"{chat.difficulty}/10"],
        ['Date Completed:', chat.modified_date.strftime('%B %d, %Y')],
        ['Report Generated:',
         exportable_report.generated_at.strftime('%B %d, %Y at %I:%M %p')],
    ]

    if chat.job_listing:
        metadata_data.append(
            ['Job Position:', chat.job_listing.title or 'N/A'])

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


def _create_performance_scores_section(
        exportable_report, heading_style, normal_style):
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
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    if exportable_report.overall_score is not None:
        scores_data = [
            ['Category', 'Score', 'Weight', 'Rating'],
            ['Professionalism',
             f"{exportable_report.professionalism_score or 0}/100",
             f"{exportable_report.professionalism_weight}%",
             get_score_rating(exportable_report.professionalism_score)],
            ['Subject Knowledge',
             f"{exportable_report.subject_knowledge_score or 0}/100",
             f"{exportable_report.subject_knowledge_weight}%",
             get_score_rating(exportable_report.subject_knowledge_score)],
            ['Clarity',
             f"{exportable_report.clarity_score or 0}/100",
             f"{exportable_report.clarity_weight}%",
             get_score_rating(exportable_report.clarity_score)],
            ['Overall Score',
             f"{exportable_report.overall_score or 0}/100",
             'N/A',
             get_score_rating(exportable_report.overall_score)],
        ]

        scores_table = Table(
            scores_data,
            colWidths=[2 * inch, 1.3 * inch, 1 * inch, 2.2 * inch])
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
            ('ROWBACKGROUNDS', (0, 1), (-1, -2),
             [colors.white, colors.HexColor('#f5f5f5')]),
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


def _create_score_rationales_section(
        exportable_report, heading_style, normal_style):
    """
    Create the score rationales section explaining each score component.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use
        normal_style: The normal text style to use

    Returns:
        list: List of flowable elements for the rationales section
    """
    elements = []

    if exportable_report.overall_score is not None:
        elements.append(
            Paragraph("Score Breakdown & Rationales", heading_style))
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#1a73e8')))
        elements.append(Spacer(1, 0.1 * inch))

        # Create styles for rationales
        category_style = ParagraphStyle(
            'CategoryText',
            parent=normal_style,
            fontSize=12,
            leading=14,
            fontName='Helvetica-Bold',
            textColor=colors.HexColor('#1a73e8'),
            spaceAfter=6,
        )

        rationale_style = ParagraphStyle(
            'RationaleText',
            parent=normal_style,
            fontSize=10,
            leading=13,
            leftIndent=12,
            wordWrap='CJK',
            spaceAfter=12,
        )

        # Professionalism
        if exportable_report.professionalism_rationale:
            elements.append(Paragraph(
                f"Professionalism: "
                f"{exportable_report.professionalism_score}/100 "
                f"(Weight: {exportable_report.professionalism_weight}%)",
                category_style
            ))
            elements.append(Paragraph(
                exportable_report.professionalism_rationale,
                rationale_style
            ))

        # Subject Knowledge
        if exportable_report.subject_knowledge_rationale:
            elements.append(Paragraph(
                f"Subject Knowledge: "
                f"{exportable_report.subject_knowledge_score}/100 "
                f"(Weight: {exportable_report.subject_knowledge_weight}%)",
                category_style
            ))
            elements.append(Paragraph(
                exportable_report.subject_knowledge_rationale,
                rationale_style
            ))

        # Clarity
        if exportable_report.clarity_rationale:
            elements.append(Paragraph(
                f"Clarity: {exportable_report.clarity_score}/100 " +
                f"(Weight: {exportable_report.clarity_weight}%)",
                category_style
            ))
            elements.append(Paragraph(
                exportable_report.clarity_rationale,
                rationale_style
            ))

        # Overall
        if exportable_report.overall_rationale:
            elements.append(Paragraph(
                f"Overall Score: {exportable_report.overall_score}/100",
                category_style
            ))
            elements.append(Paragraph(
                exportable_report.overall_rationale,
                rationale_style
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
        elements.append(HRFlowable(
            width="100%", thickness=1,
            color=colors.HexColor('#1a73e8')))
        elements.append(Spacer(1, 0.1 * inch))

        # Create a feedback style with proper word wrapping
        feedback_style = ParagraphStyle(
            'FeedbackText',
            parent=normal_style,
            fontSize=11,
            leading=14,
            wordWrap='CJK',
            rightIndent=0,
            leftIndent=0,
        )

        feedback_lines = exportable_report.feedback_text.split('\n')
        for line in feedback_lines:
            if line.strip():
                elements.append(Paragraph(line, feedback_style))
                elements.append(Spacer(1, 0.05 * inch))
        elements.append(Spacer(1, 0.2 * inch))

    return elements


def _create_interviewer_feedback_section(
        exportable_report, heading_style, normal_style):
    """
    Create the interviewer feedback section for invited interviews.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use
        normal_style: The normal text style to use

    Returns:
        list: List of flowable elements for the interviewer feedback section
    """
    elements = []
    chat = exportable_report.chat

    # Only show for invited interviews
    if chat.interview_type != 'INVITED':
        return elements

    try:
        from .models import InvitedInterview
        invitation = InvitedInterview.objects.get(chat=chat)
    except InvitedInterview.DoesNotExist:
        return elements

    # Create section header
    elements.append(Paragraph("Interviewer Feedback", heading_style))
    # Green color for interviewer section
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#28a745')))
    elements.append(Spacer(1, 0.1 * inch))

    # Check review status
    if invitation.interviewer_review_status == 'pending':
        # Show pending message
        pending_style = ParagraphStyle(
            'PendingText',
            parent=normal_style,
            fontSize=11,
            leading=14,
            textColor=colors.HexColor('#856404'),
            fontName='Helvetica-Oblique',
        )
        elements.append(Paragraph(
            "Your interviewer is currently reviewing your interview. " +
            "You will be notified when feedback is available.",
            pending_style
        ))
    else:
        # Show interviewer feedback
        if invitation.interviewer_feedback:
            feedback_style = ParagraphStyle(
                'InterviewerFeedbackText',
                parent=normal_style,
                fontSize=11,
                leading=14,
                wordWrap='CJK',
                rightIndent=0,
                leftIndent=0,
            )

            feedback_lines = invitation.interviewer_feedback.split('\n')
            for line in feedback_lines:
                if line.strip():
                    elements.append(Paragraph(line, feedback_style))
                    elements.append(Spacer(1, 0.05 * inch))

            # Add reviewer info and date
            if invitation.reviewed_at:
                meta_style = ParagraphStyle(
                    'MetaText',
                    parent=normal_style,
                    fontSize=9,
                    leading=12,
                    textColor=colors.HexColor('#666666'),
                    fontName='Helvetica-Oblique',
                )
                reviewer_name = (
                    invitation.interviewer.get_full_name() or
                    invitation.interviewer.username)
                review_date = invitation.reviewed_at.strftime(
                    '%B %d, %Y at %I:%M %p')
                elements.append(Spacer(1, 0.1 * inch))
                elements.append(Paragraph(
                    f"— Reviewed by {reviewer_name} on {review_date}",
                    meta_style
                ))
        else:
            # Reviewed but no feedback provided
            no_feedback_style = ParagraphStyle(
                'NoFeedbackText',
                parent=normal_style,
                fontSize=11,
                leading=14,
                textColor=colors.HexColor('#666666'),
                fontName='Helvetica-Oblique',
            )
            elements.append(Paragraph(
                "No additional feedback provided by interviewer.",
                no_feedback_style
            ))

    elements.append(Spacer(1, 0.2 * inch))
    return elements


def _create_recommended_exercises_section(
        exportable_report, heading_style, normal_style):
    """
    Create the recommended exercises section based on performance scores.

    Args:
        exportable_report: An ExportableReport model instance
        heading_style: The heading style to use
        normal_style: The normal text style to use

    Returns:
        list: List of flowable elements for the recommended exercises section
    """
    elements = []

    elements.append(PageBreak())
    elements.append(Paragraph("Recommended Exercises", heading_style))
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.2 * inch))

    # Introduction
    intro_style = ParagraphStyle(
        'IntroText',
        parent=normal_style,
        fontSize=11,
        leading=14,
        textColor=colors.HexColor('#1a73e8'),
        fontName='Helvetica-Bold',
        spaceAfter=12,
    )

    # Determine weakest areas based on scores
    scores = {
        'Professionalism': exportable_report.professionalism_score or 0,
        'Subject Knowledge': exportable_report.subject_knowledge_score or 0,
        'Clarity': exportable_report.clarity_score or 0,
    }

    # Sort by score to prioritize areas needing improvement
    sorted_areas = sorted(scores.items(), key=lambda x: x[1])

    # Build customized recommendations
    all_recommendations = {
        'Professionalism': [
            ("<b>Professional Communication:</b>",
             "Practice maintaining professional tone and demeanor "
             "throughout the interview. Focus on appropriate body "
             "language and active listening."),
            ("<b>Business Etiquette:</b>",
             "Review professional email writing, meeting etiquette, "
             "and workplace communication best practices."),
        ],
        'Subject Knowledge': [
            ("<b>Technical Skills:</b>",
             "Deepen your knowledge in your field through coding "
             "challenges, technical documentation, and hands-on "
             "projects."),
            ("<b>Industry Research:</b>",
             "Stay current with industry trends, tools, and best "
             "practices through articles, courses, and professional "
             "communities."),
        ],
        'Clarity': [
            ("<b>Practice STAR Method:</b>",
             "Structure your answers using Situation, Task, Action, "
             "and Result to provide clear, concise responses."),
            ("<b>Communication Skills:</b>",
             "Work on articulating your thoughts clearly. Practice "
             "explaining complex topics in simple terms."),
        ],
    }

    # Add general recommendations
    general_recommendations = [
        ("<b>Mock Interviews:</b>",
         "Continue practicing with our AI interviewer or with peers "
         "to build confidence and fluency."),
        ("<b>Company Research:</b>",
         "Learn about the companies you're interviewing with to "
         "tailor your responses and ask informed questions."),
    ]

    # Select recommendations based on scores
    recommendations = []

    # Prioritize lowest scoring areas
    for area, score in sorted_areas[:2]:  # Focus on 2 weakest areas
        if area in all_recommendations:
            recommendations.extend(all_recommendations[area])

    # Add general recommendations
    recommendations.extend(general_recommendations)

    # Customize introduction based on overall score
    overall_score = exportable_report.overall_score or 0
    if overall_score >= 90:
        intro_text = (
            "Excellent performance! To maintain and further "
            "enhance your skills:")
    elif overall_score >= 75:
        intro_text = (
            "Good performance! Here are some targeted exercises "
            "to help you excel:")
    elif overall_score >= 60:
        intro_text = (
            "To improve your interview performance, we recommend "
            "focusing on:")
    else:
        intro_text = (
            "To build stronger interview skills, we recommend "
            "starting with:")

    elements.append(Paragraph(intro_text, intro_style))

    bullet_style = ParagraphStyle(
        'BulletText',
        parent=normal_style,
        fontSize=11,
        leading=16,
        leftIndent=20,
        bulletIndent=10,
        spaceAfter=8,
    )

    for title, description in recommendations:
        text = f"• {title} {description}"
        elements.append(Paragraph(text, bullet_style))

    elements.append(Spacer(1, 0.2 * inch))

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
    elements.append(HRFlowable(
        width="100%", thickness=1,
        color=colors.HexColor('#1a73e8')))
    elements.append(Spacer(1, 0.1 * inch))

    stats_data = [
        ['Total Questions Asked:',
         str(exportable_report.total_questions_asked)],
        ['Total Responses Given:',
         str(exportable_report.total_responses_given)],
    ]

    if exportable_report.interview_duration_minutes:
        stats_data.append([
            'Interview Duration:',
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
        f"This report was automatically generated by the "
        f"Active Interview System on "
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
    elements.extend(
        _create_metadata_section(exportable_report, heading_style))
    elements.extend(
        _create_performance_scores_section(
            exportable_report, heading_style, normal_style))
    elements.extend(
        _create_score_rationales_section(
            exportable_report, heading_style, normal_style))
    elements.extend(
        _create_feedback_section(
            exportable_report, heading_style, normal_style))
    elements.extend(
        _create_interviewer_feedback_section(
            exportable_report, heading_style, normal_style))
    elements.extend(
        _create_recommended_exercises_section(
            exportable_report, heading_style, normal_style))
    elements.extend(
        _create_statistics_section(exportable_report, heading_style))
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
