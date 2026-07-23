import sys
import os
import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the parent directory (backend) to the Python path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from modules.job_management.model import Base, Job, JobCreate, JobUpdate, SalaryRulesSchema, EligibilityRulesSchema, ApplicationSettingsSchema
from modules.job_management import logic

def test_job_management():
    print("Initializing test database...")
    # Setup test database (SQLite in-memory)
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    try:
        # 1. Prepare Valid Job Data
        future_deadline = datetime.datetime.utcnow() + datetime.timedelta(days=30)
        valid_job_data = JobCreate(
            title="Senior Backend Engineer",
            description="We are looking for a Senior Backend Engineer with extensive experience in FastAPI and SQLAlchemy.",
            required_skills=["Python", "FastAPI", "SQLAlchemy"],
            preferred_skills=["Docker", "AWS", "MySQL"],
            experience="5+ years",
            package="120,000 - 150,000 USD",
            location="Remote",
            criteria="Must have a bachelor's degree in CS or equivalent.",
            openings=3,
            deadline=future_deadline,
            status="draft",
            selection_rounds=[
                {
                    "round_number": 1,
                    "name": "Online Coding Test",
                    "type": "coding",
                    "description": "Initial automated coding screening"
                },
                {
                    "round_number": 2,
                    "name": "Technical Interview 1",
                    "type": "technical",
                    "description": "Live technical interview with engineering team"
                },
                {
                    "round_number": 3,
                    "name": "HR Interview",
                    "type": "hr",
                    "description": "Culture and fit interview"
                }
            ],
            salary_rules=SalaryRulesSchema(
                min_salary=120000.0,
                max_salary=150000.0,
                currency="USD",
                is_negotiable=True,
                benefits=["Health Insurance", "401k", "Remote office stipend"]
            ),
            eligibility_rules=EligibilityRulesSchema(
                min_cgpa=None,
                allowed_degrees=["B.Tech", "M.Tech", "MCA", "B.Sc"],
                max_backlogs=0,
                min_experience_years=5
            ),
            application_settings=ApplicationSettingsSchema(
                allow_late_submissions=False,
                max_applications=500,
                ask_cover_letter=True,
                custom_questions=[{"question": "What is your notice period?", "type": "text"}]
            )
        )

        print("\n--- Test 1: Creating a Valid Job ---")
        job = logic.create_job(db=db, job_data=valid_job_data)
        assert job.id is not None
        assert job.title == "Senior Backend Engineer"
        assert job.status == "draft"
        assert len(job.selection_rounds) == 3
        print(f"SUCCESS: Job created with ID {job.id}.")

        print("\n--- Test 2: Validation Failures ---")
        # Past deadline
        invalid_job_data = valid_job_data.model_copy()
        invalid_job_data.deadline = datetime.datetime.utcnow() - datetime.timedelta(days=1)
        try:
            logic.create_job(db=db, job_data=invalid_job_data)
            assert False, "Should have raised ValueError for past deadline."
        except ValueError as e:
            print(f"SUCCESS: Caught expected validation error: {e}")



        # Invalid salary rules (min > max)
        invalid_job_data = valid_job_data.model_copy()
        invalid_job_data.salary_rules = SalaryRulesSchema(min_salary=100.0, max_salary=50.0)
        try:
            logic.create_job(db=db, job_data=invalid_job_data)
            assert False, "Should have raised ValueError for min_salary > max_salary."
        except ValueError as e:
            print(f"SUCCESS: Caught expected validation error: {e}")

        print("\n--- Test 3: Updating a Job ---")
        update_data = JobUpdate(
            title="Senior Python Backend Developer",
            openings=5,
            required_skills=["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"]
        )
        updated_job = logic.update_job(db=db, job_id=job.id, job_data=update_data)
        assert updated_job.title == "Senior Python Backend Developer"
        assert updated_job.openings == 5
        assert "PostgreSQL" in updated_job.required_skills
        print("SUCCESS: Job updated successfully.")

        print("\n--- Test 4: Publishing a Job ---")
        published_job = logic.publish_job(db=db, job_id=job.id)
        assert published_job.status == "published"
        print("SUCCESS: Job published successfully.")

        print("\n--- Test 5: Search and Filtering ---")
        # Create another job in draft
        draft_job_data = valid_job_data.model_copy()
        draft_job_data.title = "Frontend Developer"
        draft_job_data.required_skills = ["React", "TypeScript", "CSS"]
        draft_job_data.location = "New York"
        draft_job_data.salary_rules = SalaryRulesSchema(min_salary=90000.0, max_salary=110000.0)
        draft_job = logic.create_job(db=db, job_data=draft_job_data)
        
        # Search published jobs
        published_jobs = logic.search_and_filter_jobs(db=db, status="published")
        assert len(published_jobs) == 1
        assert published_jobs[0].title == "Senior Python Backend Developer"
        
        # Filter by skill
        python_jobs = logic.search_and_filter_jobs(db=db, skills=["Python"])
        assert len(python_jobs) == 1
        assert python_jobs[0].title == "Senior Python Backend Developer"
        
        # Filter by min_salary (100,000 USD)
        high_paying = logic.search_and_filter_jobs(db=db, min_salary=100000)
        assert len(high_paying) == 1
        assert high_paying[0].title == "Senior Python Backend Developer"
        
        # Filter by text search
        frontend_search = logic.search_and_filter_jobs(db=db, search_query="Frontend")
        assert len(frontend_search) == 1
        assert frontend_search[0].title == "Frontend Developer"
        print("SUCCESS: Search and filter assertions passed.")

        print("\n--- Test 6: Job Analytics ---")
        analytics = logic.get_job_analytics(db=db)
        assert analytics["total_jobs"] == 2
        assert analytics["status_counts"]["published"] == 1
        assert analytics["status_counts"]["draft"] == 1
        assert analytics["total_openings_active"] == 5  # Only published openings count
        assert analytics["location_distribution"]["Remote"] == 1
        assert analytics["location_distribution"]["New York"] == 1
        assert analytics["average_salary_published"] == 120000.0
        print(f"SUCCESS: Analytics matches expected output: {analytics}")

        print("\n--- Test 7: Closing a Job ---")
        closed_job = logic.close_job(db=db, job_id=job.id)
        assert closed_job.status == "closed"
        
        analytics_after_close = logic.get_job_analytics(db=db)
        assert analytics_after_close["status_counts"]["closed"] == 1
        assert analytics_after_close["status_counts"]["published"] == 0
        assert analytics_after_close["total_openings_active"] == 0
        print("SUCCESS: Job closed successfully.")

        print("\n--- Test 8: Deleting a Job ---")
        delete_success = logic.delete_job(db=db, job_id=job.id)
        assert delete_success is True
        
        remaining_jobs = db.query(Job).all()
        assert len(remaining_jobs) == 1
        assert remaining_jobs[0].id == draft_job.id
        print("SUCCESS: Job deleted successfully.")

        print("\n==============================")
        print("ALL TESTS PASSED SUCCESSFULLY!")
        print("==============================")

    finally:
        db.close()

if __name__ == "__main__":
    test_job_management()
