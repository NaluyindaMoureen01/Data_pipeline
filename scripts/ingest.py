"""
ingest.py
Reads raw PatentsView TSV files, cleans them with pandas,
and saves clean CSVs to data/clean/.

"""

import os
import pandas as pd

RAW_DIR   = "data/raw"
CLEAN_DIR = "data/clean"
os.makedirs(CLEAN_DIR, exist_ok=True)

#safes TSV reader with progress print

def read_tsv(filename, usecols, dtype=str):
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"\n   File not found: {path}"
            f"\n    Please download it from PatentsView and place it in data/raw/"
        )
    print(f"  Reading {filename} ...")
    df = pd.read_csv(
        path,
        sep="\t",
        usecols=usecols,
        dtype=dtype,
        low_memory=False,
        on_bad_lines="skip",
        encoding="utf-8",
        encoding_errors="replace"
    )
    print(f"   {len(df):,} rows loaded")
    return df

# 1. PATENTS
#    Source: g_patent.tsv
#            g_patent_abstract.tsv (for abstracts)

def clean_patents():
    print("\n[1/4] PATENTS")

    patents = read_tsv(
        "g_patent.tsv",
        usecols=["patent_id", "patent_type", "patent_date", "patent_title"]
    )

    abstracts = read_tsv(
        "g_patent_abstract.tsv",
        usecols=["patent_id", "patent_abstract"]
    )

    # Merge abstracts in (left join — keep patents even with no abstract)
    df = patents.merge(abstracts, on="patent_id", how="left")

    # Rename to  schema names
    df.rename(columns={
        "patent_title":    "title",
        "patent_abstract": "abstract",
        "patent_date":     "filing_date",
        "patent_type":     "type"
    }, inplace=True)

    df.dropna(subset=["patent_id"], inplace=True)
    df["patent_id"] = df["patent_id"].str.strip()

    # Parse dates, extract year
    df["filing_date"] = pd.to_datetime(df["filing_date"], errors="coerce")
    df["year"]        = df["filing_date"].dt.year.astype("Int64")
    df["filing_date"] = df["filing_date"].dt.strftime("%Y-%m-%d")

    # Clean text
    df["title"]    = df["title"].fillna("Unknown").str.strip()
    df["abstract"] = df["abstract"].fillna("").str.strip()

    df.drop_duplicates(subset=["patent_id"], inplace=True)

    out = os.path.join(CLEAN_DIR, "clean_patents.csv")
    df[["patent_id", "title", "abstract", "filing_date", "year"]].to_csv(out, index=False)
    print(f"  → Saved {len(df):,} patents  →  {out}")
    return df


# 2. INVENTORS
#    Source: g_inventor_disambiguated.tsv
#            g_location_disambiguated.tsv (for country)

def clean_inventors():
    print("\n[2/4] INVENTORS")

    inv = read_tsv(
        "g_inventor_disambiguated.tsv",
        usecols=[
            "inventor_id",
            "disambig_inventor_name_first",
            "disambig_inventor_name_last",
            "location_id"
        ]
    )

    inv.rename(columns={
        "disambig_inventor_name_first": "first_name",
        "disambig_inventor_name_last":  "last_name"
    }, inplace=True)

    inv.dropna(subset=["inventor_id"], inplace=True)

    # Build full name
    inv["first_name"] = inv["first_name"].fillna("").str.strip()
    inv["last_name"]  = inv["last_name"].fillna("").str.strip()
    inv["name"] = (inv["first_name"] + " " + inv["last_name"]).str.strip()
    inv["name"] = inv["name"].replace("", "Unknown")

    # Join location table to get country
    loc = read_tsv(
        "g_location_disambiguated.tsv",
        usecols=["location_id", "disambig_country"]
    )
    loc.rename(columns={"disambig_country": "country"}, inplace=True)
    loc.dropna(subset=["location_id"], inplace=True)
    loc.drop_duplicates(subset=["location_id"], inplace=True)

    inv = inv.merge(loc, on="location_id", how="left")

    inv["country"] = (
        inv["country"]
        .fillna("Unknown")
        .str.strip()
        .str.upper()
        .replace("", "Unknown")
    )

    inv.drop_duplicates(subset=["inventor_id"], inplace=True)

    out = os.path.join(CLEAN_DIR, "clean_inventors.csv")
    inv[["inventor_id", "name", "country"]].to_csv(out, index=False)
    print(f"  → Saved {len(inv):,} inventors  →  {out}")
    return inv


# 3. COMPANIES (ASSIGNEES)
#    Source: g_assignee_disambiguated.tsv

def clean_companies():
    print("\n[3/4] COMPANIES (ASSIGNEES)")

    df = read_tsv(
        "g_assignee_disambiguated.tsv",
        usecols=[
            "assignee_id",
            "disambig_assignee_organization",
            "disambig_assignee_individual_name_first",
            "disambig_assignee_individual_name_last",
            "assignee_type"
        ]
    )

    df.rename(columns={
        "disambig_assignee_organization":          "org_name",
        "disambig_assignee_individual_name_first": "ind_first",
        "disambig_assignee_individual_name_last":  "ind_last"
    }, inplace=True)

    df.dropna(subset=["assignee_id"], inplace=True)

    # Use org name where available; fall back to individual name
    df["org_name"]  = df["org_name"].fillna("").str.strip()
    df["ind_first"] = df["ind_first"].fillna("").str.strip()
    df["ind_last"]  = df["ind_last"].fillna("").str.strip()
    df["ind_name"]  = (df["ind_first"] + " " + df["ind_last"]).str.strip()

    df["name"] = df["org_name"].where(df["org_name"] != "", df["ind_name"])
    df["name"] = df["name"].replace("", "Unknown").fillna("Unknown")

    # Rename to match schema
    df.rename(columns={"assignee_id": "company_id"}, inplace=True)

    df.drop_duplicates(subset=["company_id"], inplace=True)

    out = os.path.join(CLEAN_DIR, "clean_companies.csv")
    df[["company_id", "name"]].to_csv(out, index=False)
    print(f"  → Saved {len(df):,} companies  →  {out}")
    return df


# 4. RELATIONSHIPS
#    Source: g_inventor_disambiguated.tsv - patent_id, inventor_id
#            g_assignee_disambiguated.tsv - patent_id, assignee_id


def clean_relationships():
    print("\n[4/4] RELATIONSHIPS")


    # Patent → Inventor links (already in the inventor disambiguated file)
    pi = read_tsv(
        "g_inventor_disambiguated.tsv",
        usecols=["patent_id", "inventor_id"]
    )
    pi.drop_duplicates(inplace=True)

    # Patent → Assignee links (already in the assignee disambiguated file)
    pa = read_tsv(
        "g_assignee_disambiguated.tsv",
        usecols=["patent_id", "assignee_id"]
    )
    pa.rename(columns={"assignee_id": "company_id"}, inplace=True)
    pa.drop_duplicates(inplace=True)

    # Outer merge so we keep patents that have inventors but no assignee & vice versa
    rel = pd.merge(pi, pa, on="patent_id", how="outer")
    rel.dropna(subset=["patent_id"], inplace=True)
    rel["patent_id"]   = rel["patent_id"].str.strip()
    rel["inventor_id"] = rel["inventor_id"].fillna("")
    rel["company_id"]  = rel["company_id"].fillna("")

    out = os.path.join(CLEAN_DIR, "clean_relationships.csv")
    rel.to_csv(out, index=False)
    print(f"   Saved {len(rel):,} relationship rows  →  {out}")
    return rel


# MAIN

if __name__ == "__main__":
    print("\n STEP 1: INGESTION & CLEANING \n")
    print(f"Reading from : {os.path.abspath(RAW_DIR)}")
    print(f"Writing to   : {os.path.abspath(CLEAN_DIR)}")

    clean_patents()
    clean_inventors()
    clean_companies()
    clean_relationships()

    print("\n All cleaning complete. Check data/clean/\n")
