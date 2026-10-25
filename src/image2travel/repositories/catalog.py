"""Catalog repository."""
from typing import Any, Optional
from ..db import init_db
import json


class CatalogRepo:
    def __init__(self):
        self.conn = init_db()
        self.conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    
    def get_active_destinations(self) -> list[dict]:
        cur = self.conn.execute("""
            SELECT d.* FROM destinations d
            JOIN entities e ON e.id = d.entity_id
            WHERE e.status = 'active'
        """)
        rows = [dict(r) for r in cur.fetchall()]
        for row in rows:
            if row.get('experience_json'):
                row['experience'] = json.loads(row['experience_json'])
            if row.get('visual_json'):
                row['visual'] = json.loads(row['visual_json'])
        return rows
    
    def get_destination(self, destination_id: str) -> Optional[dict]:
        cur = self.conn.execute("SELECT * FROM destinations WHERE entity_id = ?", (destination_id,))
        row = cur.fetchone()
        if not row:
            return None
        row = dict(row)
        if row.get('experience_json'):
            row['experience'] = json.loads(row['experience_json'])
        if row.get('visual_json'):
            row['visual'] = json.loads(row['visual_json'])
        return row
