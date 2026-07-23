# Backend Login System (FastAPI + MySQL)

## Goals
- Provide backend code for login via:
  - Email + password (no OTP)
  - Phone number + password (no OTP)
  - Google OAuth (continue with Google)
- Use FastAPI as backend.
- Use MySQL for persistence.
- JWT-based auth.

## Steps
1. Scaffold backend project structure under `c:/Recruitment/backend/`.
2. Add FastAPI app with routes:
   - `POST /auth/register`
   - `POST /auth/login/email`
   - `POST /auth/login/phone`
   - `GET/POST /auth/google/*` (OAuth)
   - `GET /auth/me` (JWT protected)
3. Implement SQLAlchemy models for `users` and `oauth_accounts` (if needed).
4. Implement password hashing with bcrypt.
5. Implement JWT access + refresh token (or access-only) strategy.
6. Add CORS config so your existing HTML pages can call the API.
7. Add environment configuration (.env example).
8. Add minimal frontend-ready endpoints response formats.
9. Provide run instructions and DB setup SQL.

