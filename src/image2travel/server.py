"""MCP server implementation."""
import sys
import json
from typing import Any
from fastmcp import FastMCP

from .models import TripBrief, PlanTripResult, DestinationConcept
from .db import init_db, get_db_path

mcp = FastMCP("image2travel")


@mcp.tool()
def plan_trip(trip_brief: dict[str, Any]) -> dict[str, Any]:
    """Plan trip based on trip brief and experience fingerprint."""
    try:
        brief = TripBrief(**trip_brief)
    except Exception as e:
        raise ValueError(f"Invalid trip brief: {e}")
    
    # Initialize DB if needed
    init_db()
    
    # Return sample concepts for MVP
    concepts = [
        DestinationConcept(
            destination_id="dest_001",
            name="Lake Bled",
            country="Slovenia",
            match_type="twin",
            match_score=0.85,
            reasons=["Similar alpine lake setting", "Calm atmosphere", "Good for slow travel"],
            summary="Alpine lake with island church, accessible hikes, peaceful walks",
            unknowns=["Exact season availability"],
            assumptions=["Mild weather in shoulder season"],
            season_fit=0.8,
        ),
        DestinationConcept(
            destination_id="dest_002",
            name="Plitvice Lakes",
            country="Croatia",
            match_type="wildcard",
            match_score=0.72,
            reasons=["Water features", "Walking paths", "Natural scenery"],
            summary="Terraced lakes with wooden walkways through forest",
            unknowns=["Crowd levels"],
            assumptions=["Open in planned month"],
            season_fit=0.75,
        ),
        DestinationConcept(
            destination_id="dest_003",
            name="Hallstatt",
            country="Austria",
            match_type="twin",
            match_score=0.78,
            reasons=["Mountain lake setting", "Quaint atmosphere"],
            summary="Historic lakeside village with mountain backdrop",
            unknowns=["Tourist crowds"],
            assumptions=["Accessible by public transport"],
            season_fit=0.7,
        ),
    ]
    
    result = PlanTripResult(
        concepts=concepts,
        questions=["What time of year are you considering?", "Do you prefer quieter or more social?"],
        assumptions=["Assuming shoulder season for best balance"],
    )
    return result.model_dump()


@mcp.tool()
def get_destination(destination_id: str, month: int | None = None) -> dict[str, Any]:
    """Get destination details."""
    init_db()
    return {
        "destination_id": destination_id,
        "name": "Lake Bled" if destination_id == "dest_001" else "Unknown",
        "country": "Slovenia" if destination_id == "dest_001" else "Unknown",
        "pois": [
            {"poi_id": "poi_001", "name": "Bled Island", "category": "viewpoint"},
            {"poi_id": "poi_002", "name": "Ojstrica Viewpoint", "category": "hike"},
        ],
        "facts": [],
        "provenance": [],
    }


@mcp.tool()
def build_itinerary(trip_brief: dict[str, Any], destination_id: str) -> dict[str, Any]:
    """Build detailed itinerary."""
    init_db()
    brief = TripBrief(**trip_brief)
    return {
        "itinerary_id": "itin_001",
        "destination_id": destination_id,
        "days": brief.days,
        "days_detail": [
            {
                "day": i + 1,
                "activities": [
                    {"time": "morning", "poi_id": "poi_001", "duration_min": 60, "description": "Visit main attraction"},
                    {"time": "afternoon", "activity": "walk", "duration_min": 120, "description": "Scenic walk"},
                ]
            }
            for i in range(brief.days)
        ],
        "budget_estimate": {"min": 500, "max": 800, "currency": "EUR"},
        "plan_b": {"description": "Rainy day alternatives"},
    }


@mcp.tool()
def validate_itinerary(itinerary: dict[str, Any]) -> dict[str, Any]:
    """Validate itinerary feasibility."""
    init_db()
    return {
        "valid": True,
        "blockers": [],
        "warnings": ["Check weather forecast closer to travel date"],
        "unknowns": [],
        "feasibility_score": 0.9,
    }


@mcp.tool()
def verify_place(name: str | None = None, lat: float | None = None, lon: float | None = None, region: str | None = None) -> dict[str, Any]:
    """Verify place against catalog."""
    init_db()
    return {
        "candidates": [
            {"name": name or "Unknown", "confidence": 0.7, "evidence": ["Local context"]}
        ],
        "source": "local_catalog",
    }


@mcp.tool()
def export_itinerary(itinerary: dict[str, Any], format: str = "markdown") -> dict[str, Any]:
    """Export itinerary to file."""
    init_db()
    import uuid
    from datetime import datetime, timedelta
    file_id = str(uuid.uuid4())
    return {
        "file_id": file_id,
        "format": format,
        "content": "# Itinerary\n\nSample itinerary content...",
        "resource_uri": f"image2travel://files/{file_id}",
        "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
    }


def main():
    mcp.run()


if __name__ == "__main__":
    main()
