"""
dashboard.py
------------
Streamlit dashboard for the Global Patent Intelligence Pipeline.

"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# ── Page config ────
st.set_page_config(
    page_title="Patent Intelligence Dashboard",
    page_icon="telescope",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = "patents.db"

# ── Custom CSS ───
st.markdown("""
<style>
    /* Main background */
    .stApp { background-color: #f8f9fa; }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e0e0e0;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    div[data-testid="metric-container"] label {
        color: #6c757d !important;
        font-size: 12px !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    div[data-testid="metric-container"] div[data-testid="stMetricValue"] {
        color: #1f3a5f !important;
        font-size: 28px !important;
        font-weight: 700 !important;
    }

    /* Headers */
    h1, h2, h3 { color: #1f3a5f !important; }

    /* Section divider */
    .section-title {
        font-size: 13px;
        font-weight: 600;
        color: #495057;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin: 24px 0 8px 0;
        border-bottom: 2px solid #0066cc;
        padding-bottom: 6px;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background-color: #f0f0f0;
        border-radius: 8px;
        padding: 4px;
        gap: 4px;
    }
    .stTabs [data-baseweb="tab"] {
        color: #495057;
        border-radius: 6px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0066cc !important;
        color: #ffffff !important;
    }

    /* Dataframe */
    .stDataFrame { border: 1px solid #e0e0e0; border-radius: 8px; }

    /* Plotly chart background */
    .js-plotly-plot { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ── Plotly theme defaults ───
PLOT_LAYOUT = dict(
    paper_bgcolor="#ffffff",
    plot_bgcolor="#f8f9fa",
    font=dict(color="#1f3a5f", family="sans-serif"),
    margin=dict(l=20, r=20, t=50, b=20),
    colorway=["#0066cc", "#00a6d6", "#29a538",
               "#ff6600", "#d62246", "#7cb342"],
)

# DATA LOADING (cached)

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at `{DB_PATH}`. "
                 "Please run `load_db.py` first.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=300)
def load_summary():
    conn = get_conn()
    total     = pd.read_sql("SELECT COUNT(*) AS n FROM patents", conn).iloc[0, 0]
    inventors = pd.read_sql("SELECT COUNT(*) AS n FROM inventors", conn).iloc[0, 0]
    companies = pd.read_sql("SELECT COUNT(*) AS n FROM companies", conn).iloc[0, 0]
    countries = pd.read_sql(
        "SELECT COUNT(DISTINCT country) AS n FROM inventors "
        "WHERE country NOT IN ('Unknown','')", conn
    ).iloc[0, 0]
    return int(total), int(inventors), int(companies), int(countries)


@st.cache_data(ttl=300)
def load_yearly(year_min, year_max):
    conn = get_conn()
    return pd.read_sql(f"""
        SELECT year, COUNT(*) AS patents
        FROM patents
        WHERE year BETWEEN {year_min} AND {year_max}
        GROUP BY year ORDER BY year
    """, conn)


@st.cache_data(ttl=300)
def load_top_inventors(limit):
    conn = get_conn()
    return pd.read_sql(f"""
        SELECT i.name, i.country,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
        GROUP BY i.inventor_id
        ORDER BY patents DESC LIMIT {limit}
    """, conn)


@st.cache_data(ttl=300)
def load_top_companies(limit):
    conn = get_conn()
    return pd.read_sql(f"""
        SELECT c.name,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        WHERE r.company_id != ''
        GROUP BY c.company_id
        ORDER BY patents DESC LIMIT {limit}
    """, conn)


@st.cache_data(ttl=300)
def load_countries():
    conn = get_conn()
    return pd.read_sql("""
        SELECT i.country,
               COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
          AND i.country NOT IN ('Unknown','')
        GROUP BY i.country
        ORDER BY patents DESC LIMIT 30
    """, conn)


@st.cache_data(ttl=300)
def load_recent_patents(limit=100):
    conn = get_conn()
    return pd.read_sql(f"""
        SELECT p.patent_id, p.title, p.year, p.filing_date,
               i.name AS inventor, c.name AS company
        FROM patents p
        LEFT JOIN relationships r ON p.patent_id = r.patent_id
        LEFT JOIN inventors i     ON r.inventor_id = i.inventor_id
        LEFT JOIN companies c     ON r.company_id  = c.company_id
        WHERE p.year IS NOT NULL
          AND r.inventor_id != ''
        ORDER BY p.year DESC, p.patent_id DESC
        LIMIT {limit}
    """, conn)


@st.cache_data(ttl=300)
def search_patents(query, limit=50):
    conn = get_conn()
    q = query.replace("'", "''")
    return pd.read_sql(f"""
        SELECT patent_id, title, year, filing_date
        FROM patents
        WHERE title LIKE '%{q}%'
           OR abstract LIKE '%{q}%'
        ORDER BY year DESC
        LIMIT {limit}
    """, conn)

# SIDEBAR

with st.sidebar:
    st.markdown("## 🔬 Patent Intel")
    st.markdown("---")

    st.markdown('<p class="section-title">Filters</p>', unsafe_allow_html=True)

    year_range = st.slider(
        "Year range", min_value=1976, max_value=2025,
        value=(2000, 2025), step=1
    )

    top_n = st.select_slider(
        "Top N results", options=[5, 10, 15, 20, 25, 30],
        value=15
    )

    st.markdown("---")
    st.markdown('<p class="section-title">Search Patents</p>',
                unsafe_allow_html=True)
    search_query = st.text_input("Keyword search", placeholder="e.g. machine learning")

    st.markdown("---")
    st.markdown(
        "<small style='color:#6c757d'>Data: PatentsView (USPTO)<br>"
        "Pipeline: Python + SQLite</small>",
        unsafe_allow_html=True
    )

# HEADER

st.markdown(
    "<h1 style='margin-bottom:4px'>🔬 Global Patent Intelligence</h1>"
    "<p style='color:#6c757d;margin-top:0'>Interactive analysis of USPTO patent data</p>",
    unsafe_allow_html=True
)

# ── KPI Metrics ────
total, n_inventors, n_companies, n_countries = load_summary()
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Patents",   f"{total:,}")
c2.metric("Inventors",       f"{n_inventors:,}")
c3.metric("Companies",       f"{n_companies:,}")
c4.metric("Countries",       f"{n_countries:,}")

st.markdown("<br>", unsafe_allow_html=True)


# TABS

tab_trends, tab_inventors, tab_companies, tab_countries, tab_search = st.tabs([
    " Trends", " Inventors", " Companies",
    " Countries", " Search"
])


# ── TAB 1: TRENDS ────
with tab_trends:
    st.markdown("### Patent Filings Over Time")

    df_year = load_yearly(year_range[0], year_range[1])

    if df_year.empty:
        st.info("No data for the selected year range.")
    else:
        df_year["rolling5"] = df_year["patents"].rolling(5, center=True).mean()

        fig = make_subplots(specs=[[{"secondary_y": False}]])
        fig.add_trace(go.Bar(
            x=df_year["year"], y=df_year["patents"],
            name="Annual", marker_color="#4f9cf9",
            opacity=0.5
        ))
        fig.add_trace(go.Scatter(
            x=df_year["year"], y=df_year["rolling5"],
            name="5-yr avg", line=dict(color="#f97b4f", width=2.5)
        ))
        fig.update_layout(
            **PLOT_LAYOUT,
            title="Patents Per Year",
            xaxis_title="Year",
            yaxis_title="Patents",
            legend=dict(orientation="h", y=1.08),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Stats row
        col1, col2, col3 = st.columns(3)
        peak = df_year.loc[df_year["patents"].idxmax()]
        col1.metric("Peak Year",   str(int(peak["year"])))
        col2.metric("Peak Count",  f"{int(peak['patents']):,}")
        col3.metric("Avg / Year",  f"{int(df_year['patents'].mean()):,}")

        # Raw table (collapsed)
        with st.expander("View raw yearly data"):
            st.dataframe(df_year.set_index("year"), use_container_width=True)


# ── TAB 2: INVENTORS ───
with tab_inventors:
    st.markdown("## Top Inventors by Patent Count")

    df_inv = load_top_inventors(top_n)

    col_chart, col_table = st.columns([3, 2])

    with col_chart:
        fig = px.bar(
            df_inv.iloc[::-1], x="patents", y="name",
            orientation="h",
            color="patents",
            color_continuous_scale="Blues",
            labels={"patents": "Patents", "name": "Inventor"},
        )
        fig.update_layout(**PLOT_LAYOUT, height=500,
                          coloraxis_showscale=False,
                          yaxis_title="",
                          xaxis_title="Patent Count")
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Patents: %{x:,}<extra></extra>"
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_table:
        st.markdown("## Inventor Details")
        df_display = df_inv.copy()
        df_display.index = range(1, len(df_display) + 1)
        df_display.columns = ["Name", "Country", "Patents"]
        st.dataframe(df_display, use_container_width=True, height=480)

    # Country breakdown of top inventors
    st.markdown("## Countries of Top Inventors")
    country_counts = df_inv["country"].value_counts().reset_index()
    country_counts.columns = ["country", "count"]
    fig2 = px.pie(
        country_counts, values="count", names="country",
        hole=0.45,
        color_discrete_sequence=px.colors.sequential.Blues_r
    )
    fig2.update_layout(**PLOT_LAYOUT, height=350)
    fig2.update_traces(
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>%{value} inventors<extra></extra>"
    )
    st.plotly_chart(fig2, use_container_width=True)


# ── TAB 3: COMPANIES ───
with tab_companies:
    st.markdown("## Top Companies by Patent Count")

    df_co = load_top_companies(top_n)

    fig = px.bar(
        df_co.iloc[::-1], x="patents", y="name",
        orientation="h",
        color="patents",
        color_continuous_scale="Teal",
        labels={"patents": "Patents", "name": "Company"},
    )
    fig.update_layout(**PLOT_LAYOUT, height=560,
                      coloraxis_showscale=False,
                      yaxis_title="",
                      xaxis_title="Patent Count")
    fig.update_traces(
        hovertemplate="<b>%{y}</b><br>Patents: %{x:,}<extra></extra>"
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("## Full Table")
    df_co_display = df_co.copy()
    df_co_display.index = range(1, len(df_co_display) + 1)
    df_co_display.columns = ["Company", "Patents"]
    st.dataframe(df_co_display, use_container_width=True)


# ── TAB 4: COUNTRIES ───
with tab_countries:
    st.markdown("## Patent Output by Country")

    df_ctr = load_countries()
    total_ctr = df_ctr["patents"].sum()
    df_ctr["share"] = (df_ctr["patents"] / total_ctr * 100).round(2)

    col_map, col_bar = st.columns([3, 2])

    with col_map:
        fig = px.choropleth(
            df_ctr,
            locations="country",
            locationmode="ISO-3 ",
            color="patents",
            hover_name="country",
            color_continuous_scale="Blues",
            title="World Patent Map",
            labels={"patents": "Patents"},
        )
        fig.update_layout(
            **PLOT_LAYOUT,
            height=420,
            geo=dict(
                bgcolor="#f8f9fa",
                landcolor="#e0e0e0",
                oceancolor="#e8f4f8",
                showocean=True,
                lakecolor="#e8f4f8",
                showlakes=True,
                framecolor="#cccccc"
            )
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_bar:
        fig2 = px.bar(
            df_ctr.head(15).iloc[::-1],
            x="patents", y="country",
            orientation="h",
            color="share",
            color_continuous_scale="Blues",
            labels={"patents": "Patents", "country": "Country",
                    "share": "Share %"},
        )
        fig2.update_layout(**PLOT_LAYOUT, height=420,
                           yaxis_title="",
                           xaxis_title="Patent Count",
                           coloraxis_showscale=False)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("## Country Breakdown Table")
    df_ctr_display = df_ctr.copy()
    df_ctr_display.index = range(1, len(df_ctr_display) + 1)
    df_ctr_display.columns = ["Country", "Patents", "Share %"]
    st.dataframe(df_ctr_display, use_container_width=True)


# ── TAB 5: SEARCH ────
with tab_search:
    st.markdown("## Search Patents")

    if search_query:
        with st.spinner(f"Searching for '{search_query}' ..."):
            results = search_patents(search_query)

        if results.empty:
            st.warning(f"No patents found matching **'{search_query}'**.")
        else:
            st.success(f"Found **{len(results):,}** patents matching "
                       f"**'{search_query}'**")
            results.index = range(1, len(results) + 1)
            results.columns = ["Patent ID", "Title", "Year", "Filing Date"]
            st.dataframe(results, use_container_width=True, height=500)

            # Year distribution of results
            year_dist = results["Year"].value_counts().sort_index()
            fig = px.bar(
                x=year_dist.index, y=year_dist.values,
                labels={"x": "Year", "y": "Results"},
                title=f"Search Results by Year: '{search_query}'"
            )
            fig.update_traces(marker_color="#4f9cf9")
            fig.update_layout(**PLOT_LAYOUT, height=280)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Enter a keyword in the sidebar to search patents by title or abstract.")

        st.markdown("## Recent Patents")
        recent = load_recent_patents(50)
        recent.index = range(1, len(recent) + 1)
        st.dataframe(recent, use_container_width=True, height=400)
