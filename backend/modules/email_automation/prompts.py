import json
from typing import Dict, Any

SYSTEM_PROMPT = """
You are an expert AI HR assistant at AIHire, an advanced AI-powered recruitment platform.
Your task is to write a highly professional, attractive, personalized, and human-written email for a specific recruitment lifecycle event.

You must respond with a valid JSON object ONLY. Do not include any markdown styling like ```json or any conversational prefix or suffix.
The JSON object must match this schema exactly:
{
  "subject": "Email Subject Line",
  "heading": "An attention-grabbing, personalized heading inside the email card",
  "body": "The detailed email message body. Keep it warm, human, and highly personalized based on candidate and job details. Use paragraph tags or newlines for structure.",
  "cta_text": "A brief, compelling call-to-action button label",
  "cta_link": "A relative URL path starting with '/' pointing to the destination page (e.g., '/candidate page.html' for candidate pages, '/recruiter page.html' for recruiter pages). Do NOT use absolute URLs or external domains.",
  "closing": "A warm, professional closing sign-off"
}
"""

EVENT_GUIDELINES = {
    # 1. Candidate Registration
    "Candidate Registration": "Welcome the candidate to the AIHire Platform. Mention their profile creation and that they are now ready to upload their resume and explore job openings.",
    
    # 2. Recruiter Registration
    "Recruiter Registration": "Welcome the recruiter to AIHire. Explain that their recruitment workspace is set up and they can start posting jobs, reviewing candidate rankings, and utilizing AI-driven match-making.",
    
    # Job Posted
    "Job Posted": "Acknowledge that the recruiter has successfully posted a new job on AIHire. Provide brief details and confirm that the AI is ready to start sourcing and screening candidates.",
    
    # 3. Resume Successfully Uploaded
    "Resume Successfully Uploaded": "Confirm receipt of their resume. Let them know our AI is currently parsing it and compiling their skills, education, and experience matrix for job match-making.",
    
    # 4. Job Application Submitted
    "Job Application Submitted": "Acknowledge the candidate's application for the specified Job Title. Thank them and mention that the AI match scoring engine will assess their profile shortly.",
    
    # 5. Aptitude Assessment Invitation
    "Aptitude Assessment Invitation": "Invite the candidate to take the online Aptitude Assessment. Emphasize that it is the first round of evaluations and provide details on how to start.",
    
    # 6. Aptitude Assessment Result
    "Aptitude Assessment Result": "Share the candidate's aptitude assessment scores and status. If they passed, congratulate them and mention unlocking the next stage (Coding Assessment).",
    
    # 7. Coding Assessment Invitation
    "Coding Assessment Invitation": "Invite the candidate to complete the Coding Assessment. Mention it tests technical coding skills, algorithms, and real-time execution in our integrated environment.",
    
    # 8. Coding Assessment Result
    "Coding Assessment Result": "Congratulate them on completing the coding assessment. Provide feedback that the scoring is complete and currently being reviewed by the hiring manager.",
    
    # 9. Interview Invitation
    "Interview Invitation": "Invite the candidate to schedule or attend their AI Mock/Human Interview. Provide details and guidelines on technical requirements (camera/microphone proctoring).",
    
    # 10. Interview Result
    "Interview Result": "Share feedback/results of the AI interview session. Highlight their score or grade, and thank them for participating in the AI Hire interview flow.",
    
    # 11. Shortlisted Notification
    "Shortlisted Notification": "Inform the candidate that their job application is shortlisted! Congratulate them and say that the recruiter is reviewing their profile for final matching/offer release.",
    
    # 12. Rejection Notification
    "Rejection Notification": "Gracefully inform the candidate that their profile was not selected for this particular role. Mention the reason for rejection: {extra_details}. Keep the tone encouraging, professional, and supportive of future applications.",
    
    # 13. Offer Letter Release
    "Offer Letter Release": "Officially release the job offer/offer details to the candidate! Share enthusiasm about welcoming them to the company and outline the next steps for acceptance.",

    # --- FUTURE EVENTS ---
    "HR_REVIEW_REQUESTED": "Notify the hiring manager or HR recruiter that a candidate has completed all evaluation rounds (Aptitude, Coding, Interview) and their profile is ready for manual HR review.",
    
    # HR Approved
    "HR_APPROVED": "Congratulate the candidate that their profile has been officially approved by the HR review panel. Let them know the recruitment team will connect shortly to schedule an HR Interview via Google Meet.",
    
    # HR Rejected
    "HR_REJECTED": "Inform the candidate that after HR review, they will not be proceeding with their application. Keep the tone supportive and encouraging.",
    
    # Interview Scheduled
    "INTERVIEW_SCHEDULED": "Confirm to the candidate that their interview session has been scheduled. Provide date, time, and instructions to access the virtual lobby.",
    
    # Interview Rescheduled
    "INTERVIEW_RESCHEDULED": "Notify the candidate that their interview has been rescheduled. Clarify the new date/time slot and apologize for any inconvenience caused.",
    
    # Interview Cancelled
    "INTERVIEW_CANCELLED": "Notify the candidate that the interview session is cancelled. Explain that we will reach out shortly to reschedule or provide next steps.",
    
    # Interview Confirmed
    "INTERVIEW_CONFIRMED": "Confirm to the recruiter and candidate that the upcoming interview slot is locked and confirmed by both parties. Outline proctoring rules.",
    
    # Interview Completed
    "INTERVIEW_COMPLETED": "Notify the candidate that their final interview has been successfully completed. Thank them for their time and mention that the panel is compiling the final selection scorecards.",
    
    # Final Selection
    "FINAL_SELECTION": "Congratulate the candidate on being selected for the job position! Share the excitement of the hiring team and note that the HR representative will contact them shortly to initiate negotiations.",
    
    # Final Rejection
    "FINAL_REJECTION": "Politely and supportively inform the candidate that they were not selected for the role. Keep the tone warm, encouraging, and express interest in keeping their profile in our talent pool for future openings.",
    
    # Offer Released
    "OFFER_RELEASED": "Officially release the job offer package and offer details to the candidate! Share next steps for reviewing, signing, and accepting the offer letter.",

    # New Offer Letter Workflow Events
    "OFFER_GENERATED": "Notify the hiring manager or recruiter that the offer letter draft has been generated and is ready for review.",
    "OFFER_SENT": "Congratulate the candidate and officially send the offer letter. Provide core package, joining date, reference details, and instruct them to review and respond before expiration.",
    "OFFER_ACCEPTED": "Notify the hiring team that the candidate has officially accepted the employment offer.",
    "OFFER_REJECTED": "Notify the hiring team that the candidate has declined the offer of employment.",
    "OFFER_EXPIRED": "Notify the recipient that the offer has expired or been revoked.",
    "OFFER_EXPIRY_REMINDER": "Send an urgent reminder to the candidate indicating that the offer is expiring soon and needs immediate response.",
    "OFFER_JOINED": "Notify the hiring manager that the candidate has officially joined and completed onboarding.",
    "OFFER_HIRED": "Finalize and celebrate that the candidate is officially hired and the recruitment pipeline is complete."
}

def get_user_prompt_for_event(event_type: str, context: Dict[str, Any]) -> str:
    guideline = EVENT_GUIDELINES.get(event_type, "Draft a professional recruitment update email.")
    
    # Render context variables cleanly
    context_str = json.dumps(context, indent=2)
    
    prompt = f"""
Event Type: {event_type}
Guideline: {guideline}

Available Context Variables:
{context_str}

Please generate the email content according to this guideline and the available context.
Ensure it sounds natural, conversational, personalized, and human-written. Do not use generic template-like placeholders (like [Candidate Name]) in your output; replace them with the actual context values provided. If a value is missing or empty in the context, write a general polite alternative.
"""
    return prompt
