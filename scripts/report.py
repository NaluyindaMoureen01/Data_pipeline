"""
report.py

Reads from patents.db and generates:
  1. Console report (terminal output)
  2. CSV exports  → outputs/top_inventors.csv
                  → outputs/top_companies.csv
                  → outputs/country_trends.csv
  3. JSON report  → outputs/patent_report.json
"""

import os
import json
import sqlite3
import pandas as pd

DB_PATH    = "patents.db"
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_conn():
    return sqlite3.connect(DB_PATH)


# QUERIES

def query_total_patents(conn):
    return pd.read_sql("SELECT COUNT(*) AS total FROM patents", conn).iloc[0, 0]


def query_top_inventors(conn, limit=20):
    sql = """
        SELECT i.name, i.country,
               COUNT(DISTINCT r.patent_id) AS patent_count
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
        GROUP BY i.inventor_id
        ORDER BY patent_count DESC
        LIMIT ?
    """
    return pd.read_sql(sql, conn, params=(limit,))


def query_top_companies(conn, limit=20):
    sql = """
        SELECT c.name,
               COUNT(DISTINCT r.patent_id) AS patent_count
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        WHERE r.company_id != ''
        GROUP BY c.company_id
        ORDER BY patent_count DESC
        LIMIT ?
    """
    return pd.read_sql(sql, conn, params=(limit,))


def query_top_countries(conn, limit=20):
    sql = """
        SELECT i.country,
               COUNT(DISTINCT r.patent_id) AS patent_count,
               ROUND(
                   100.0 * COUNT(DISTINCT r.patent_id) /
                   (SELECT COUNT(DISTINCT patent_id)
                    FROM relationships WHERE inventor_id != ''), 2
               ) AS share_pct
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
          AND i.country != 'Unknown'
        GROUP BY i.country
        ORDER BY patent_count DESC
        LIMIT ?
    """
    return pd.read_sql(sql, conn, params=(limit,))


def query_yearly_trends(conn):
    sql = """
        SELECT year, COUNT(*) AS patent_count
        FROM patents
        WHERE year IS NOT NULL AND year BETWEEN 1976 AND 2025
        GROUP BY year
        ORDER BY year
    """
    return pd.read_sql(sql, conn)


# REPORT A: CONSOLE

def print_console_report(total, inventors, companies, countries, trends):
    banner = "=" * 55

    print(f"\n{banner}")
    print(" " * 15 + "PATENT INTELLIGENCE REPORT")
    print(f"{banner}\n")

    print(f"  Total Patents in Database:  {total:,}\n")

    # Top Inventors
    print("  TOP 10 INVENTORS")
    print("  " + "-" * 40)
    for i, row in inventors.head(10).iterrows():
        rank = i + 1
        print(f"  {rank:>2}. {row['name']:<35} {row['patent_count']:>6} patents  [{row['country']}]")

    print()

    # Top Companies
    print("  TOP 10 COMPANIES")
    print("  " + "-" * 40)
    for i, row in companies.head(10).iterrows():
        rank = i + 1
        print(f"  {rank:>2}. {row['name']:<35} {row['patent_count']:>6} patents")

    print()

    # Top Countries
    print("  TOP 10 COUNTRIES")
    print("  " + "-" * 40)
    for i, row in countries.head(10).iterrows():
        rank = i + 1
        print(f"  {rank:>2}. {row['country']:<10}  {row['patent_count']:>8} patents  ({row['share_pct']}%)")

    print()

    # Yearly trend summary
    if not trends.empty:
        recent = trends[trends["year"] >= 2015]
        if not recent.empty:
            peak_row = recent.loc[recent["patent_count"].idxmax()]
            print(f"  RECENT TREND  (2015–2025)")
            print("  " + "-" * 40)
            print(f"  Peak year: {int(peak_row['year'])} with {int(peak_row['patent_count']):,} patents")
            print(f"  Latest year in data: {int(trends['year'].max())}")

    print(f"\n{banner}\n")


# REPORT B: CSV EXPORTS

def export_csvs(inventors, companies, countries, trends):
    inv_path = os.path.join(OUTPUT_DIR, "top_inventors.csv")
    com_path = os.path.join(OUTPUT_DIR, "top_companies.csv")
    ctr_path = os.path.join(OUTPUT_DIR, "country_trends.csv")
    yr_path  = os.path.join(OUTPUT_DIR, "yearly_trends.csv")

    inventors.to_csv(inv_path, index=False)
    companies.to_csv(com_path, index=False)
    countries.to_csv(ctr_path, index=False)
    trends.to_csv(yr_path, index=False)

    print(f"  CSV exports saved:")
    print(f"    {inv_path}")
    print(f"    {com_path}")
    print(f"    {ctr_path}")
    print(f"    {yr_path}")


# REPORT C: JSON

def export_json(total, inventors, companies, countries, trends):
    report = {
        "total_patents": int(total),
        "top_inventors": [
            {
                "rank":         i + 1,
                "name":         row["name"],
                "country":      row["country"],
                "patent_count": int(row["patent_count"])
            }
            for i, row in inventors.head(20).iterrows()
        ],
        "top_companies": [
            {
                "rank":         i + 1,
                "name":         row["name"],
                "patent_count": int(row["patent_count"])
            }
            for i, row in companies.head(20).iterrows()
        ],
        "top_countries": [
            {
                "country":      row["country"],
                "patent_count": int(row["patent_count"]),
                "share_pct":    float(row["share_pct"])
            }
            for _, row in countries.iterrows()
        ],
        "yearly_trends": [
            {
                "year":         int(row["year"]),
                "patent_count": int(row["patent_count"])
            }
            for _, row in trends.iterrows()
        ]
    }

    json_path = os.path.join(OUTPUT_DIR, "patent_report.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"  JSON report saved: {json_path}")
    return report


# MAIN

if __name__ == "__main__":
    print("\n Connecting to database ...")
    conn = get_conn()

    print("Running queries ...")
    total     = query_total_patents(conn)
    inventors = query_top_inventors(conn)
    companies = query_top_companies(conn)
    countries = query_top_countries(conn)
    trends    = query_yearly_trends(conn)

    conn.close()

    # Console report
    print_console_report(total, inventors, companies, countries, trends)

    # CSV exports
    print("Exporting CSVs ...")
    export_csvs(inventors, companies, countries, trends)

    # JSON export
    print("Exporting JSON ...")
    export_json(total, inventors, companies, countries, trends)

    print("\n All reports generated successfully.\n")
