# ============================================================
# 5_Cluster_Heatmap.py
# Google Play Store Intelligence Dashboard
#
# Professional Cluster Heatmap Analytics
#
# Developed using:
# Streamlit | Pandas | Plotly | Scikit-Learn
#
# ============================================================


import streamlit as st
import pandas as pd
import numpy as np

from pathlib import Path
from datetime import datetime

import pytz

import plotly.express as px
import plotly.graph_objects as go

from sklearn.preprocessing import StandardScaler
from scipy.cluster.hierarchy import linkage, leaves_list



# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(

    page_title="Google Play Intelligence | Cluster Heatmap",

    page_icon="🔥",

    layout="wide"

)



# ============================================================
# PROFESSIONAL CSS
# ============================================================

st.markdown(
"""
<style>


.main-title{

font-size:42px;
font-weight:800;
text-align:center;
margin-bottom:0px;

}


.sub-title{

font-size:18px;
text-align:center;
color:#777;
margin-bottom:35px;

}



.metric-card{

background:#ffffff;

padding:20px;

border-radius:15px;

box-shadow:
0 4px 12px rgba(0,0,0,0.08);

text-align:center;

}



.metric-value{

font-size:32px;

font-weight:700;

}



.metric-label{

font-size:15px;

color:#777;

}



.section-title{

font-size:26px;

font-weight:700;

margin-top:35px;

margin-bottom:15px;

}



.info-box{

padding:15px;

border-radius:12px;

background:#f8f9fa;

}



</style>

""",
unsafe_allow_html=True
)



# ============================================================
# TIME ACCESS CONTROL
# ============================================================


IST = pytz.timezone(
    "Asia/Kolkata"
)


current_time = datetime.now(
    IST
)


if not (
    15 <= current_time.hour < 17
):

    st.warning(

        """
        ⏰ This analytics module is available only

        **03:00 PM - 05:00 PM IST**

        """

    )

    st.stop()



# ============================================================
# HEADER
# ============================================================


st.markdown(

"""
<div class="main-title">

🔥 Google Play Store Intelligence

</div>


<div class="sub-title">

Interactive Hierarchical Cluster Heatmap
for Category Performance Analysis

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
        "Dataset not found."
    )

    st.stop()



# ============================================================
# LOAD DATA
# ============================================================


@st.cache_data

def load_dataset(path):

    return pd.read_csv(

        path,

        encoding="utf-8",

        on_bad_lines="skip"

    )


df = load_dataset(
    DATA_FILE
)



# ============================================================
# COLUMN STANDARDIZATION
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
# DATA CLEANING
# ============================================================


def convert_number(value):

    value=str(value)

    value=(

        value

        .replace(",","")

        .replace("+","")

    )


    try:

        return float(value)

    except:

        return np.nan




def convert_size(value):

    value=str(value)


    if "M" in value:

        return float(

            value.replace(
                "M",
                ""
            )

        )


    if "k" in value:

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




df["rating"]=pd.to_numeric(

    df["rating"],

    errors="coerce"

)



df["reviews"]=df["reviews"].apply(
    convert_number
)



df["installs"]=df["installs"].apply(
    convert_number
)



df["size_mb"]=df["size"].apply(
    convert_size
)



df["last_updated"]=pd.to_datetime(

    df["last_updated"],

    errors="coerce"

)



df["update_month"]=(
    df["last_updated"]
    .dt.month_name()
)



# ============================================================
# REMOVE APPLICATIONS WITH NUMBERS
# ============================================================


df=df[

~df["app"]

.astype(str)

.str.contains(

r"\d",

regex=True

)

]



# ============================================================
# BUSINESS FILTER CONDITIONS
# ============================================================


filtered=df[


(df["rating"]>=4.0)

&

(df["size_mb"]>10)

&

(df["installs"]>=10000)

&

(df["reviews"]>1000)

&

(df["update_month"]=="January")


]



if filtered.empty:

    st.error(
        "No records match the selected restrictions."
    )

    st.stop()



# ============================================================
# KPI SECTION
# ============================================================


st.markdown(

'<div class="section-title">📊 Performance Overview</div>',

unsafe_allow_html=True

)



k1,k2,k3,k4 = st.columns(4)



with k1:

    st.metric(

        "Filtered Apps",

        f"{len(filtered):,}"

    )



with k2:

    st.metric(

        "Categories",

        filtered["category"].nunique()

    )



with k3:

    st.metric(

        "Average Rating",

        f"{filtered.rating.mean():.2f}"

    )



with k4:

    st.metric(

        "Total Installs",

        f"{filtered.installs.sum()/1e6:.1f}M"

    )



# ============================================================
# SIDEBAR CONTROL PANEL
# ============================================================


st.sidebar.title(
    "⚙ Analytics Controls"
)



top_categories=st.sidebar.slider(

    "Top Categories",

    5,

    15,

    10

)



heatmap_type=st.sidebar.radio(

    "Heatmap Display",

    [

        "Normalized Z Score",

        "Raw Values"

    ]

)



st.sidebar.subheader(
    "Composite Score Weights"
)



w1=st.sidebar.slider(
    "Weighted Rating",
    0.0,
    1.0,
    0.25
)


w2=st.sidebar.slider(
    "Reviews",
    0.0,
    1.0,
    0.20
)


w3=st.sidebar.slider(
    "Installs",
    0.0,
    1.0,
    0.20
)


w4=st.sidebar.slider(
    "Average Size",
    0.0,
    1.0,
    0.10
)


w5=st.sidebar.slider(
    "Engagement Rate",
    0.0,
    1.0,
    0.15
)


w6=st.sidebar.slider(
    "Update Frequency",
    0.0,
    1.0,
    0.10
)



# ============================================================
# CATEGORY LEVEL ANALYTICS
# ============================================================


def weighted_rating(data):

    return np.average(

        data["rating"],

        weights=data["reviews"]

    )



category_df=(

filtered

.groupby("category")

.apply(

lambda x:pd.Series({

"Weighted Rating":
weighted_rating(x),

"Total Reviews":
x.reviews.sum(),

"Total Installs":
x.installs.sum(),

"Average Size":
x.size_mb.mean(),

"Engagement Rate":
(
x.reviews.sum()
/
x.installs.sum()
)
*100,


"Update Frequency":
x["last_updated"].nunique() if "last_updated" in x.columns else len(x)

})

)

.reset_index()

)



features=[

"Weighted Rating",

"Total Reviews",

"Total Installs",

"Average Size",

"Engagement Rate",

"Update Frequency"

]


# ============================================================
# NORMALIZATION
# ============================================================


scaler=StandardScaler()


scaled=scaler.fit_transform(

category_df[features]

)



normalized=pd.DataFrame(

scaled,

columns=features

)



# ============================================================
# COMPOSITE SCORE
# ============================================================


normalized["Composite Score"]=(

normalized["Weighted Rating"]*w1

+

normalized["Total Reviews"]*w2

+

normalized["Total Installs"]*w3

+

normalized["Average Size"]*w4

+

normalized["Engagement Rate"]*w5

+

normalized["Update Frequency"]*w6

)



category_df["Composite Score"]=normalized["Composite Score"]



category_df=(

category_df

.sort_values(

"Composite Score",

ascending=False

)

.head(top_categories)

)


# ============================================================
# END PART 1
# ============================================================
# ============================================================
# PART 2
# CLUSTERING + VISUAL ANALYTICS
# ============================================================


# ============================================================
# HIERARCHICAL CLUSTERING
# ============================================================


cluster_matrix = (

    category_df[features]

)



cluster_scaled = StandardScaler().fit_transform(

    cluster_matrix

)



linked = linkage(

    cluster_scaled,

    method="ward"

)



cluster_order = leaves_list(

    linked

)



clustered_categories = (

    category_df

    .iloc[cluster_order]

)



# ============================================================
# HEATMAP DATA PREPARATION
# ============================================================


if heatmap_type == "Normalized Z Score":


    heatmap_data = pd.DataFrame(

        StandardScaler()

        .fit_transform(

            clustered_categories[features]

        ),

        columns=features,

        index=clustered_categories["category"]

    )


else:


    heatmap_data = (

        clustered_categories

        .set_index("category")[features]

    )



# ============================================================
# CLUSTER HEATMAP
# ============================================================


st.markdown(

'<div class="section-title">🔥 Hierarchical Cluster Heatmap</div>',

unsafe_allow_html=True

)



fig_heatmap = px.imshow(

    heatmap_data,

    text_auto=".2f",

    aspect="auto",

    color_continuous_scale="RdBu",

    labels={

        "x":"Performance Metrics",

        "y":"App Categories",

        "color":"Value"

    }

)



fig_heatmap.update_layout(

    height=650,

    template="plotly_white"

)



st.plotly_chart(

    fig_heatmap,

    width='stretch'

)



# ============================================================
# COMPOSITE SCORE RANKING
# ============================================================


st.markdown(

'<div class="section-title">🏆 Category Performance Ranking</div>',

unsafe_allow_html=True

)



ranking_df=(

category_df

.sort_values(

"Composite Score",

ascending=False

)

)



fig_rank = px.bar(

    ranking_df,

    x="category",

    y="Composite Score",

    text="Composite Score",

    color="Composite Score",

    color_continuous_scale="Viridis",

    title="Weighted Composite Score Ranking"

)



fig_rank.update_traces(

    texttemplate="%{text:.2f}",

    textposition="outside"

)



fig_rank.update_layout(

    height=500,

    template="plotly_white"

)



st.plotly_chart(

    fig_rank,

    width='stretch'

)



# ============================================================
# TOP AND LOWEST PERFORMERS
# ============================================================


left,right = st.columns(2)



with left:


    st.subheader(

        "🥇 Top 3 Categories"

    )


    top3=(

        ranking_df

        .head(3)

        [["category","Composite Score"]]

    )


    st.dataframe(

        top3,

        hide_index=True,

        width='stretch'

    )



with right:


    st.subheader(

        "⚠ Improvement Areas"

    )


    bottom3=(

        ranking_df

        .tail(3)

        [["category","Composite Score"]]

    )


    st.dataframe(

        bottom3,

        hide_index=True,

        width='stretch'

    )



# ============================================================
# CATEGORY COMPARISON
# ============================================================


st.markdown(

'<div class="section-title">📌 Category Comparison</div>',

unsafe_allow_html=True

)



selected_category = st.selectbox(

    "Select Category",

    clustered_categories["category"]

)



selected_data=(

category_df

[

category_df["category"]

==selected_category

]

)



radar_values = [

selected_data["Weighted Rating"].iloc[0],

selected_data["Total Reviews"].iloc[0],

selected_data["Total Installs"].iloc[0],

selected_data["Average Size"].iloc[0],

selected_data["Engagement Rate"].iloc[0],

selected_data["Update Frequency"].iloc[0]

]



radar_labels=[

"Rating",

"Reviews",

"Installs",

"Size",

"Engagement",

"Updates"

]



fig_radar = go.Figure()



fig_radar.add_trace(

go.Scatterpolar(

r=radar_values,

theta=radar_labels,

fill="toself",

name=selected_category

)

)



fig_radar.update_layout(

polar=dict(

radialaxis=dict(

visible=True

)

),

height=550,

title=f"{selected_category} Performance Profile"

)



st.plotly_chart(

fig_radar,

width='stretch'

)



# ============================================================
# METRIC COMPARISON TABLE
# ============================================================


st.markdown(

'<div class="section-title">📊 Detailed Metrics</div>',

unsafe_allow_html=True

)



detail_table=(

category_df

.sort_values(

"Composite Score",

ascending=False

)

)



st.dataframe(

detail_table,

width='stretch',

hide_index=True

)



# ============================================================
# INSIGHTS
# ============================================================


st.markdown(

'<div class="section-title">💡 Automated Insights</div>',

unsafe_allow_html=True

)



best_category=(

ranking_df.iloc[0]["category"]

)



best_score=(

ranking_df.iloc[0]["Composite Score"]

)



lowest_category=(

ranking_df.iloc[-1]["category"]

)



st.success(

f"""

🏆 Best Performing Category:

**{best_category}**

Composite Score:

**{best_score:.2f}**

"""

)



st.warning(

f"""

📌 Category requiring improvement:

**{lowest_category}**

"""

)



# ============================================================
# DOWNLOAD SECTION
# ============================================================


st.markdown(

'<div class="section-title">⬇ Download Reports</div>',

unsafe_allow_html=True

)



download_csv = category_df.to_csv(

    index=False

)



st.download_button(

    label="📥 Download Category Analysis CSV",

    data=download_csv,

    file_name="cluster_heatmap_analysis.csv",

    mime="text/csv"

)



heatmap_csv = heatmap_data.to_csv()



st.download_button(

    label="🔥 Download Heatmap Data",

    data=heatmap_csv,

    file_name="cluster_heatmap_values.csv",

    mime="text/csv"

)



# ============================================================
# FOOTER
# ============================================================


st.markdown("---")



st.markdown(

"""

<div style="text-align:center;color:#777">

<b>Google Play Store Intelligence Dashboard</b><br>

Hierarchical Cluster Heatmap Analytics<br>

Python • Pandas • Scikit-Learn • Plotly • Streamlit

</div>

""",

unsafe_allow_html=True

)
