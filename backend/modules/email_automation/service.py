import os
import json
import logging
import requests
import datetime
from typing import Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session
from core.database import SessionLocal

from .models import EmailLog
from .email_sender import send_smtp_email, render_branded_html, FALLBACK_TEMPLATES
from .email_logger import update_email_log
from modules.job_management.model import Notification

logger = logging.getLogger(__name__)

def generate_email_content(event_type: str, context: Dict[str, Any]) -> Tuple[Dict[str, str], str]:
    """
    Tries generating email content using the fallback sequence:
    OpenRouter -> Groq -> Gemini -> Predefined static template.
    Returns (content_dict, method_used).
    """
    from .prompts import SYSTEM_PROMPT, get_user_prompt_for_event
    
    # 1. Format the fallback content for defaults/context merging
    fallback_tpl = FALLBACK_TEMPLATES.get(event_type, {
        "subject": f"Update from AIHire: {event_type}",
        "heading": "AIHire Notification",
        "body": "This is an update regarding your profile or applications on AIHire.",
        "cta_text": "Open Portal",
        "cta_link": "/candidate page.html",
        "closing": "Best regards,\nThe AIHire Team"
    })
    
    # Pre-render fallback values with context
    merged_fallback = {}
    for key, val in fallback_tpl.items():
        if isinstance(val, str):
            try:
                merged_fallback[key] = val.format(**context)
            except Exception:
                merged_fallback[key] = val
        else:
            merged_fallback[key] = val

    prompt = get_user_prompt_for_event(event_type, context)
    
    # --- 1. OPENROUTER ---
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    openrouter_model = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash:free")
    
    if openrouter_key:
        try:
            logger.info("Drafting email content via OpenRouter...")
            headers = {
                "Authorization": f"Bearer {openrouter_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://127.0.0.1:8000",
                "X-Title": "AIHire Email Generator"
            }
            payload = {
                "model": openrouter_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                content = _clean_and_parse_json(raw_text, merged_fallback)
                return content, "OpenRouter"
            else:
                logger.warning(f"OpenRouter response failed: {resp.status_code} - {resp.text}. Trying Groq...")
        except Exception as ex:
            logger.error(f"OpenRouter generation failed: {ex}. Trying Groq...")

    # --- 2. GROQ ---
    groq_key = os.environ.get("GROQ_API_KEY")
    groq_model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    if groq_key:
        try:
            logger.info("Drafting email content via Groq...")
            headers = {
                "Authorization": f"Bearer {groq_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": groq_model,
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7,
                "response_format": {"type": "json_object"}
            }
            resp = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                raw_text = resp.json()["choices"][0]["message"]["content"].strip()
                content = _clean_and_parse_json(raw_text, merged_fallback)
                return content, "Groq"
            else:
                logger.warning(f"Groq response failed: {resp.status_code} - {resp.text}. Trying Gemini...")
        except Exception as ex:
            logger.error(f"Groq generation failed: {ex}. Trying Gemini...")

    # --- 3. GEMINI ---
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        try:
            logger.info("Drafting email content via Gemini...")
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            
            # Combine system prompt guidelines into Gemini call
            combined_prompt = f"{SYSTEM_PROMPT}\n\n{prompt}"
            response = model.generate_content(combined_prompt)
            raw_text = response.text.strip()
            content = _clean_and_parse_json(raw_text, merged_fallback)
            return content, "Gemini"
        except Exception as ex:
            logger.error(f"Gemini generation failed: {ex}. Falling back to Predefined templates.")

    # --- 4. PREDEFINED STATIC TEMPLATES ---
    logger.info("AI Generation fallback: Using predefined static template.")
    return merged_fallback, "Predefined Template"

def _clean_and_parse_json(raw_text: str, fallback: Dict[str, str]) -> Dict[str, str]:
    """Cleans and extracts JSON payload from LLM responses."""
    text = raw_text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines[-1].startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
        
    try:
        data = json.loads(text)
        # Validate schema keys
        required_keys = ["subject", "heading", "body", "cta_text", "cta_link", "closing"]
        for key in required_keys:
            if key not in data or not data[key]:
                data[key] = fallback.get(key, "")
        return data
    except Exception as e:
        logger.error(f"JSON parsing of LLM response failed: {e}. Raw: {raw_text}")
        return fallback

def process_email_generation_and_send(log_id: int, context: Dict[str, Any]):
    """
    Synchronous processor running in background thread/task.
    Generates structured content, wraps in HTML, sends over SMTP, and registers notifications.
    """
    db = SessionLocal()
    try:
        log = db.query(EmailLog).filter(EmailLog.id == log_id).first()
        if not log:
            logger.error(f"EmailLog #{log_id} not found in database.")
            return

        # 1. Generate Structured Content
        if log.generated_html and log.generated_subject:
            logger.info(f"Resending cached email HTML directly for log #{log_id}")
            attachment_path = context.get("attachment_path")
            attachment_name = context.get("attachment_name")
            html = log.generated_html
            subject = log.generated_subject
            success, err_msg = send_smtp_email(
                log.recipient_email, 
                subject, 
                html, 
                attachment_path=attachment_path, 
                attachment_name=attachment_name
            )
        else:
            content, method = generate_email_content(log.email_type, context)
            logger.info(f"Generated content for log #{log_id} using {method}")
            
            # 2. Render branded responsive HTML
            html = render_branded_html(log.email_type, content, context)
            subject = content["subject"]
            
            # 3. Deliver SMTP Email
            attachment_path = context.get("attachment_path")
            attachment_name = context.get("attachment_name")
            success, err_msg = send_smtp_email(
                log.recipient_email, 
                subject, 
                html, 
                attachment_path=attachment_path, 
                attachment_name=attachment_name
            )
            
        # 4. Update Logs & Persist In-App Notification
        if success:
            update_email_log(
                db=db,
                log_id=log_id,
                status="Sent",
                subject=subject,
                content_json=json.dumps(content) if not (log.generated_html and log.generated_subject) else log.generated_content_json,
                html=html
            )
            
            # Write Notification
            try:
                target_user_id = log.candidate_id or log.user_id
                if target_user_id:
                    # If we used cached HTML, body might be shortened from cached html or we just fetch from log subject/message
                    notif_msg = log.body[:150] + "..." if log.body and len(log.body) > 150 else (log.body or "Notification details inside portal.")
                    if not (log.generated_html and log.generated_subject):
                        notif_msg = content["body"][:150] + "..." if len(content["body"]) > 150 else content["body"]
                        
                    notif = Notification(
                        user_id=target_user_id,
                        title=subject,
                        message=notif_msg,
                        type=log.email_type,
                        is_read=0
                    )
                    db.add(notif)
                    db.commit()
                    logger.info(f"Written notification for user {target_user_id}")
            except Exception as notif_ex:
                logger.error(f"Failed to write notification: {notif_ex}")
        else:
            update_email_log(
                db=db,
                log_id=log_id,
                status="Failed",
                subject=subject,
                content_json=json.dumps(content) if not (log.generated_html and log.generated_subject) else log.generated_content_json,
                html=html,
                error_message=err_msg
            )
    except Exception as ex:
        logger.error(f"Unhandled error in email background processor: {ex}")
        try:
            update_email_log(
                db=db,
                log_id=log_id,
                status="Failed",
                error_message=str(ex)
            )
        except Exception:
            pass
    finally:
        db.close()
