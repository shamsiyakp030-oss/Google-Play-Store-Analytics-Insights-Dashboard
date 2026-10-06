# 📊 Google Play Store Analytics & Insights Dashboard

<div align="center">

### An Interactive Data Analytics & Business Intelligence Dashboard

**Built with Python, Streamlit, Plotly, Pandas, NumPy, Scikit-learn, and optional Power BI**

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Interactive_App-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Pandas](https://img.shields.io/badge/Pandas-Data_Analysis-150458?style=for-the-badge&logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![NumPy](https://img.shields.io/badge/NumPy-Numerical_Computing-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive_Visualization-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com/)
[![Scikit-learn](https://img.shields.io/badge/Scikit--learn-Machine_Learning-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Power BI](https://img.shields.io/badge/Power_BI-Business_Intelligence-F2C811?style=for-the-badge&logo=powerbi&logoColor=black)](https://powerbi.microsoft.com/)

**[🚀 Live Dashboard](https://app-play-store-analytics-dashboard-pmmyeqzcgbnuutsuxyihxb.streamlit.app/)** · **[💻 GitHub Repository](https://github.com/shamsiyakp030-oss/Google-Play-Store-Analytics-Insights-Dashboard)**

</div>

---

## 🌟 Project Overview

**Google Play Store Analytics & Insights Dashboard** is an interactive data analytics and business intelligence application developed as part of a Google Play Store Data Analytics Internship project.

The project transforms Google Play Store application data into meaningful insights through data cleaning, preprocessing, exploratory analysis, statistical analysis, interactive visualizations, category comparisons, trend analysis, clustering, and dashboard reporting.

The application is implemented as a multi-page **Streamlit** dashboard and uses **Plotly** for interactive visual analytics. **Scikit-learn** supports normalization and clustering analysis, while **Power BI** is included as an optional business-intelligence component.

---

## 🎯 Project Objectives

- 🧹 Clean, transform, and preprocess Google Play Store data.
- 🔎 Perform exploratory data analysis.
- 📊 Build interactive dashboards for application performance analysis.
- 📈 Analyze ratings, reviews, installs, size, categories, and update patterns.
- 🔵 Explore relationships and dense regions in app-performance data.
- 🌞 Analyze category and rating hierarchies using a Sunburst visualization.
- 🗓️ Analyze monthly installation patterns using a calendar heatmap.
- 🌊 Compare category trends using a streamgraph.
- 🔥 Rank and cluster categories using normalized performance metrics.
- 🎯 Compare category performance across multiple dimensions using a radar chart.
- 💡 Generate data-driven business insights through interactive analytics.

---

## ✨ Key Features

### 📊 Interactive Analytics

- Multi-page Streamlit dashboard
- Dynamic filters and selectors
- Interactive Plotly visualizations
- KPI cards and summary metrics
- Category-level comparisons
- Interactive hover information
- Data-driven business insights

### 🧹 Data Processing

- Missing-value handling
- Duplicate detection
- Data type conversion
- Numeric normalization
- Feature transformation
- Category and app-level filtering
- Shared reusable data-cleaning utilities

### 📈 Advanced Analysis

- Hexbin density analysis
- Sunburst hierarchy analysis
- Calendar heatmap and trend analysis
- Streamgraph category trends
- Hierarchical clustering
- Z-score normalization
- Composite category ranking
- Radar-based multi-metric comparison

### 🖥️ Dashboard Experience

- Professional dark-themed interface
- Separate analytical modules
- IST-based access controls where required by the project specification
- Download-ready project assets
- Optional Power BI reporting

---

## 📊 Dashboard Modules

| # | Module | Python File | Purpose |
|---|---|---|---|
| 🏠 | Executive Overview | `app.py` | Landing page, KPIs, project overview, and navigation |
| 🔵 | Hexbin Density | `1_Hexbin_Density.py` | Analyze app size, rating, installs, and dense performance regions |
| 🌞 | Sunburst Analysis | `2_Sunburst_Analysis.py` | Explore Country → Category → App Type → Rating Band hierarchy |
| 🗓️ | Calendar Heatmap | `3_Calendar_Heatmap.py` | Analyze monthly installs, growth, rolling averages, and forecast status |
| 🌊 | Streamgraph Analysis | `4_Streamgraph_Analysis.py` | Compare category activity and trends over time |
| 🔥 | Cluster Heatmap | `5_Cluster_Heatmap.py` | Rank and cluster the top categories using multiple performance metrics |
| 🎯 | Radar Chart | `6_Radar_Chart.py` | Compare category performance across multiple dimensions |

---

## 🔍 Analytical Highlights

### 🔵 Hexbin Density

The Hexbin module explores the relationship between **app size and rating**, using installation intensity to understand dense regions of the dataset.

### 🌞 Sunburst Analysis

The Sunburst module provides a hierarchical view of:

**Country → Category → App Type → Rating Band**

It supports category filtering, installation-based sizing, review-weighted rating analysis, drill-down exploration, and interactive hover details.

When a dataset does not contain a genuine country field, the dashboard does not fabricate country-level results.

### 🗓️ Calendar Heatmap

The Calendar Heatmap focuses on **monthly installs** and uses:

- Category selection
- Monthly installation analysis
- Month-over-month growth
- Three-month rolling averages
- Forecast-versus-actual comparison
- Interactive hover information

This module uses:

```text
data/googleplaystore (2).csv
