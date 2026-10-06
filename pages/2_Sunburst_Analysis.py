import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.cleaning import load_data  # type: ignore[reportMissingImports]
from utils.time_control import check_time  # type: ignore[reportMissingImports]

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
st.set_page_config(
    page_title="Google Play | Sunburst Intelligence",
    page_icon="🟢",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --------------------------------------------------
# PROFESSIONAL DARK THEME
# --------------------------------------------------
st.markdown(
    """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: #0b0f14; color: #f4f7fb; }
    [data-testid="stSidebar"] { background: #111720; border-right: 1px solid #26313d; }
    [data-testid="stSidebar"] * { color: #e5edf5; }
    .hero {
        background: linear-gradient(120deg, #172b30, #14232b 55%, #17202d);
        border: 1px solid #29443f; padding: 28px 32px; border-radius: 18px;
        margin: 8px 0 24px 0;
    }
    .hero-label { color: #55d6a5; font-size: 12px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; }
    .hero h1 { font-size: 30px; font-weight: 800; color: #fff; margin: 12px 0 8px 0; }
    .hero p { color: #b4c4d0; font-size: 14px; margin: 0; }
    .section-title { font-size: 19px; font-weight: 700; color: #f4f7fb; margin: 22px 0 14px 0; }
    .metric-card {
        background: linear-gradient(145deg, #171f29, #121922); border: 1px solid #283541;
        border-radius: 15px; padding: 20px; min-height: 120px;
    }
    .metric-label { font-size: 12px; font-weight: 600; color: #9eafbf; margin-bottom: 12px; }
    .metric-value { font-size: 27px; font-weight: 800; color: #fff; letter-spacing: -0.7px; }
    .metric-note { font-size: 11px; color: #57d5a1; margin-top: 7px; }
    .insight-card {
        background: #141c25; border: 1px solid #283541; border-left: 3px solid #42c997;
        border-radius: 10px; padding: 16px 18px; min-height: 100px;
    }
    .insight-label { color: #9eafbf; font-size: 12px; font-weight: 600; }
    .insight-value { color: #fff; font-size: 19px; font-weight: 700; margin-top: 9px; }
    .footer { color: #82909e; font-size: 11px; text-align: center; padding: 20px 0 5px 0; border-top: 1px solid #283541; margin-top: 30px; }
    div[data-testid="stPlotlyChart"] { background: #111720; border: 1px solid #283541; border-radius: 16px; padding: 10px; }
</style>
""",
    unsafe_allow_html=True,
)

# --------------------------------------------------
# STRICT TIME RESTRICTION: 6 PM - 8 PM IST
# --------------------------------------------------
if not check_time(18, 20):
    st.warning("This analytics page is available only between 6 PM and 8 PM IST.")
    st.stop()

# --------------------------------------------------
# HELPERS
# --------------------------------------------------
def compact_number(value: float) -> str:
    if value >= 1e9:
        return f"{value / 1e9:.2f}B"
    if value >= 1e6:
        return f"{value / 1e6:.2f}M"
    if value >= 1e3:
        return f"{value / 1e3:.1f}K"
    return f"{value:,.0f}"


def clean_installs(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace(",", "", regex=False)
        .str.replace("+", "", regex=False)
        .str.strip(),
        errors="coerce",
    )


def clean_size_mb(data: pd.DataFrame) -> pd.Series:
    # The uploaded dataset includes Size_MB, which is the safest source.
    if "Size_MB" in data.columns:
        return pd.to_numeric(data["Size_MB"], errors="coerce")

    # Fallback for projects where load_data() only returns raw Size.
    raw = data["Size"].astype(str).str.strip()
    numeric = pd.to_numeric(raw.str.extract(r"([\d.]+)", expand=False), errors="coerce")
    is_kb = raw.str.contains(r"k$", case=False, regex=True, na=False)
    numeric.loc[is_kb] = numeric.loc[is_kb] / 1024.0
    numeric.loc[raw.str.contains("Varies with device", case=False, na=False)] = pd.NA
    return numeric


def weighted_rating(group: pd.DataFrame) -> float:
    review_sum = group["Reviews"].sum()
    if review_sum <= 0:
        return 0.0
    return float((group["Rating"] * group["Reviews"]).sum() / review_sum)


# Tamil / French / Spanish display translations.
TRANSLATIONS = {
    "FAMILY": "குடும்பம் · Famille · Familia",
    "TOOLS": "கருவிகள் · Outils · Herramientas",
    "PHOTOGRAPHY": "புகைப்படம் · Photographie · Fotografía",
    "PRODUCTIVITY": "உற்பத்தித்திறன் · Productivité · Productividad",
    "HEALTH_AND_FITNESS": "உடல்நலம் & உடற்பயிற்சி · Santé & Fitness · Salud y Fitness",
    "VIDEO_PLAYERS": "வீடியோ பிளேயர்கள் · Lecteurs vidéo · Reproductores de vídeo",
    "LIFESTYLE": "வாழ்க்கை முறை · Style de vie · Estilo de vida",
    "FINANCE": "நிதி · Finance · Finanzas",
    "BUSINESS": "வணிகம் · Affaires · Negocios",
    "ENTERTAINMENT": "பொழுதுபோக்கு · Divertissement · Entretenimiento",
}

# --------------------------------------------------
# LOAD + PREPARE DATA
# --------------------------------------------------
@st.cache_data(show_spinner="Loading and preparing app data...")
def get_data() -> pd.DataFrame:
    data = load_data().copy()

    required = ["App", "Category", "Rating", "Reviews", "Installs", "Size", "Type"]
    missing = [c for c in required if c not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data["App"] = data["App"].astype("string").str.strip()
    data["Category"] = data["Category"].astype("string").str.strip().str.upper()
    data["Type"] = data["Type"].fillna("Unknown").astype(str).str.strip()
    data["Rating"] = pd.to_numeric(data["Rating"], errors="coerce")
    data["Reviews"] = pd.to_numeric(
        data["Reviews"].astype(str).str.replace(",", "", regex=False), errors="coerce"
    )
    data["Installs"] = clean_installs(data["Installs"])
    data["Size_MB_Clean"] = clean_size_mb(data)

    data = data.dropna(
        subset=["App", "Category", "Rating", "Reviews", "Installs", "Size_MB_Clean", "Type"]
    )

    # Exact task eligibility rules.
    eligible = data[
        (data["Rating"] >= 4.0)
        & (data["Installs"] > 10_000)
        & (data["Reviews"] > 1_000)
        & (data["Size_MB_Clean"].between(15, 80, inclusive="both"))
        & (~data["App"].str.contains(r"\d", regex=True, na=False))
        & (~data["Category"].str.startswith(("A", "C", "G", "S"), na=False))
    ].copy()

    if eligible.empty:
        return eligible

    # Automatic top-five eligible categories by GLOBAL total installs.
    top_five = (
        eligible.groupby("Category", observed=True)["Installs"]
        .sum()
        .nlargest(5)
        .index
    )
    eligible = eligible[eligible["Category"].isin(top_five)].copy()

    # Dataset has no true Country field, so use an explicit Global placeholder.
    eligible["Country"] = "Global"
    eligible["App Type"] = eligible["Type"].replace({"Free": "Free Apps", "Paid": "Paid Apps"})
    eligible["App Type"] = eligible["App Type"].fillna("Unknown")

    eligible["Rating Band"] = pd.cut(
        eligible["Rating"],
        bins=[3.999, 4.2, 4.5, 4.7, 5.001],
        labels=["4.0–4.2", "4.2–4.5", "4.5–4.7", "4.7–5.0"],
        include_lowest=True,
        right=True,
    ).astype("string")

    eligible["Display Category"] = eligible["Category"].map(TRANSLATIONS).fillna(eligible["Category"])
    return eligible


try:
    df = get_data()
except Exception as exc:
    st.error(f"Dataset loading error: {exc}")
    st.stop()

if df.empty:
    st.warning("No apps satisfy all required Sunburst eligibility rules.")
    st.stop()

# --------------------------------------------------
# HERO
# --------------------------------------------------
st.markdown(
    """
<div class="hero">
    <div class="hero-label">Google Play Store · Data Intelligence</div>
    <h1>Hierarchical Sunburst Analysis</h1>
    <p>Country → Category → App Type → Rating Band · segment size = installs · colour = review-weighted rating.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.info(
    "Country note: this dataset has no real Country column, so the first hierarchy level is shown as “Global”. "
    "It should not be interpreted as country-specific analysis."
)

# --------------------------------------------------
# KPI METRICS
# --------------------------------------------------
total_installs = float(df["Installs"].sum())
total_apps = int(df["App"].nunique())
total_categories = int(df["Category"].nunique())
overall_weighted = weighted_rating(df)

k1, k2, k3, k4 = st.columns(4)
metrics = [
    (k1, "TOTAL INSTALLS", compact_number(total_installs), "Eligible top-five categories"),
    (k2, "APPS ANALYZED", f"{total_apps:,}", "Unique eligible app names"),
    (k3, "WEIGHTED RATING", f"{overall_weighted:.2f}/5", "Weighted by review count"),
    (k4, "CATEGORIES", f"{total_categories}", "Automatically selected top five"),
]
for col, label, value, note in metrics:
    with col:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-note">{note}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

# --------------------------------------------------
# BUILD EXPLICIT SUNBURST NODES
# --------------------------------------------------
def node_stats(group: pd.DataFrame) -> tuple[float, float, float, int]:
    return (
        float(group["Installs"].sum()),
        float(group["Reviews"].sum()),
        weighted_rating(group),
        int(group["App"].nunique()),
    )


nodes: list[dict] = []

def add_node(node_id: str, label: str, parent: str, group: pd.DataFrame) -> None:
    installs, reviews, wr, apps = node_stats(group)
    nodes.append(
        {
            "id": node_id,
            "label": label,
            "parent": parent,
            "value": installs,
            "reviews": reviews,
            "weighted": wr,
            "apps": apps,
        }
    )


add_node("Global", "Global", "", df)

for category, cat_group in df.groupby("Display Category", observed=True, sort=False):
    cat_id = f"Global|{category}"
    add_node(cat_id, str(category), "Global", cat_group)

    for app_type, type_group in cat_group.groupby("App Type", observed=True, sort=False):
        type_id = f"{cat_id}|{app_type}"
        add_node(type_id, str(app_type), cat_id, type_group)

        for rating_band, band_group in type_group.groupby("Rating Band", observed=True, sort=False):
            band_id = f"{type_id}|{rating_band}"
            add_node(band_id, str(rating_band), type_id, band_group)

node_df = pd.DataFrame(nodes)

# Highlight every node above 1M installs with a gold border.
line_colors = ["#d4af37" if value > 1_000_000 else "#111720" for value in node_df["value"]]
line_widths = [3 if value > 1_000_000 else 1.5 for value in node_df["value"]]

customdata = node_df[["reviews", "weighted", "apps"]].to_numpy()

fig = go.Figure(
    go.Sunburst(
        ids=node_df["id"],
        labels=node_df["label"],
        parents=node_df["parent"],
        values=node_df["value"],
        branchvalues="total",
        marker=dict(
            colors=node_df["weighted"],
            colorscale="RdYlGn",
            cmin=4.0,
            cmax=5.0,
            colorbar=dict(title="Weighted Rating"),
            line=dict(color=line_colors, width=line_widths),
        ),
        customdata=customdata,
        textinfo="label+percent parent",
        insidetextorientation="radial",
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Installs: %{value:,.0f}<br>"
            "Parent contribution: %{percentParent:.2%}<br>"
            "Unique apps: %{customdata[2]:,.0f}<br>"
            "Reviews: %{customdata[0]:,.0f}<br>"
            "Review-weighted rating: %{customdata[1]:.2f}<br>"
            "<extra></extra>"
        ),
        maxdepth=4,
    )
)

fig.update_layout(
    height=760,
    paper_bgcolor="#111720",
    plot_bgcolor="#111720",
    font=dict(family="Inter, sans-serif", color="#f4f7fb", size=12),
    margin=dict(t=20, b=20, l=15, r=15),
)

st.markdown('<div class="section-title">Install Distribution Explorer</div>', unsafe_allow_html=True)
st.caption("Click any segment to drill down. Gold outlines mark hierarchy segments with more than 1,000,000 installs.")
st.plotly_chart(
    fig,
    width='stretch',
    config={"displaylogo": False, "responsive": True, "scrollZoom": False},
)

# --------------------------------------------------
# CATEGORY PERFORMANCE
# --------------------------------------------------
category_rows = []
for category, group in df.groupby("Category", observed=True):
    category_rows.append(
        {
            "Category": category,
            "Translated Label": TRANSLATIONS.get(category, category),
            "Total Installs": float(group["Installs"].sum()),
            "Unique Apps": int(group["App"].nunique()),
            "Total Reviews": float(group["Reviews"].sum()),
            "Weighted Rating": weighted_rating(group),
        }
    )
category_stats = pd.DataFrame(category_rows).sort_values("Total Installs", ascending=False)

top_row = category_stats.iloc[0]
top_share = (top_row["Total Installs"] / total_installs * 100) if total_installs else 0

i1, i2, i3 = st.columns(3)
for col, label, value in [
    (i1, "Highest-install category", top_row["Category"]),
    (i2, "Category install share", f"{top_share:.1f}%"),
    (i3, "Highest category installs", compact_number(top_row["Total Installs"])),
]:
    with col:
        st.markdown(
            f'<div class="insight-card"><div class="insight-label">{label}</div><div class="insight-value">{value}</div></div>',
            unsafe_allow_html=True,
        )

with st.expander("View detailed top-five category performance", expanded=False):
    display_stats = category_stats.copy()
    display_stats["Total Installs"] = display_stats["Total Installs"].map(lambda x: f"{x:,.0f}")
    display_stats["Total Reviews"] = display_stats["Total Reviews"].map(lambda x: f"{x:,.0f}")
    display_stats["Weighted Rating"] = display_stats["Weighted Rating"].map(lambda x: f"{x:.3f}")
    st.dataframe(display_stats, width='stretch', hide_index=True)

# --------------------------------------------------
# REQUIREMENT AUDIT
# --------------------------------------------------
with st.expander("Eligibility rules used in this chart"):
    st.markdown(
        """
- Rating **≥ 4.0**
- Installs **> 10,000**
- Reviews **> 1,000**
- App size **15–80 MB**
- App name contains **no digits**
- Categories beginning with **A, C, G, or S are excluded**
- Only the **top five eligible categories by global installs** are retained
- Segment colour = **review-weighted average rating**
- Gold outline = hierarchy segment with **> 1,000,000 installs**
- Page visible only from **6 PM to 8 PM IST**
        """
    )

st.markdown(
    """
<div class="footer">
    GOOGLE PLAY STORE ANALYTICS · SUNBURST INTELLIGENCE<br>
    Interactive Data Visualization | Streamlit + Plotly
</div>
""",
    unsafe_allow_html=True,
)
