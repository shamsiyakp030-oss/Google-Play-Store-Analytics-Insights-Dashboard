import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ============================================================
# PAGE CONFIG + THEME
# ============================================================
st.set_page_config(
    page_title="Hexbin Intelligence | Play Store Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] {font-family: Inter, sans-serif;}
.stApp {background: #080b14; color: #f5f7fb;}
[data-testid="stHeader"] {background: rgba(8,11,20,.92);}
[data-testid="stSidebar"] {background: #0e1321; border-right: 1px solid #20283b;}
[data-testid="stSidebar"] * {color: #e8ecf5;}
h1,h2,h3 {color:#f7f8fc !important; letter-spacing:-.03em;}
p, label, .stCaption {color:#aab4c8;}
.block-container {padding-top: 1.6rem; padding-bottom: 2rem; max-width: 1600px;}
div[data-testid="stMetric"] {
 background: linear-gradient(145deg,#151d30,#101625);
 border:1px solid #27324a; border-radius:16px; padding:17px 18px;
 box-shadow:0 8px 26px rgba(0,0,0,.18); min-height:112px;
}
div[data-testid="stMetricLabel"] {color:#aab6cc !important; font-size:.83rem;}
div[data-testid="stMetricValue"] {color:#fff !important; font-size:1.65rem; font-weight:750;}
div[data-testid="stMetricDelta"] {font-size:.76rem;}
section[data-testid="stVerticalBlock"] > div:has(> div > .section-anchor) {gap:.4rem;}
.hero {
 background: radial-gradient(circle at 85% 10%,rgba(99,102,241,.24),transparent 35%),
 linear-gradient(120deg,#151d31,#101525 62%,#191329);
 border:1px solid #29334b; border-radius:22px; padding:25px 28px; margin:4px 0 20px;
}
.hero-kicker {font-size:.75rem; color:#a5b4fc; font-weight:700; text-transform:uppercase; letter-spacing:.16em;}
.hero-title {font-size:2rem; font-weight:800; color:#fff; margin:7px 0 4px;}
.hero-sub {color:#aab6cc; font-size:.94rem;}
.pill {display:inline-block;border:1px solid #35415d;background:#1b2540;color:#c7d2fe;
 padding:5px 10px;border-radius:99px;font-size:.72rem;margin:8px 5px 0 0;}
.section-head {font-size:1.15rem;font-weight:750;color:#f5f7fb;margin:8px 0 2px;}
.section-sub {font-size:.82rem;color:#8e9bb2;margin-bottom:12px;}
.insight {
 background:#111827;border:1px solid #263149;border-left:3px solid #a855f7;
 border-radius:12px;padding:14px 16px;margin:5px 0;color:#dbe3f2;min-height:82px;
}
div.stButton > button, div.stDownloadButton > button {
 border-radius:10px;border:1px solid #384664;background:#202b45;color:#f8fafc;font-weight:600;
}
div.stButton > button:hover, div.stDownloadButton > button:hover {border-color:#a855f7;color:#fff;}
[data-testid="stDataFrame"] {border:1px solid #263149;border-radius:12px;overflow:hidden;}
hr {border-color:#242d42;}
</style>
""", unsafe_allow_html=True)

# ============================================================
# ACCESS WINDOW: 5 PM–7 PM IST (uses project utility if present)
# ============================================================
def allowed_now():
    try:
        from utils.time_control import check_time
        return bool(check_time(17, 19))
    except Exception:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Kolkata"))
        return 17 <= now.hour < 19

if not allowed_now():
    st.warning("This visualization is available only between 5 PM and 7 PM IST.")
    st.stop()

# ============================================================
# DATA LOADING + NORMALIZATION
# ============================================================
@st.cache_data(show_spinner="Loading Google Play Store data...")
def load_source():
    try:
        from utils.cleaning import load_data
        try:
            raw = load_data()
            if isinstance(raw, pd.DataFrame) and not raw.empty:
                return raw.copy()
        except TypeError:
            pass
    except Exception:
        pass

    candidates = [
        Path("data/googleplaystore.csv"),
        Path("googleplaystore.csv"),
        Path("../data/googleplaystore.csv"),
        Path("../googleplaystore.csv"),
    ]
    for path in candidates:
        if path.exists():
            return pd.read_csv(path)
    raise FileNotFoundError(
        "Dataset not found. Place googleplaystore.csv in data/ or the project root."
    )

def parse_installs(series):
    return pd.to_numeric(
        series.astype(str).str.replace(",", "", regex=False)
              .str.replace("+", "", regex=False).str.strip(),
        errors="coerce"
    )

def parse_size(series):
    s = series.astype(str).str.strip().str.upper()
    out = pd.to_numeric(s.str.extract(r"([\d.]+)")[0], errors="coerce")
    out = out.where(~s.str.contains("M", na=False), out)
    out = out.where(~s.str.contains("K", na=False), out / 1024)
    out = out.where(~s.str.contains("VARIES", na=False), np.nan)
    return out

try:
    raw = load_source()
except Exception as e:
    st.error(f"Could not load the dataset: {e}")
    st.info("Expected columns include App, Category, Rating, Reviews, Installs and Size.")
    st.stop()

# Normalize common source formats
df = raw.copy()
df.columns = [str(c).strip() for c in df.columns]
required = ["App", "Category", "Rating", "Reviews", "Installs", "Size"]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Missing required columns: {', '.join(missing)}")
    st.stop()

df["App"] = df["App"].fillna("Unknown").astype(str)
df["Category"] = df["Category"].fillna("Uncategorized").astype(str).str.upper().str.strip()
df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
df["Reviews"] = pd.to_numeric(df["Reviews"].astype(str).str.replace(",", "", regex=False), errors="coerce")
df["Installs"] = parse_installs(df["Installs"])
df["Size"] = parse_size(df["Size"])
df = df.replace([np.inf, -np.inf], np.nan)
df = df.dropna(subset=["Rating", "Reviews", "Installs", "Size"])
df = df[
    df["Rating"].between(0,5) & (df["Reviews"] >= 0) &
    (df["Installs"] >= 0) & (df["Size"] > 0)
].copy()
if df.empty:
    st.warning("No valid records remain after cleaning.")
    st.stop()

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div class="hero">
 <div class="hero-kicker">Google Play Store · Advanced Analytics</div>
 <div class="hero-title">Hexbin Density Intelligence</div>
 <div class="hero-sub">Explore how app size and user ratings relate to install activity, category patterns, and statistical outliers.</div>
 <span class="pill">Interactive analytics</span><span class="pill">IQR outlier detection</span><span class="pill">5 PM–7 PM IST</span>
</div>
""", unsafe_allow_html=True)

# ============================================================
# SIDEBAR CONTROLS
# ============================================================
st.sidebar.markdown("## 🎛️ Analysis controls")
st.sidebar.caption("Adjust the dataset and chart behavior.")

all_categories = sorted(df["Category"].unique().tolist())
default_categories = [c for c in all_categories if c in [
    "GAME","BEAUTY","BUSINESS","COMICS","COMMUNICATION",
    "DATING","ENTERTAINMENT","SOCIAL","EVENTS"
]]
if not default_categories:
    default_categories = all_categories

with st.sidebar:
    categories = st.multiselect("Categories", all_categories, default=default_categories)
    search_text = st.text_input("Search app name", placeholder="Type an app name...")
    size_min, size_max = float(df["Size"].min()), float(df["Size"].max())
    size_range = st.slider("App size (MB)", size_min, size_max, (size_min, size_max))
    rating_range = st.slider("Rating", 0.0, 5.0, (3.5, 5.0), step=0.1)
    inst_min, inst_max = int(df["Installs"].min()), int(df["Installs"].max())
    inst_range = st.slider("Installs", inst_min, inst_max, (inst_min, inst_max))
    rev_min, rev_max = int(df["Reviews"].min()), int(df["Reviews"].max())
    rev_range = st.slider("Reviews", rev_min, rev_max, (rev_min, rev_max))
    st.markdown("---")
    bins = st.slider("Hexbin resolution", 8, 45, 24)
    show_game = st.toggle("Highlight Game apps in pink", value=True)
    show_outliers = st.toggle("Show IQR outliers", value=True)
    show_labels = st.toggle("Label outlier apps", value=False)
    st.caption("IQR outliers are calculated within each selected category after filtering.")

filtered = df[
    df["Category"].isin(categories) &
    df["Size"].between(*size_range) &
    df["Rating"].between(*rating_range) &
    df["Installs"].between(*inst_range) &
    df["Reviews"].between(*rev_range)
].copy()
if search_text.strip():
    filtered = filtered[filtered["App"].str.contains(search_text.strip(), case=False, na=False)]

if filtered.empty:
    st.warning("No apps match these filters. Widen the ranges or select more categories.")
    st.stop()

# ============================================================
# OUTLIERS
# ============================================================
def category_iqr_outliers(data):
    parts = []
    for cat, group in data.groupby("Category", observed=True):
        q1, q3 = group["Installs"].quantile([.25, .75])
        iqr = q3 - q1
        lo, hi = max(0, q1 - 1.5 * iqr), q3 + 1.5 * iqr
        o = group[(group["Installs"] < lo) | (group["Installs"] > hi)].copy()
        if not o.empty:
            o["IQR Lower"] = lo
            o["IQR Upper"] = hi
            o["Outlier Direction"] = np.where(o["Installs"] > hi, "High installs", "Low installs")
            parts.append(o)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=list(data.columns)+["IQR Lower","IQR Upper","Outlier Direction"])

outliers = category_iqr_outliers(filtered)
games = filtered[filtered["Category"] == "GAME"]
total_installs = filtered["Installs"].sum()
game_share = len(games) / len(filtered) * 100 if len(filtered) else 0
median_rating = filtered["Rating"].median()

# ============================================================
# KPI CARDS
# ============================================================
st.markdown('<div class="section-head">Performance snapshot</div><div class="section-sub">Metrics update automatically with your filters.</div>', unsafe_allow_html=True)
kpis = st.columns(4)
kpis[0].metric("Apps analyzed", f"{len(filtered):,}", f"{len(categories)} categories selected")
kpis[1].metric("Average rating", f"{filtered['Rating'].mean():.2f} / 5", f"Median {median_rating:.2f}")
kpis[2].metric("Total installs", f"{total_installs:,.0f}", "Across filtered apps")
kpis[3].metric("Average app size", f"{filtered['Size'].mean():.1f} MB", f"Range {filtered['Size'].min():.1f}–{filtered['Size'].max():.1f}")
kpis2 = st.columns(4)
kpis2[0].metric("Total reviews", f"{filtered['Reviews'].sum():,.0f}")
kpis2[1].metric("Game app share", f"{game_share:.1f}%", f"{len(games):,} Game apps")
kpis2[2].metric("IQR outliers", f"{len(outliers):,}", f"{len(outliers)/len(filtered)*100:.1f}% of filtered apps")
kpis2[3].metric("Categories represented", f"{filtered['Category'].nunique():,}", "In current selection")
st.markdown("---")

# ============================================================
# HEXAGONAL AGGREGATION (pointy-top axial grid)
# ============================================================
def hexbin_aggregate(data, n_bins):
    """Assign points to a pointy-top hex grid and aggregate mean installs."""
    x = data["Size"].to_numpy(dtype=float)
    y = data["Rating"].to_numpy(dtype=float)
    z = data["Installs"].to_numpy(dtype=float)
    xmin, xmax = float(np.min(x)), float(np.max(x))
    ymin, ymax = float(np.min(y)), float(np.max(y))
    xspan = max(xmax - xmin, 1e-9)
    yspan = max(ymax - ymin, 1e-9)
    # Hex width and height tuned to the data aspect; use normalized coordinates.
    xn = (x - xmin) / xspan
    yn = (y - ymin) / yspan
    dx = 1.0 / max(n_bins, 2)
    dy = dx * np.sqrt(3) / 2
    q = np.round(xn / dx - yn / (2 * dy)).astype(int)
    r = np.round(yn / dy).astype(int)
    # Convert axial coordinates to hex centers in normalized space.
    cx = (q + r / 2) * dx
    cy = r * dy
    temp = pd.DataFrame({"q":q, "r":r, "cx":cx, "cy":cy, "installs":z})
    agg = temp.groupby(["q","r","cx","cy"], as_index=False).agg(
        mean_installs=("installs","mean"),
        app_count=("installs","size"),
        median_installs=("installs","median")
    )
    agg["x_center"] = xmin + agg["cx"] * xspan
    agg["y_center"] = ymin + agg["cy"] * yspan
    return agg

st.markdown('<div class="section-head">App size × rating density</div><div class="section-sub">True hexagonal aggregation. Color represents mean installs; hover for app count and median installs.</div>', unsafe_allow_html=True)
hexes = hexbin_aggregate(filtered, bins)
if len(filtered) > 1 and len(hexes) > 0:
    # Scatter markers are sized to visually approximate hexagonal cells.
    fig_hex = go.Figure()
    marker_sizes = np.full(len(hexes), max(12, 760 / bins))
    fig_hex.add_trace(go.Scatter(
        x=hexes["x_center"], y=hexes["y_center"], mode="markers",
        marker=dict(
            symbol="hexagon", size=marker_sizes,
            color=hexes["mean_installs"], colorscale=[
                [0,"#24294a"],[.25,"#5141a5"],[.55,"#8b3fbb"],[.8,"#d946a6"],[1,"#ffb4dc"]
            ],
            colorbar=dict(title="Mean<br>installs", tickformat="~s"),
            line=dict(color="rgba(230,235,255,.22)", width=.7),
            showscale=True
        ),
        customdata=hexes[["app_count","median_installs","mean_installs"]].to_numpy(),
        hovertemplate=(
            "App size: %{x:.2f} MB<br>Rating: %{y:.2f}<br>"
            "Apps in hex: %{customdata[0]}<br>"
            "Mean installs: %{customdata[2]:,.0f}<br>"
            "Median installs: %{customdata[1]:,.0f}<extra></extra>"
        ),
        name="Hexbin regions"
    ))
    if show_outliers and not outliers.empty:
        fig_hex.add_trace(go.Scatter(
            x=outliers["Size"], y=outliers["Rating"], mode="markers+text" if show_labels else "markers",
            text=outliers["App"] if show_labels else None,
            textposition="top center",
            marker=dict(color="#ff5b62", size=11, symbol="diamond", line=dict(color="#fff",width=1)),
            customdata=outliers[["Category","Installs","Reviews"]].to_numpy(),
            hovertemplate="<b>%{text}</b><br>Size: %{x:.2f} MB<br>Rating: %{y:.2f}<br>Category: %{customdata[0]}<br>Installs: %{customdata[1]:,.0f}<br>Reviews: %{customdata[2]:,.0f}<extra>IQR outlier</extra>",
            name="IQR outliers"
        ))
    if show_game and not games.empty:
        fig_hex.add_trace(go.Scatter(
            x=games["Size"], y=games["Rating"], mode="markers",
            marker=dict(color="#ff69b4", size=7, opacity=.72, line=dict(color="#fff",width=.4)),
            customdata=games[["App","Installs","Reviews"]].to_numpy(),
            hovertemplate="<b>%{customdata[0]}</b><br>Size: %{x:.2f} MB<br>Rating: %{y:.2f}<br>Installs: %{customdata[1]:,.0f}<br>Reviews: %{customdata[2]:,.0f}<extra>Game app</extra>",
            name="Game apps"
        ))
    fig_hex.update_layout(
        template="plotly_dark", height=590, margin=dict(l=15,r=20,t=20,b=20),
        paper_bgcolor="#080b14", plot_bgcolor="#0e1422",
        xaxis_title="App size (MB)", yaxis_title="Rating",
        hovermode="closest", legend=dict(orientation="h",y=1.08,x=0)
    )
    fig_hex.update_xaxes(gridcolor="#202a3e", zerolinecolor="#202a3e")
    fig_hex.update_yaxes(gridcolor="#202a3e", zerolinecolor="#202a3e", range=[0,5])
    st.plotly_chart(fig_hex, width='stretch')
else:
    st.info("Select more than one app to display density regions.")

# ============================================================
# DISTRIBUTIONS + CATEGORY COMPARISON
# ============================================================
st.markdown("---")
st.markdown('<div class="section-head">Distribution & category intelligence</div><div class="section-sub">Compare app size, ratings, and category-level install patterns.</div>', unsafe_allow_html=True)
c1, c2 = st.columns(2)
with c1:
    dist = px.histogram(filtered, x="Size", nbins=35, marginal="box",
        color_discrete_sequence=["#8b5cf6"], title="App size distribution",
        labels={"Size":"App size (MB)","count":"Apps"})
    dist.update_layout(template="plotly_dark",height=400,paper_bgcolor="#080b14",plot_bgcolor="#0e1422",showlegend=False)
    dist.update_xaxes(gridcolor="#202a3e")
    st.plotly_chart(dist,width='stretch')
with c2:
    rating_dist = px.histogram(filtered, x="Rating", nbins=25, marginal="rug",
        color_discrete_sequence=["#22c5b5"], title="Rating distribution",
        labels={"Rating":"Rating","count":"Apps"})
    rating_dist.update_layout(template="plotly_dark",height=400,paper_bgcolor="#080b14",plot_bgcolor="#0e1422",showlegend=False)
    rating_dist.update_xaxes(gridcolor="#202a3e")
    st.plotly_chart(rating_dist,width='stretch')

summary = filtered.groupby("Category", as_index=False).agg(
    Apps=("App","count"), Mean_Rating=("Rating","mean"),
    Mean_Installs=("Installs","mean"), Median_Installs=("Installs","median"),
    Mean_Size=("Size","mean"), Reviews=("Reviews","sum")
)
c3,c4 = st.columns(2)
with c3:
    catfig = px.bar(summary.sort_values("Mean_Installs"), x="Mean_Installs", y="Category",
        orientation="h", color="Mean_Installs",
        color_continuous_scale=["#3730a3","#8b5cf6","#ec4899"],
        title="Average installs by category",
        labels={"Mean_Installs":"Mean installs","Category":"Category"})
    catfig.update_layout(template="plotly_dark",height=450,paper_bgcolor="#080b14",plot_bgcolor="#0e1422",showlegend=False,coloraxis_showscale=False)
    st.plotly_chart(catfig,width='stretch')
with c4:
    cat_scatter = px.scatter(summary,x="Mean_Size",y="Mean_Rating",size="Apps",color="Category",
        hover_data={"Apps":True,"Mean_Installs":":,.0f","Reviews":":,.0f"},
        title="Category profile: average size vs rating",
        labels={"Mean_Size":"Mean app size (MB)","Mean_Rating":"Mean rating"})
    cat_scatter.update_layout(template="plotly_dark",height=450,paper_bgcolor="#080b14",plot_bgcolor="#0e1422")
    st.plotly_chart(cat_scatter,width='stretch')

# ============================================================
# APP LEADERBOARD + INSIGHTS
# ============================================================
st.markdown("---")
st.markdown('<div class="section-head">App leaderboard</div><div class="section-sub">Find the leading apps in the current filtered selection.</div>', unsafe_allow_html=True)
tab1,tab2,tab3 = st.tabs(["Most installs","Highest rated","Most reviewed"])
with tab1:
    leaders = filtered.sort_values(["Installs","Rating"],ascending=False).head(10)
    st.dataframe(leaders[["App","Category","Installs","Rating","Reviews","Size"]],width='stretch',hide_index=True)
with tab2:
    leaders = filtered[filtered["Reviews"] > 0].sort_values(["Rating","Reviews"],ascending=False).head(10)
    st.dataframe(leaders[["App","Category","Rating","Reviews","Installs","Size"]],width='stretch',hide_index=True)
with tab3:
    leaders = filtered.sort_values(["Reviews","Rating"],ascending=False).head(10)
    st.dataframe(leaders[["App","Category","Reviews","Rating","Installs","Size"]],width='stretch',hide_index=True)

st.markdown("---")
st.markdown('<div class="section-head">Automated insights</div><div class="section-sub">Observations calculated from the active filter selection.</div>', unsafe_allow_html=True)
top_install_cat = summary.loc[summary["Mean_Installs"].idxmax()] if not summary.empty else None
top_rating_cat = summary.loc[summary["Mean_Rating"].idxmax()] if not summary.empty else None
largest = filtered.loc[filtered["Size"].idxmax()]
popular = filtered.loc[filtered["Installs"].idxmax()]
ins_cols = st.columns(2)
insights = [
    ("📈 Install leader category", f"{top_install_cat['Category']} has the highest average installs ({top_install_cat['Mean_Installs']:,.0f}) among selected categories." if top_install_cat is not None else "No category data."),
    ("⭐ Rating leader category", f"{top_rating_cat['Category']} has the highest mean rating ({top_rating_cat['Mean_Rating']:.2f}/5)." if top_rating_cat is not None else "No category data."),
    ("📦 Largest app", f"{largest['App']} is the largest app in this selection at {largest['Size']:.2f} MB."),
    ("🚀 Install leader app", f"{popular['App']} has the most installs in this selection ({popular['Installs']:,.0f})."),
    ("🎮 Game representation", f"Game apps account for {game_share:.1f}% of the filtered records."),
    ("🔎 Outlier review", f"{len(outliers):,} records are flagged by category-wise IQR install thresholds.")
]
for i,(title,body) in enumerate(insights):
    with ins_cols[i%2]:
        st.markdown(f'<div class="insight"><b>{title}</b><br>{body}</div>',unsafe_allow_html=True)

# ============================================================
# OUTLIERS + DATA EXPORT
# ============================================================
st.markdown("---")
with st.expander(f"🔴 IQR outlier details ({len(outliers):,})", expanded=False):
    if outliers.empty:
        st.info("No outliers found for the current filters.")
    else:
        cols = ["App","Category","Size","Rating","Installs","Reviews","IQR Lower","IQR Upper","Outlier Direction"]
        st.dataframe(outliers[cols].sort_values("Installs",ascending=False),width='stretch',hide_index=True)

with st.expander("🧾 Explore filtered dataset", expanded=False):
    st.caption(f"{len(filtered):,} rows · {len(filtered.columns):,} columns")
    st.dataframe(filtered,width='stretch',hide_index=True)

download_col1,download_col2 = st.columns([1,1])
with download_col1:
    st.download_button("⬇️ Download filtered apps (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="play_store_hexbin_filtered.csv",mime="text/csv",width='stretch')
with download_col2:
    if not outliers.empty:
        st.download_button("⬇️ Download IQR outliers (CSV)",
            data=outliers.to_csv(index=False).encode("utf-8"),
            file_name="play_store_iqr_outliers.csv",mime="text/csv",width='stretch')
    else:
        st.button("No outliers to export",disabled=True,width='stretch')

st.markdown("---")
st.caption("Google Play Store Analytics · Hexbin Density Intelligence · Built with Streamlit, Pandas, NumPy and Plotly")
