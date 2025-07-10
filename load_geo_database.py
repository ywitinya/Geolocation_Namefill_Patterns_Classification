import sqlite3
from collections import defaultdict
from NaryTree import (NaryTree, MatchNode)


def connect_geo_db(db_path="geo_name_un_locode.db"):
    """Connect to the SQLite geo database."""
    return sqlite3.connect(db_path)


def load_geo_names(cursor, country_iso):
    """
    Load GeoNames entries for a given country code.
    Returns a list of dicts with name, ascii, and alternates set.
    """
    cursor.execute("""
        SELECT name, ascii_name, alternate_names 
        FROM geo_names 
        WHERE country_code = ?;
    """, (country_iso,))
    
    results = []
    for name, ascii_name, alternates in cursor.fetchall():
        alt_set = set(a.strip().lower() for a in alternates.split(',') if a.strip()) if alternates else set()
        results.append({
            'name': name.lower(),
            'ascii': ascii_name.lower(),
            'alternates': alt_set
        })
    return results


def load_un_locode(cursor, country_iso):
    """
    Load UN LOCODE city-level data for a given country.
    Returns a list of dicts.
    """
    cursor.execute("""
        SELECT locode, name, ascii_name 
        FROM un_locode 
        WHERE country_code = ?;
    """, (country_iso,))
    
    return [
        {
            'locode': row[0].strip().lower(),
            'name': row[1].strip().lower(),
            'ascii': row[2].strip().lower()
        }
        for row in cursor.fetchall()
    ]


def load_un_locode_subdiv(cursor, country_iso):
    """
    Load UN LOCODE subdivision-level data for a given country.
    Returns a list of dicts.
    """
    cursor.execute("""
        SELECT code, name, type 
        FROM un_locode_subdiv 
        WHERE country_code = ?;
    """, (country_iso,))
    
    return [
        {
            'code': row[0].strip().lower(),
            'name': row[1].strip().lower(),
            'type': row[2].strip().lower()
        }
        for row in cursor.fetchall()
    ]


def load_directional_terms(cursor):
    """
    Load global directional/region terms (e.g., 'east', 'central').
    Returns a flat set of lowercase terms.
    """
    cursor.execute("SELECT term FROM directional_terms;")
    return set(row[0].strip().lower() for row in cursor.fetchall())


def load_geo_classification_terms(cursor):
    """
    Load general geo-classification terms (e.g., 'afnic', 'apnic', 'atlantic').
    Returns a flat set of lowercase keywords.
    """
    cursor.execute("SELECT keyword FROM geo_classification_terms;")
    return set(row[0].strip().lower() for row in cursor.fetchall())

if __name__ == "__main__":
    conn = connect_geo_db()
    c = conn.cursor()
    
    iso = "ZW"  # Example ISO country code

    geo_names = load_geo_names(c, iso)
    unlocode = load_un_locode(c, iso)
    subdivs = load_un_locode_subdiv(c, iso)
    directionals = load_directional_terms(c)
    geo_keywords = load_geo_classification_terms(c)

    # print(f"GeoNames: {len(geo_names)} entries")
    # print(f"UN LOCODE: {len(unlocode)} entries")
    # print(f"Subdivs: {len(subdivs)} entries")
    # print(f"Directional terms: {directionals}")
    # print(f"Classification terms: {geo_keywords}")
    
    conn.close()
