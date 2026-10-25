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
    
    # Countries
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("country_si", "country", "active", now, now))
    conn.execute("INSERT OR IGNORE INTO countries (entity_id, iso2, name, default_currency) VALUES (?,?,?,?)", 
                 ("country_si", "SI", "Slovenia", "EUR"))
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("country_hr", "country", "active", now, now))
    conn.execute("INSERT OR IGNORE INTO countries (entity_id, iso2, name, default_currency) VALUES (?,?,?,?)", 
                 ("country_hr", "HR", "Croatia", "EUR"))
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("country_at", "country", "active", now, now))
    conn.execute("INSERT OR IGNORE INTO countries (entity_id, iso2, name, default_currency) VALUES (?,?,?,?)", 
                 ("country_at", "AT", "Austria", "EUR"))
    
    # Destinations
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("dest_001", "destination", "active", now, now))
    conn.execute("""INSERT OR REPLACE INTO destinations 
        (entity_id, slug, name, country_id, region, lat, lon, timezone, bbox_json, 
         summary, experience_json, visual_json, anti_features_json, 
         min_trip_days, max_trip_days, taxonomy_version, editorial_reviewed_at) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 ("dest_001", "lake-bled", "Lake Bled", "country_si", "Upper Carniola",
                  46.3683, 14.1147, "Europe/Ljubljana", None,
                  "Alpine lake with island church, accessible hikes, peaceful walks",
                  json.dumps({"emotions": ["calm", "awe"], "pace": "slow", "effort": "easy"}),
                  json.dumps({"landscape": ["lake", "mountain", "forest"], "palette": ["blue", "green"]}),
                  json.dumps([]), 1, 7, "1.0", now))
    
    for m in range(1, 13):
        conn.execute("INSERT OR REPLACE INTO destination_months (destination_id, month, season_score, crowd_score, availability) VALUES (?,?,?,?,?)",
                     ("dest_001", m, 0.85 if m in [5,6,9,10] else 0.65, 0.4 if m in [4,5,10,11] else 0.7, "open"))
    
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("dest_002", "destination", "active", now, now))
    conn.execute("""INSERT OR REPLACE INTO destinations 
        (entity_id, slug, name, country_id, region, lat, lon, timezone, bbox_json, 
         summary, experience_json, visual_json, anti_features_json, 
         min_trip_days, max_trip_days, taxonomy_version, editorial_reviewed_at) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 ("dest_002", "plitvice-lakes", "Plitvice Lakes", "country_hr", "Lika-Senj",
                  44.8654, 15.5820, "Europe/Zagreb", None,
                  "Terraced lakes with wooden walkways through forest",
                  json.dumps({"emotions": ["awe"], "pace": "moderate", "effort": "moderate"}),
                  json.dumps({"landscape": ["forest", "river", "lake"], "palette": ["green", "turquoise"]}),
                  json.dumps([]), 1, 7, "1.0", now))
    for m in range(1, 13):
        conn.execute("INSERT OR REPLACE INTO destination_months (destination_id, month, season_score, crowd_score, availability) VALUES (?,?,?,?,?)",
                     ("dest_002", m, 0.9 if m in [5,6,9] else 0.6, 0.8 if m in [6,7,8] else 0.4, "open"))
    
    conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)", 
                 ("dest_003", "destination", "active", now, now))
    conn.execute("""INSERT OR REPLACE INTO destinations 
        (entity_id, slug, name, country_id, region, lat, lon, timezone, bbox_json, 
         summary, experience_json, visual_json, anti_features_json, 
         min_trip_days, max_trip_days, taxonomy_version, editorial_reviewed_at) 
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                 ("dest_003", "hallstatt", "Hallstatt", "country_at", "Salzkammergut",
                  47.5622, 13.6493, "Europe/Vienna", None,
                  "Historic lakeside village with mountain backdrop",
                  json.dumps({"emotions": ["nostalgia", "awe"], "pace": "slow", "effort": "easy"}),
                  json.dumps({"landscape": ["lake", "mountain", "village"], "palette": ["blue", "grey"]}),
                  json.dumps([]), 1, 5, "1.0", now))
    for m in range(1, 13):
        conn.execute("INSERT OR REPLACE INTO destination_months (destination_id, month, season_score, crowd_score, availability) VALUES (?,?,?,?,?)",
                     ("dest_003", m, 0.8 if m in [5,6,9,10] else 0.7, 0.9 if m in [6,7,8] else 0.5, "open"))
    
    # POIs
    for i, (pid, name, cat, did) in enumerate([
        ("poi_001", "Bled Island", "viewpoint", "dest_001"),
        ("poi_002", "Ojstrica Viewpoint", "hike", "dest_001"),
        ("poi_003", "Vintgar Gorge", "walk", "dest_001"),
        ("poi_004", "Velika Slap", "waterfall", "dest_002"),
        ("poi_005", "Hallstatt Skywalk", "viewpoint", "dest_003"),
    ]):
        conn.execute("INSERT OR IGNORE INTO entities (id, kind, status, created_at, updated_at) VALUES (?,?,?,?,?)",
                     (pid, "poi", "active", now, now))
        conn.execute("""INSERT OR REPLACE INTO pois 
            (entity_id, name, category, lat, lon, coordinate_kind, duration_min, effort, osm_tags_json)
            VALUES (?,?,?,?,?,?,?,?,?)""",
                     (pid, name, cat, None, None, "unknown", 60, "easy", "{}"))
        conn.execute("INSERT OR IGNORE INTO destination_pois (destination_id, poi_id, role, priority) VALUES (?,?,?,?)",
                     (did, pid, "anchor" if i < 2 else "optional", 10-i))
    
    # Prices
    conn.execute("INSERT OR IGNORE INTO currencies (code, minor_units) VALUES (?,?)", ("EUR", 2))
    for did in ["dest_001", "dest_002", "dest_003"]:
        conn.execute("""INSERT OR IGNORE INTO price_estimates 
            (id, entity_id, category, travel_style, currency, low_minor, high_minor, basis, method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
                     (f"pe_{did}_lodging_mid", did, "lodging", "mid", "EUR", 5000, 8000, "room_night", "seed"))
        conn.execute("""INSERT OR IGNORE INTO price_estimates 
            (id, entity_id, category, travel_style, currency, low_minor, high_minor, basis, method)
            VALUES (?,?,?,?,?,?,?,?,?)""",
                     (f"pe_{did}_food_mid", did, "food", "mid", "EUR", 2500, 4000, "person_day", "seed"))
    
    conn.commit()
    print("Seed complete")


def data_check():
    from ..data_check import DataChecker
    checker = DataChecker()
    result = checker.check()
    print(f"Destinations: {result['destinations']}")
    print(f"POIs: {result['pois']}")
    print(f"Claims: {result['claims']}")
    if result['issues']:
        for issue in result['issues']:
            print(f"ISSUE: {issue}")
    print("Data check complete")
    return result


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
