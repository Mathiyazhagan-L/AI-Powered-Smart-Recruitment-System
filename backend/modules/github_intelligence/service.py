import os
import re
import logging
import requests
import threading
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com"


def extract_github_username(url: str) -> str | None:
    """
    Extracts the username from a GitHub URL.
    Validates formatting and handles leading/trailing spaces and slashes.
    """
    if not url:
        return None
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        parsed = urlparse(url)
        if "github.com" not in parsed.netloc.lower():
            return None
        path_parts = [p for p in parsed.path.split('/') if p]
        if path_parts:
            username = path_parts[0]
            # Simple validation for GitHub username
            if re.match(r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$", username):
                return username
        return None
    except Exception:
        return None


def fetch_github_data(username: str) -> dict:
    """
    Queries public GitHub APIs for the given username.
    Returns a dict with "profile", "repos", and "error" keys.
    """
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    try:
        # 1. Fetch User Profile
        profile_res = requests.get(f"{GITHUB_API_URL}/users/{username}", headers=headers, timeout=10)
        if profile_res.status_code != 200:
            logger.warning(f"GitHub user profile fetch failed for '{username}': {profile_res.status_code}")
            if profile_res.status_code == 403:
                return {"error": "GitHub API rate limit reached. Please try again later."}
            elif profile_res.status_code == 404:
                return {"error": "GitHub profile not found."}
            else:
                return {"error": f"GitHub API returned error status: {profile_res.status_code}"}
        profile_data = profile_res.json()

        # 2. Fetch User Repositories
        repos_res = requests.get(f"{GITHUB_API_URL}/users/{username}/repos?per_page=100", headers=headers, timeout=10)
        if repos_res.status_code != 200:
            logger.warning(f"GitHub repositories fetch failed for '{username}': {repos_res.status_code}")
            if repos_res.status_code == 403:
                return {"error": "GitHub API rate limit reached. Please try again later."}
            else:
                repos_data = []
        else:
            repos_data = repos_res.json()

        return {
            "profile": profile_data,
            "repos": repos_data,
            "error": None
        }
    except requests.exceptions.Timeout:
        logger.error(f"GitHub API connection timeout for '{username}'")
        return {"error": "GitHub service connection timed out."}
    except Exception as e:
        logger.error(f"GitHub API connection error for '{username}': {e}")
        return {"error": "GitHub service is temporarily unavailable."}


def evaluate_github_profile(github_url: str) -> dict | None:
    """
    Parses GitHub URL, fetches statistics, calculates components, 
    and returns a formatted dict containing scores and summary.
    """
    username = extract_github_username(github_url)
    if not username:
        return {
            "github_score": None,
            "github_repositories": None,
            "github_stars": None,
            "github_followers": None,
            "github_languages": None,
            "github_summary": {
                "error": "Invalid GitHub URL format.",
                "total_repos": 0,
                "total_stars": 0,
                "total_forks": 0,
                "followers": 0,
                "following": 0,
                "primary_languages": [],
                "inferred_skills": []
            }
        }

    res = fetch_github_data(username)
    if res.get("error"):
        return {
            "github_score": 0,
            "github_repositories": 0,
            "github_stars": 0,
            "github_followers": 0,
            "github_languages": [],
            "github_summary": {
                "error": res["error"],
                "total_repos": 0,
                "total_stars": 0,
                "total_forks": 0,
                "followers": 0,
                "following": 0,
                "primary_languages": [],
                "inferred_skills": []
            }
        }

    profile = res["profile"]
    repos = res["repos"]

    total_repos = len(repos)
    total_stars = sum(repo.get("stargazers_count", 0) for repo in repos)
    total_forks = sum(repo.get("forks_count", 0) for repo in repos)
    followers = profile.get("followers", 0)
    following = profile.get("following", 0)

    # 1. Repositories Component (Max 20 pts)
    repos_score = min(20, total_repos * 2)

    # 2. Stars Component (Max 20 pts)
    stars_score = min(20, total_stars * 4)

    # 3. Activity Component (Max 20 pts)
    # Check if updated in the last 90 days
    recently_updated = False
    now = datetime.utcnow()
    for repo in repos:
        updated_at_str = repo.get("updated_at")
        if updated_at_str:
            try:
                # GitHub returns ISO 8601 strings (e.g. "2011-01-26T19:14:43Z")
                updated_at = datetime.strptime(updated_at_str.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
                if (now - updated_at).days <= 90:
                    recently_updated = True
                    break
            except Exception:
                pass

    activity_score = min(20, followers * 3 + (10 if recently_updated else 5))

    # 4. Language Diversity Component (Max 20 pts)
    languages = set()
    for repo in repos:
        lang = repo.get("language")
        if lang:
            languages.add(lang.strip())
    primary_languages = sorted(list(languages))
    diversity_score = min(20, len(primary_languages) * 5)

    # 5. Technical Skills Component (Max 20 pts)
    tech_skills_pool = [
        "python", "javascript", "machine learning", "deep learning", 
        "fastapi", "react", "sql", "html", "css", "docker", "kubernetes", 
        "langchain", "typescript", "c++", "java", "django", "flask", 
        "pytorch", "tensorflow", "node.js", "nosql", "postgresql", "aws", "gcp"
    ]
    detected_skills = set()
    for repo in repos:
        name = repo.get("name", "").lower()
        lang = repo.get("language", "").lower() if repo.get("language") else ""
        topics = [t.lower() for t in repo.get("topics", [])]

        for skill in tech_skills_pool:
            if skill in name or skill == lang or skill in topics:
                # Format formatting logic
                formatted = skill.title() if len(skill) > 3 else skill.upper()
                if formatted == "Javascript":
                    formatted = "JavaScript"
                elif formatted == "Typescript":
                    formatted = "TypeScript"
                elif formatted == "Fastapi":
                    formatted = "FastAPI"
                elif formatted == "Postgresql":
                    formatted = "PostgreSQL"
                elif formatted == "Sql":
                    formatted = "SQL"
                elif formatted == "Aws":
                    formatted = "AWS"
                elif formatted == "Gcp":
                    formatted = "GCP"
                elif formatted == "Css":
                    formatted = "CSS"
                elif formatted == "Html":
                    formatted = "HTML"
                detected_skills.add(formatted)

    inferred_skills = sorted(list(detected_skills))
    skills_score = min(20, len(inferred_skills) * 4)

    # Final Combined Score
    github_score = repos_score + stars_score + activity_score + diversity_score + skills_score
    github_score = min(100, max(0, github_score))

    summary = {
        "total_repos": total_repos,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "followers": followers,
        "following": following,
        "primary_languages": primary_languages,
        "inferred_skills": inferred_skills
    }

    return {
        "github_score": github_score,
        "github_repositories": total_repos,
        "github_stars": total_stars,
        "github_followers": followers,
        "github_languages": primary_languages,
        "github_summary": summary
    }


def run_github_evaluation_task(profile_id: int, github_url: str):
    """
    Thread target function executing the profile analysis and committing database changes.
    """
    from core.database import SessionLocal
    from modules.candidate.profile.model import CandidateProfile

    db = SessionLocal()
    try:
        eval_res = evaluate_github_profile(github_url)
        if eval_res:
            profile = db.query(CandidateProfile).filter(CandidateProfile.id == profile_id).first()
            if profile:
                profile.github_score = eval_res["github_score"]
                profile.github_summary = eval_res["github_summary"]
                profile.github_last_updated = datetime.utcnow()
                profile.github_repositories = eval_res["github_repositories"]
                profile.github_stars = eval_res["github_stars"]
                profile.github_followers = eval_res["github_followers"]
                profile.github_languages = eval_res["github_languages"]
                db.commit()
                logger.info(f"GitHub intelligence evaluation succeeded for candidate profile id: {profile_id}")
    except Exception as e:
        logger.error(f"GitHub background evaluation failed for candidate profile id: {profile_id}: {e}", exc_info=True)
        try:
            db.rollback()
        except Exception as rb_err:
            logger.error(f"Failed to rollback database: {rb_err}")
    finally:
        db.close()


def trigger_background_github_evaluation(profile_id: int, github_url: str):
    """
    Fires off a non-blocking daemon thread to calculate/cache GitHub intelligence.
    """
    if not github_url:
        return
    thread = threading.Thread(target=run_github_evaluation_task, args=(profile_id, github_url))
    thread.daemon = True
    thread.start()
