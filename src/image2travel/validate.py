"""Itinerary validation."""
from typing import Any


class ItineraryValidator:
    def validate(self, itinerary: dict) -> dict[str, Any]:
        """Validate itinerary."""
        blockers = []
        warnings = []
        unknowns = []
        
        days = itinerary.get("days", 0)
        if days < 1 or days > 7:
            blockers.append({"code": "invalid_days", "message": "Days must be between 1 and 7"})
        
        if not itinerary.get("days_detail"):
            blockers.append({"code": "missing_schedule", "message": "No schedule provided"})
        
        warnings.append({"code": "weather_unknown", "message": "Check weather forecast closer to travel date"})
        
        return {
            "valid": len(blockers) == 0,
            "blockers": blockers,
            "warnings": warnings,
            "unknowns": unknowns,
            "feasibility_score": 0.9 if len(blockers) == 0 else 0.3,
        }
