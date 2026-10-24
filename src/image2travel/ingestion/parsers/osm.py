"""OSM parser stub."""
from typing import Any


class OSMParser:
    def parse_pbf(self, path: str) -> list[dict[str, Any]]:
        """Parse OSM PBF file."""
        return []
    
    def parse_overpass(self, data: dict) -> list[dict[str, Any]]:
        """Parse Overpass API response."""
        return []
