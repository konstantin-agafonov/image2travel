"""Destination matching logic."""
from typing import Any
from .db import init_db
from .repositories import CatalogRepo
import json


class DestinationMatcher:
    def __init__(self):
        self.conn = init_db()
        self.conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
        self.repo = CatalogRepo()
    
    def filter(self, fingerprint: dict, brief: dict) -> list[dict]:
        """Filter destinations."""
        return self.repo.get_active_destinations()
    
    def score(self, destinations: list[dict], fingerprint: dict) -> list[tuple[dict, float]]:
        """Score destinations."""
        scored = []
        for dest in destinations:
            score = 0.7
            emotions = fingerprint.get('emotions', []) if fingerprint else []
            dest_exp = dest.get('experience', {})
            if emotions and dest_exp.get('emotions'):
                if any(e in dest_exp.get('emotions', []) for e in emotions):
                    score += 0.1
            scored.append((dest, min(score, 1.0)))
        return scored
    
    def diversify(self, scored: list[tuple[dict, float]]) -> list[tuple[dict, float]]:
        """Diversify results."""
        return sorted(scored, key=lambda x: x[1], reverse=True)
    
    def match(self, fingerprint: dict, brief: dict) -> list[dict]:
        """Full matching pipeline."""
        filtered = self.filter(fingerprint, brief)
        scored = self.score(filtered, fingerprint)
        diversified = self.diversify(scored)
        results = []
        match_types = ["exact", "twin", "wildcard"]
        for i, (dest, score) in enumerate(diversified[:3]):
            match_type = match_types[i] if i < len(match_types) else "wildcard"
            if score < 0.75 and i == 0:
                match_type = "twin"
            results.append({
                "destination_id": dest["entity_id"],
                "name": dest["name"],
                "country": "SI",
                "match_type": match_type,
                "match_score": round(score, 2),
                "reasons": ["Similar atmosphere"],
                "summary": dest.get("summary", ""),
                "unknowns": [],
                "assumptions": [],
                "season_fit": round(score * 0.9, 2),
            })
        return results
