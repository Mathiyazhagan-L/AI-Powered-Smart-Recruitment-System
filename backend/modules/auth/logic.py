import random
import hashlib
import datetime
import jwt
import os
import smtplib
import bcrypt
import hmac

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# CryptContext is removed to avoid passlib initialization issues with bcrypt 5.0.0
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests

from .model import User
from .model import OTPRecord

# Explicitly load .env from the backend directory with override
env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env")
load_dotenv(env_path, override=True)

# ==========================================
# JWT SETTINGS
# ==========================================

SECRET_KEY = os.getenv(
    "JWT_SECRET",
    "super_secret_key"
)

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_HOURS = 24
REMEMBER_ME_EXPIRE_HOURS = 24 * 30  # 30 days

# Temporary in-memory store for OTPs in development/testing
_last_otp_codes = {}

PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 200000
PBKDF2_SALT_BYTES = 16


# ==========================================
# PASSWORD HASHING
# ==========================================

def hash_password(password: str) -> str:
    print("hash_password CALLED WITH:")
    print("  password TYPE:", type(password))
    try:
        print("  password LEN (chars):", len(password))
        print("  password VALUE:", password)
    except Exception as e:
        print("  Failed to print password info:", e)
    
    try:
        salt = os.urandom(PBKDF2_SALT_BYTES)
        derived = hashlib.pbkdf2_hmac(
            PBKDF2_ALGORITHM,
            password.encode("utf-8"),
            salt,
            PBKDF2_ITERATIONS
        )
        return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${derived.hex()}"
    except Exception as e:
        import traceback
        print("EXCEPTION IN hash_password:")
        traceback.print_exc()
        raise e


def verify_password(plain: str, hashed: str) -> bool:
    print("verify_password CALLED WITH:")
    print("  plain TYPE:", type(plain), "hashed TYPE:", type(hashed))
    try:
        print("  plain LEN:", len(plain))
    except Exception as e:
        print("  Failed to print plain info:", e)

    if isinstance(hashed, str) and hashed.startswith("pbkdf2_sha256$"):
        try:
            _, iterations, salt_hex, hash_hex = hashed.split("$", 3)
            salt = bytes.fromhex(salt_hex)
            expected = bytes.fromhex(hash_hex)
            derived = hashlib.pbkdf2_hmac(
                PBKDF2_ALGORITHM,
                plain.encode("utf-8"),
                salt,
                int(iterations)
            )
            return hmac.compare_digest(derived, expected)
        except Exception as e:
            import traceback
            print("EXCEPTION IN verify_password (pbkdf2):")
            traceback.print_exc()
            return False

    if isinstance(hashed, str) and hashed.startswith("$2"):
        try:
            return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
        except Exception as e:
            import traceback
            print("EXCEPTION IN verify_password (bcrypt):")
            traceback.print_exc()
            return False

    print("verify_password: unsupported hash format.")
    return False


# ==========================================
# OTP GENERATION
# ==========================================

def generate_otp():

    return str(
        random.randint(
            100000,
            999999
        )
    )


# ==========================================
# HASH OTP
# ==========================================

def hash_otp(code):

    return hashlib.sha256(
        code.encode()
    ).hexdigest()


# ==========================================
# SEND EMAIL OTP
# ==========================================

def send_email_otp(
    email: str,
    otp: str,
    subject: str = "AIHire Verification Code",
    purpose: str = "verification"
):

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    msg = MIMEMultipart()

    msg["From"] = smtp_user
    msg["To"] = email
    msg["Subject"] = subject

    body = f"""
Hello,

Your AIHire {purpose} code is:

  {otp}

This code will expire in 5 minutes.

If you did not request this, please ignore this email.

Thank you,
AIHire Team
"""

    msg.attach(
        MIMEText(body, "plain")
    )

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"  [SMTP] Email sent to {email} with OTP: {otp}")
    except Exception as e:
        print(f"  [SMTP ERROR] Failed to send email to {email}: {e}")
        print(f"  [SMTP FALLBACK] OTP for {email} is: {otp}")


# ==========================================
# CREATE ACCESS TOKEN
# ==========================================

def create_access_token(
    data: dict,
    remember_me: bool = False
):

    payload = data.copy()

    expire_hours = (
        REMEMBER_ME_EXPIRE_HOURS if remember_me
        else ACCESS_TOKEN_EXPIRE_HOURS
    )

    expire = (
        datetime.datetime.utcnow()
        + datetime.timedelta(hours=expire_hours)
    )

    payload.update({"exp": expire})

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ==========================================
# VERIFY ACCESS TOKEN
# ==========================================

def verify_access_token(token: str):

    return jwt.decode(
        token,
        SECRET_KEY,
        algorithms=[ALGORITHM]
    )


# ==========================================
# SAVE OTP
# ==========================================

def save_otp(
    target: str,
    db: Session
):

    otp = generate_otp()

    hashed_otp = hash_otp(otp)

    expires_at = (
        datetime.datetime.utcnow()
        + datetime.timedelta(minutes=5)
    )

    otp_record = OTPRecord(
        target=target,
        otp_code=hashed_otp,
        expires_at=expires_at,
        is_used=False
    )

    db.add(otp_record)
    db.commit()
    db.refresh(otp_record)

    # Save to helper for local verification/auto-fill
    _last_otp_codes[target] = otp
    _last_otp_codes["__last__"] = otp

    if "@" in target:
        send_email_otp(target, otp)

    return otp


# ==========================================
# VERIFY OTP
# ==========================================

def verify_otp(
    target: str,
    code: str,
    db: Session
):

    record = (
        db.query(OTPRecord)
        .filter(
            OTPRecord.target == target,
            OTPRecord.is_used == False
        )
        .order_by(OTPRecord.created_at.desc())
        .first()
    )

    if not record:
        raise ValueError("OTP not found")

    if record.expires_at < datetime.datetime.utcnow():
        raise ValueError("OTP expired")

    if record.otp_code != hash_otp(code):
        raise ValueError("Invalid OTP")

    record.is_used = True
    db.commit()

    return True


# ==========================================
# FIND USER
# ==========================================

def get_user(
    db: Session,
    email=None,
    phone=None
):

    if email:
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    if phone:
        return (
            db.query(User)
            .filter(User.phone == phone)
            .first()
        )

    return None


# ==========================================
# REGISTER USER (legacy)
# ==========================================

def create_user(
    db: Session,
    email=None,
    phone=None,
    role="candidate"
):

    user = User(
        email=email,
        phone=phone,
        role=role,
        is_active=True,
        is_verified=True,
        auth_provider="email"
    )

    if email:
        user.email_verified = True

    if phone:
        user.phone_verified = True

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ==========================================
# LOGIN OR REGISTER (legacy)
# ==========================================

def authenticate_or_register_user(
    db: Session,
    email=None,
    phone=None,
    role="candidate"
):

    user = get_user(db=db, email=email, phone=phone)

    if user:
        return user

    return create_user(db=db, email=email, phone=phone, role=role)


# ==========================================
# NEW: REGISTER USER (email + password)
# ==========================================

def register_user(
    db: Session,
    full_name: str,
    email: str,
    otp_code: str,
    mobile_number: str,
    password: str,
    role: str
):
    """
    Verifies the OTP and creates a fully verified user account.
    Raises ValueError on invalid OTP, duplicate email, or duplicate mobile.
    """

    # Check duplicate email
    existing_email = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )
    if existing_email:
        raise ValueError("An account with this email already exists.")

    # Check duplicate mobile (stored in phone column)
    existing_phone = (
        db.query(User)
        .filter(User.phone == mobile_number)
        .first()
    )
    if existing_phone:
        raise ValueError("An account with this mobile number already exists.")

    # Verify OTP before creating the user
    verify_otp(target=email, code=otp_code, db=db)

    # Create verified user
    user = User(
        full_name=full_name,
        email=email,
        phone=mobile_number,
        role=role,
        password_hash=hash_password(password),
        is_verified=True,
        email_verified=True,
        phone_verified=False,
        is_active=True,
        auth_provider="email"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        auto_create_profile_for_user(db, user)
    except Exception as e:
        print(f"Failed to auto-create profile during registration: {e}")

    return user

# ==========================================
# NEW: VERIFY REGISTRATION OTP
# ==========================================

def verify_registration(
    db: Session,
    email: str,
    otp_code: str
):
    """
    Verifies the registration OTP and activates the user account.
    """

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise ValueError("No account found for this email.")

    if user.is_verified:
        raise ValueError("Account is already verified.")

    # Verify OTP
    verify_otp(target=email, code=otp_code, db=db)

    # Activate account
    user.is_verified = True
    user.email_verified = True
    db.commit()
    db.refresh(user)

    # Trigger Welcome Email
    try:
        from modules.email_automation.triggers import trigger_email
        event_type = "Candidate Registration" if user.role == "candidate" else "Recruiter Registration"
        
        candidate_id = user.id if user.role == "candidate" else None
        recruiter_id = user.id if user.role == "recruiter" else None
        
        trigger_email(
            event_type=event_type,
            candidate_id=candidate_id,
            recruiter_id=recruiter_id,
            context={
                "extra_details": f"Welcome to AIHire as a {user.role.capitalize()}!"
            },
            db=db
        )
    except Exception as e:
        print(f"Failed to send welcome email: {e}")

    return user


# ==========================================
# NEW: LOGIN
# ==========================================

def login_user(
    db: Session,
    email: str,
    password: str
):
    """
    Validates email/password credentials.
    Returns the User object on success.
    Raises ValueError on invalid credentials.
    """

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise ValueError("Invalid email or password.")

    if user.auth_provider == "google" and not user.password_hash:
        raise ValueError(
            "This account was created with Google. Please sign in with Google."
        )

    if not user.password_hash:
        raise ValueError("Invalid email or password.")

    if not verify_password(password, user.password_hash):
        raise ValueError("Invalid email or password.")

    if not user.is_verified:
        raise ValueError(
            "Your email is not verified. Please check your inbox for the OTP."
        )

    if not user.is_active:
        raise ValueError("Your account has been deactivated.")

    return user


# ==========================================
# NEW: FORGOT PASSWORD — SEND OTP
# ==========================================

def send_forgot_password_otp(
    db: Session,
    email: str
):
    """
    Sends a password-reset OTP to the given email.
    Always returns success message (don't leak whether email exists).
    """

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        # Don't reveal that the email doesn't exist
        return True

    if user.auth_provider == "google" and not user.password_hash:
        raise ValueError(
            "This account uses Google Sign-In. "
            "You cannot reset the password."
        )

    otp = generate_otp()
    hashed_otp = hash_otp(otp)
    expires_at = (
        datetime.datetime.utcnow()
        + datetime.timedelta(minutes=5)
    )

    otp_record = OTPRecord(
        target=email,
        otp_code=hashed_otp,
        expires_at=expires_at,
        is_used=False
    )
    db.add(otp_record)
    db.commit()

    # Save to helper for local verification/auto-fill
    _last_otp_codes[email] = otp
    _last_otp_codes["__last__"] = otp

    send_email_otp(
        email,
        otp,
        subject="AIHire — Password Reset Code",
        purpose="password reset"
    )

    return True


# ==========================================
# NEW: RESET PASSWORD
# ==========================================

def reset_password(
    db: Session,
    email: str,
    otp_code: str,
    new_password: str
):
    """
    Verifies OTP and updates the user's password.
    """
    print("reset_password logic function CALLED WITH:")
    print("  email:", email)
    print("  otp_code:", otp_code)
    print("  new_password:", new_password)
    print("  new_password LEN:", len(new_password))

    user = (
        db.query(User)
        .filter(User.email == email)
        .first()
    )

    if not user:
        raise ValueError("No account found for this email.")

    # Verify OTP
    verify_otp(target=email, code=otp_code, db=db)

    # Update password
    print("  Calling hash_password(new_password)...")
    user.password_hash = hash_password(new_password)
    db.commit()

    return True


# ==========================================
# NEW: GOOGLE COMPLETE REGISTRATION
# ==========================================

def google_complete_registration(
    db: Session,
    google_id: str,
    email: str,
    full_name: str,
    mobile_number: str,
    role: str
):
    """
    Creates a new account for a Google user who needs to supply
    mobile number and role.
    """

    # Check duplicate mobile
    existing_phone = (
        db.query(User)
        .filter(User.phone == mobile_number)
        .first()
    )
    if existing_phone:
        raise ValueError("An account with this mobile number already exists.")

    user = User(
        full_name=full_name,
        email=email,
        phone=mobile_number,
        role=role,
        google_id=google_id,
        password_hash=None,
        is_verified=True,
        email_verified=True,
        phone_verified=False,
        is_active=True,
        auth_provider="google"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    try:
        auto_create_profile_for_user(db, user)
    except Exception as e:
        print(f"Failed to auto-create profile during Google registration completion: {e}")

    return user

def verify_google_token(db: Session, auth_code: str):
    """
    Exchanges the Google authorization code for tokens, verifies the ID token, 
    and returns the User if they exist.
    If the user does not exist, returns a dict with 'needs_completion': True
    and the decoded payload.
    """
    try:
        import os

        print("="*70)
        print("verify_google_token() called")
        print("Current Working Directory:", os.getcwd())
        print("GOOGLE_CLIENT_ID:", repr(os.getenv("GOOGLE_CLIENT_ID")))
        print("GOOGLE_CLIENT_SECRET:", "Loaded" if os.getenv("GOOGLE_CLIENT_SECRET") else "Missing")
        print("="*70)

        client_id = os.getenv("GOOGLE_CLIENT_ID")
        print("client_id variable =", repr(client_id))
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id:
            raise ValueError("Google Client ID is not configured on the server.")
        if not client_secret:
            raise ValueError("Google Client Secret is required to exchange auth code.")
            
        import urllib.parse
        # Ensure the auth code is properly unquoted in case the frontend sent it URL-encoded
        clean_code = urllib.parse.unquote(auth_code)

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": clean_code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": "postmessage",
            "grant_type": "authorization_code"
        }
        r = requests.post(token_url, data=data)
        if not r.ok:
            raise ValueError(f"Failed to exchange auth code: {r.text}")
            
        token_data = r.json()
        id_token_jwt = token_data.get("id_token")
        if not id_token_jwt:
            raise ValueError("No id_token in response")
            
        idinfo = id_token.verify_oauth2_token(id_token_jwt, google_requests.Request(), client_id)

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        google_id = idinfo['sub']
        email = idinfo['email']
        
        # Check if user exists by email
        user = get_user(db, email)
        if user:
            # If they exist but didn't have google_id, update it
            if not user.google_id:
                user.google_id = google_id
                user.auth_provider = "google"
            user.email_verified = True
            user.is_verified = True
            db.commit()
            return {"user": user}
            
        # If user does not exist, they need to complete registration (role + phone)
        return {
            "needs_completion": True,
            "google_id": google_id,
            "email": email,
            "full_name": idinfo.get('name', ''),
        }
    except ValueError as e:
        # Invalid token
        raise ValueError(f"Invalid Google token: {str(e)}")


def auto_create_profile_for_user(db: Session, user: User):
    """
    Automatically creates a CandidateProfile or CompanyProfile for a newly registered user,
    and generates their candidate_code or company_code.
    """
    role_lower = user.role.lower() if user.role else ""
    if role_lower == "candidate":
        from modules.candidate.profile.model import CandidateProfile
        existing = db.query(CandidateProfile).filter(CandidateProfile.user_id == user.id).first()
        if not existing:
            profile = CandidateProfile(
                user_id=user.id,
                full_name=user.full_name or "Candidate Name",
                email=user.email,
                phone=user.phone,
                candidate_status="NEW",
                profile_completion=0
            )
            db.add(profile)
            db.commit()
            db.refresh(profile)
            profile.candidate_code = f"AIH{profile.id:04d}"
            db.commit()
            db.refresh(profile)
            print(f"Auto-created CandidateProfile for user {user.email} with code {profile.candidate_code}")
    elif role_lower in ("company", "recruiter"):
        from modules.company_profile.model import CompanyProfile
        existing = db.query(CompanyProfile).filter(CompanyProfile.user_id == user.id).first()
        if not existing:
            company = CompanyProfile(
                user_id=user.id,
                company_name=user.full_name or "Company Name",
                company_email=user.email,
                company_phone=user.phone,
                website="",
                is_email_verified=False,
                verification_status="Pending"
            )
            db.add(company)
            db.commit()
            db.refresh(company)
            company.company_code = f"AIHR{company.id:04d}"
            db.commit()
            db.refresh(company)
            print(f"Auto-created CompanyProfile for user {user.email} with code {company.company_code}")