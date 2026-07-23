from pydantic import BaseModel
from typing import List, Dict


class DashboardOverviewResponse(BaseModel):
    total_jobs: int
    total_candidates: int
    total_applications: int
    selected_candidates: int
    high_potential_candidates: int
    medium_potential_candidates: int
    rejected_candidates: int


class SkillCountResponse(BaseModel):
    skill: str
    count: int


class SkillGapItem(BaseModel):
    skill: str
    missing_count: int


class CandidateRankingAnalyticsItem(BaseModel):
    rank: int
    candidate_id: int
    score: int
    prediction: str


class PredictionDistributionResponse(BaseModel):
    Selected: int
    High_Potential: int
    Medium_Potential: int
    Rejected: int

    class Config:
        populate_by_name = True


class HiringFunnelResponse(BaseModel):
    Applied: int
    Screened: int
    Shortlisted: int
    Interviewed: int
    Selected: int
