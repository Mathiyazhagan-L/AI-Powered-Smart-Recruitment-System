# AI-Powered smart Recruitment Platform

## Introduction
The **AI-Powered Recruitment & Hiring Platform** is an enterprise-grade, end-to-end recruitment solution designed to automate and streamline the hiring lifecycle. By combining **Artificial Intelligence (Google Gemini)**, **Machine Learning candidate fit scoring**, **AI Anti-Cheat Proctoring (YOLOv8)**, **GitHub Intelligence**, and **Automated Resume Parsing**, the platform replaces traditional, manual screening with smart, objective evaluations. It provides dedicated interfaces for candidates to take assessments and track applications, and for recruiters to manage hiring pipelines, review proctoring logs, and generate offer letters.

---

## Features

### Candidate Portal
- **Smart Job Feed**: Browse and search active job openings.
- **Automated Profile Autofill**: Instant extraction of experience, skills, and education from uploaded resumes.
- **Multi-Modal Assessment Suite**:
  - Timed Multiple-Choice Questions (MCQ) testing.
  - In-browser coding challenges with real-time evaluation.
  - Asynchronous audio/video recorded responses.
- **AI Anti-Cheat Monitoring**: Active tab-switch detection, window focus logging, and camera proctoring warnings.
- **Real-Time Application Status**: Live pipeline tracking from initial screening to offer acceptance.

### Recruiter Workspace
- **Dynamic Kanban Pipeline**: Drag-and-drop applicant management across customizable hiring stages.
- **AI Candidate Match & Scoring**: Machine learning candidate suitability scores and automated evaluations.
- **GitHub Intelligence**: Technical profile analysis checking public repos, commit frequency, and language distribution.
- **Proctoring Audit Logs**: Detailed breakdown of assessment focus violations and webcam alerts.
- **HR Review Queue**: Streamlined manual scoring overrides and candidate approvals.
- **PDF Offer Letter Generator**: Custom offer letter creation with automated variable replacement and download.
- **Recruitment Analytics**: Funnel conversion metrics, time-to-hire statistics, and candidate performance insights.

---

## Technology Stack

| Component | Technologies Used |
| :--- | :--- |
| **Frontend Applications** | Next.js 14 (App Router), React 18, TypeScript |
| **Monorepo Tools** | Turborepo |
| **Styling & Components** | Tailwind CSS, Shadcn UI / Radix UI, Lucide Icons |
| **State Management** | TanStack React Query (v5), React Context API |
| **Backend API Framework** | Python 3.10+, FastAPI, Uvicorn |
| **Database & ORM** | MySQL, SQLAlchemy, PyMySQL |
| **AI Evaluation Engine** | Google Generative AI (`google-generativeai` / Gemini Pro) |
| **Proctoring & Vision** | OpenCV, YOLOv8 (`ultralytics`) |
| **Authentication & Security** | JWT (`python-jose`, `passlib`, `bcrypt`) |

---

## System Architecture

```mermaid
graph TD
    subgraph Frontend Workspace [Turborepo Monorepo]
        CP[Candidate App - Next.js]
        RP[Recruiter App - Next.js]
    end

    subgraph Backend Core [FastAPI Service]
        API[REST API Gateway]
        AUTH[Auth & Security Module]
        PARSER[Resume Parser]
        EVAL[AI Evaluation Module]
        PROCTOR[AI Proctoring Engine]
        GH[GitHub Intelligence Module]
        OFFER[Offer Management Module]
        ANALYTICS[Analytics & Funnel Engine]
    end

    subgraph Storage & External Services
        DB[(MySQL Database)]
        GEMINI[Google Gemini API]
        GITHUB[GitHub REST API]
    end

    CP -->|HTTP / JSON| API
    RP -->|HTTP / JSON| API
    API --> AUTH
    API --> PARSER
    API --> EVAL
    API --> PROCTOR
    API --> GH
    API --> OFFER
    API --> ANALYTICS

    EVAL --> GEMINI
    GH --> GITHUB
    AUTH & PARSER & EVAL & PROCTOR & OFFER & ANALYTICS --> DB
```

---

## Workflow

```mermaid
flowchart LR
    A[Job Created by Recruiter] --> B[Candidate Applies & Uploads Resume]
    B --> C[Resume Parsed & Profile Auto-Filled]
    C --> D[GitHub Intelligence Analysis]
    D --> E[Candidate Takes Assessment & Proctoring Active]
    E --> F[AI & ML Model Compute Fit Score]
    F --> G[Recruiter Reviews Candidate & Proctoring Logs]
    G --> H[Interview Scheduled]
    H --> I[HR Review & PDF Offer Letter Generated]
    I --> J[Candidate Accepts Offer]
```

---

## Folder Structure

```gcode
Recruitment/
├── 📂 backend/                             # Python FastAPI Backend
│   ├── 📂 modules/                         # Core domain logic
│   │   ├── 📂 ai_evaluation/               # Gemini AI scoring engine
│   │   ├── 📂 analytics/                   # Recruitment metrics & reports
│   │   ├── 📂 assessment/                  # Question Bank & MCQ engine
│   │   ├── 📂 auth/                        # Authentication & RBAC
│   │   ├── 📂 candidate/                   # Profile & application APIs
│   │   ├── 📂 coding_assessment/           # Code execution sandbox & test cases
│   │   ├── 📂 company_profile/             # Company branding & profiles
│   │   ├── 📂 email_automation/            # Automated email templates & notifications
│   │   ├── 📂 github_intelligence/         # Candidate GitHub profile scraper
│   │   ├── 📂 hr_review/                   # HR review queue & manual overrides
│   │   ├── 📂 interview_assessment/        # Video/audio response evaluation
│   │   ├── 📂 interview_scheduling/        # Slot booking & meeting links
│   │   ├── 📂 job_management/              # Jobs & pipeline management
│   │   ├── 📂 ml_prediction/               # Fit score ML model
│   │   ├── 📂 offer_management/            # PDF offer letter generator
│   │   ├── 📂 proctoring/                  # Anti-cheat & webcam monitoring
│   │   ├── 📂 recruiter_workspace/          # Recruiter tools & candidate comparison
│   │   └── 📂 resume_parser/               # Resume PDF/Doc parser
│   ├── 📄 main.py                          # FastAPI Application entrypoint
│   └── 📄 requirements.txt                 # Backend Python packages
│
└── 📂 frontend/                            # Turborepo Frontend Workspace
    ├── 📂 apps/
    │   ├── 📂 candidate/                   # Next.js Candidate Portal
    │   └── 📂 recruiter/                   # Next.js Recruiter Workspace
    ├── 📂 packages/                        # Shared packages (UI, Tailwind, TS configs)
    └── 📄 turbo.json                       # Turborepo task configuration
```

---

## Installation

### Prerequisites
- **Node.js**: v18.x or higher
- **Python**: v3.10 or higher
- **MySQL Database Server**

### Step 1: Backend Setup
```bash
# Navigate to the backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
.\venv\Scripts\activate

# Activate virtual environment (Linux/macOS)
# source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# Run backend server
uvicorn main:app --reload --port 8000
```

### Step 2: Frontend Setup
```bash
# Navigate to the frontend directory
cd frontend

# Install monorepo dependencies
npm install

# Start development servers
npm run dev
```

---

## Environment Variables

Create a `.env` file inside the `backend/` directory with the following variables:

```ini
# Database Settings
DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/recruitment_db

# Security & Authentication
SECRET_KEY=your_jwt_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# AI Configuration
GEMINI_API_KEY=your_google_gemini_api_key

# Email Automation Settings
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

---

## Usage

1. **Recruiter Flow**:
   - Access `http://localhost:3001` to login as a Recruiter.
   - Post a new job opportunity and configure hiring pipeline stages.
   - Review applicant match scores, proctoring violation logs, and GitHub intelligence scores.
   - Drag candidate cards across pipeline stages and trigger PDF offer letter generation.

2. **Candidate Flow**:
   - Access `http://localhost:3000` to login as a Candidate.
   - Upload resume for profile autofill.
   - Browse job feed and submit application.
   - Complete assigned timed MCQs, coding challenges, and recorded video interview rounds under proctoring.

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register a new user (Candidate / Recruiter) |
| `POST` | `/api/auth/login` | Authenticate user and return JWT access token |
| `GET` | `/api/jobs/` | List all open job postings |
| `POST` | `/api/jobs/` | Create a new job posting (Recruiter only) |
| `POST` | `/api/candidate/resume-parse` | Upload resume PDF and return extracted JSON |
| `POST` | `/api/assessments/submit` | Submit MCQ assessment answers |
| `POST` | `/api/coding/execute` | Execute candidate code against test cases |
| `POST` | `/api/proctoring/log` | Record proctoring violations (tab switch, face count) |
| `GET` | `/api/github/analyze/{username}` | Fetch and score GitHub user profile |
| `POST` | `/api/offers/generate` | Generate candidate PDF offer letter |

---

## Database Schema

Key entities in the recruitment relational database include:
- **`users`**: Stores authentication credentials, user roles (Candidate, Recruiter, Admin), and profiles.
- **`jobs`**: Job postings, job descriptions, required skills, department, and pipeline configurations.
- **`applications`**: Link between candidates and jobs, stage tracking, match scores, and overall status.
- **`assessments`**: Question banks, test configurations, candidate responses, and score records.
- **`proctoring_logs`**: Log entries for webcam detections, focus losses, and tab switches per assessment session.
- **`offers`**: Offer letter details, generated PDF storage paths, salary info, and acceptance status.

---

## AI Features

- **Gemini LLM Scoring Engine**: Evaluates qualitative assessment responses against ideal model solutions.
- **Machine Learning Fit Scoring**: Predictive algorithm evaluating candidate suitability based on resume skills, test scores, and GitHub metrics.
- **YOLOv8 Anti-Cheat Vision**: Detects multiple faces, missing faces, or prohibited device usage during live webcam assessments.
- **GitHub Intelligence Scraper**: Calculates technical contribution metrics from public open-source activity.

---

## Screenshots

### 👤 Candidate Portal Screenshots
| Candidate Dashboard | Jobs Overview |
| :---: | :---: |
| ![Dashboard](./assets/screenshots/dashboard.png) | ![Jobs](./assets/screenshots/jobs.png) |

| Assessment Interface | Application Tracking |
| :---: | :---: |
| ![Assessment Page](./assets/screenshots/assessment_page.png) | ![Application Tracking](./assets/screenshots/application_tracking.png) |

| Offer Page | Login Page |
| :---: | :---: |
| ![Offer Page](./assets/screenshots/offer_page.png) | ![Login Page](./assets/screenshots/login_page.png) |

---

### 💼 Recruiter Workspace Screenshots
| Recruiter Dashboard | Candidate Management |
| :---: | :---: |
| ![Recruiter Dashboard](./assets/screenshots/recruiter_dashboard.png) | ![Candidate Management](./assets/screenshots/candidate_management_recruiter.png) |

| Job Management | Offer Management |
| :---: | :---: |
| ![Job Management](./assets/screenshots/job_management_recruiter.png) | ![Offer Management](./assets/screenshots/offer_management_recruiter.png) |

---

## Future Enhancements

- 🎙️ **Live AI Technical Interviewer**: Interactive real-time voice AI conducting live technical rounds.
- 📱 **Mobile Application**: Native React Native mobile app for candidates.
- 🌐 **ATS Integrations**: Direct integration with Greenhouse, Lever, and Workday.
- 🔒 **Blockchain Verification**: Verifiable digital credentials for candidate certificates and degrees.

---

## Contributors

- **Mathiyazhagan L** ([@Mathiyazhagan-L](https://github.com/Mathiyazhagan-L)) - Full-Stack & AI Development

---

## License

This project is proprietary and confidential. All rights reserved.

---

## Contact

For technical queries, support, or feedback regarding this recruitment platform:
- **Email**: support@recruitment-platform.com
- **Project Repository**: [AI-Powered-Smart-Recruitment-System](https://github.com/Mathiyazhagan-L/AI-Powered-Smart-Recruitment-System)

