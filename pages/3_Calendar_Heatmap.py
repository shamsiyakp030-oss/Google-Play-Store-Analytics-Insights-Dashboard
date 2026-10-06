import sys
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import pytz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.time_control import check_time

st.set_page_config(page_title="Google Play Calendar Analytics", page_icon="📅", layout="wide")

if not check_time(18, 21):
    st.warning("This visualization is available only between 6 PM and 9 PM IST.")
    st.stop()

st.markdown("""
<style>
.stApp{background:#080b12;color:#f6f7fb}.block-container{max-width:1500px;padding-top:1.4rem}
.hero{background:linear-gradient(135deg,#111827,#0b1220);border:1px solid #27324a;border-radius:20px;padding:24px 28px;margin-bottom:18px}
.hero h1{margin:0;color:#fff}.hero p{color:#aeb9cc;margin:7px 0 0}.note{color:#98a5ba;font-size:.86rem}
</style>
""", unsafe_allow_html=True)

DATA_FILE = PROJECT_ROOT / "data" / "googleplaystore (2).csv"

@st.cache_data(show_spinner="Loading Google Play analytics data...")
def load_data(path, mtime):
    df = pd.read_csv(path, low_memory=False)
    required = ["App","Category","Rating","Reviews","Installs","Size","Last Updated","Sentiment_Subjectivity"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError("Missing required columns: " + ", ".join(missing))
    df["App"] = df["App"].astype("string").str.strip()
    df["Category"] = df["Category"].astype("string").str.strip().str.upper()
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce")
    df["Reviews"] = pd.to_numeric(df["Reviews"].astype(str).str.replace(",","",regex=False), errors="coerce")
    df["Installs_num"] = pd.to_numeric(df["Installs"].astype(str).str.replace(",","",regex=False).str.replace("+","",regex=False), errors="coerce")
    if "Size_MB" in df.columns:
        df["Size_MB_num"] = pd.to_numeric(df["Size_MB"], errors="coerce")
    else:
        raw = df["Size"].astype(str)
        df["Size_MB_num"] = pd.to_numeric(raw.str.extract(r"([0-9]*\\.?[0-9]+)")[0], errors="coerce")
        df.loc[raw.str.contains("k", case=False, na=False), "Size_MB_num"] /= 1024
    df["Sentiment_Subjectivity"] = pd.to_numeric(df["Sentiment_Subjectivity"], errors="coerce")
    df["Last Updated"] = pd.to_datetime(df["Last Updated"], errors="coerce")
    df = df.dropna(subset=["App","Category","Rating","Reviews","Installs_num","Size_MB_num","Sentiment_Subjectivity","Last Updated"])
    df = df[df["Rating"].between(0,5) & df["Installs_num"].ge(0) & df["Reviews"].ge(0)].copy()
    df["Date"] = df["Last Updated"].dt.normalize()
    df["Month"] = df["Last Updated"].dt.to_period("M").dt.to_timestamp()
    return df

try:
    df = load_data(DATA_FILE, DATA_FILE.stat().st_mtime)
except Exception as e:
    st.error(f"Dataset loading error: {e}")
    st.stop()

st.markdown('<div class="hero"><h1>📅 Google Play Calendar Heatmap & Forecast</h1><p>Monthly install activity by last-update date for the top five eligible categories.</p></div>', unsafe_allow_html=True)
st.caption("Note: the dataset records total install lower bounds, not installs generated on each update date. The calendar therefore shows install lower bounds associated with apps by their last-update date.")

# Exact eligibility rules requested.
eligible = df[
    (df["Rating"] >= 4.0) &
    (df["Installs_num"] > 10_000) &
    (df["Reviews"] > 500) &
    (df["Size_MB_num"].between(15, 80, inclusive="both")) &
    (df["Sentiment_Subjectivity"] > 0.5) &
    (df["Category"].str.startswith(("E","C","B"), na=False)) &
    (~df["App"].str.match(r"^[XYZ]", case=False, na=False)) &
    (~df["App"].str.contains("S", case=False, na=False, regex=False))
].copy()

if eligible.empty:
    st.error("No records meet all calendar eligibility filters.")
    st.stop()

# Rank categories by total install lower bound, which is the available install metric.
top_categories = (eligible.groupby("Category")["Installs_num"].sum().nlargest(5).index.tolist())
eligible = eligible[eligible["Category"].isin(top_categories)].copy()
labels = {"All Top 5 Categories": "All Top 5 Categories", **{c:c.replace("_"," ").title() for c in top_categories}}

with st.sidebar:
    st.header("🎛️ Calendar Controls")
    selected_category = st.selectbox("Category", ["All Top 5 Categories"] + top_categories, format_func=lambda x: labels[x])
    metric = st.selectbox("Calendar metric", ["Install Lower Bound", "Reviews", "Eligible Apps"], index=0)
    st.subheader("Eligibility")
    for line in ["Rating ≥ 4.0","Installs > 10,000","Reviews > 500","Size 15–80 MB","Subjectivity > 0.5","Category starts E/C/B","App name not starting X/Y/Z","App name does not contain S"]:
        st.caption("✓ " + line)

filtered = eligible if selected_category == "All Top 5 Categories" else eligible[eligible["Category"] == selected_category]
if filtered.empty:
    st.warning("No eligible records for the selected category.")
    st.stop()

# Monthly calendar selection.
months = sorted(filtered["Month"].dropna().unique())
selected_month = st.sidebar.selectbox("Calendar month", months, format_func=lambda x: pd.Timestamp(x).strftime("%B %Y"))
month_start = pd.Timestamp(selected_month).normalize()
month_end = month_start + pd.offsets.MonthEnd(1)
month_days = pd.date_range(month_start, month_end, freq="D")
month_df = filtered[filtered["Date"].between(month_start, month_end)].copy()

if metric == "Install Lower Bound":
    daily = month_df.groupby("Date")["Installs_num"].sum()
elif metric == "Reviews":
    daily = month_df.groupby("Date")["Reviews"].sum()
else:
    daily = month_df.groupby("Date")["App"].nunique()
daily = daily.reindex(month_days, fill_value=0)

# True monthly calendar: Monday-first, seven columns, blanks before/after the month.
first_weekday = month_start.weekday()
values = [None] * first_weekday + daily.tolist()
while len(values) % 7:
    values.append(None)
weeks = len(values) // 7
z = np.array([[np.nan if v is None else float(v) for v in values[w*7:(w+1)*7]] for w in range(weeks)])
custom = np.empty((weeks,7), dtype=object)
for w in range(weeks):
    for d in range(7):
        idx = w*7+d-first_weekday
        custom[w,d] = month_days[idx].strftime("%d %b %Y") if 0 <= idx < len(month_days) else ""

fig = go.Figure(go.Heatmap(z=z, x=["Mon","Tue","Wed","Thu","Fri","Sat","Sun"], y=[f"Week {i+1}" for i in range(weeks)], customdata=custom, colorscale="Viridis", hovertemplate="<b>%{customdata}</b><br>"+metric+": %{z:,.0f}<extra></extra>", xgap=4, ygap=4, colorbar=dict(title=metric)))
fig.update_layout(height=360, margin=dict(l=20,r=20,t=25,b=20), paper_bgcolor="#080b12", plot_bgcolor="#080b12", font_color="#f6f7fb", xaxis=dict(side="top"), yaxis=dict(autorange="reversed"))
st.plotly_chart(fig, width='stretch')

# Monthly series, growth, and 3-month moving average forecast.
monthly = filtered.groupby("Month").agg(Installs=("Installs_num","sum"), Reviews=("Reviews","sum"), Apps=("App","nunique")).sort_index()
monthly["3-Month Moving Average"] = monthly[metric.replace("Install Lower Bound","Installs").replace("Eligible Apps","Apps")].rolling(3,min_periods=1).mean()
monthly["MoM Growth %"] = monthly[metric.replace("Install Lower Bound","Installs").replace("Eligible Apps","Apps")].pct_change()*100

k1,k2,k3,k4=st.columns(4)
k1.metric("Eligible Apps", f"{filtered['App'].nunique():,}")
k2.metric("Total Reviews", f"{filtered['Reviews'].sum():,.0f}")
k3.metric("Install Lower Bound", f"{filtered['Installs_num'].sum():,.0f}")
latest=monthly["MoM Growth %"].dropna()
k4.metric("Latest MoM Growth", "N/A" if latest.empty else f"{latest.iloc[-1]:+.2f}%")

st.subheader("📈 Monthly Trend & 3-Month Moving Average")
value_col = metric.replace("Install Lower Bound","Installs").replace("Eligible Apps","Apps")
trend = go.Figure()
trend.add_trace(go.Scatter(x=monthly.index,y=monthly[value_col],mode="lines+markers",name=metric,customdata=monthly[["Reviews","Apps"]].to_numpy(),hovertemplate="<b>%{x|%B %Y}</b><br>"+metric+": %{y:,.0f}<br>Reviews: %{customdata[0]:,.0f}<br>Apps: %{customdata[1]:,.0f}<extra></extra>"))
trend.add_trace(go.Scatter(x=monthly.index,y=monthly["3-Month Moving Average"],mode="lines",name="3-Month Moving Average",hovertemplate="<b>%{x|%B %Y}</b><br>Moving average: %{y:,.0f}<extra></extra>"))
trend.update_layout(height=430,template="plotly_dark",hovermode="x unified",xaxis_title="Month",yaxis_title=metric)
st.plotly_chart(trend,width='stretch')

st.subheader("📊 Month-over-Month Growth")
growth=monthly.dropna(subset=["MoM Growth %"])
if growth.empty:
    st.info("At least two months are needed to calculate month-over-month growth.")
else:
    gf=go.Figure(go.Bar(x=growth.index,y=growth["MoM Growth %"],customdata=growth[[value_col,"Reviews","Apps"]].to_numpy(),hovertemplate="<b>%{x|%B %Y}</b><br>Growth: %{y:.2f}%<br>Metric: %{customdata[0]:,.0f}<br>Reviews: %{customdata[1]:,.0f}<br>Apps: %{customdata[2]:,.0f}<extra></extra>"))
    gf.update_layout(height=360,template="plotly_dark",xaxis_title="Month",yaxis_title="Growth (%)")
    st.plotly_chart(gf,width='stretch')

st.subheader("🏷️ Top-Five Category Summary")
summary=(eligible.groupby("Category").agg(Apps=("App","nunique"),Installs=("Installs_num","sum"),Reviews=("Reviews","sum"),Avg_Rating=("Rating","mean"),Avg_Subjectivity=("Sentiment_Subjectivity","mean")).sort_values("Installs",ascending=False).reset_index())
summary["Category"]=summary["Category"].str.replace("_"," ").str.title()
st.dataframe(summary,width='stretch',hide_index=True)
