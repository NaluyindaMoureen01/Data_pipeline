# Global Patent Intelligence Data Pipeline

A high-performance data pipeline and interactive analytics dashboard for processing and visualizing global patent trends. This project ingests PatentsView TSV data, cleans it using pandas, stores it in a optimized SQLite database, and provides both a console-based reporting tool and a premium Streamlit dashboard.

---

##  Key Features

- **End-to-End Pipeline**: From raw TSV ingestion to relational database storage.
- **Interactive Dashboard**: Premium UI with real-time filtering, geographic maps, and trend analysis.
- **Console Reporting**: Instant validation and summary statistics via command line.
- **Advanced SQL**: Utilizes CTEs, Window Functions, and optimized indexing for large datasets.
- **Rich Aesthetics**: Custom CSS styling with dark mode optimization and responsive layouts.

---

##  Project Structure

```text
Data-pipeline/
├── data/
│   ├── raw/            - Place source TSV files here
│   └── clean/          - Processed CSV files (Patents, Inventors, Companies)
├── scripts/
│   ├── ingest.py       - Step 1: Data cleaning & normalization
│   ├── load_db.py      - Step 2: SQLite database population
│   ├── dashboard.py    - Step 3: Interactive Streamlit Dashboard
│   ├── style.css       - Custom CSS for the dashboard
│   └── console_report.py - Command-line summary report
├── sql/
│   ├── schema.sql      - Database table and index definitions
│   └── queries.sql     - Analytical SQL queries (CTEs, Ranks, Joins)
├── patents.db          - Optimized SQLite Database (auto-generated)
└── readme.txt          - Quick-start guide and submission links
```

---

##  Getting Started

### 1. Prerequisites
Ensure you have Python 3.9+ and the required packages installed:
```bash
pip install streamlit pandas plotly sqlite3
```

### 2. Data Preparation
1. Download required TSV files from [PatentsView](https://data.uspto.gov/bulkdata/datasets/pvgpatdis).
2. Place the following files in `data/raw/`:
   - `g_patent.tsv`, `g_inventor_disambiguated.tsv`, etc.

### 3. Running the Pipeline
```bash
# Step 1: Clean and process raw data
python scripts/ingest.py

# Step 2: Load data into SQLite
python scripts/load_db.py

# Step 3: Launch the interactive Dashboard
streamlit run scripts/dashboard.py

# Step 4: Generate Console Summary
python scripts/console_report.py
```

---

##  Analytical Capabilities

The system provides deep insights across four primary dimensions:
1. **Trends**: Annual grant counts with 5-year rolling averages and peak detection.
2. **Inventors**: Top global inventors ranked by output with nationality distribution.
3. **Companies**: Analysis of the world's leading patent holders (Assignees).
4. **Countries**: Global geographic heatmap with interactive country-level filtering.

---

##  Project Links

-  Dashboard Links
 Local URL: http://localhost:8501
 Network URL: http://10.150.5.88:8501

---
