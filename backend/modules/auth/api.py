from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from core.database import get_db

from .schema import (
    SendOTPRequest,
    VerifyOTPRequest,
    RegisterRequest,
    VerifyRegistrationRequest,
    LoginRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    GoogleVerifyRequest,
    GoogleCompleteRequest,
)

from .logic import (
    save_otp,
    verify_otp,
    authenticate_or_register_user,
    create_access_token,
    verify_access_token,
    register_user,
    verify_registration,
    login_user,
    send_forgot_password_otp,
    reset_password,
    verify_google_token,
    google_complete_registration,
    get_user,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


# ==========================================
# SEND OTP (legacy)
# ==========================================

@router.post("/otp/send")
def send_otp(
    payload: SendOTPRequest,
    db: Session = Depends(get_db)
):

    try:
        if payload.intent == "register" and payload.method == "email":
            existing_user = get_user(db=db, email=payload.target)
            if existing_user:
                raise HTTPException(status_code=400, detail="You already have an account.")

        save_otp(target=payload.target, db=db)
        return {"success": True, "message": "OTP sent successfully"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# VERIFY OTP (legacy)
# ==========================================

@router.post("/otp/verify")
def verify_otp_api(
    payload: VerifyOTPRequest,
    db: Session = Depends(get_db)
):

    try:
        verify_otp(target=payload.target, code=payload.code, db=db)

        email = None
        phone = None

        if payload.method.lower() == "email":
            email = payload.target
        elif payload.method.lower() == "phone":
            phone = payload.target

        role = payload.role
        if role == "recruiter":
            role = "company"

        user = authenticate_or_register_user(
            db=db, email=email, phone=phone, role=role
        )

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
                "is_active": user.is_active
            }
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==========================================
# GET LAST OTP (dev utility)
# ==========================================

@router.get("/otp/last")
def get_last_otp_api(
    target: str = None
):
    """
    Returns the last generated OTP. Useful for testing and development.
    """
    from .logic import _last_otp_codes
    if target:
        code = _last_otp_codes.get(target)
    else:
        code = _last_otp_codes.get("__last__")
    
    if not code:
        raise HTTPException(status_code=404, detail="No OTP code found.")
        
    return {"code": code}


# ==========================================
# REGISTER — STEP 1: Create account + send OTP
# ==========================================


@router.post("/register")
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Creates an unverified account and sends an email OTP.
    """

    try:
        # Validate passwords match
        if payload.password != payload.confirm_password:
            raise ValueError("Passwords do not match.")

        # Normalise role
        role = payload.role.lower()
        if role == "recruiter":
            role = "company"
        if role not in ("candidate", "company"):
            raise ValueError("Role must be 'candidate' or 'company'.")

        user = register_user(
            db=db,
            full_name=payload.full_name,
            email=payload.email,
            otp_code=payload.otp_code,
            mobile_number=payload.mobile_number,
            password=payload.password,
            role=role,
        )

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "phone_verified": user.phone_verified,
                "is_active": user.is_active
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Registration failed. Please try again.")


# ==========================================
# REGISTER — STEP 2: Verify OTP + activate
# ==========================================

@router.post("/register/verify")
def register_verify(
    payload: VerifyRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies the email OTP and activates the account.
    Returns an access token so the user is immediately logged in.
    """

    try:
        user = verify_registration(
            db=db,
            email=payload.email,
            otp_code=payload.otp_code,
        )

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "auth_provider": user.auth_provider,
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Verification failed. Please try again.")


# ==========================================
# LOGIN
# ==========================================

@router.post("/login")
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Email + Password login. Returns JWT access token.
    """

    try:
        user = login_user(
            db=db,
            email=payload.email,
            password=payload.password,
        )

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role},
            remember_me=payload.remember_me or False,
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "auth_provider": user.auth_provider,
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Login failed. Please try again.")


# ==========================================
# FORGOT PASSWORD — Send OTP
# ==========================================


# ==========================================
# CHANGE PASSWORD (authenticated)
# ==========================================

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=256)

@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    try:
        token = credentials.credentials
        jwt_payload = verify_access_token(token)
        user_id = jwt_payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        from .model import User
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if not user.password_hash:
            raise HTTPException(status_code=400, detail="Cannot change password for social login accounts")

        # Verify current password
        import bcrypt
        if not bcrypt.checkpw(payload.current_password.encode("utf-8"), user.password_hash.encode("utf-8")):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

        # Hash new password
        hashed = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user.password_hash = hashed
        db.commit()

        return {"success": True, "message": "Password changed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to change password")


@router.post("/forgot-password")
def forgot_password(
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):

    try:
        send_forgot_password_otp(db=db, email=payload.email)

        return {
            "success": True,
            "message": "If an account exists for this email, a password reset code has been sent.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to send reset code. Please try again.")


# ==========================================
# RESET PASSWORD
# ==========================================

@router.post("/reset-password")
def reset_password_api(
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    print("INCOMING REQUEST PAYLOAD FOR POST /auth/reset-password:")
    try:
        print("  email:", payload.email)
        print("  otp_code:", payload.otp_code)
        print("  new_password:", payload.new_password)
        print("  confirm_password:", payload.confirm_password)
    except Exception as log_err:
        print("  Failed to log payload:", log_err)

    new_password = payload.new_password
    confirm_password = payload.confirm_password
    
    # 5. Add temporary debug logs:
    print("NEW PASSWORD:", new_password)
    print("LEN:", len(new_password))
    
    # 2. Verify new_password length before hashing
    print("VERIFYING new_password LENGTH:", len(new_password))
    if len(new_password) > 256:
        raise ValueError("Password must be 256 characters or fewer.")
    
    # 3. Verify confirm_password length before hashing
    print("VERIFYING confirm_password LENGTH:", len(confirm_password))
    if len(confirm_password) > 256:
        raise ValueError("Password must be 256 characters or fewer.")

    # 4. Check whether otp_code or other field is accidentally passed
    print("CHECKING fields passed: target_email =", payload.email, "otp_code =", payload.otp_code)

    try:
        if payload.new_password != payload.confirm_password:
            raise ValueError("Passwords do not match.")

        reset_password(
            db=db,
            email=payload.email,
            otp_code=payload.otp_code,
            new_password=payload.new_password,
        )

        return {"success": True, "message": "Password reset successfully. You can now log in."}

    except ValueError as e:
        import traceback
        print("ValueError in reset_password_api:")
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        import traceback
        print("Unexpected Exception in reset_password_api:")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Password reset failed. Please try again.")


# GOOGLE VERIFY TOKEN
# ==========================================

@router.post("/google/verify")
def google_verify(
    payload: GoogleVerifyRequest,
    db: Session = Depends(get_db)
):
    """
    Verifies the Google JWT token sent from the client.
    If the user exists, returns an access token to log them in.
    If the user is new, returns a special status instructing the client
    to collect their role and mobile number.
    """
    try:
        print("="*70)
        print("POST /auth/google/verify endpoint reached")
        print("Payload:", payload)
        print("="*70)
        result = verify_google_token(db=db, auth_code=payload.credential)
        
        if result.get("needs_completion"):
            return result
            
        user = result["user"]
        
        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "auth_provider": user.auth_provider,
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Google verification failed.")

# ==========================================
# GOOGLE COMPLETE REGISTRATION
# ==========================================

@router.post("/google/complete")
def google_complete(
    payload: GoogleCompleteRequest,
    db: Session = Depends(get_db)
):
    """
    Called when a new Google user provides their mobile + role.
    """

    try:
        role = payload.role.lower()
        if role == "recruiter":
            role = "company"
        if role not in ("candidate", "company"):
            raise ValueError("Role must be 'candidate' or 'company'.")

        user = google_complete_registration(
            db=db,
            google_id=payload.google_id,
            email=payload.email,
            full_name=payload.full_name,
            mobile_number=payload.mobile_number,
            role=role,
        )

        access_token = create_access_token(
            {"sub": str(user.id), "role": user.role}
        )

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "phone": user.phone,
                "role": user.role,
                "full_name": user.full_name,
                "email_verified": user.email_verified,
                "is_verified": user.is_verified,
                "is_active": user.is_active,
                "auth_provider": user.auth_provider,
            }
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        raise HTTPException(status_code=500, detail="Google registration failed.")


# ==========================================
# CURRENT USER
# ==========================================

@router.get("/me")
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):

    try:
        token = credentials.credentials
        payload = verify_access_token(token)

        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token: missing subject")

        # Ensure we return complete user details (including email) rather than just JWT claims
        from .model import User

        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user.id,
            "email": user.email,
            "username": user.full_name or (user.email.split('@')[0] if user.email else None),
            "role": user.role
        }

    except HTTPException:
        raise
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or Expired Token"
        )


# ==========================================
# HEALTH CHECK
# ==========================================

@router.get("/")
def auth_health():

    return {
        "module": "Authentication",
        "status": "Running"
    }