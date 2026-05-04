-- schema.sql
-- Creates all tables and indexes for the patent pipeline

PRAGMA journal_mode=WAL;

-- CORE TABLES

CREATE TABLE IF NOT EXISTS patents (
    patent_id   TEXT PRIMARY KEY,
    title       TEXT,
    abstract    TEXT,
    filing_date TEXT,   -- stored as YYYY-MM-DD string
    year        INTEGER
);

CREATE TABLE IF NOT EXISTS inventors (
    inventor_id TEXT PRIMARY KEY,
    name        TEXT,
    country     TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    company_id  TEXT PRIMARY KEY,
    name        TEXT
);

-- RELATIONSHIP TABLE

CREATE TABLE IF NOT EXISTS relationships (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    patent_id   TEXT,
    inventor_id TEXT,
    company_id  TEXT,
    FOREIGN KEY (patent_id)   REFERENCES patents(patent_id),
    FOREIGN KEY (inventor_id) REFERENCES inventors(inventor_id),
    FOREIGN KEY (company_id)  REFERENCES companies(company_id)
);

-- INDEXES FOR QUERY PERFORMANCE

CREATE INDEX IF NOT EXISTS idx_rel_patent   ON relationships(patent_id);
CREATE INDEX IF NOT EXISTS idx_rel_inventor ON relationships(inventor_id);
CREATE INDEX IF NOT EXISTS idx_rel_company  ON relationships(company_id);
CREATE INDEX IF NOT EXISTS idx_patents_year ON patents(year);
