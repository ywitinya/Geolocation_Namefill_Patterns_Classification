import sqlite3
import csv
import os


# --- Create Schema ---
schema = {
    "geo_names": """
        CREATE TABLE IF NOT EXISTS geo_names (
            geoid INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ascii_name TEXT,
            country_code TEXT,
            alternate_names TEXT
        );
    """,
    "un_locode_subdiv": """
        CREATE TABLE IF NOT EXISTS un_locode_subdiv (
            country_code TEXT,
            code TEXT,
            name TEXT,
            type TEXT,
            PRIMARY KEY(country_code, code)
        );
    """,
    "un_locode": """
        CREATE TABLE IF NOT EXISTS un_locode (
            country_code TEXT,
            locode TEXT,
            name TEXT,
            ascii_name TEXT,
            subdivision TEXT,
            coordinates TEXT,
            PRIMARY KEY(country_code, locode)
        );
    """,
    "directional_terms": """
        CREATE TABLE IF NOT EXISTS directional_terms (
            term TEXT PRIMARY KEY,
            category TEXT
        );
    """,
    "geo_classification_terms": """
    CREATE TABLE IF NOT EXISTS geo_classification_terms (
        keyword TEXT PRIMARY KEY,
        category TEXT,    -- e.g. 'continent', 'ocean', 'region', 'RIR', etc.
        description TEXT  -- free-text explanation
    );
    """

}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Build a comprehensive GeoNames + UN LOCODE SQLite database.")
    parser.add_argument("--db", default="geo_name_un_locode.db", help="Output SQLite database path (default: geo_name_un_locode.db)")
    parser.add_argument("--geonames", help="Path to GeoNames file (.txt)")
    parser.add_argument("--unlocode", nargs="+", help="Path(s) to UN LOCODE CSV files")
    parser.add_argument("--subdiv", nargs="+", help="Path(s) to UN LOCODE Subdivision CSV files")
    parser.add_argument("--skip-directional", action="store_true", help="Skip inserting directional terms")
    parser.add_argument("--skip-continents", action="store_true", help="Skip inserting continent keywords")

    args = parser.parse_args()
    DB_PATH = args.db

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Create schema
    for ddl in schema.values():
        c.execute(ddl)
    conn.commit()

    # --- Load GeoNames ---
    if args.geonames:
        path = args.geonames
        with open(path, 'r', encoding='latin-1') as f:
            count = 0
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 9:
                    continue

                name = parts[1].lower()
                asciiname = parts[2].lower()
                alternates = parts[3].strip()
                alternates = ','.join([alt.strip() for alt in parts[3].split(',') if alt.strip()])
                country = parts[8].strip()

                c.execute("""
                    INSERT OR IGNORE INTO geo_names (name, ascii_name, country_code, alternate_names)
                    VALUES (?, ?, ?, ?)
                """, (name, asciiname, country, alternates))
                count += 1
            print(f" Inserted {count} GeoNames entries.")

    # --- Load UN/LOCODE entries ---
    if args.unlocode:
        total = 0
        for path in args.unlocode:
            with open(path, 'r', encoding='latin-1') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) >= 12:
                        country = row[1].strip()
                        locode = row[2].strip()
                        name = row[3].strip()
                        ascii_name = row[4].strip()
                        subdiv = row[5].strip()
                        coordinates = row[10].strip()
                
                        c.execute("""
                            INSERT OR IGNORE INTO un_locode (country_code, locode, name, ascii_name, subdivision, coordinates)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (country, locode, name, ascii_name, subdiv, coordinates))
                        count += 1
                print(f" Inserted {count} UN/LOCODE entries from {path}")
                total += count
        print(f" Total UN/LOCODE rows: {total}")

    # --- Load UN/LOCODE Subdivision entries ---
    if args.subdiv:
        total = 0
        for path in args.subdiv:
            with open(path, 'r', encoding='latin-1') as f:
                reader = csv.reader(f)
                count = 0
                for row in reader:
                    if len(row) >= 4:
                        country = row[0].strip()
                        code = row[1].strip()
                        name = row[2].strip()
                        type_ = row[3].strip()
                        c.execute("""
                            INSERT OR IGNORE INTO un_locode_subdiv (country_code, code, name, type)
                            VALUES (?, ?, ?, ?)
                        """, (country, code, name, type_))
                        count += 1
                print(f" Inserted {count} subdivision entries from {path}")
                total += count
        print(f" Total subdivision entries: {total}")

    # --- hardcoded Tables ---
    if not args.skip_directional:
        direction_terms = [
            ('north', 'direction'), ('south', 'direction'), ('east', 'direction'), ('west', 'direction'),
            ('northeast', 'direction'), ('northwest', 'direction'),
            ('southeast', 'direction'), ('southwest', 'direction'),
            ('central', 'region'), ('midwest', 'region'), ('interior', 'region')
        ]
        c.executemany("INSERT OR IGNORE INTO directional_terms (term, category) VALUES (?, ?)", direction_terms)
        print(" Inserted directional terms.")

    if not args.skip_continents:
        classification_terms = [
            ('africa', 'continent', 'African continent'),
            ('europe', 'continent', 'European continent'),
            ('asia', 'continent', 'Asian continent'),
            ('america', 'continent', 'North or South America'),
            ('oceania', 'continent', 'Australia, NZ, and surrounding islands'),
            ('antarctica', 'continent', 'Antarctic continent'),
            
            ('atlantic', 'ocean', 'Atlantic Ocean region'),
            ('pacific', 'ocean', 'Pacific Ocean region'),
            ('indian', 'ocean', 'Indian Ocean region'),

            ('apnic', 'RIR', 'Asia-Pacific Network Information Centre'),
            ('arin', 'RIR', 'American Registry for Internet Numbers'),
            ('ripe', 'RIR', 'Réseaux IP Européens Network Coordination Centre'),
            ('lacnic', 'RIR', 'Latin America and Caribbean Network Information Centre'),
            ('afnic', 'RIR', 'French Network Information Centre'),

            ('eastafrica', 'region', 'Eastern African region'),
            ('westafrica', 'region', 'Western African region'),
            ('middleeast', 'region', 'Middle Eastern region'),
            ('caribbean', 'region', 'Caribbean island group'),

            # amazon regions ---
            ('me', 'aws-region', 'Middle Eastern region'),
            ('af', 'aws-region', 'African continent'),
            ('eu', 'aws-region', 'European continent'),
            ('ap', 'aws-region', 'Asia Pacific continent'),
            ('ca', 'aws-region', 'Canada Northern America'),
            ('il', 'aws-region', 'Israel Middle East'),
            ('sa', 'aws-region', 'South American continent'),
            ('mx', 'aws-region', 'Mexico Northern America'),
            ('us', 'aws-region', 'US region North America')
        ]

        c.executemany("""
            INSERT OR IGNORE INTO geo_classification_terms (keyword, category, description)
            VALUES (?, ?, ?)
        """, classification_terms)


    conn.commit()
    conn.close()

    print(f"\n Finished. Database saved at: {DB_PATH}")
