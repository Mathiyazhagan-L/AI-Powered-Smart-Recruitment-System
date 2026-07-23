import os
import json
import pytest
from datetime import date
from sqlalchemy import text
from core.database import SessionLocal
from modules.resume_parser.services.autofill_service import (
    autofill_candidate_tables,
    normalize_proficiency_level,
    parse_education_entry,
    parse_experience_entry,
    parse_project_entry,
)


def test_normalize_proficiency_level():
    """Test proficiency level normalization."""
    assert normalize_proficiency_level("intermediate") == "intermediate"
    assert normalize_proficiency_level("junior") == "intermediate"
    assert normalize_proficiency_level("senior") == "advanced"
    assert normalize_proficiency_level("expert") == "expert"
    assert normalize_proficiency_level("") == "intermediate"


def test_parse_education_entry():
    """Test education entry parsing."""
    entry = {
        "degree_line": "Bachelor of Computer Science",
        "institution": "MIT",
        "years": ["2020"],
        "user_id": 1,
    }
    result = parse_education_entry(entry)
    assert result["degree"] == "Bachelor of Computer Science"
    assert result["institution"] == "MIT"
    assert result["start_year"] == 2020
    assert result["user_id"] == 1


def test_parse_experience_entry():
    """Test experience entry parsing."""
    entry = {
        "line": "Software Engineer at Google",
        "user_id": 1,
    }
    result = parse_experience_entry(entry)
    assert result["job_title"] == "Software Engineer"
    assert result["company_name"] == "Google"
    assert result["user_id"] == 1


def test_parse_project_entry():
    """Test project entry parsing."""
    entry = {
        "project_name": "AI Resume Parser",
        "description": "Automated resume parsing system",
        "technologies": ["Python", "FastAPI"],
        "user_id": 1,
    }
    result = parse_project_entry(entry)
    assert result["project_name"] == "AI Resume Parser"
    assert result["technologies"] == ["Python", "FastAPI"]
    assert result["user_id"] == 1


def test_autofill_candidate_tables():
    """Test autofill candidate tables with parsed resume data."""
    candidate_id = 99  # Use high ID to avoid conflicts
    test_parsed = {
        "personal": {
            "name": "Test Candidate",
            "email": "test.candidate@example.com",
            "phone": "+1 234 567 8900",
        },
        "summary": "Experienced software engineer",
        "skills": ["Python", "SQL", "Docker"],
        "education": [
            {
                "degree_line": "Bachelor of Science",
                "institution": "Test University",
                "years": ["2020"],
            }
        ],
        "experience": [
            {"line": "Senior Engineer at TestCorp"}
        ],
        "projects": [
            {
                "project_name": "Test Project",
                "description": "A test project",
                "technologies": ["Python"],
            }
        ],
    }

    with SessionLocal() as db:
        # Clean up any existing data for this candidate
        for table in [
            "candidate_profiles",
            "candidate_education",
            "candidate_experience",
            "candidate_projects",
            "candidate_skills",
        ]:
            db.execute(text(f"DELETE FROM {table} WHERE user_id = :uid"), {"uid": candidate_id})
        db.commit()

        # Run autofill
        autofill_candidate_tables(db=db, candidate_id=candidate_id, parsed=test_parsed)
        db.commit()

        # Verify results
        profile_count = db.execute(
            text("SELECT COUNT(*) FROM candidate_profiles WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).scalar()
        education_count = db.execute(
            text("SELECT COUNT(*) FROM candidate_education WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).scalar()
        experience_count = db.execute(
            text("SELECT COUNT(*) FROM candidate_experience WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).scalar()
        project_count = db.execute(
            text("SELECT COUNT(*) FROM candidate_projects WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).scalar()
        skill_count = db.execute(
            text("SELECT COUNT(*) FROM candidate_skills WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).scalar()

        assert profile_count == 1, f"Expected 1 profile, got {profile_count}"
        assert education_count == 1, f"Expected 1 education, got {education_count}"
        assert experience_count == 1, f"Expected 1 experience, got {experience_count}"
        assert project_count == 1, f"Expected 1 project, got {project_count}"
        assert skill_count == 3, f"Expected 3 skills, got {skill_count}"

        # Verify profile data
        profile = db.execute(
            text("SELECT full_name, email, phone FROM candidate_profiles WHERE user_id = :uid"),
            {"uid": candidate_id},
        ).fetchone()
        assert profile[0] == "Test Candidate"
        assert profile[1] == "test.candidate@example.com"
        assert profile[2] == "+1 234 567 8900"

        # Clean up
        for table in [
            "candidate_profiles",
            "candidate_education",
            "candidate_experience",
            "candidate_projects",
            "candidate_skills",
        ]:
            db.execute(text(f"DELETE FROM {table} WHERE user_id = :uid"), {"uid": candidate_id})
        db.commit()


if __name__ == "__main__":
    test_normalize_proficiency_level()
    test_parse_education_entry()
    test_parse_experience_entry()
    test_parse_project_entry()
    test_autofill_candidate_tables()
    print("All autofill tests passed!")
