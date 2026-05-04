# Global Patent Intelligence Data Pipeline

A complete data pipeline that ingests PatentsView TSV data, cleans it with
pandas, stores it in SQLite, and generates analytical reports.

---

## Project Structure

patent-pipeline/
├── data/
│   ├── raw/          ← place downloaded TSV files here
│   └── clean/        ← auto-generated cleaned CSVs
├── scripts/
│   ├── ingest.py     ← Step 1: clean & process TSV files
│   ├── load_db.py    ← Step 2: load into SQLite
│   └── report.py     ← Step 3: generate reports
├── sql/
│   ├── schema.sql    ← table definitions
│   └── queries.sql   ← all 7 analytical queries
├── outputs/          ← CSV and JSON reports saved here
├── patents.db        ← SQLite database (auto-created)
├── requirements.txt
└── README.md
```

## Getting the Data

1. Go to: https://data.uspto.gov/bulkdata/datasets/pvgpatdis
2. Download these TSV files:
   - `g_patent.tsv` — patent ID, title, date, type
   - `g_patent_abstract.tsv` — patent abstracts (separate file!)
   - `g_inventor_disambiguated.tsv` — inventors + location_id
   - `g_location_disambiguated.tsv` — location_id → country mapping
   - `g_assignee_disambiguated.tsv` — companies/assignees (also has patent↔assignee links)
   

## Running the Pipeline
Run all three steps in order:

```bash
# Step 1 — Clean the data
python scripts/ingest.py

# Step 2 — Load into SQLite database
python scripts/load_db.py

# Step 3 — Generate all reports
python scripts/report.py
```

---

## Outputs

| File | Description |
| `data/clean/clean_patents.csv` | Cleaned patent records |
| `data/clean/clean_inventors.csv` | Cleaned inventor records |
| `data/clean/clean_companies.csv` | Cleaned company records |
| `patents.db` | SQLite database with all tables |
| `outputs/top_inventors.csv` | Top 20 inventors by patent count |
| `outputs/top_companies.csv` | Top 20 companies by patent count |
| `outputs/country_trends.csv` | Patent counts by country |
| `outputs/yearly_trends.csv` | Patent counts by year |
| `outputs/patent_report.json` | Full JSON report |

---

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
