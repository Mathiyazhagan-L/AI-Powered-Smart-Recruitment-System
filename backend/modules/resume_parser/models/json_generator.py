from copy import deepcopy
from typing import Any


STANDARD_JSON = {
    "personal": {
        "full_name": None,
        "email": None,
        "phone": None,
        "location": None,
        "linkedin_url": None,
        "github_url": None,
        "portfolio_url": None,
    },
    "summary": None,
    "skills": [],
    "education": [],
    "experience": [],
    "projects": [],
    "certifications": [],
    "awards": [],
}


class JsonGenerator:
    """Creates the public standardized resume JSON response."""

    def generate(self, parsed_data: dict[str, Any], resume_id: str | None = None, file_url: str | None = None) -> dict:
        output = deepcopy(STANDARD_JSON)
        for key in output:
            if key == "personal":
                output["personal"].update(parsed_data.get("personal") or {})
            else:
                output[key] = parsed_data.get(key, output[key])
        score = 0
        
        # Base 20 for having a name and email
        if output["personal"].get("full_name") and output["personal"].get("email"):
            score += 20
        
        # Skills max 20
        if len(output.get("skills", [])) > 5:
            score += 20
        elif len(output.get("skills", [])) > 0:
            score += 10
            
        # Education max 20
        if len(output.get("education", [])) > 0:
            score += 20
            
        # Experience max 30
        if len(output.get("experience", [])) > 0:
            score += 30
            
        # Projects max 10
        if len(output.get("projects", [])) > 0:
            score += 10

        output["confidence_score"] = score

        if resume_id:
            output["resume_id"] = resume_id
        if file_url:
            output["file_url"] = file_url
        return output
