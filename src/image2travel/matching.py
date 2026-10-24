"""Destination matching logic."""
from typing import Any
from .db import init_db


class DestinationMatcher:
    def __init__(self):
        self.conn = init_db()
        self.conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    
    def filter(self, fingerprint: dict, brief: dict) -> list[dict]:
        """Filter destinations."""
        cur = self.conn.execute("SELECT * FROM destinations WHERE entity_id IN (SELECT entity_id FROM entities WHERE status='active')")
        return [dict(row) for row in cur.fetchall()]
    
    def score(self, destinations: list[dict], fingerprint: dict) -> list[tuple[dict, float]]:
        """Score destinations."""
        scored = []
        for dest in destinations:
            score = 0.7  # Base score
            scored.append((dest, score))
        return scored
    
    def diversify(self, scored: list[tuple[dict, float]]) -> list[tuple[dict, float]]:
        """Diversify results."""
        return scored
    
    def match(self, fingerprint: dict, brief: dict) -> list[dict]:
        """Full matching pipeline."""
        filtered = self.filter(fingerprint, brief)
        scored = self.score(filtered, fingerprint)
        diversified = self.diversify(scored)
        results = []
        for i, (dest, score) in enumerate(diversified[:3]):
            match_type = "exact" if i == 0 and score > 0.8 else ("twin" if i == 1 else "wildcard")
            results.append({
                "destination_id": dest["entity_id"],
                "name": dest["name"],
                "country": "SI",
                "match_type": match_type,
                "match_score": score,
                "reasons": ["Similar atmosphere"],
                "summary": dest["summary"],
                "unknowns": [],
                "assumptions": [],
                "season_fit": 0.8,
            })
        return results
