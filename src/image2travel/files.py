"""File operations."""
import uuid
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from .db import get_data_dir, init_db


class FileManager:
    def __init__(self):
        self.data_dir = get_data_dir()
        self.conn = init_db()
        self.conn.row_factory = lambda c, r: dict(zip([col[0] for col in c.description], r))
    
    def save_export(self, content: str, format: str = "markdown") -> dict:
        file_id = str(uuid.uuid4())
        ext = format if format != "markdown" else "md"
        filename = f"{file_id}.{ext}"
        tmp_path = self.data_dir / "files" / "tmp" / filename
        export_path = self.data_dir / "files" / "exports" / filename
        
        tmp_path.write_text(content, encoding='utf-8')
        tmp_path.rename(export_path)
        
        size = export_path.stat().st_size
        sha256 = hashlib.sha256(content.encode('utf-8')).hexdigest()
        now = datetime.utcnow().isoformat() + 'Z'
        expires = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
        
        self.conn.execute(
            "INSERT OR REPLACE INTO files (id, kind, relative_path, mime_type, size_bytes, sha256, created_at, expires_at) VALUES (?,?,?,?,?,?,?,?)",
            (file_id, 'export', f"files/exports/{filename}", f"text/{format}", size, sha256, now, expires)
        )
        self.conn.commit()
        
        return {
            "file_id": file_id,
            "format": format,
            "content": content,
            "resource_uri": f"image2travel://files/{file_id}",
            "expires_at": expires,
        }
