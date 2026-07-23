from modules.resume_parser.parser.resume_parser import ResumeParser


def test_resume_parser_generates_standard_sections():
    raw_text = """
    Jane Doe
    jane@example.com | +91 98765 43210
    LinkedIn: https://linkedin.com/in/janedoe
    GitHub: https://github.com/janedoe

    Summary
    Machine learning engineer with experience building NLP products.

    Skills
    Python, FastAPI, PostgreSQL, AWS, NLP, TensorFlow, Communication

    Education
    B.Tech in Computer Science
    Example Institute of Technology
    CGPA: 8.7
    2024

    Experience
    Machine Learning Intern at Example AI
    Jan 2024 - Jun 2024
    Built document extraction APIs.

    Projects
    Resume Parser
    Technologies: Python, FastAPI, PostgreSQL
    Parsed resumes into JSON. https://github.com/janedoe/resume-parser

    Certifications
    AWS Cloud Practitioner - Amazon 2024

    Awards
    Winner - AI Hackathon
    """

    parsed = ResumeParser().parse(raw_text)

    assert parsed["personal"]["full_name"] == "Jane Doe"
    assert parsed["personal"]["email"] == "jane@example.com"
    assert parsed["education"][0]["graduation_year"] == "2024"
    assert parsed["experience"][0]["internship"] is True
    assert parsed["projects"][0]["github_link"] == "https://github.com/janedoe/resume-parser"
    assert any(group["category"] == "programming_languages" for group in parsed["skills"])


def test_resume_parser_returns_empty_arrays_for_missing_sections():
    parsed = ResumeParser().parse("Alex Smith\nalex@example.com")

    assert parsed["education"] == []
    assert parsed["experience"] == []
    assert parsed["projects"] == []
    assert parsed["certifications"] == []
    assert parsed["awards"] == []
