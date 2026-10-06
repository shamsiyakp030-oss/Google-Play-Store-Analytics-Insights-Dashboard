# ============================================================
# 6_Free_vs_Paid_Radar.py
# Google Play Store Analytics
#
# Free vs Paid Application Performance Radar Analysis
#
# Restrictions:
# - Visible only 01:00 PM - 02:00 PM IST
# - Installs >= 10,000
# - Paid Revenue > $10,000
# - Android Version > 4.0
# - Size > 15 MB
# - Content Rating = Everyone
# - App Name <= 30 characters
#
# Analytics:
# - Percentile Normalization
# - Weighted Rating
# - Engagement Rate
# - Revenue Calculation
# - Composite Performance Score
# ============================================================


import streamlit as st
import pandas as pd
import numpy as np
import re

from pathlib import Path
from datetime import datetime

import pytz

import plotly.express as px
import plotly.graph_objects as go



# ============================================================
# PAGE CONFIGURATION
# ============================================================


st.set_page_config(

    page_title="Free vs Paid Radar Analytics",

    page_icon="📡",

    layout="wide"

)



# ============================================================
# PROFESSIONAL STYLE
# ============================================================


st.markdown(

"""
<style>


.main-title{

font-size:42px;
font-weight:800;
text-align:center;

}



.sub-title{

font-size:18px;
text-align:center;
color:#777;

}



.section-title{

font-size:26px;
font-weight:700;
margin-top:30px;

}


.card{

padding:20px;
border-radius:15px;
background:white;
box-shadow:0 4px 15px rgba(0,0,0,0.08);
text-align:center;

}


</style>

""",

unsafe_allow_html=True

)



# ============================================================
# TIME RESTRICTION
# ============================================================


IST = pytz.timezone(
    "Asia/Kolkata"
)


current_time = datetime.now(
    IST
)


if not (

    13 <= current_time.hour < 14

):

    st.warning(

        """
        ⏰ Free vs Paid Radar Analysis

        is available only between

        **01:00 PM - 02:00 PM IST**

        """

    )

    st.stop()



# ============================================================
# HEADER
# ============================================================


st.markdown(

"""
<div class="main-title">

📡 Google Play Store Intelligence

</div>


<div class="sub-title">

Free vs Paid Application Performance Radar

</div>

""",

unsafe_allow_html=True

)



# ============================================================
# DATA PATH
# ============================================================


CURRENT_DIR = Path(
    __file__
).resolve().parent


PROJECT_ROOT = CURRENT_DIR.parent


DATA_FILE = (

    PROJECT_ROOT

    /
    "data"

    /
    "googleplaystore.csv"

)



if not DATA_FILE.exists():

    st.error(
        "Dataset file not found."
    )

    st.stop()



# ============================================================
# LOAD DATA
# ============================================================


@st.cache_data

def load_data(path):

    return pd.read_csv(

        path,

        encoding="utf-8",

        on_bad_lines="skip"

    )



df = load_data(
    DATA_FILE
)



# ============================================================
# COLUMN CLEANING
# ============================================================


df.columns=(

    df.columns

    .str.strip()

    .str.lower()

    .str.replace(
        " ",
        "_"
    )

)



# ============================================================
# CLEANING FUNCTIONS
# ============================================================


def clean_number(value):

    value=str(value)


    value=(

        value

        .replace(
            ",",
            ""
        )

        .replace(
            "+",
            ""
        )

    )


    try:

        return float(value)

    except:

        return np.nan




def clean_size(value):

    value=str(value)


    if "M" in value:

        return float(

            value.replace(
                "M",
                ""
            )

        )


    elif "k" in value:

        return (

            float(

                value.replace(
                    "k",
                    ""
                )

            )

            /

            1024

        )


    return np.nan




def clean_price(value):

    value=str(value)


    value=(

        value

        .replace(
            "$",
            ""
        )

        .strip()

    )


    try:

        return float(value)

    except:

        return 0




def clean_android(value):

    value=str(value)


    match = re.search(r"[0-9]+(?:\.[0-9]+)?", value)
    return float(match.group()) if match else np.nan



# ============================================================
# APPLY CLEANING
# ============================================================


df["installs_num"] = (

    df["installs"]

    .apply(clean_number)

)



df["reviews_num"] = (

    df["reviews"]

    .apply(clean_number)

)



df["size_mb"] = (

    df["size"]

    .apply(clean_size)

)



df["price_num"] = (

    df["price"]

    .apply(clean_price)

)



df["rating_num"] = pd.to_numeric(

    df["rating"],

    errors="coerce"

)



df["android_version_num"] = (

    df["android_ver"]

    .apply(clean_android)

)



# ============================================================
# REMOVE INVALID APP NAMES
# ============================================================


df=df[

    df["app"]

    .astype(str)

    .str.len()

    <=30

]



df=df[

    ~

    df["app"]

    .astype(str)

    .str.contains(
        r"\d",
        regex=True
    )

]



# ============================================================
# CALCULATIONS
# ============================================================


df["app_type"]=np.where(

    df["price_num"]>0,

    "Paid",

    "Free"

)



df["revenue"]= (

    df["installs_num"]

    *

    df["price_num"]

)



# ============================================================
# FILTER CONDITIONS
# ============================================================


filtered=df[


(df["installs_num"]>=10000)

&

(df["android_version_num"]>4.0)

&

(df["size_mb"]>15)

&

(df["content_rating"]=="Everyone")

&

(

(df["app_type"]=="Free")

|

(

(df["app_type"]=="Paid")

&

(df["revenue"]>10000)

)

)


]



if filtered.empty:

    st.error(
        "No applications match the selected conditions."
    )

    st.stop()



# ============================================================
# TOP 5 CATEGORIES BY INSTALLS
# ============================================================


top_categories=(

filtered

.groupby("category")

["installs_num"]

.sum()

.sort_values(

ascending=False

)

.head(5)

.index

)



filtered=filtered[

filtered["category"]

.isin(top_categories)

]



# ============================================================
# METRIC FUNCTIONS
# ============================================================


def weighted_rating(group):

    return (

        np.sum(

            group["rating_num"]

            *

            group["reviews_num"]

        )

        /

        np.sum(
            group["reviews_num"]
        )

    )



# ============================================================
# CATEGORY TYPE SUMMARY
# ============================================================


summary=(

filtered

.groupby(

[
"category",
"app_type"

]

)

.apply(

lambda x:pd.Series({

"Average Installs":
x["installs_num"].mean(),


"Weighted Rating":
weighted_rating(x),


"Total Reviews":
x["reviews_num"].sum(),


"Average Size":
x["size_mb"].mean(),


"Revenue":
x["revenue"].sum(),


"Engagement Rate":
(
x["reviews_num"].sum()

/

x["installs_num"].sum()

)*100


})

)

.reset_index()

)



# ============================================================
# END PART 1
# ============================================================
# ============================================================
# PART 2
# NORMALIZATION + RADAR + INSIGHTS
# ============================================================


# ============================================================
# PERCENTILE NORMALIZATION
# ============================================================


metrics = [

    "Average Installs",

    "Weighted Rating",

    "Total Reviews",

    "Average Size",

    "Revenue",

    "Engagement Rate"

]



def percentile_normalize(series):

    p25 = series.quantile(0.25)

    p75 = series.quantile(0.75)


    if p75-p25 == 0:

        return 0


    return (

        series-p25

    ) / (

        p75-p25

    )



normalized_summary = summary.copy()



for col in metrics:

    normalized_summary[col+"_Norm"] = (

        percentile_normalize(

            normalized_summary[col]

        )

    )



# ============================================================
# COMPOSITE PERFORMANCE SCORE
# ============================================================


weights={

    "Average Installs_Norm":0.20,

    "Weighted Rating_Norm":0.25,

    "Total Reviews_Norm":0.20,

    "Average Size_Norm":0.05,

    "Revenue_Norm":0.15,

    "Engagement Rate_Norm":0.15

}



normalized_summary["Composite Score"]=0



for col,w in weights.items():

    normalized_summary["Composite Score"] += (

        normalized_summary[col]*w

    )



# ============================================================
# SIDEBAR CONTROL
# ============================================================


st.sidebar.title(
    "⚙ Radar Controls"
)



view_mode = st.sidebar.selectbox(

    "Comparison View",

    [

        "Overall Comparison",

        "Individual Category"

    ]

)



if view_mode=="Individual Category":


    selected_category = st.sidebar.selectbox(

        "Select Category",

        top_categories

    )


else:

    selected_category=None



# ============================================================
# PREPARE RADAR DATA
# ============================================================


if view_mode=="Overall Comparison":


    radar_df=(

        normalized_summary

        .groupby("app_type")

        [

        [

        "Average Installs_Norm",

        "Weighted Rating_Norm",

        "Total Reviews_Norm",

        "Average Size_Norm",

        "Revenue_Norm",

        "Engagement Rate_Norm"

        ]

        ]

        .mean()

        .reset_index()

    )


    title_text = (

        "Overall Free vs Paid Performance"

    )


else:


    radar_df=(

        normalized_summary

        [

        normalized_summary["category"]

        ==selected_category

        ]

    )


    title_text=(

        f"{selected_category} - Free vs Paid Comparison"

    )



# ============================================================
# RADAR CHART
# ============================================================


st.markdown(

'<div class="section-title">📡 Interactive Performance Radar</div>',

unsafe_allow_html=True

)



radar_metrics=[

"Average Installs_Norm",

"Weighted Rating_Norm",

"Total Reviews_Norm",

"Average Size_Norm",

"Revenue_Norm",

"Engagement Rate_Norm"

]


radar_labels=[

"Installs",

"Rating",

"Reviews",

"Size",

"Revenue",

"Engagement"

]



fig_radar=go.Figure()



for _,row in radar_df.iterrows():


    fig_radar.add_trace(

        go.Scatterpolar(

            r=[

                row[x]

                for x in radar_metrics

            ],

            theta=radar_labels,

            fill="toself",

            name=row["app_type"]

        )

    )



fig_radar.update_layout(

    title=title_text,

    polar=dict(

        radialaxis=dict(

            visible=True,

            range=[0,1]

        )

    ),

    height=650,

    template="plotly_white"

)



st.plotly_chart(

    fig_radar,

    width='stretch'

)



# ============================================================
# PERFORMANCE WINNER
# ============================================================


st.markdown(

'<div class="section-title">🏆 Performance Result</div>',

unsafe_allow_html=True

)



winner_df=(

normalized_summary

.groupby("app_type")

["Composite Score"]

.mean()

.sort_values(

ascending=False

)

)



winner=winner_df.index[0]


winner_score=winner_df.iloc[0]



st.success(

f"""

🏆 Better Performing App Type:

## {winner}

Composite Performance Score:

**{winner_score:.3f}**

"""

)



# ============================================================
# SCORE COMPARISON
# ============================================================


fig_score=px.bar(

winner_df.reset_index(),

x="app_type",

y="Composite Score",

color="app_type",

text="Composite Score",

title="Free vs Paid Composite Score Comparison"

)



fig_score.update_traces(

texttemplate="%{text:.3f}",

textposition="outside"

)



fig_score.update_layout(

height=450,

template="plotly_white"

)



st.plotly_chart(

fig_score,

width='stretch'

)



# ============================================================
# CATEGORY PERFORMANCE TABLE
# ============================================================


st.markdown(

'<div class="section-title">📊 Category Performance Details</div>',

unsafe_allow_html=True

)



display_table=(

normalized_summary

.sort_values(

"Composite Score",

ascending=False

)

)



st.dataframe(

display_table,

width='stretch',

hide_index=True

)



# ============================================================
# KPI CARDS
# ============================================================


st.markdown(

'<div class="section-title">📌 Dataset Summary</div>',

unsafe_allow_html=True

)



c1,c2,c3,c4=st.columns(4)



with c1:

    st.metric(

        "Filtered Apps",

        f"{len(filtered):,}"

    )


with c2:

    st.metric(

        "Top Categories",

        len(top_categories)

    )


with c3:

    st.metric(

        "Free Apps",

        len(

            filtered[

            filtered.app_type=="Free"

            ]

        )

    )


with c4:

    st.metric(

        "Paid Apps",

        len(

            filtered[

            filtered.app_type=="Paid"

            ]

        )

    )



# ============================================================
# DOWNLOAD SECTION
# ============================================================


st.markdown(

'<div class="section-title">⬇ Download Analysis</div>',

unsafe_allow_html=True

)



csv_data=(

normalized_summary

.to_csv(

index=False

)

)



st.download_button(

    "📥 Download Radar Analysis CSV",

    csv_data,

    file_name="free_paid_radar_analysis.csv",

    mime="text/csv"

)



# ============================================================
# FOOTER
# ============================================================


st.markdown("---")



st.markdown(

"""

<div style="text-align:center;color:#777">


<b>Google Play Store Intelligence Dashboard</b>


<br>


Free vs Paid Application Radar Analytics


<br>


Python • Pandas • Plotly • Streamlit


</div>

""",

unsafe_allow_html=True

)
