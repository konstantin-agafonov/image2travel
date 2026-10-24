"""Itinerary building."""
from typing import Any


class ItineraryBuilder:
    def build(self, trip_brief: dict, destination_id: str) -> dict[str, Any]:
        """Build itinerary."""
        days = trip_brief.get("days", 3)
        return {
            "itinerary_id": f"itin_{destination_id}",
            "destination_id": destination_id,
            "days": days,
            "days_detail": [
                {
                    "day": i + 1,
                    "title": f"Day {i + 1}",
                    "activities": [
                        {"time": "09:00", "type": "poi", "poi_id": "poi_001", "duration_min": 90, "description": "Explore"},
                        {"time": "14:00", "type": "walk", "duration_min": 120, "description": "Scenic walk"},
                        {"time": "17:00", "type": "free", "duration_min": 60, "description": "Relax"},
                    ]
                }
                for i in range(days)
            ],
            "budget_estimate": {"accommodation": 300, "food": 150, "transport": 100, "activities": 50, "total_min": 500, "total_max": 600, "currency": "EUR"},
            "transfers": [],
            "plan_b": {"description": "Indoor alternatives for rainy weather", "options": []},
            "assumptions": ["Prices are estimates for shoulder season"],
        }
