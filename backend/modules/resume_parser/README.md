# AI Resume Parsing Module

Production-ready Python backend for parsing resumes, returning standardized JSON, and optionally storing files/data in Supabase.

## Features

- Supports PDF, DOCX, DOC, TXT, JPG, JPEG, and PNG.
- Modular extractor and parser layers.
- Batch parsing for multiple uploaded resumes.
- Standard JSON response with `null` and empty arrays for missing values.
- Supabase Storage upload and PostgreSQL persistence.
- FastAPI endpoints ready for ATS or recruitment platform integration.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

The current implementation uses `spacy.blank("en")`, so the model download is optional for this version. Install Tesseract OCR separately if you want image parsing.

Copy `.env.example` to `.env` and set your Supabase values. Run `supabase/schema.sql` in the Supabase SQL editor before using `/upload`.

## Run

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs` for interactive API docs.

## API

- `POST /auth/otp/send`: generate a local development OTP for candidate/recruiter login.
- `POST /auth/otp/verify`: verify OTP and return a JWT access token.
- `GET /auth/otp/last`: development helper used by the static frontend to auto-fill the mock OTP.
- `GET /auth/me`: return the logged-in user using `Authorization: Bearer <token>`.
- `POST /parse`: parse one or more files without storing in Supabase.
- `POST /upload`: parse files, upload originals to Supabase Storage, and store parsed records.
- `GET /resume/{id}`: fetch stored resume row.
- `GET /resume/{id}/json`: fetch stored standardized JSON.

Both upload endpoints accept multipart form-data with a repeated `files` field.

If `FRONTEND_DIR` points to your design folder, `/` serves `startpage.html`, `/candidate page.html` serves the candidate page, and `/recruiter page.html` serves the recruiter page. The local auth store defaults to `app_data/aihire_auth.json` so it can run before you connect a production database.

## Output Shape

```json
{
  "personal": {},
  "summary": null,
  "skills": [],
  "education": [],
  "experience": [],
  "projects": [],
  "certifications": [],
  "awards": []
}
```

## Notes

- Legacy DOC extraction depends on `textract`, which may require system packages depending on your OS.
- Image extraction depends on a local Tesseract installation.
- Heuristic parsers are intentionally isolated so a future LLM, semantic search, scoring, or ATS enrichment layer can be added without changing the public API.
