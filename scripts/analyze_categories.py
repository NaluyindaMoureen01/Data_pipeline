"""
analyze_categories.py
---------------------
Advanced analysis of patent categories using CPC classification data.
Falls back gracefully to type-based analysis if CPC file is unavailable.

Outputs:
  - outputs/category_summary.csv
  - outputs/category_trends.csv
  - outputs/charts/category_breakdown.png
  - outputs/charts/category_trends.png
  - outputs/charts/top_companies_by_category.png
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

DB_PATH   = "patents.db"
RAW_DIR   = "data/raw"
OUT_DIR   = "outputs"
CHART_DIR = "outputs/charts"
os.makedirs(CHART_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)

# ── Style (matches visualize.py) ───
DARK_BG  = "#0f1117"
CARD_BG  = "#1a1d27"
ACCENT   = "#4f9cf9"
ACCENT2  = "#f97b4f"
ACCENT3  = "#4ff9a1"
TEXT     = "#e8eaf0"
SUBTEXT  = "#8b90a0"

plt.rcParams.update({
    "figure.facecolor": DARK_BG,
    "axes.facecolor":   CARD_BG,
    "axes.edgecolor":   "#2e3244",
    "axes.labelcolor":  TEXT,
    "axes.titlecolor":  TEXT,
    "axes.titlesize":   14,
    "axes.titleweight": "bold",
    "axes.titlepad":    14,
    "xtick.color":      SUBTEXT,
    "ytick.color":      SUBTEXT,
    "text.color":       TEXT,
    "grid.color":       "#2e3244",
    "grid.linestyle":   "--",
    "grid.linewidth":   0.5,
})

def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    print(f"  → Chart saved: {path}")

def db_conn():
    return sqlite3.connect(DB_PATH)

# CPC SECTION LABELS
# Full names for each top-level CPC section letter

CPC_LABELS = {
    "A": "Human Necessities",
    "B": "Performing Operations / Transporting",
    "C": "Chemistry / Metallurgy",
    "D": "Textiles / Paper",
    "E": "Fixed Constructions",
    "F": "Mechanical Engineering",
    "G": "Physics",
    "H": "Electricity",
    "Y": "New Tech / Cross-Sectional",
}

# LOAD CPC DATA
# Try to read g_cpc_current.tsv from data/raw/.
# If not available, fall back to patent_type from the patents table.

def load_cpc_data():
    cpc_path = os.path.join(RAW_DIR, "g_cpc_current.tsv")

    if os.path.exists(cpc_path):
        print("  Found g_cpc_current.tsv — using CPC classification data.")
        cpc = pd.read_csv(
            cpc_path,
            sep="\t",
            usecols=["patent_id", "cpc_section", "cpc_class",
                     "cpc_subclass", "cpc_type"],
            dtype=str,
            low_memory=False,
            on_bad_lines="skip"
        )
        # Keep only inventional (primary) classifications
        cpc = cpc[cpc["cpc_type"].str.lower() == "inventional"]
        # One row per patent — keep the first/primary section
        cpc.drop_duplicates(subset=["patent_id"], inplace=True)
        cpc["category"] = cpc["cpc_section"].map(CPC_LABELS).fillna("Other")
        cpc["section"]  = cpc["cpc_section"]
        return cpc[["patent_id", "section", "category", "cpc_class", "cpc_subclass"]]

    else:
        print("  g_cpc_current.tsv not found — falling back to patent_type analysis.")
        conn = db_conn()
        df = pd.read_sql(
            "SELECT patent_id, COALESCE(NULLIF(type,''), 'utility') AS section "
            "FROM patents", conn
        )
        conn.close()
        df["category"] = df["section"].str.title()
        df["cpc_class"]    = df["section"]
        df["cpc_subclass"] = df["section"]
        return df

# ANALYSIS 1: Category Breakdown (pie + bar)

def analyze_category_breakdown(cpc):
    print("\n[1/4] Category breakdown ...")

    summary = (cpc.groupby(["section", "category"])
                   .size()
                   .reset_index(name="patent_count")
                   .sort_values("patent_count", ascending=False))

    total = summary["patent_count"].sum()
    summary["share_pct"] = (summary["patent_count"] / total * 100).round(2)

    # Save CSV
    csv_path = os.path.join(OUT_DIR, "category_summary.csv")
    summary.to_csv(csv_path, index=False)
    print(f"  → CSV saved: {csv_path}")

    # ── Chart: horizontal bar ───
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle("Patent Category Distribution", fontsize=16,
                 fontweight="bold", color=TEXT, y=1.01)

    # Left: bar chart
    ax = axes[0]
    df_plot = summary.head(9).iloc[::-1]
    palette = sns.color_palette("mako", len(df_plot))
    bars = ax.barh(df_plot["category"], df_plot["patent_count"],
                   color=palette, height=0.65)
    for bar, val in zip(bars, df_plot["patent_count"]):
        ax.text(bar.get_width() + df_plot["patent_count"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center", fontsize=8, color=TEXT)
    ax.set_title("Patents by CPC Section")
    ax.set_xlabel("Patent Count")
    ax.xaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.grid(axis="x", alpha=0.4)
    ax.set_xlim(0, df_plot["patent_count"].max() * 1.2)

    # Right: pie chart
    ax2 = axes[1]
    ax2.set_facecolor(DARK_BG)
    wedge_colors = sns.color_palette("mako", len(summary.head(9)))
    wedges, texts, autotexts = ax2.pie(
        summary.head(9)["patent_count"],
        labels=summary.head(9)["section"],
        autopct="%1.1f%%",
        colors=wedge_colors,
        startangle=140,
        pctdistance=0.82,
        wedgeprops=dict(linewidth=1.5, edgecolor=DARK_BG)
    )
    for t in texts:
        t.set_color(TEXT)
        t.set_fontsize(10)
    for at in autotexts:
        at.set_color(DARK_BG)
        at.set_fontsize(8)
        at.set_fontweight("bold")
    ax2.set_title("Share by CPC Section")

    fig.tight_layout()
    save(fig, "category_breakdown.png")
    return summary

# ANALYSIS 2: Category Trends Over Time

def analyze_category_trends(cpc):
    print("\n[2/4] Category trends over time ...")

    conn = db_conn()
    patents_years = pd.read_sql(
        "SELECT patent_id, year FROM patents WHERE year IS NOT NULL", conn
    )
    conn.close()

    merged = cpc.merge(patents_years, on="patent_id", how="inner")
    merged = merged[merged["year"].between(1990, 2025)]

    # Top 6 categories for legibility
    top6 = (merged.groupby("category")["patent_id"]
                   .count().nlargest(6).index.tolist())
    merged = merged[merged["category"].isin(top6)]

    trends = (merged.groupby(["year", "category"])
                    .size()
                    .reset_index(name="patent_count"))

    csv_path = os.path.join(OUT_DIR, "category_trends.csv")
    trends.to_csv(csv_path, index=False)
    print(f"  → CSV saved: {csv_path}")

    # ── Chart ───
    fig, ax = plt.subplots(figsize=(14, 6))
    fig.patch.set_facecolor(DARK_BG)

    palette = sns.color_palette("tab10", len(top6))
    for i, cat in enumerate(top6):
        sub = trends[trends["category"] == cat]
        ax.plot(sub["year"], sub["patent_count"],
                label=cat, color=palette[i],
                linewidth=2, marker="o", markersize=3)

    ax.set_title("Patent Category Trends (1990–2025)")
    ax.set_xlabel("Year")
    ax.set_ylabel("Patents Granted")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
    ax.legend(loc="upper left", fontsize=8,
              framealpha=0.4, borderpad=0.8)
    ax.grid(alpha=0.35)
    fig.tight_layout()
    save(fig, "category_trends.png")
    return trends

# ANALYSIS 3: Top Companies per Category

def analyze_companies_by_category(cpc):
    print("\n[3/4] Top companies by category ...")

    conn = db_conn()
    rel = pd.read_sql(
        "SELECT patent_id, company_id FROM relationships "
        "WHERE company_id != ''", conn
    )
    companies = pd.read_sql("SELECT company_id, name FROM companies", conn)
    conn.close()

    merged = (cpc[["patent_id", "category"]]
              .merge(rel, on="patent_id", how="inner")
              .merge(companies, on="company_id", how="left"))

    # Top 3 companies per top-5 category
    top5_cats = (merged.groupby("category")["patent_id"]
                       .count().nlargest(5).index.tolist())
    merged = merged[merged["category"].isin(top5_cats)]

    top_co = (merged.groupby(["category", "name"])
                    .size()
                    .reset_index(name="patents")
                    .sort_values(["category", "patents"], ascending=[True, False]))
    top_co = top_co.groupby("category").head(4)

    # ── Chart: grouped bars ───
    fig, axes = plt.subplots(1, len(top5_cats),
                             figsize=(16, 6), sharey=False)
    fig.patch.set_facecolor(DARK_BG)
    fig.suptitle("Top Companies by Patent Category",
                 fontsize=15, fontweight="bold", color=TEXT)

    for ax, cat in zip(axes, top5_cats):
        sub = top_co[top_co["category"] == cat].head(4)
        labels = [n[:18] + "…" if len(n) > 18 else n
                  for n in sub["name"]]
        colors = sns.color_palette("cool", len(sub))
        bars = ax.bar(range(len(sub)), sub["patents"],
                      color=colors, width=0.6)
        ax.set_xticks(range(len(sub)))
        ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=7)
        ax.set_title(cat[:28], fontsize=9, fontweight="bold")
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
        ax.grid(axis="y", alpha=0.35)
        for bar, val in zip(bars, sub["patents"]):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + sub["patents"].max() * 0.02,
                    f"{int(val):,}", ha="center",
                    fontsize=7, color=TEXT)

    fig.tight_layout()
    save(fig, "top_companies_by_category.png")

# ANALYSIS 4: Emerging Technologies (fastest growing categories)

def analyze_emerging_tech(cpc):
    print("\n[4/4] Emerging technology trends ...")

    conn = db_conn()
    years = pd.read_sql(
        "SELECT patent_id, year FROM patents "
        "WHERE year BETWEEN 2010 AND 2025", conn
    )
    conn.close()

    merged = cpc.merge(years, on="patent_id", how="inner")

    # Compare 2010–2016 vs 2017–2025
    early  = merged[merged["year"] <= 2016]
    recent = merged[merged["year"] >  2016]

    early_counts  = early.groupby("category")["patent_id"].count()
    recent_counts = recent.groupby("category")["patent_id"].count()

    growth = pd.DataFrame({
        "early_2010_2016":  early_counts,
        "recent_2017_2025": recent_counts
    }).fillna(0)

    growth["growth_pct"] = (
        (growth["recent_2017_2025"] - growth["early_2010_2016"])
        / growth["early_2010_2016"].replace(0, 1) * 100
    ).round(1)

    growth = growth.sort_values("growth_pct", ascending=False).reset_index()

    print("\n  === FASTEST GROWING PATENT CATEGORIES ===")
    for _, row in growth.iterrows():
        arrow = "▲" if row["growth_pct"] > 0 else "▼"
        print(f"  {arrow} {row['category']:<40} "
              f"{row['growth_pct']:>+.1f}%")

    # ── Chart ───
    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor(DARK_BG)

    colors = [ACCENT3 if v > 0 else ACCENT2
              for v in growth["growth_pct"]]
    bars = ax.barh(growth["category"], growth["growth_pct"],
                   color=colors, height=0.6)

    ax.axvline(0, color=SUBTEXT, linewidth=0.8, linestyle="--")
    ax.set_title("Patent Category Growth: 2010–2016 vs 2017–2025")
    ax.set_xlabel("Growth (%)")
    ax.grid(axis="x", alpha=0.35)

    for bar, val in zip(bars, growth["growth_pct"]):
        xpos = bar.get_width() + (1 if val >= 0 else -1)
        ax.text(xpos,
                bar.get_y() + bar.get_height() / 2,
                f"{val:+.1f}%", va="center",
                fontsize=8,
                color=ACCENT3 if val >= 0 else ACCENT2)

    fig.tight_layout()
    save(fig, "emerging_tech_growth.png")

    csv_path = os.path.join(OUT_DIR, "emerging_tech_growth.csv")
    growth.to_csv(csv_path, index=False)
    print(f"  → CSV saved: {csv_path}")

# MAIN

if __name__ == "__main__":
    print("\n ADVANCED CATEGORY ANALYSIS \n")

    print("Loading category data ...")
    cpc = load_cpc_data()
    print(f"  → {len(cpc):,} patent-category rows loaded")

    analyze_category_breakdown(cpc)
    analyze_category_trends(cpc)
    analyze_companies_by_category(cpc)
    analyze_emerging_tech(cpc)

    print("\n Advanced analysis complete.\n")
    print("Charts saved in : outputs/charts/")
    print("CSVs saved in   : outputs/\n")
