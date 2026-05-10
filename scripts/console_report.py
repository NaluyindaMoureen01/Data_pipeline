"""
console_report.py — Global Patent Intelligence Data Pipeline
============================================================
Generates a summary report of the processed patent data.
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "patents.db"

def generate_report():
    print("="*60)
    print("      GLOBAL PATENT INTELLIGENCE - PIPELINE REPORT")
    print(f"      Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        
        # 1. Pipeline Summary
        print("\n[1] PIPELINE SUMMARY")
        print("-" * 20)
        
        total_patents = pd.read_sql("SELECT COUNT(*) FROM patents", conn).iloc[0,0]
        total_inventors = pd.read_sql("SELECT COUNT(*) FROM inventors", conn).iloc[0,0]
        total_companies = pd.read_sql("SELECT COUNT(*) FROM companies", conn).iloc[0,0]
        year_range = pd.read_sql("SELECT MIN(year), MAX(year) FROM patents", conn).iloc[0]
        
        print(f"Total Patents Indexed   : {total_patents:,}")
        print(f"Total Inventors Found   : {total_inventors:,}")
        print(f"Total Companies Found   : {total_companies:,}")
        print(f"Data Coverage Range     : {int(year_range[0])} - {int(year_range[1])}")
        
        # 2. Top Countries
        print("\n[2] TOP 10 COUNTRIES (By Patent Count)")
        print("-" * 40)
        countries = pd.read_sql("""
            SELECT i.country, COUNT(DISTINCT r.patent_id) as patents
            FROM relationships r
            JOIN inventors i ON r.inventor_id = i.inventor_id
            WHERE i.country != '' AND i.country != 'Unknown'
            GROUP BY i.country ORDER BY patents DESC LIMIT 10
        """, conn)
        
        for i, row in countries.iterrows():
            print(f"{i+1:2}. {row['country']:15} : {row['patents']:,} patents")
            
        # 3. Top Companies
        print("\n[3] TOP 5 ASSIGNEES (Companies)")
        print("-" * 40)
        companies = pd.read_sql("""
            SELECT c.name, COUNT(DISTINCT r.patent_id) as patents
            FROM relationships r
            JOIN companies c ON r.company_id = c.company_id
            GROUP BY c.name ORDER BY patents DESC LIMIT 5
        """, conn)
        
        for i, row in companies.iterrows():
            print(f"{i+1:2}. {row['name'][:30]:30} : {row['patents']:,} patents")
            
        print("\n" + "="*60)
        print("      PIPELINE STATUS: SUCCESSFUL ")
        print("="*60)
        
        conn.close()
        
    except Exception as e:
        print(f"\nERROR GENERATING REPORT: {e}")

if __name__ == "__main__":
    generate_report()
