"""File export handling."""
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from .db import get_data_dir


class FileExporter:
    def __init__(self):
        self.export_dir = get_data_dir() / "files" / "exports"
        self.export_dir.mkdir(parents=True, exist_ok=True)
    
    def export_markdown(self, itinerary: dict) -> dict:
        file_id = str(uuid.uuid4())
        content = f"# Itinerary: {itinerary.get('destination_id')}\n\n"
        content += f"Days: {itinerary.get('days')}\n\n"
        for day in itinerary.get('days_detail', []):
            content += f"## Day {day['day']}\n"
            for act in day.get('activities', []):
                content += f"- {act.get('time', '')}: {act.get('description')}\n"
            content += "\n"
        filepath = self.export_dir / f"{file_id}.md"
        filepath.write_text(content)
        return {
            "file_id": file_id,
            "format": "markdown",
            "content": content,
            "resource_uri": f"image2travel://files/{file_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
            "path": str(filepath),
        }
    
    def export_ics(self, itinerary: dict) -> dict:
        file_id = str(uuid.uuid4())
        content = "BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//Image2Travel//EN\nEND:VCALENDAR\n"
        filepath = self.export_dir / f"{file_id}.ics"
        filepath.write_text(content)
        return {
            "file_id": file_id,
            "format": "ics",
            "content": content,
            "resource_uri": f"image2travel://files/{file_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
            "path": str(filepath),
        }
    
    def export_geojson(self, itinerary: dict) -> dict:
        file_id = str(uuid.uuid4())
        content = json.dumps({"type": "FeatureCollection", "features": []})
        filepath = self.export_dir / f"{file_id}.geojson"
        filepath.write_text(content)
        return {
            "file_id": file_id,
            "format": "geojson",
            "content": content,
            "resource_uri": f"image2travel://files/{file_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat() + "Z",
            "path": str(filepath),
        }
