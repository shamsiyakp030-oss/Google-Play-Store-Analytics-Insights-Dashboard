import re
import pandas as pd


def rating_filter(df, minimum_rating):
    return df.loc[df["Rating"] >= minimum_rating].copy()


def installs_filter(df, minimum_installs):
    return df.loc[df["Installs"] >= minimum_installs].copy()


def reviews_filter(df, minimum_reviews):
    return df.loc[df["Reviews"] >= minimum_reviews].copy()


def size_filter(df, min_size, max_size):
    return df.loc[df["Size_MB"].between(min_size, max_size, inclusive="both")].copy()


def exclude_app_names(df, letters):
    pattern = "|".join(re.escape(str(x)) for x in letters)
    return df.loc[~df["App"].astype(str).str.contains(pattern, case=False, na=False, regex=True)].copy()


def category_filter(df, categories):
    return df.loc[df["Category"].isin(categories)].copy()
