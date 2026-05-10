"""
dashboard.py — Global Patent Intelligence Dashboard

"""

import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Patent Intelligence",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

DB_PATH = "patents.db"

# ── Design tokens ────
BG      = "#060912"
SURFACE = "#0b0f1e"
CARD    = "#0e1525"
CARD2   = "#111d30"
BORDER  = "#182235"
BORDER2 = "#1f3050"
ACCENT  = "#3b9eff"
ACCENT2 = "#ff6b3d"
ACCENT3 = "#00d4a8"
ACCENT4 = "#9b7dff"
GOLD    = "#f5c842"
PINK    = "#f472b6"
TEXT    = "#eef2f8"
TEXT2   = "#b8c4d8"
SUBTEXT = "#4a607a"
DIM     = "#0d1828"

# ── Master CSS (loaded from style.css) ──────
_css_path = os.path.join(os.path.dirname(__file__), "style.css")
with open(_css_path, "r", encoding="utf-8") as _f:
    _css = _f.read()

_root_vars = f"""
:root {{
  --bg:      {BG};      --surface: {SURFACE};
  --card:    {CARD};    --card2:   {CARD2};
  --border:  {BORDER};  --border2: {BORDER2};
  --accent:  {ACCENT};  --accent2: {ACCENT2};
  --accent3: {ACCENT3}; --accent4: {ACCENT4};
  --gold:    {GOLD};    --pink:    {PINK};
  --text:    {TEXT};    --text2:   {TEXT2};
  --subtext: {SUBTEXT}; --dim:     {DIM};
}}
"""


st.markdown(f"<style>{_root_vars}{_css}</style>", unsafe_allow_html=True)


# ── Plotly chart base ──────
def chart(height=420, title=""):
    return dict(
        paper_bgcolor=CARD,
        plot_bgcolor=CARD,
        font=dict(color=TEXT2, family="IBM Plex Mono, monospace", size=11),
        title=dict(
            text=f"<b>{title}</b>" if title else "",
            font=dict(size=13, color=TEXT, family="Outfit, sans-serif"),
            x=0.015, y=0.97,
        ),
        margin=dict(l=16, r=16, t=52 if title else 20, b=20),
        height=height,
        colorway=[ACCENT, ACCENT2, ACCENT3, ACCENT4, GOLD, PINK],
        legend=dict(
            bgcolor="rgba(0,0,0,0)",
            bordercolor=BORDER,
            borderwidth=1,
            font=dict(size=10, family="IBM Plex Mono, monospace"),
            orientation="h",
            y=1.08,
        ),
        xaxis=dict(gridcolor=BORDER, linecolor=BORDER2,
                   tickfont=dict(size=10), zerolinecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, linecolor=BORDER2,
                   tickfont=dict(size=10), zerolinecolor=BORDER),
        hoverlabel=dict(
            bgcolor=CARD2, bordercolor=BORDER2,
            font=dict(family="IBM Plex Mono, monospace", size=12, color=TEXT),
        ),
    )


# ── Data loaders ─────
@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        st.error(f"Database not found at `{DB_PATH}`. Run `python scripts/load_db.py` first.")
        st.stop()
    return sqlite3.connect(DB_PATH, check_same_thread=False)


@st.cache_data(ttl=300)
def load_summary():
    c = get_conn()
    total  = pd.read_sql("SELECT COUNT(*) AS n FROM patents", c).iloc[0, 0]
    inv    = pd.read_sql("SELECT COUNT(*) AS n FROM inventors", c).iloc[0, 0]
    co     = pd.read_sql("SELECT COUNT(*) AS n FROM companies", c).iloc[0, 0]
    ctr    = pd.read_sql(
        "SELECT COUNT(DISTINCT country) AS n FROM inventors "
        "WHERE country NOT IN ('Unknown','')", c
    ).iloc[0, 0]
    yr_min = pd.read_sql(
        "SELECT MIN(year) AS n FROM patents WHERE year IS NOT NULL", c
    ).iloc[0, 0]
    yr_max = pd.read_sql(
        "SELECT MAX(year) AS n FROM patents WHERE year IS NOT NULL", c
    ).iloc[0, 0]
    return int(total), int(inv), int(co), int(ctr), int(yr_min), int(yr_max)


@st.cache_data(ttl=300)
def load_yearly(y0, y1):
    return pd.read_sql(f"""
        SELECT year, COUNT(*) AS patents FROM patents
        WHERE year BETWEEN {y0} AND {y1}
        GROUP BY year ORDER BY year
    """, get_conn())


@st.cache_data(ttl=300)
def load_top_inventors(n):
    return pd.read_sql(f"""
        SELECT i.name, i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
        GROUP BY i.inventor_id ORDER BY patents DESC LIMIT {n}
    """, get_conn())


@st.cache_data(ttl=300)
def load_top_companies(n):
    return pd.read_sql(f"""
        SELECT c.name, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN companies c ON r.company_id = c.company_id
        WHERE r.company_id != ''
        GROUP BY c.company_id ORDER BY patents DESC LIMIT {n}
    """, get_conn())


@st.cache_data(ttl=300)
def load_countries():
    return pd.read_sql("""
        SELECT i.country, COUNT(DISTINCT r.patent_id) AS patents
        FROM relationships r
        JOIN inventors i ON r.inventor_id = i.inventor_id
        WHERE r.inventor_id != ''
          AND i.country NOT IN ('Unknown','')
        GROUP BY i.country ORDER BY patents DESC LIMIT 30
    """, get_conn())







# ── Sidebar ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:4px 0 24px">
      <div style="font-size:11px;color:{SUBTEXT};
                  font-family:'IBM Plex Mono',monospace;
                  letter-spacing:0.12em;text-transform:uppercase;
                  margin-bottom:6px;">◈ Patent Intel</div>
      <div style="font-size:24px;font-weight:900;color:{TEXT};
                  letter-spacing:-0.03em;line-height:1.1;">
        Global<br><span style="color:{ACCENT};">Patents</span>
      </div>
      <div style="font-size:11px;color:{SUBTEXT};margin-top:5px;
                  font-family:'IBM Plex Mono',monospace;">
        USPTO · PatentsView · 1976–2025
      </div>
    </div>
    <div style="height:1px;background:linear-gradient(90deg,{BORDER2},transparent);
                margin-bottom:24px;"></div>
    """, unsafe_allow_html=True)
    
    st.markdown(f"""<div style="font-size:10px;font-weight:600;color:{SUBTEXT};
      text-transform:uppercase;letter-spacing:0.13em;
      font-family:'IBM Plex Mono',monospace;margin-bottom:12px;">
      ⊞  Filters</div>""", unsafe_allow_html=True)

    year_range = st.slider("Year Range", 1976, 2025, (1995, 2024), step=1)
    top_n      = st.select_slider("Top N Results", [5, 10, 15, 20, 25, 30], value=15)

    st.markdown(f"""<div style="height:1px;background:{BORDER};margin:20px 0;"></div>
    <div style="font-size:10px;font-weight:600;color:{SUBTEXT};
      text-transform:uppercase;letter-spacing:0.13em;
      font-family:'IBM Plex Mono',monospace;margin-bottom:12px;">
      ⊡  Display</div>""", unsafe_allow_html=True)

    show_tables  = st.toggle("Show data tables",     value=True)
    show_rolling = st.toggle("Show rolling average", value=True)

    st.markdown(f"""
    <div style="margin-top:28px;padding:16px;background:{SURFACE};
                border:1px solid {BORDER};border-radius:12px;">
      <div style="font-size:10px;font-weight:600;color:{SUBTEXT};
                  text-transform:uppercase;letter-spacing:0.12em;
                  font-family:'IBM Plex Mono',monospace;margin-bottom:10px;">
        ℹ  About
      </div>
      <div style="font-size:11px;color:{SUBTEXT};line-height:2.1;
                  font-family:'IBM Plex Mono',monospace;">
        Source &nbsp;: PatentsView<br>
        Coverage: 1976 – 2025<br>
        Engine &nbsp;: Python · SQLite<br>
        Charts &nbsp;: Plotly
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────
total, n_inv, n_co, n_ctr, yr_min, yr_max = load_summary()

st.markdown(f"""
<div style="margin-bottom:32px;">
  <div class="header-badge">LIVE ANALYTICS DASHBOARD</div>
  <h1 class="page-title">Global <span>Patent</span> Intelligence</h1>
  <p class="page-subtitle">
    Comprehensive analysis of USPTO granted patent data &nbsp;·&nbsp; {yr_min} – {yr_max}
  </p>
</div>
""", unsafe_allow_html=True)


# ── KPI cards ──────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4, gap="medium")
kpi_data = [
    (k1, "Total Patents",  f"{total:,}",  "Granted patents indexed",   ACCENT),
    (k2, "Inventors",      f"{n_inv:,}",  "Disambiguated profiles",    ACCENT2),
    (k3, "Companies",      f"{n_co:,}",   "Assignee organisations",    ACCENT3),
    (k4, "Countries",      f"{n_ctr:,}",  "Inventor nationalities",    ACCENT4),
]
for col, label, val, sub, color in kpi_data:
    with col:
        st.markdown(f"""
        <div class="stat-card" style="border-top:2px solid {color};">
          <div class="sc-label">{label}</div>
          <div class="sc-value" style="color:{color};">{val}</div>
          <div class="sc-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div class="dash-divider"></div>', unsafe_allow_html=True)


# ── Tabs ───────────────────────────────────────────────────────────────
tab_trends, tab_inv, tab_co, tab_ctr = st.tabs([
    "  📈  Trends  ",
    "  👤  Inventors  ",
    "  🏢  Companies  ",
    "  🌍  Countries  ",
])


# ══════════════════════════════════════════════════════════════════════
# TAB 1 — TRENDS
# ══════════════════════════════════════════════════════════════════════
with tab_trends:
    st.markdown(f"""
    <div class="section-heading">
      <div class="sh-icon" style="background:rgba(59,158,255,0.12);">📈</div>
      <div>
        <div class="sh-text">Patent Filing Trends</div>
        <div class="sh-sub">Annual grant counts and moving averages · {year_range[0]}–{year_range[1]}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    df_yr = load_yearly(year_range[0], year_range[1])

    if df_yr.empty:
        st.info("No data for the selected year range. Adjust the slider in the sidebar.")
    else:
        df_yr["rolling5"] = df_yr["patents"].rolling(5, center=True).mean()
        peak = df_yr.loc[df_yr["patents"].idxmax()]

        fig_trend = go.Figure()
        fig_trend.add_trace(go.Bar(
            x=df_yr["year"], y=df_yr["patents"],
            name="Annual Grants",
            marker=dict(
                color=df_yr["patents"],
                colorscale=[[0,"#0a1a35"],[0.4,"#0f3060"],[1.0,ACCENT]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{x}</b><br>Patents: <b>%{y:,}</b><extra></extra>",
        ))
        if show_rolling:
            fig_trend.add_trace(go.Scatter(
                x=df_yr["year"], y=df_yr["rolling5"],
                name="5-Year Avg",
                line=dict(color=ACCENT2, width=2.8, dash="dot"),
                hovertemplate="<b>%{x}</b><br>5-yr avg: <b>%{y:,.0f}</b><extra></extra>",
            ))

        fig_trend.add_annotation(
            x=peak["year"], y=peak["patents"],
            text=f"<b>Peak {int(peak['year'])}</b><br>{int(peak['patents']):,}",
            showarrow=True, arrowhead=3, arrowsize=1.2,
            arrowcolor=ACCENT2, arrowwidth=1.8,
            font=dict(color=ACCENT2, size=11, family="IBM Plex Mono"),
            bgcolor=CARD2, bordercolor=ACCENT2,
            borderwidth=1, borderpad=8, ay=-55, ax=20,
        )
        fig_trend.update_layout(
            **chart(height=430, title="USPTO Granted Patents Per Year"),
            barmode="overlay",
            # yaxis=dict(gridcolor=BORDER, tickformat=",", linecolor=BORDER2),
            # xaxis=dict(gridcolor="rgba(0,0,0,0)", linecolor=BORDER2),
        )
        st.plotly_chart(fig_trend, use_container_width=True,
                        config={"displayModeBar": False})

        # Period stat cards
        st.markdown('<div class="sub-label">Period Statistics</div>',
                    unsafe_allow_html=True)

        growth_pct = (
            (df_yr["patents"].iloc[-1] - df_yr["patents"].iloc[0])
            / df_yr["patents"].iloc[0] * 100
        )
        c_g   = ACCENT3 if growth_pct > 0 else "#f87171"
        arrow = "▲" if growth_pct > 0 else "▼"

        s1, s2, s3, s4 = st.columns(4, gap="medium")
        stats = [
            (s1, "Peak Year",     str(int(peak['year'])),          f"{int(peak['patents']):,} patents granted", ACCENT2),
            (s2, "Annual Average",f"{int(df_yr['patents'].mean()):,}", "Across selected period",              ACCENT),
            (s3, "Period Total",  f"{int(df_yr['patents'].sum()):,}",  f"{year_range[0]} – {year_range[1]}",  ACCENT3),
            (s4, "Period Growth", f"{arrow} {abs(growth_pct):.1f}%",  f"{year_range[0]} → {year_range[1]}",  c_g),
        ]
        for col, lbl, val, sub, color in stats:
            with col:
                st.markdown(f"""
                <div class="stat-card" style="border-top:2px solid {color};">
                  <div class="sc-label">{lbl}</div>
                  <div class="sc-value" style="color:{color};">{val}</div>
                  <div class="sc-sub">{sub}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Decade breakdown
        df_yr["decade"] = (df_yr["year"] // 10 * 10).astype(str) + "s"
        dec_avg = df_yr.groupby("decade")["patents"].mean().reset_index()
        dec_avg.columns = ["decade", "avg"]

        fig_dec = px.bar(
            dec_avg, x="decade", y="avg",
            color="avg",
            color_continuous_scale=[[0,"#0a1a35"],[0.5,"#0f3060"],[1,ACCENT3]],
            labels={"avg": "Avg / Year", "decade": ""},
        )
        fig_dec.update_traces(
            hovertemplate="<b>%{x}</b><br>Avg: %{y:,.0f} patents/yr<extra></extra>",
            marker_line_width=0,
        )
        fig_dec.update_layout(
            **chart(height=290, title="Average Annual Patents by Decade"),
            coloraxis_showscale=False,
            # xaxis=dict(gridcolor="rgba(0,0,0,0)", linecolor=BORDER2),
            # yaxis=dict(gridcolor=BORDER, tickformat=",", linecolor=BORDER2),
        )
        st.plotly_chart(fig_dec, use_container_width=True,
                        config={"displayModeBar": False})

        if show_tables:
            with st.expander("📄  Raw yearly data"):
                st.dataframe(
                    df_yr[["year","patents"]].set_index("year")
                    .rename(columns={"patents":"Patent Count"}),
                    use_container_width=True,
                )


# ══════════════════════════════════════════════════════════════════════
# TAB 2 — INVENTORS
# ══════════════════════════════════════════════════════════════════════
with tab_inv:
    st.markdown(f"""
    <div class="section-heading">
      <div class="sh-icon" style="background:rgba(255,107,61,0.12);">👤</div>
      <div>
        <div class="sh-text">Top Inventors</div>
        <div class="sh-sub">Ranked by total patents granted · Top {top_n} profiles</div>
      </div>
    </div>""", unsafe_allow_html=True)

    df_inv = load_top_inventors(top_n)
    df_inv["patents"] = pd.to_numeric(df_inv["patents"], errors="coerce").fillna(0)
    col_chart, col_list = st.columns([3, 2], gap="large")

    with col_chart:
        fig_inv = go.Figure(go.Bar(
            x=df_inv["patents"], y=df_inv["name"],
            orientation="h",
            marker=dict(
                color=df_inv["patents"],
                colorscale=[[0,"#0a1a35"],[0.5,"#0d3568"],[1,ACCENT]],
                line=dict(width=0),
            ),
            customdata=df_inv["country"],
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Country: %{customdata}<br>"
                "Patents: <b>%{x:,}</b><extra></extra>"
            ),
        ))
        fig_inv.update_layout(
            **chart(height=540, title=f"Top {top_n} Inventors by Patent Count"),
        )
        fig_inv.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)",
                             tickfont=dict(size=11), linecolor=BORDER2)
        fig_inv.update_xaxes(gridcolor=BORDER, tickformat=",", linecolor=BORDER2)
        st.plotly_chart(fig_inv, use_container_width=True,
                        config={"displayModeBar": False})

    with col_list:
        st.markdown('<div class="sub-label">Inventor Profiles</div>',
                    unsafe_allow_html=True)
        for rank, row in enumerate(df_inv.head(12).itertuples(), 1):
            rank_color = (GOLD if rank == 1 else
                          TEXT2 if rank == 2 else
                          ACCENT2 if rank == 3 else SUBTEXT)
            bar_w = int(row.patents / df_inv["patents"].max() * 100)
            st.markdown(f"""
            <div class="rank-item">
              <div class="ri-rank" style="color:{rank_color};">#{rank}</div>
              <div style="flex:1;overflow:hidden;margin:0 8px;">
                <div class="ri-name">{row.name}</div>
                <div style="height:3px;background:{BORDER};border-radius:2px;margin-top:5px;">
                  <div style="height:100%;width:{bar_w}%;
                              background:linear-gradient(90deg,{ACCENT},{ACCENT4});
                              border-radius:2px;"></div>
                </div>
              </div>
              <div class="ri-country">{row.country}</div>
              <div class="ri-count">{row.patents:,}</div>
            </div>""", unsafe_allow_html=True)

    # Country breakdown
    st.markdown('<div class="sub-label" style="margin-top:28px;">Nationality of Top Inventors</div>',
                unsafe_allow_html=True)

    ctr_inv = df_inv["country"].value_counts().reset_index()
    ctr_inv.columns = ["country", "count"]

    cp, cb = st.columns(2, gap="large")
    with cp:
        fig_pie = go.Figure(go.Pie(
            labels=ctr_inv["country"], values=ctr_inv["count"],
            hole=0.58, textinfo="label+percent",
            textfont=dict(size=11, family="IBM Plex Mono"),
            marker=dict(
                colors=[ACCENT, ACCENT2, ACCENT3, ACCENT4,
                        GOLD, PINK, "#a3e635", "#67e8f9"],
                line=dict(color=CARD, width=2.5),
            ),
            hovertemplate="<b>%{label}</b><br>%{value} inventors (%{percent})<extra></extra>",
        ))
        fig_pie.update_layout(
            **chart(height=320, title="Country Distribution"),
            showlegend=True,
            legend_orientation="v", legend_x=1.0, legend_y=0.5,
            legend_font=dict(size=10),
        )
        st.plotly_chart(fig_pie, use_container_width=True,
                        config={"displayModeBar": False})

    with cb:
        fig_cib = px.bar(
            ctr_inv, x="country", y="count",
            color="count",
            color_continuous_scale=[[0,"#0a2518"],[1,ACCENT3]],
            labels={"count": "Inventors", "country": ""},
        )
        fig_cib.update_traces(
            hovertemplate="<b>%{x}</b><br>%{y} inventors<extra></extra>",
            marker_line_width=0,
        )
        fig_cib.update_layout(
            **chart(height=320, title="Inventors per Country"),
            coloraxis_showscale=False,
        )
        fig_cib.update_xaxes(gridcolor="rgba(0,0,0,0)", linecolor=BORDER2)
        fig_cib.update_yaxes(gridcolor=BORDER, linecolor=BORDER2)
        st.plotly_chart(fig_cib, use_container_width=True,
                        config={"displayModeBar": False})

    if show_tables:
        with st.expander("📄  Full inventor table"):
            d = df_inv.copy()
            d.index = range(1, len(d)+1)
            d.columns = ["Inventor", "Country", "Patents"]
            st.dataframe(d, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 3 — COMPANIES
# ══════════════════════════════════════════════════════════════════════
with tab_co:
    st.markdown(f"""
    <div class="section-heading">
      <div class="sh-icon" style="background:rgba(0,212,168,0.12);">🏢</div>
      <div>
        <div class="sh-text">Top Patent Holders</div>
        <div class="sh-sub">Companies ranked by portfolio size · Top {top_n}</div>
      </div>
    </div>""", unsafe_allow_html=True)

    df_co = load_top_companies(top_n)
    df_co["patents"] = pd.to_numeric(df_co["patents"], errors="coerce").fillna(0)
    df_co["share"]   = (df_co["patents"] / df_co["patents"].sum() * 100).round(1)

    fig_co = go.Figure(go.Bar(
        x=df_co["patents"], y=df_co["name"],
        orientation="h",
        marker=dict(
            color=df_co["patents"],
            colorscale=[[0,"#0a251a"],[0.4,"#0d4a32"],[1,ACCENT3]],
            line=dict(width=0),
        ),
        customdata=df_co["share"],
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Patents: <b>%{x:,}</b><br>"
            "Share: %{customdata:.1f}%<extra></extra>"
        ),
    ))
    fig_co.update_layout(
        **chart(height=580, title=f"Top {top_n} Patent Holders"),
    )
    fig_co.update_yaxes(autorange="reversed", gridcolor="rgba(0,0,0,0)",
                        tickfont=dict(size=11), linecolor=BORDER2)
    fig_co.update_xaxes(gridcolor=BORDER, tickformat=",", linecolor=BORDER2)
    st.plotly_chart(fig_co, use_container_width=True,
                    config={"displayModeBar": False})

    st.markdown('<div class="sub-label">Portfolio Market Share</div>',
                unsafe_allow_html=True)

    fig_tree = px.treemap(
        df_co.head(12), path=["name"], values="patents",
        color="patents",
        color_continuous_scale=[[0,"#0a251a"],[0.5,"#0d5540"],[1,ACCENT3]],
        custom_data=["share"],
    )
    fig_tree.update_traces(
        texttemplate="<b>%{label}</b><br>%{value:,}",
        hovertemplate="<b>%{label}</b><br>Patents: %{value:,}<br>Share: %{customdata[0]:.1f}%<extra></extra>",
        textfont=dict(family="Outfit, sans-serif", size=12, color=TEXT),
        marker=dict(line=dict(color=BG, width=2.5)),
    )
    fig_tree.update_layout(
        **chart(height=400, title="Patent Portfolio Treemap — Top 12"),
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_tree, use_container_width=True,
                    config={"displayModeBar": False})

    if show_tables:
        with st.expander("📄  Full company table"):
            d = df_co[["name","patents","share"]].copy()
            d.index = range(1, len(d)+1)
            d.columns = ["Company", "Patents", "Share %"]
            st.dataframe(d, use_container_width=True)


# ══════════════════════════════════════════════════════════════════════
# TAB 4 — COUNTRIES
# ══════════════════════════════════════════════════════════════════════
with tab_ctr:
    st.markdown(f"""
    <div class="section-heading">
      <div class="sh-icon" style="background:rgba(155,125,255,0.12);">🌍</div>
      <div>
        <div class="sh-text">Global Patent Distribution</div>
        <div class="sh-sub">Patent output by inventor nationality · {n_ctr} countries</div>
      </div>
    </div>""", unsafe_allow_html=True)

    df_ctr = load_countries()
    df_ctr["patents"] = pd.to_numeric(df_ctr["patents"], errors="coerce").fillna(0)
    
    # ── ISO-2 to ISO-3 Mapping (for Choropleth) ───────────────────────
    # Plotly's ISO-3 mode needs 3-letter codes, but data has 2-letter codes.
    _iso_map = {
        'US': 'USA', 'CN': 'CHN', 'JP': 'JPN', 'DE': 'DEU', 'KR': 'KOR',
        'GB': 'GBR', 'FR': 'FRA', 'CA': 'CAN', 'CH': 'CHE', 'TW': 'TWN',
        'IN': 'IND', 'NL': 'NLD', 'SE': 'SWE', 'IL': 'ISR', 'IT': 'ITA',
        'AU': 'AUS', 'AT': 'AUT', 'FI': 'FIN', 'BE': 'BEL', 'DK': 'DNK',
        'SG': 'SGP', 'ES': 'ESP', 'RU': 'RUS', 'BR': 'BRA', 'IE': 'IRL',
        'NO': 'NOR', 'PL': 'POL', 'CZ': 'CZE', 'NZ': 'NZL', 'TR': 'TUR'
    }
    df_ctr["iso3"] = df_ctr["country"].map(_iso_map).fillna(df_ctr["country"])
    
    df_ctr["share"] = (df_ctr["patents"] / df_ctr["patents"].sum() * 100).round(2)
    df_ctr["rank"]  = range(1, len(df_ctr) + 1)
    df_ctr["cumshare"] = df_ctr["share"].cumsum().round(2)

    # ── Session state for selected country ────────────────────────────
    if "selected_country" not in st.session_state:
        st.session_state["selected_country"] = None

    sel_country = st.session_state["selected_country"]

    # ── Choropleth map ─────────────────────────────────────────────────
    fig_map = px.choropleth(
        df_ctr,
        locations="iso3", locationmode="ISO-3",
        color="patents", hover_name="country",
        custom_data=["share", "rank", "cumshare"],
        color_continuous_scale=[
            [0.0,"#0a1428"],[0.1,"#0e2d5e"],
            [0.4,"#1464a8"],[0.7,ACCENT],[1.0,"#d0eeff"],
        ],
        labels={"patents":"Patents","share":"Share %"},
    )
    fig_map.update_traces(
        hovertemplate=(
            "<b>%{hovertext}</b><br>"
            "─────────────────<br>"
            "🏅 Global Rank : <b>#%{customdata[1]}</b><br>"
            "📄 Patents     : <b>%{z:,}</b><br>"
            "📊 Share       : <b>%{customdata[0]:.2f}%</b><br>"
            "📈 Cumul. Share: <b>%{customdata[2]:.2f}%</b><br>"
            "<i style='font-size:10px'>Click to filter charts below</i>"
            "<extra></extra>"
        )
    )

    # highlight selected country with a bright border
    if sel_country:
        sel_iso3 = _iso_map.get(sel_country, sel_country)
        fig_map.add_trace(go.Choropleth(
            locations=[sel_iso3], locationmode="ISO-3",
            z=[1],
            colorscale=[[0, "rgba(0,0,0,0)"], [1, "rgba(0,0,0,0)"]],
            showscale=False,
            marker=dict(line=dict(color=ACCENT2, width=3)),
            hoverinfo="skip",
        ))

    fig_map.update_layout(
        **chart(height=480, title="Global Patent Distribution by Country  ·  Click a country to filter"),
        geo=dict(
            bgcolor=CARD, landcolor="#16243a",
            oceancolor="#080e1c", showocean=True,
            lakecolor="#080e1c", showlakes=True,
            framecolor=BORDER, showcoastlines=True,
            coastlinecolor=BORDER2, showland=True,
        ),
        coloraxis_colorbar=dict(
            title=dict(text="Patents",
                       font=dict(size=11, family="IBM Plex Mono", color=TEXT2)),
            tickfont=dict(size=9, family="IBM Plex Mono", color=TEXT2),
            thickness=10, len=0.55,
            bgcolor=SURFACE, bordercolor=BORDER, tickformat=",",
        ),
    )

    map_event = st.plotly_chart(
        fig_map, use_container_width=True,
        config={"displayModeBar": False},
        on_select="rerun", key="map_select",
    )

    # ── Handle click event ─────────────────────────────────────────────
    pts = (map_event.selection or {}).get("points", [])
    if pts:
        # Get clicked code (could be ISO-2 from hovertext or ISO-3 from location)
        raw_clicked = pts[0].get("hovertext") or pts[0].get("location")
        
        # Convert back to ISO-2 if it's an ISO-3 code
        _rev_map = {v: k for k, v in _iso_map.items()}
        clicked  = _rev_map.get(raw_clicked, raw_clicked)

        if clicked and clicked != st.session_state["selected_country"]:
            st.session_state["selected_country"] = clicked
            st.rerun()

    # ── Filter status bar ──────────────────────────────────────────────
    if sel_country:
        row = df_ctr[df_ctr["country"] == sel_country]
        if not row.empty:
            r = row.iloc[0]
            fc1, fc2 = st.columns([5, 1])
            with fc1:
                st.markdown(
                    f"""<div style="background:rgba(59,158,255,0.08);border:1px solid {BORDER2};
                    border-radius:10px;padding:10px 18px;font-family:'IBM Plex Mono',monospace;
                    font-size:12px;color:{TEXT};">
                    🔍 Filtered: <b style="color:{ACCENT};">{sel_country}</b>
                    &nbsp;·&nbsp; Rank <b>#{int(r['rank'])}</b>
                    &nbsp;·&nbsp; <b>{int(r['patents']):,}</b> patents
                    &nbsp;·&nbsp; <b>{r['share']:.2f}%</b> global share
                    </div>""", unsafe_allow_html=True
                )
            with fc2:
                if st.button("✕ Clear filter", key="clear_map_filter"):
                    st.session_state["selected_country"] = None
                    st.rerun()

    st.markdown('<div class="sub-label">Regional Breakdown</div>',
                unsafe_allow_html=True)

    # ── Apply filter to charts below ───────────────────────────────────
    if sel_country and sel_country in df_ctr["country"].values:
        df_chart = df_ctr[df_ctr["country"] == sel_country]
        bar_title = f"Patent Profile — {sel_country}"
    else:
        df_chart = df_ctr.head(15)
        bar_title = "Top 15 Countries by Patent Count"

    rc1, rc2 = st.columns([3, 2], gap="large")
    with rc1:
        bar_colors = [
            ACCENT if (sel_country and row["country"] == sel_country) else c
            for _, row in df_chart.iterrows()
            for c in [ACCENT]
        ] if not sel_country else [ACCENT] * len(df_chart)

        fig_cbar = go.Figure(go.Bar(
            x=df_chart["country"],
            y=df_chart["patents"],
            marker=dict(
                color=df_chart["patents"],
                colorscale=[[0,"#0a1428"],[0.5,"#0e3060"],[1,ACCENT]],
                line=dict(
                    color=[ACCENT2 if (sel_country and r == sel_country) else "rgba(0,0,0,0)"
                           for r in df_chart["country"]],
                    width=2,
                ),
            ),
            customdata=df_chart[["share", "rank"]].values,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Rank   : <b>#%{customdata[1]}</b><br>"
                "Patents: <b>%{y:,}</b><br>"
                "Share  : <b>%{customdata[0]:.2f}%</b>"
                "<extra></extra>"
            ),
        ))
        fig_cbar.update_layout(
            **chart(height=380, title=bar_title),
        )
        fig_cbar.update_xaxes(gridcolor="rgba(0,0,0,0)", tickangle=-35, linecolor=BORDER2)
        fig_cbar.update_yaxes(gridcolor=BORDER, tickformat=",", linecolor=BORDER2)
        st.plotly_chart(fig_cbar, use_container_width=True,
                        config={"displayModeBar": False})

    with rc2:
        top8  = df_ctr.head(8).copy()
        other = pd.DataFrame([{
            "country": "Other",
            "patents":  df_ctr.iloc[8:]["patents"].sum(),
            "share":    df_ctr.iloc[8:]["share"].sum(),
            "rank": 9, "cumshare": 100.0,
        }])
        pie_df = pd.concat([top8, other], ignore_index=True)

        pull_vals = [
            0.12 if (sel_country and r == sel_country) else 0
            for r in pie_df["country"]
        ]

        fig_cpie = go.Figure(go.Pie(
            labels=pie_df["country"], values=pie_df["patents"],
            hole=0.55, textinfo="label+percent",
            textfont=dict(size=10, family="IBM Plex Mono"),
            pull=pull_vals,
            marker=dict(
                colors=[ACCENT, ACCENT2, ACCENT3, ACCENT4,
                        GOLD, PINK, "#a3e635", "#67e8f9", SUBTEXT],
                line=dict(color=CARD, width=2.5),
            ),
            hovertemplate="<b>%{label}</b><br>%{value:,} patents (%{percent})<extra></extra>",
        ))
        fig_cpie.update_layout(
            **chart(height=380, title="Share by Country"),
            legend_orientation="v", legend_x=1.0, legend_y=0.5,
            legend_font=dict(size=9),
        )
        st.plotly_chart(fig_cpie, use_container_width=True,
                        config={"displayModeBar": False})

    # Insight cards
    st.markdown('<div class="sub-label">Key Insights</div>',
                unsafe_allow_html=True)

    if sel_country and sel_country in df_ctr["country"].values:
        r = df_ctr[df_ctr["country"] == sel_country].iloc[0]
        top3_share = df_ctr.head(3)["share"].sum()
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        insights = [
            (ci1, "Selected Country", r["country"],
             f"Rank #{int(r['rank'])} globally", ACCENT2),
            (ci2, "Patent Count",     f"{int(r['patents']):,}",
             f"{r['share']:.2f}% of all indexed patents", ACCENT),
            (ci3, "Cumulative Share", f"{r['cumshare']:.1f}%",
             f"Top {int(r['rank'])} countries combined", ACCENT3),
        ]
    else:
        top_c      = df_ctr.iloc[0]
        top3_share = df_ctr.head(3)["share"].sum()
        ci1, ci2, ci3 = st.columns(3, gap="medium")
        insights = [
            (ci1, "Leading Country", top_c['country'],
             f"{int(top_c['patents']):,} patents · {top_c['share']:.1f}% of total", ACCENT2),
            (ci2, "Top 3 Combined",  f"{top3_share:.1f}%",
             " · ".join(df_ctr.head(3)["country"].tolist()), ACCENT),
            (ci3, "Countries Active", str(n_ctr),
             "Unique inventor nationalities", ACCENT3),
        ]
    for col, lbl, val, sub, color in insights:
        with col:
            st.markdown(f"""
            <div class="stat-card" style="border-top:2px solid {color};">
              <div class="sc-label">{lbl}</div>
              <div class="sc-value" style="color:{color};">{val}</div>
              <div class="sc-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    if show_tables:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("📄  Full country table"):
            d = df_ctr[["country", "rank", "patents", "share", "cumshare"]].copy()
            d.index = range(1, len(d)+1)
            d.columns = ["Country", "Rank", "Patents", "Share %", "Cumul. Share %"]
            st.dataframe(d, use_container_width=True)


# ── Footer ─────────────────────────────────────────────────────────────
st.markdown(f"""
<div style="margin-top:60px;padding:22px 0 8px;
            border-top:1px solid {BORDER};
            display:flex;justify-content:space-between;
            align-items:center;flex-wrap:wrap;gap:8px;">
  <div style="font-size:11px;color:{SUBTEXT};
              font-family:'IBM Plex Mono',monospace;">
    🔬 &nbsp;Global Patent Intelligence &nbsp;·&nbsp; USPTO PatentsView
  </div>
  <div style="font-size:11px;color:{SUBTEXT};
              font-family:'IBM Plex Mono',monospace;">
    <span style="color:{ACCENT};">Streamlit</span> &nbsp;·&nbsp;
    <span style="color:{ACCENT3};">Python</span> &nbsp;·&nbsp;
    <span style="color:{ACCENT2};">SQLite</span> &nbsp;·&nbsp;
    <span style="color:{ACCENT4};">Plotly</span>
  </div>
</div>
""", unsafe_allow_html=True)
