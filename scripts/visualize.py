"""
visualize.py
------------
Generates data visualizations from patents.db and saves them
as PNG files to outputs/charts/.

Charts produced:
  1. patents_per_year.png       - line chart of yearly trends
  2. top_inventors.png          - horizontal bar chart
  3. top_companies.png          - horizontal bar chart
  4. top_countries.png          - bar chart with share %
  5. cpc_categories.png         - patent categories breakdown (if available)
  6. country_heatmap.png        - decade × country heatmap
"""

import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings
warnings.filterwarnings("ignore")

DB_PATH    = "patents.db"
CHART_DIR  = "outputs/charts"
os.makedirs(CHART_DIR, exist_ok=True)

# ── Global style ──
DARK_BG   = "#0f1117"
CARD_BG   = "#1a1d27"
ACCENT    = "#4f9cf9"
ACCENT2   = "#f97b4f"
ACCENT3   = "#4ff9a1"
TEXT      = "#e8eaf0"
SUBTEXT   = "#8b90a0"

plt.rcParams.update({
    "figure.facecolor":  DARK_BG,
    "axes.facecolor":    CARD_BG,
    "axes.edgecolor":    "#2e3244",
    "axes.labelcolor":   TEXT,
    "axes.titlecolor":   TEXT,
    "axes.titlesize":    15,
    "axes.titleweight":  "bold",
    "axes.titlepad":     16,
    "xtick.color":       SUBTEXT,
    "ytick.color":       SUBTEXT,
    "xtick.labelsize":   9,
    "ytick.labelsize":   9,
    "text.color":        TEXT,
    "grid.color":        "#2e3244",
    "grid.linestyle":    "--",
    "grid.linewidth":    0.6,
    "legend.facecolor":  CARD_BG,
    "legend.edgecolor":  "#2e3244",
    "font.family":       "DejaVu Sans",
})

def conn():
    return sqlite3.connect(DB_PATH)

def save(fig, name):
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight",
                facecolor=DARK_BG, edgecolor="none")
    plt.close(fig)
    print(f"  → Saved {path}")

# 1. PATENTS PER YEAR  (line chart)

def chart_patents_per_year():
    df = pd.read_sql("""
        SELECT year, COUNT(*) AS patents
        FROM patents
        WHERE year BETWEEN 1976 AND 2025
        GROUP BY year ORDER BY year
    """, conn())

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.patch.set_facecolor(DARK_BG)

    ax.fill_between(df["year"], df["patents"],
                    alpha=0.18, color=ACCENT)
    ax.plot(df["year"], df["patents"],
            color=ACCENT, linewidth=2.2, zorder=3)

    # Highlight peak year
    peak = df.loc[df["patents"].idxmax()]
    ax.scatter(peak["year"], peak["patents"],
               color=ACCENT2, s=90, zorder=5)
    ax.annotate(f'Peak: {int(peak["year"])} ({int(peak["patents"]):,})',
                xy=(peak["year"], peak["patents"]),
                xytext=(10, 12), textcoords="offset points",
                color=ACCENT2, fontsize=9, fontweight="bold")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"))
    ax.set_title("Patents Granted Per Year")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Patents")
    ax.grid(axis="y", alpha=0.5)
    ax.set_xlim(df["year"].min(), df["year"].max())

    fig.tight_layout()
    save(fig, "patents_per_year.png")

# 2. TOP 15 INVENTORS  (horizontal bar)

def chart_top_inventors():
    df = pd.read_sql("""
        SELECT i.name, i.country,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
        GROUP BY i.inventor_id
        ORDER BY patents DESC LIMIT 15
    """, conn())
    df = df.iloc[::-1]   # flip so highest is on top

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor(DARK_BG)

    colors = [ACCENT if i % 2 == 0 else ACCENT3
              for i in range(len(df))]
    bars = ax.barh(df["name"], df["patents"],
                   color=colors, height=0.65, zorder=3)

    # Value labels
    for bar, val in zip(bars, df["patents"]):
        ax.text(bar.get_width() + df["patents"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center",
                fontsize=8.5, color=TEXT)

    ax.set_title("Top 15 Inventors by Patent Count")
    ax.set_xlabel("Number of Patents")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"))
    ax.grid(axis="x", alpha=0.4)
    ax.set_xlim(0, df["patents"].max() * 1.15)
    fig.tight_layout()
    save(fig, "top_inventors.png")


# 3. TOP 15 COMPANIES  (horizontal bar)

def chart_top_companies():
    df = pd.read_sql("""
        SELECT c.name,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        WHERE r.company_id != ''
        GROUP BY c.company_id
        ORDER BY patents DESC LIMIT 15
    """, conn())
    df = df.iloc[::-1]

    fig, ax = plt.subplots(figsize=(11, 7))
    fig.patch.set_facecolor(DARK_BG)

    # Gradient-like palette
    palette = sns.color_palette("cool", len(df))
    bars = ax.barh(df["name"], df["patents"],
                   color=palette, height=0.65, zorder=3)

    for bar, val in zip(bars, df["patents"]):
        ax.text(bar.get_width() + df["patents"].max() * 0.01,
                bar.get_y() + bar.get_height() / 2,
                f"{int(val):,}", va="center",
                fontsize=8.5, color=TEXT)

    ax.set_title("Top 15 Companies by Patent Count")
    ax.set_xlabel("Number of Patents")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"))
    ax.grid(axis="x", alpha=0.4)
    ax.set_xlim(0, df["patents"].max() * 1.15)
    fig.tight_layout()
    save(fig, "top_companies.png")

# 4. TOP COUNTRIES  (bar + share % twin axis)

def chart_top_countries():
    df = pd.read_sql("""
        SELECT i.country,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != '' AND i.country NOT IN ('Unknown','')
        GROUP BY i.country
        ORDER BY patents DESC LIMIT 20
    """, conn())

    total = df["patents"].sum()
    df["share"] = (df["patents"] / total * 100).round(2)

    fig, ax1 = plt.subplots(figsize=(13, 6))
    fig.patch.set_facecolor(DARK_BG)

    x = range(len(df))
    bars = ax1.bar(x, df["patents"],
                   color=ACCENT, alpha=0.85,
                   width=0.6, zorder=3)
    bars[0].set_color(ACCENT2)   # highlight top country

    ax1.set_xticks(list(x))
    ax1.set_xticklabels(df["country"], rotation=35, ha="right")
    ax1.set_ylabel("Patent Count")
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda v, _: f"{int(v):,}"))
    ax1.grid(axis="y", alpha=0.4)

    # Twin axis for share %
    ax2 = ax1.twinax() if hasattr(ax1, "twinax") else ax1.twinx()
    ax2.plot(list(x), df["share"],
             color=ACCENT3, linewidth=2,
             marker="o", markersize=5, zorder=4)
    ax2.set_ylabel("Share of Total (%)", color=ACCENT3)
    ax2.tick_params(axis="y", colors=ACCENT3)
    ax2.set_facecolor(CARD_BG)

    ax1.set_title("Top 20 Countries by Patent Output")
    fig.tight_layout()
    save(fig, "top_countries.png")

# 5. DECADE × COUNTRY HEATMAP

def chart_country_heatmap():
    df = pd.read_sql("""
        SELECT i.country,
               (p.year / 10) * 10 AS decade,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        JOIN patents   p ON r.patent_id   = p.patent_id
        WHERE r.inventor_id != ''
          AND i.country NOT IN ('Unknown','')
          AND p.year IS NOT NULL
        GROUP BY i.country, decade
        ORDER BY patents DESC
    """, conn())

    # Top 12 countries only for readability
    top12 = (df.groupby("country")["patents"]
               .sum().nlargest(12).index.tolist())
    df = df[df["country"].isin(top12)]

    pivot = df.pivot_table(index="country", columns="decade",
                           values="patents", fill_value=0)

    fig, ax = plt.subplots(figsize=(13, 7))
    fig.patch.set_facecolor(DARK_BG)

    sns.heatmap(pivot, ax=ax,
                cmap="YlOrRd",
                linewidths=0.4,
                linecolor="#0f1117",
                annot=True,
                fmt=",",
                annot_kws={"size": 8},
                cbar_kws={"shrink": 0.7})

    ax.set_title("Patent Output by Country & Decade")
    ax.set_xlabel("Decade")
    ax.set_ylabel("")
    ax.tick_params(axis="x", rotation=0)
    ax.tick_params(axis="y", rotation=0)
    fig.tight_layout()
    save(fig, "country_heatmap.png")

# 6. ROLLING 5-YEAR AVERAGE  (trend smoothing)

def chart_rolling_average():
    df = pd.read_sql("""
        SELECT year, COUNT(*) AS patents
        FROM patents
        WHERE year BETWEEN 1976 AND 2025
        GROUP BY year ORDER BY year
    """, conn())

    df["rolling"] = df["patents"].rolling(5, center=True).mean()

    fig, ax = plt.subplots(figsize=(13, 5))
    fig.patch.set_facecolor(DARK_BG)

    ax.bar(df["year"], df["patents"],
           color=ACCENT, alpha=0.3, width=0.8, zorder=2,
           label="Annual count")
    ax.plot(df["year"], df["rolling"],
            color=ACCENT2, linewidth=2.5, zorder=4,
            label="5-year rolling average")

    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{int(x):,}"))
    ax.set_title("Patent Trends with 5-Year Rolling Average")
    ax.set_xlabel("Year")
    ax.set_ylabel("Number of Patents")
    ax.legend()
    ax.grid(axis="y", alpha=0.4)
    fig.tight_layout()
    save(fig, "rolling_average.png")


# MAIN

if __name__ == "__main__":
    print("\n STEP 4: VISUALIZATIONS \n")
    print(f"Saving charts to {os.path.abspath(CHART_DIR)}\n")

    chart_patents_per_year()
    chart_top_inventors()
    chart_top_companies()
    chart_top_countries()
    chart_country_heatmap()
    chart_rolling_average()

    print(f"\n✓ All charts saved to {CHART_DIR}/\n")
