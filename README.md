# Global Patent Intelligence Data Pipeline

A complete data pipeline that ingests PatentsView TSV data, cleans it with pandas, stores it in SQLite, and generates analytical reports.

---

## Project Structure

patent-pipeline/
data/
 raw/        - place downloaded TSV files here
 clean/      - auto-generated cleaned CSVs
scripts/
 ingest.py    - Step 1: clean & process TSV files
 load_db.py   -  Step 2: load into SQLite
 report.py    -  Step 3: generate reports
sql/
 schema.sql   - table definitions
 queries.sql  - all 7 analytical queries
outputs/  
 charts        
 CSV and JSON reports saved here
patents.db  - SQLite database (auto-created)
requirements.txt
README.md


## Getting the Data

1. Download from: https://data.uspto.gov/bulkdata/datasets/pvgpatdis
2. Download these TSV files:
   - `g_patent.tsv` 
   - `g_patent_abstract.tsv` 
   - `g_inventor_disambiguated.tsv` 
   - `g_location_disambiguated.tsv`
   - `g_assignee_disambiguated.tsv` 
   

## Running the Pipeline
Run all three steps in order:

# Step 1 — Clean the data
python scripts/ingest.py

# Step 2 — Load into SQLite database
python scripts/load_db.py

# Step 3 — Generate all reports
python scripts/report.py

---

## Outputs

### Cleaned Data
- `data/clean/clean_patents.csv` 
- `data/clean/clean_inventors.csv` 
- `data/clean/clean_companies.csv` 

### Database
- `patents.db` — SQLite database with all processed data

### Analytical Reports (CSV)
- `outputs/top_inventors.csv` — Top inventors by patent count
- `outputs/top_companies.csv` — Top companies by patent count
- `outputs/country_trends.csv` — Patent trends by country
- `outputs/yearly_trends.csv` — Patent trends by year
- `outputs/category_trends.csv` — Technology category trends
- `outputs/category_summary.csv` — Category distribution summary
- `outputs/emerging_tech_growth.csv` — Emerging technology growth metrics

### Reports (JSON)
- `outputs/patent_report.json` — Comprehensive patent analysis report

### Visualizations (PNG Charts)
- `outputs/charts/top_inventors.png` — Top inventors bar chart
- `outputs/charts/top_companies.png` — Top companies bar chart
- `outputs/charts/top_companies_by_category.png` — Companies by technology category
- `outputs/charts/top_countries.png` — Patents by country
- `outputs/charts/country_heatmap.png` — Country patent heatmap
- `outputs/charts/patents_per_year.png` — Patent filings over time
- `outputs/charts/yearly_trends.png` — Year-over-year trend analysis
- `outputs/charts/rolling_average.png` — Patent filing rolling average
- `outputs/charts/category_breakdown.png` — Technology category breakdown
- `outputs/charts/emerging_tech_growth.png` — Emerging tech growth visualization 


## SQL Queries

All 7 required queries are in `sql/queries.sql`:

| Query | Description |
|-------|-------------|
| Q1 | Top inventors by patent count |
| Q2 | Top companies by patent count |
| Q3 | Top countries with share % |
| Q4 | Patents per year (1976–2025) |
| Q5 | JOIN: patents + inventors + companies |
| Q6 | CTE: above-average inventors |
| Q7 | RANK: inventors ranked within each country (window functions) |

---

## Technologies Used

- **Python** — data ingestion and pipeline orchestration
- **pandas** — data cleaning and transformation
- **SQLite** — relational database storage
- **SQL** — analytical queries including CTEs and window functions
- **GitHub** — version control
