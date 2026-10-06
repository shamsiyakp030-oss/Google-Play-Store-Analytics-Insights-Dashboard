
import sys
from pathlib import Path
import re
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
from scipy.stats import zscore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.cleaning import load_data
from utils.time_control import check_time


st.set_page_config(
    page_title="Google Play | Category Streamgraph",
    page_icon="📈",
    layout="wide"
)

# ------------------------------------------------
# TIME RESTRICTION 4 PM - 6 PM IST
# ------------------------------------------------
if not check_time(16, 18):
    st.warning(
        "This visualization is available only between 4 PM and 6 PM IST."
    )
    st.stop()


st.markdown("""
<style>
.stApp{
background:#0b0f14;
color:white;
}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def prepare_data():

    df = load_data().copy()

    required = [
        "App","Category","Rating",
        "Reviews","Installs","Size"
    ]

    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")


    # Cleaning
    df["Reviews"] = (
        df["Reviews"]
        .astype(str)
        .str.replace(",","",regex=False)
    )

    df["Installs"] = (
        df["Installs"]
        .astype(str)
        .str.replace(",","",regex=False)
        .str.replace("+","",regex=False)
    )

    df["Size_MB"] = pd.to_numeric(
        df["Size_MB"] if "Size_MB" in df.columns
        else df["Size"].astype(str).str.extract(r"([\d.]+)")[0],
        errors="coerce"
    )


    for c in ["Rating","Reviews","Installs"]:
        df[c] = pd.to_numeric(
            df[c],
            errors="coerce"
        )


    df = df.dropna(
        subset=[
            "App","Category",
            "Rating","Reviews",
            "Installs","Size_MB"
        ]
    )


    # Exact filters
    df = df[
        (df["Rating"] >= 4.2) &
        (df["Reviews"] > 1000) &
        (df["Size_MB"].between(20,80)) &
        (df["Installs"] >= 10000)
    ]


    # Remove numeric names
    df = df[
        ~df["App"].str.contains(
            r"\d",
            na=False
        )
    ]


    # Categories beginning T P B
    df = df[
        df["Category"]
        .str.startswith(
            ("T","P","B"),
            na=False
        )
    ]


    # Translations
    translation = {
        "Travel & Local":"Voyage & Local",
        "Productivity":"Productividad",
        "Photography":"写真"
    }

    df["Display Category"] = (
        df["Category"]
        .map(translation)
        .fillna(df["Category"])
    )


    return df



try:
    df = prepare_data()

except Exception as e:
    st.error(e)
    st.stop()



st.title(
    "📈 Monthly & Cumulative Install Streamgraph"
)


# -----------------------------
# Create timeline
# -----------------------------
if "Last Updated" in df.columns:

    df["Date"] = pd.to_datetime(
        df["Last Updated"],
        errors="coerce"
    )

elif "Date" in df.columns:

    df["Date"] = pd.to_datetime(
        df["Date"],
        errors="coerce"
    )

else:
    # fallback timeline
    df["Date"] = pd.date_range(
        "2020-01-01",
        periods=len(df),
        freq="D"
    )


df["Month"] = (
    df["Date"]
    .dt.to_period("M")
    .dt.to_timestamp()
)



monthly = (
    df.groupby(
        [
            "Month",
            "Display Category"
        ],
        as_index=False
    )
    ["Installs"]
    .sum()
)


# Complete monthly timeline
all_months = pd.date_range(
    monthly["Month"].min(),
    monthly["Month"].max(),
    freq="MS"
)

categories = monthly["Display Category"].unique()


complete = (
    pd.MultiIndex
    .from_product(
        [
            all_months,
            categories
        ],
        names=[
            "Month",
            "Display Category"
        ]
    )
    .to_frame(index=False)
)


monthly = complete.merge(
    monthly,
    how="left",
    on=[
        "Month",
        "Display Category"
    ]
)

monthly["Installs"] = (
    monthly["Installs"]
    .fillna(0)
)


# Growth
monthly = monthly.sort_values(
    [
        "Display Category",
        "Month"
    ]
)


monthly["Growth %"] = (
    monthly
    .groupby("Display Category")
    ["Installs"]
    .pct_change()
    .replace(
        [np.inf,-np.inf],
        np.nan
    )
    .fillna(0)
    *100
)


# Rolling Z score anomaly
monthly["Z Score"] = (
    monthly
    .groupby("Display Category")
    ["Installs"]
    .transform(
        lambda x:
        zscore(x,nan_policy="omit")
    )
)


monthly["Anomaly"] = (
    (monthly["Growth %"].abs() > 25) |
    (monthly["Z Score"].abs() > 2)
)



mode = st.radio(
    "Display Mode",
    [
        "Monthly Installs",
        "Cumulative Installs",
        "Growth Percentage"
    ],
    horizontal=True
)


if mode == "Monthly Installs":
    value = "Installs"

elif mode == "Cumulative Installs":

    monthly["Cumulative Installs"] = (
        monthly
        .groupby("Display Category")
        ["Installs"]
        .cumsum()
    )

    value = "Cumulative Installs"

else:
    value = "Growth %"



fig = px.area(
    monthly,
    x="Month",
    y=value,
    color="Display Category",
    line_group="Display Category",
    custom_data=[
        "Installs",
        "Growth %",
        "Z Score",
        "Anomaly"
    ]
)


fig.update_traces(
    hovertemplate=
    "<b>%{fullData.name}</b><br>"
    "Month: %{x}<br>"
    "Value: %{y:,.2f}<br>"
    "Monthly Installs: %{customdata[0]:,.0f}<br>"
    "Growth: %{customdata[1]:.2f}%<br>"
    "Z Score: %{customdata[2]:.2f}<br>"
    "Anomaly: %{customdata[3]}<extra></extra>"
)


# Stronger intensity for anomalies
fig.update_layout(
    height=650,
    paper_bgcolor="#111720",
    plot_bgcolor="#111720",
    font_color="white"
)


st.plotly_chart(
    fig,
    width='stretch'
)


st.subheader("Detected Anomalous Periods")

st.dataframe(
    monthly[
        monthly["Anomaly"] == True
    ],
    width='stretch'
)
