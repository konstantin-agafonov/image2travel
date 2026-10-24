"""Pydantic models for contracts."""
from typing import Any, Literal
from pydantic import BaseModel, Field


class ExperienceFingerprint(BaseModel):
    emotions: list[str] = Field(default_factory=list)
    landscape: list[str] = Field(default_factory=list)
    pace: str = "moderate"
    effort: str = "easy"
    season_hint: str | None = None
    time_of_day: str | None = None
    weather_hint: str | None = None
    crowd_tolerance: str = "moderate"
    activity_level: str = "light"
    sensory: list[str] = Field(default_factory=list)
    visible_elements: list[str] = Field(default_factory=list)
    interpretations: list[str] = Field(default_factory=list)
    confidence: dict[str, float] = Field(default_factory=dict)


class TripBrief(BaseModel):
    days: int = Field(ge=1, le=7)
    month: int | None = Field(default=None, ge=1, le=12)
    budget_range: str | None = None
    people: int = Field(default=1, ge=1)
    start_location: str | None = None
    must_haves: list[str] = Field(default_factory=list)
    avoid: list[str] = Field(default_factory=list)
    priorities: list[str] = Field(default_factory=list)
    fingerprint: ExperienceFingerprint | None = None
    text_context: str | None = None


class DestinationConcept(BaseModel):
    destination_id: str
    name: str
    country: str
    match_type: Literal["exact", "twin", "wildcard"]
    match_score: float
    reasons: list[str] = Field(default_factory=list)
    summary: str
    unknowns: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    season_fit: float | None = None
    feasibility_hint: str | None = None


class PlanTripResult(BaseModel):
    concepts: list[DestinationConcept]
    questions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    method: str = "image2travel"
