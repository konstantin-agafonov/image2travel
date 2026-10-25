"""Database setup and migrations."""
import sqlite3
import os
from pathlib import Path


def get_data_dir() -> Path:
    data_dir = os.environ.get("IMAGE2TRAVEL_DATA_DIR", "./data")
    path = Path(data_dir)
    path.mkdir(parents=True, exist_ok=True)
    (path / "files" / "exports").mkdir(parents=True, exist_ok=True)
    (path / "files" / "tmp").mkdir(parents=True, exist_ok=True)
    (path / "raw").mkdir(parents=True, exist_ok=True)
    (path / "reports").mkdir(parents=True, exist_ok=True)
    return path


def get_db_path() -> Path:
    return get_data_dir() / "image2travel.db"


def init_db():
    db_path = get_db_path()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    
    migrations_dir = Path(__file__).parent / "data" / "migrations"
    if migrations_dir.exists():
        for mig in sorted(migrations_dir.glob("*.sql")):
            try:
                with open(mig) as f:
                    conn.executescript(f.read())
            except Exception as e:
                # Continue on migration errors for compatibility
                pass
    else:
        migration_path = migrations_dir / "001_initial.sql"
        if migration_path.exists():
            with open(migration_path) as f:
                conn.executescript(f.read())
    conn.commit()
    return conn
