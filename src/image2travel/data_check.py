"""Data validation/checking."""
from .db import init_db


class DataChecker:
    def check(self) -> dict:
        conn = init_db()
        issues = []
        cur = conn.execute("SELECT COUNT(*) as c FROM destinations")
        dest_count = cur.fetchone()['c']
        cur = conn.execute("SELECT COUNT(*) as c FROM pois")
        poi_count = cur.fetchone()['c']
        cur = conn.execute("SELECT COUNT(*) as c FROM claims")
        claims_count = cur.fetchone()['c']
        return {
            "destinations": dest_count,
            "pois": poi_count,
            "claims": claims_count,
            "issues": issues,
            "ok": len(issues) == 0
        }
