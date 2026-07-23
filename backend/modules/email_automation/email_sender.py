import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Fallback structured content if LLM fails
FALLBACK_TEMPLATES = {
    "Candidate Registration": {
        "subject": "Welcome to AIHire!",
        "heading": "Welcome, {candidate_name}!",
        "body": "Thank you for registering on the AIHire Recruitment Platform. We are excited to help you find your dream job. Get started by completing your profile and uploading your resume.",
        "cta_text": "Complete Profile",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\nThe AIHire Team"
    },
    "Recruiter Registration": {
        "subject": "Welcome to AIHire Recruitment Workspace",
        "heading": "Welcome to AIHire, {recruiter_name}!",
        "body": "Your recruiter workspace is ready. You can now publish job openings, run AI evaluation matching, and track candidate progress through our smart pipeline.",
        "cta_text": "Access Dashboard",
        "cta_link": "/recruiter page.html",
        "closing": "Best regards,\nThe AIHire Team"
    },
    "Resume Successfully Uploaded": {
        "subject": "Resume Upload Confirmed - AIHire",
        "heading": "Resume Uploaded successfully!",
        "body": "Your resume was received and is currently being parsed by our AI models to build your skill, experience, and education profile automatically.",
        "cta_text": "View Profile",
        "cta_link": "/candidate page.html",
        "closing": "Sincerely,\nThe AIHire AI Engine"
    },
    "Job Application Submitted": {
        "subject": "Application Received: {job_title} at {company_name}",
        "heading": "Application Received!",
        "body": "Thank you for applying for the position of {job_title} at {company_name}. We have received your application and our AI engine is compiling your suitability scorecard.",
        "cta_text": "Track Application",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Recruitment Team"
    },
    "Aptitude Assessment Invitation": {
        "subject": "Invitation: Aptitude Assessment for {job_title}",
        "heading": "Aptitude Assessment Unlock!",
        "body": "You are invited to complete the online Aptitude Assessment for the {job_title} role at {company_name}. This assessment is the first milestone in our workflow.",
        "cta_text": "Start Assessment",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "Aptitude Assessment Result": {
        "subject": "Aptitude Assessment Results Reviewed: {job_title}",
        "heading": "Aptitude Results Published",
        "body": "Thank you for completing the aptitude assessment. We have calculated your scores. Please check your status to see if you unlocked the next round.",
        "cta_text": "View Result",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "Coding Assessment Invitation": {
        "subject": "Invitation: Coding Assessment for {job_title}",
        "heading": "Coding Round Invitation",
        "body": "Congratulations on advancing! You are invited to complete the technical Coding Assessment. This round evaluates your problem-solving and coding capabilities.",
        "cta_text": "Start Coding",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "Coding Assessment Result": {
        "subject": "Coding Assessment Complete - {job_title}",
        "heading": "Coding Round Completed",
        "body": "Thank you for submitting your coding solutions. We have successfully recorded your scores. The hiring team is currently reviewing your code quality and efficiency.",
        "cta_text": "Check Scorecard",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "Interview Invitation": {
        "subject": "Invitation: AI Mock Interview for {job_title}",
        "heading": "Interview Round Invitation",
        "body": "We would like to invite you to the AI Mock Interview session for the {job_title} position at {company_name}. Please prepare your camera and microphone.",
        "cta_text": "Start Interview",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "Interview Result": {
        "subject": "AI Interview Feedback Available - {job_title}",
        "heading": "Interview Feedback Compiled",
        "body": "Thank you for completing your mock interview session. The AI HR review is complete and a detailed strengths and weaknesses scorecard is now available in your portal.",
        "cta_text": "View Feedback Report",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "Shortlisted Notification": {
        "subject": "Application Update: Shortlisted for {job_title}!",
        "heading": "Congratulations! You're Shortlisted",
        "body": "We are excited to inform you that your application for {job_title} at {company_name} has been shortlisted by the recruiting team for final review.",
        "cta_text": "View Application",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Recruiting Team"
    },
    "Rejection Notification": {
        "subject": "Update on your application for {job_title}",
        "heading": "Application Status Update",
        "body": "Thank you for your interest in the {job_title} position at {company_name}. While we were impressed with your qualifications, we have decided to move forward with other candidates. We appreciate your time and wish you success.",
        "cta_text": "Explore Jobs",
        "cta_link": "/candidate page.html",
        "closing": "Sincerely,\n{company_name} Recruitment Team"
    },
    "Offer Letter Release": {
        "subject": "Congratulations! Offer Letter Released: {job_title}",
        "heading": "Official Job Offer Enclosed!",
        "body": "We are thrilled to offer you the position of {job_title} at {company_name}! Our team is excited about the skills and expertise you bring to our team.",
        "cta_text": "Review Offer Letter",
        "cta_link": "/candidate page.html",
        "closing": "Warm welcome,\n{company_name} HR Team"
    },
    
    # Future events fallbacks
    "HR_REVIEW_REQUESTED": {
        "subject": "Candidate Ready for HR Review: {job_title}",
        "heading": "Candidate Action Required",
        "body": "Candidate {candidate_name} ({candidate_code}) has completed all automated assessment rounds for {job_title}. Their profile is ready for manual HR review.",
        "cta_text": "Access Dashboard",
        "cta_link": "/recruiter page.html",
        "closing": "Automated notification from AIHire"
    },
    "HR_APPROVED": {
        "subject": "HR Panel Approval - {job_title}",
        "heading": "Approved by HR Panel!",
        "body": "Your application for the position of {job_title} at {company_name} has been officially approved by the HR panel. The recruitment team will reach out soon to discuss onboarding.",
        "cta_text": "View Details",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "HR_REJECTED": {
        "subject": "Application Update - HR Panel Decision",
        "heading": "Application Status Update",
        "body": "Thank you for participating in the HR review panel for the {job_title} position at {company_name}. Unfortunately, we are not moving forward with your application. We wish you the best.",
        "cta_text": "View Portal",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "INTERVIEW_SCHEDULED": {
        "subject": "Interview Scheduled: {interview_title} - {job_title}",
        "heading": "Your Interview is Scheduled!",
        "body": "Your interview for the position of {job_title} at {company_name} has been scheduled.<br><br><b>Details:</b><br>- Title: {interview_title}<br>- Date: {interview_date}<br>- Time: {interview_time}<br>- Duration: {duration_minutes} minutes<br>- Mode: {interview_mode}<br>- Interviewer: {interviewer_name}<br>- Meet Link: {google_meet_link}<br><br>Notes: {additional_notes}",
        "cta_text": "Access Lobby",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "INTERVIEW_RESCHEDULED": {
        "subject": "Interview Rescheduled: {interview_title} - {job_title}",
        "heading": "Interview Schedule Updated",
        "body": "Your upcoming interview for the position of {job_title} at {company_name} has been updated to a new time slot.<br><br><b>Updated Schedule:</b><br>- Title: {interview_title}<br>- Date: {interview_date}<br>- Time: {interview_time}<br>- Duration: {duration_minutes} minutes<br>- Mode: {interview_mode}<br>- Interviewer: {interviewer_name}<br>- Meet Link: {google_meet_link}<br><br>Notes: {additional_notes}",
        "cta_text": "View New Schedule",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "INTERVIEW_CANCELLED": {
        "subject": "Interview Cancelled: {interview_title} - {job_title}",
        "heading": "Interview Cancelled",
        "body": "Your interview for the position of {job_title} at {company_name} has been cancelled.<br><br><b>Cancelled Session Details:</b><br>- Title: {interview_title}<br>- Date: {interview_date}<br>- Time: {interview_time}<br><br>Our team will contact you shortly to reschedule or clarify next steps.",
        "cta_text": "Check Status",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "INTERVIEW_CONFIRMED": {
        "subject": "Interview Confirmed: {interview_title} - {job_title}",
        "heading": "Interview Slot Locked & Confirmed",
        "body": "Great news! Your upcoming interview for the position of {job_title} at {company_name} is confirmed and locked in.<br><br><b>Schedule:</b><br>- Title: {interview_title}<br>- Date: {interview_date}<br>- Time: {interview_time}<br>- Mode: {interview_mode}<br>- Meet Link: {google_meet_link}",
        "cta_text": "Access Details",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "INTERVIEW_COMPLETED": {
        "subject": "Interview Completed - {interview_title} - {job_title}",
        "heading": "Interview Round Completed",
        "body": "Thank you for completing the final interview round: {interview_title} for {job_title} at {company_name}. Our panel is currently evaluating your performance and compiling the final scorecard. We will get back to you shortly.",
        "cta_text": "View Portal",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\n{company_name} Team"
    },
    "FINAL_SELECTION": {
        "subject": "Congratulations! You are Selected for {job_title}",
        "heading": "Hiring Selection Confirmed!",
        "body": "We are thrilled to inform you that you have been selected for the {job_title} position at {company_name}! The hiring team was highly impressed by your qualifications and assessments.",
        "cta_text": "Check Status",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "FINAL_REJECTION": {
        "subject": "Update on your application for {job_title}",
        "heading": "Application Status Update",
        "body": "Thank you for your time and effort in applying and interviewing for the {job_title} position at {company_name}. While we went with another candidate for this role, we would love to keep you in mind for future openings.",
        "cta_text": "Explore Jobs",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "OFFER_RELEASED": {
        "subject": "Official Job Offer Released: {job_title}",
        "heading": "Your Job Offer is Ready!",
        "body": "We are excited to officially release your job offer package for the {job_title} role at {company_name}! Please log in to review the terms and complete acceptance.",
        "cta_text": "Review Offer",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "OFFER_GENERATED": {
        "subject": "Offer Letter Draft Generated: {position_title}",
        "heading": "Offer Letter Draft Ready",
        "body": "A new revision version of the offer letter draft has been generated for candidate {candidate_name} for the position of {position_title} at {company_name}. Please review the draft and trigger delivery when ready.",
        "cta_text": "Review Draft",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_SENT": {
        "subject": "Official Employment Offer from {company_name}: {position_title}",
        "heading": "Congratulations! You have received a Job Offer!",
        "body": "Dear {candidate_name}, we are pleased to officially offer you the position of {position_title} at {company_name}. Please review the terms, conditions, and salary details in the attached offer letter and submit your response by {offer_expiry_date}.<br/><br/><b>Offer Highlights:</b><br/>- Position: {position_title}<br/>- Package: {package_amount}<br/>- Expected Joining Date: {joining_date}<br/>- Offer Reference: {offer_reference}",
        "cta_text": "Review & Accept Offer",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_ACCEPTED": {
        "subject": "Job Offer Accepted: {candidate_name} - {position_title}",
        "heading": "Job Offer Accepted!",
        "body": "Congratulations! Candidate {candidate_name} has accepted our offer of employment for the position of {position_title} at {company_name}.<br/><br/><b>Details:</b><br/>- Position: {position_title}<br/>- Expected Joining Date: {joining_date}<br/>- Reference: {offer_reference}",
        "cta_text": "View Portal",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_REJECTED": {
        "subject": "Offer Declined: {candidate_name} - {position_title}",
        "heading": "Offer Declined",
        "body": "Candidate {candidate_name} has declined the offer of employment for the position of {position_title} at {company_name}.",
        "cta_text": "View Profile",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_EXPIRED": {
        "subject": "Job Offer Expired: {position_title}",
        "heading": "Job Offer Expired",
        "body": "The job offer reference {offer_reference} for the position of {position_title} at {company_name} has expired or been revoked.",
        "cta_text": "View Portal",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_EXPIRY_REMINDER": {
        "subject": "Urgent Reminder: Job Offer Expiration Notice - {position_title}",
        "heading": "Your Job Offer is Expiring Soon!",
        "body": "Dear {candidate_name}, this is a friendly reminder that your employment offer for the position of {position_title} at {company_name} is set to expire on {offer_expiry_date}. Please review the attached document and submit your response before the expiration date.",
        "cta_text": "Review Offer Now",
        "cta_link": "/candidate page.html",
        "closing": "Warm regards,\n{company_name} Recruitment Team"
    },
    "OFFER_JOINED": {
        "subject": "Onboarding Complete: Candidate Joined - {candidate_name}",
        "heading": "Candidate Onboarded successfully",
        "body": "We are happy to record that {candidate_name} has officially joined the team as {position_title} on {joined_date}.",
        "cta_text": "View Portal",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Team"
    },
    "OFFER_HIRED": {
        "subject": "Hiring Complete: {candidate_name} is Hired!",
        "heading": "Hiring Status Finalized",
        "body": "The recruitment lifecycle for {candidate_name} has been completed and their status has been updated to Hired for the {position_title} position.",
        "cta_text": "View Analytics",
        "cta_link": "/recruiter page.html",
        "closing": "Warm regards,\n{company_name} Team"
    }
}

def render_branded_html(event_type: str, content: Dict[str, str], context: Dict[str, Any]) -> str:
    """
    Renders structured JSON email content into a premium, responsive branded HTML template.
    """
    subject = content.get("subject", "Notification from AIHire")
    heading = content.get("heading", "AIHire Notification")
    body = content.get("body", "").replace("\n", "<br/>")
    cta_text = content.get("cta_text", "Open Portal")
    cta_link = content.get("cta_link", "#")
    closing = content.get("closing", "Best regards,\nThe AIHire Team")

    # If the LLM hallucinated an absolute aihire.com URL, extract the path and map it locally
    if cta_link and "aihire.com" in cta_link:
        import urllib.parse
        parsed = urllib.parse.urlparse(cta_link)
        cta_link = parsed.path
        if not cta_link.startswith("/"):
            cta_link = "/" + cta_link

    # If cta_link is relative, prepend localhost for testing / local deployment
    if cta_link and cta_link.startswith("/"):
        cta_link = f"http://127.0.0.1:8000{cta_link}"

    # Extract context variables
    candidate_name = context.get("candidate_name")
    candidate_code = context.get("candidate_code")
    job_title = context.get("job_title")
    company_name = context.get("company_name", "AIHire")
    recruiter_name = context.get("recruiter_name")
    
    aptitude_score = context.get("aptitude_score")
    coding_score = context.get("coding_score")
    interview_score = context.get("interview_score")
    interview_status = context.get("interview_status")
    
    company_logo = context.get("company_logo", "https://cdn-icons-png.flaticon.com/512/3850/3850285.png") # AIHire logo
    status_badge = event_type.replace("_", " ").title()

    # Cards builder
    candidate_card_html = ""
    if candidate_name:
        candidate_card_html = f"""
        <div style="background-color: #ffffff; border: 1px solid #e2dfff; border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.05);">
            <h4 style="margin: 0 0 10px 0; color: #3525cd; font-size: 14px; font-family: 'Hanken Grotesk', Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">Candidate Information</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #464555;">
                <tr>
                    <td style="padding: 4px 0; font-weight: bold; width: 40%;">Name:</td>
                    <td style="padding: 4px 0;">{candidate_name}</td>
                </tr>
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Code:</td><td style="padding: 4px 0; font-family: monospace;">{candidate_code}</td></tr>' if candidate_code else ''}
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Aptitude Score:</td><td style="padding: 4px 0; font-weight: bold; color: #10b981;">{aptitude_score}%</td></tr>' if aptitude_score is not None else ''}
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Coding Score:</td><td style="padding: 4px 0; font-weight: bold; color: #4f46e5;">{coding_score}%</td></tr>' if coding_score is not None else ''}
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Interview Score:</td><td style="padding: 4px 0; font-weight: bold; color: #8b5cf6;">{interview_score}%</td></tr>' if interview_score is not None else ''}
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Interview Status:</td><td style="padding: 4px 0;"><span style="background-color: #fef3c7; color: #d97706; padding: 2px 8px; border-radius: 9999px; font-size: 11px; font-weight: bold;">{interview_status}</span></td></tr>' if interview_status else ''}
            </table>
        </div>
        """

    job_card_html = ""
    if job_title:
        job_card_html = f"""
        <div style="background-color: #ffffff; border: 1px solid #e2dfff; border-radius: 12px; padding: 16px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(79, 70, 229, 0.05);">
            <h4 style="margin: 0 0 10px 0; color: #f97316; font-size: 14px; font-family: 'Hanken Grotesk', Arial, sans-serif; text-transform: uppercase; letter-spacing: 0.5px;">Job Details</h4>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; color: #464555;">
                <tr>
                    <td style="padding: 4px 0; font-weight: bold; width: 40%;">Position:</td>
                    <td style="padding: 4px 0; font-weight: bold; color: #0b1c30;">{job_title}</td>
                </tr>
                <tr>
                    <td style="padding: 4px 0; font-weight: bold;">Company:</td>
                    <td style="padding: 4px 0;">{company_name}</td>
                </tr>
                {f'<tr><td style="padding: 4px 0; font-weight: bold;">Recruiter:</td><td style="padding: 4px 0;">{recruiter_name}</td></tr>' if recruiter_name else ''}
            </table>
        </div>
        """

    # Fully styled premium responsive HTML wrapper supporting Dark Mode styling hooks
    html_template = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8"/>
    <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
    <title>{subject}</title>
    <style>
        @media only screen and (max-width: 600px) {{
            .main-card {{
                width: 100% !important;
                border-radius: 0px !important;
                border-left: none !important;
                border-right: none !important;
            }}
        }}
        @media (prefers-color-scheme: dark) {{
            body {{
                background-color: #0b1c30 !important;
            }}
            .main-card {{
                background-color: #132742 !important;
                border: 1px solid #1e3a63 !important;
            }}
            .text-main {{
                color: #eaf1ff !important;
            }}
            .text-secondary {{
                color: #cbdbf5 !important;
            }}
            .inner-card {{
                background-color: #1e3a63 !important;
                border: 1px solid #2b4c7e !important;
                color: #eaf1ff !important;
            }}
        }}
    </style>
</head>
<body style="margin: 0; padding: 0; background-color: #f8f9ff; font-family: 'Inter', Arial, sans-serif; -webkit-font-smoothing: antialiased;">
    <table border="0" cellpadding="0" cellspacing="0" width="100%" style="table-layout: fixed;">
        <tr>
            <td align="center" style="padding: 40px 10px 40px 10px;">
                <!-- Card Container -->
                <table border="0" cellpadding="0" cellspacing="0" width="600" class="main-card" style="background-color: #ffffff; border: 1px solid #dce9ff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(15, 23, 42, 0.05);">
                    <!-- Branded Header -->
                    <tr>
                        <td align="center" style="background: linear-gradient(135deg, #3525cd 0%, #4d44e3 100%); padding: 30px 40px; color: #ffffff; text-align: center;">
                            <img src="{company_logo}" alt="Company Logo" style="height: 48px; width: auto; margin-bottom: 12px; border-radius: 8px;"/>
                            <div style="font-size: 24px; font-weight: bold; font-family: 'Hanken Grotesk', Arial, sans-serif; letter-spacing: -0.5px;">{company_name}</div>
                            <div style="font-size: 11px; text-transform: uppercase; font-family: monospace; letter-spacing: 2px; margin-top: 5px; opacity: 0.85;">Recruitment Portal</div>
                        </td>
                    </tr>
                    
                    <!-- Content Area -->
                    <tr>
                        <td style="padding: 40px; background-color: transparent;">
                            <!-- Status Pill Badge -->
                            <div style="margin-bottom: 20px; text-align: left;">
                                <span style="background-color: #eff4ff; color: #3525cd; border: 1px solid #c3c0ff; padding: 6px 14px; border-radius: 9999px; font-size: 11px; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;">{status_badge}</span>
                            </div>
                            
                            <!-- Email Heading -->
                            <h2 class="text-main" style="margin: 0 0 20px 0; color: #0b1c30; font-size: 22px; font-weight: 700; font-family: 'Hanken Grotesk', Arial, sans-serif; line-height: 28px;">{heading}</h2>
                            
                            <!-- Email Body Text -->
                            <p class="text-secondary" style="margin: 0 0 30px 0; color: #464555; font-size: 15px; line-height: 24px;">{body}</p>
                            
                            <!-- Candidate & Job Details Cards -->
                            {candidate_card_html}
                            {job_card_html}
                            
                            <!-- Call To Action Button -->
                            {f'''
                            <div style="text-align: center; margin: 35px 0;">
                                <a href="{cta_link}" target="_blank" style="background-color: #3525cd; color: #ffffff; padding: 14px 28px; border-radius: 12px; font-size: 14px; font-weight: bold; text-decoration: none; display: inline-block; box-shadow: 0 4px 15px rgba(53, 37, 205, 0.3);">
                                    {cta_text}
                                </a>
                            </div>
                            ''' if cta_text and cta_link and cta_link != '#' else ''}
                            
                            <!-- Professional Closing -->
                            <p class="text-secondary" style="margin: 30px 0 0 0; color: #464555; font-size: 14px; line-height: 20px;">
                                {closing}
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer Area -->
                    <tr>
                        <td align="center" style="background-color: #f8f9ff; padding: 25px 40px; border-top: 1px solid #eff4ff; text-align: center; color: #777587; font-size: 12px;">
                            <div style="font-weight: bold; color: #565e74; margin-bottom: 5px;">AIHire Inc.</div>
                            <div style="margin-bottom: 15px;">Smart, AI-powered match-making and recruitment platform.</div>
                            <div style="font-size: 10px; color: #9997a8;">This is an automated notification. Please do not reply directly to this email.</div>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html_template

def send_smtp_email(
    to_email: str, 
    subject: str, 
    html_content: str, 
    attachment_path: str = None, 
    attachment_name: str = None
) -> Tuple[bool, str]:
    """
    Delivers rendered HTML email using SMTP service configured in .env.
    Supports optional file attachments.
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_EMAIL") or os.environ.get("SMTP_USER")
    smtp_password = os.environ.get("SMTP_PASSWORD")
    smtp_sender = os.environ.get("SMTP_SENDER") or smtp_user
    
    if not smtp_host or not smtp_user or not smtp_password:
        err = "SMTP configuration missing in environment (.env). Check SMTP_HOST, SMTP_EMAIL, SMTP_PASSWORD."
        logger.error(err)
        return False, err
        
    try:
        msg = MIMEMultipart("mixed")
        msg["From"] = smtp_sender
        msg["To"] = to_email
        msg["Subject"] = subject
        
        # Create body container
        body_part = MIMEMultipart("alternative")
        html_part = MIMEText(html_content, "html", "utf-8")
        body_part.attach(html_part)
        msg.attach(body_part)
        
        # Attach file if present
        if attachment_path and os.path.exists(attachment_path):
            from email.mime.base import MIMEBase
            from email import encoders
            try:
                with open(attachment_path, "rb") as f:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={attachment_name or os.path.basename(attachment_path)}"
                )
                msg.attach(part)
                logger.info(f"Attached file {attachment_path} to email.")
            except Exception as att_err:
                logger.error(f"Failed to attach file {attachment_path}: {att_err}")
        
        # Connect and send
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_sender, to_email, msg.as_string())
        server.quit()
        
        logger.info(f"Email successfully delivered to {to_email}")
        return True, ""
    except Exception as e:
        err_msg = str(e)
        logger.error(f"Failed to deliver SMTP email to {to_email}: {err_msg}")
        return False, err_msg
