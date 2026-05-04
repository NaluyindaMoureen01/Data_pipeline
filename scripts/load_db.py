"""
load_db.py

Loads cleaned CSV files into a SQLite database (patents.db).
Creates the schema first, then bulk-inserts all rows.
"""

import os
import sqlite3
import pandas as pd

CLEAN_DIR = "data/clean"
DB_PATH   = "patents.db"

ROW_LIMIT = 500_000  # For testing, set to None to load all rows

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    # Performance tweaks for bulk inserts
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.execute("PRAGMA cache_size=-64000")   # 64 MB cache
    conn.execute("PRAGMA temp_store=MEMORY")
    return conn


def create_schema(conn):
    """Create all tables from scratch (drop if exist for reproducibility)."""
    print("Creating database schema ...")
    cursor = conn.cursor()

    cursor.executescript("""
        PRAGMA journal_mode=WAL;

        DROP TABLE IF EXISTS relationships;
        DROP TABLE IF EXISTS patents;
        DROP TABLE IF EXISTS inventors;
        DROP TABLE IF EXISTS companies;

        CREATE TABLE patents (
            patent_id   TEXT PRIMARY KEY,
            title       TEXT,
            abstract    TEXT,
            filing_date TEXT,
            year        INTEGER
        );

        CREATE TABLE inventors (
            inventor_id TEXT PRIMARY KEY,
            name        TEXT,
            country     TEXT
        );

        CREATE TABLE companies (
            company_id  TEXT PRIMARY KEY,
            name        TEXT
        );

        CREATE TABLE relationships (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            patent_id   TEXT,
            inventor_id TEXT,
            company_id  TEXT,
            FOREIGN KEY (patent_id)   REFERENCES patents(patent_id),
            FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
            FOREIGN KEY (company_id)  REFERENCES companies(company_id)
        );

        CREATE INDEX idx_rel_patent   ON relationships(patent_id);
        CREATE INDEX idx_rel_inventor ON relationships(inventor_id);
        CREATE INDEX idx_rel_company  ON relationships(company_id);
        CREATE INDEX idx_patents_year ON patents(year);
    """)
    conn.commit()
    print("  → Schema created.")


def load_table(conn, csv_file, table_name, chunksize=50_000):
    """Load a CSV into a SQLite table in chunks."""
    path = os.path.join(CLEAN_DIR, csv_file)
    if not os.path.exists(path):
        print(f"  {csv_file} not found  skipping.")
        return

    print(f"Loading {csv_file} → {table_name} ...")
    total = 0
    rows_left  = ROW_LIMIT

    for chunk in pd.read_csv(path, dtype=str, chunksize=chunksize):
        # Trim chunk if we're about to exceed the limit
        if rows_left is not None:
            if rows_left <= 0:
                break
            if len(chunk) > rows_left:
                chunk = chunk.iloc[:rows_left]

        # Convert year column to numeric if present
        if "year" in chunk.columns:
            chunk["year"] = pd.to_numeric(chunk["year"], errors="coerce")

        chunk.to_sql(table_name, conn, if_exists="append", index=False)
        total += len(chunk)

        if rows_left is not None:
            rows_left -= len(chunk)

            limit_str = f"/{ROW_LIMIT:,}" if ROW_LIMIT else ""
        print(f"    {total:>10,}{limit_str} rows inserted ...", end="\r")

    conn.commit()
    print(f"  → Inserted {total:,} rows into {table_name}.")


if __name__ == "__main__":
    print("\n DATABASE LOADING \n")

    if ROW_LIMIT:
        print(f"  ROW_LIMIT = {ROW_LIMIT:,} (edit load_db.py to change)\n")
    else:
        print("   ROW_LIMIT = None — loading full dataset \n")
    conn = get_connection()

    create_schema(conn)
    load_table(conn, "clean_patents.csv",       "patents")
    load_table(conn, "clean_inventors.csv",     "inventors")
    load_table(conn, "clean_companies.csv",     "companies")
    load_table(conn, "clean_relationships.csv", "relationships")

    conn.close()
    print(f"\n Database ready at {DB_PATH}\n")
