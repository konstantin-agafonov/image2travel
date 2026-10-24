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
    
    migration_path = Path(__file__).parent / "data" / "migrations" / "001_initial.sql"
    if migration_path.exists():
        with open(migration_path) as f:
            conn.executescript(f.read())
    else:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS entities (
          id TEXT PRIMARY KEY,
          kind TEXT NOT NULL CHECK (kind IN ('country', 'destination', 'poi')),
          status TEXT NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'active', 'retired')),
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS countries (
          entity_id TEXT PRIMARY KEY REFERENCES entities(id),
          iso2 TEXT NOT NULL UNIQUE CHECK (length(iso2) = 2),
          name TEXT NOT NULL,
          default_currency TEXT
        );
        CREATE TABLE IF NOT EXISTS destinations (
          entity_id TEXT PRIMARY KEY REFERENCES entities(id),
          slug TEXT NOT NULL UNIQUE,
          name TEXT NOT NULL,
          country_id TEXT NOT NULL REFERENCES countries(entity_id),
          region TEXT,
          lat REAL NOT NULL CHECK (lat BETWEEN -90 AND 90),
          lon REAL NOT NULL CHECK (lon BETWEEN -180 AND 180),
          timezone TEXT NOT NULL,
          bbox_json TEXT CHECK (bbox_json IS NULL OR json_valid(bbox_json)),
          summary TEXT NOT NULL,
          experience_json TEXT NOT NULL CHECK (json_valid(experience_json)),
          visual_json TEXT NOT NULL CHECK (json_valid(visual_json)),
          anti_features_json TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(anti_features_json)),
          min_trip_days INTEGER NOT NULL DEFAULT 1 CHECK (min_trip_days >= 1),
          max_trip_days INTEGER NOT NULL DEFAULT 7 CHECK (max_trip_days >= min_trip_days),
          taxonomy_version TEXT NOT NULL DEFAULT '1.0',
          editorial_reviewed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS destination_months (
          destination_id TEXT NOT NULL REFERENCES destinations(entity_id),
          month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
          season_score REAL CHECK (season_score BETWEEN 0 AND 1),
          crowd_score REAL CHECK (crowd_score BETWEEN 0 AND 1),
          availability TEXT NOT NULL DEFAULT 'unknown'
            CHECK (availability IN ('open', 'limited', 'closed', 'unknown')),
          note TEXT,
          PRIMARY KEY (destination_id, month)
        );
        CREATE TABLE IF NOT EXISTS pois (
          entity_id TEXT PRIMARY KEY REFERENCES entities(id),
          name TEXT NOT NULL,
          category TEXT NOT NULL,
          lat REAL CHECK (lat BETWEEN -90 AND 90),
          lon REAL CHECK (lon BETWEEN -180 AND 180),
          coordinate_kind TEXT NOT NULL DEFAULT 'unknown'
            CHECK (coordinate_kind IN ('entrance', 'point', 'representative', 'unknown')),
          duration_min INTEGER CHECK (duration_min > 0),
          effort TEXT CHECK (effort IN ('easy', 'moderate', 'hard', 'unknown')),
          osm_tags_json TEXT NOT NULL DEFAULT '{}' CHECK (json_valid(osm_tags_json))
        );
        CREATE TABLE IF NOT EXISTS destination_pois (
          destination_id TEXT NOT NULL REFERENCES destinations(entity_id),
          poi_id TEXT NOT NULL REFERENCES pois(entity_id),
          role TEXT NOT NULL DEFAULT 'optional'
            CHECK (role IN ('anchor', 'optional', 'backup', 'logistics')),
          priority INTEGER NOT NULL DEFAULT 0,
          PRIMARY KEY (destination_id, poi_id)
        );
        """)
    conn.commit()
    return conn
