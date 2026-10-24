"""CLI for ingestion/seed."""
import argparse
import json
from ..db import init_db


def seed(dry_run=False):
    """Seed database with initial data."""
    print(f"Seeding (dry_run={dry_run})...")
    conn = init_db()
    from datetime import datetime
    now = datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("country_si", "country", "active", now, now))
    conn.execute("INSERT OR IGNORE INTO countries (entity_id, iso2, name) VALUES (?,?,?)", 
                 ("country_si", "SI", "Slovenia"))
    
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("dest_001", "destination", "active", now, now))
    conn.execute("""INSERT OR IGNORE INTO destinations 
        (entity_id, slug, name, country_id, region, lat, lon, timezone, bbox_json, 
         summary, experience_json, visual_json, anti_features_json, 
         min_trip_days, max_trip_days, taxonomy_version, editorial_reviewed_at) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 ("dest_001", "lake-bled", "Lake Bled", "country_si", "Upper Carniola",
                  46.3683, 14.1147, "Europe/Ljubljana", None,
                  "Alpine lake with island church, peaceful atmosphere",
                  json.dumps({"emotions": ["calm"], "pace": "slow"}),
                  json.dumps({"landscape": ["lake", "mountain"], "palette": ["blue", "green"]}),
                  json.dumps([]), 1, 7, "1.0", now))
    
    for m in range(1, 13):
        conn.execute("INSERT OR IGNORE INTO destination_months (destination_id, month, season_score, crowd_score, availability) VALUES (?,?,?,?,?)",
                     ("dest_001", m, 0.8 if m in [5,6,9,10] else 0.6, 0.5, "open"))
    
    conn.commit()
    print("Seed complete")


def data_check():
    print("Running data check...")
    conn = init_db()
    cur = conn.execute("SELECT COUNT(*) as c FROM destinations")
    print(f"Destinations: {cur.fetchone()['c']}")
    cur = conn.execute("SELECT COUNT(*) as c FROM pois")
    print(f"POIs: {cur.fetchone()['c']}")
    print("Data check complete")


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    sp_seed = subparsers.add_parser('seed')
    sp_seed.add_argument('--dry-run', action='store_true')
    subparsers.add_parser('data-check')
    
    args = parser.parse_args()
    if args.command == 'seed':
        seed(getattr(args, 'dry_run', False))
    elif args.command == 'data-check':
        data_check()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
