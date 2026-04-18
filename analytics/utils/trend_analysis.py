import pandas as pd
import numpy as np

# CGWB classification thresholds (CGWB norms, depth in m below ground level)
RISK_THRESHOLDS = {
    'Safe':           (0,  20),
    'Semi-Critical':  (20, 40),
    'Critical':       (40, 60),
    'Over-Exploited': (60, float('inf')),
}

def classify_risk(level):
    if level <= 20:   return 'Safe'
    elif level <= 40: return 'Semi-Critical'
    elif level <= 60: return 'Critical'
    else:             return 'Over-Exploited'

def add_risk_classification(df):
    df = df.copy()
    df['risk_category'] = df['groundwater_level'].apply(classify_risk)
    return df

def compute_depletion_rate(df):
    """Year-over-year depletion per district (positive = depleting deeper)."""
    df = df.sort_values(['state', 'district', 'year']).copy()
    df['prev_level']    = df.groupby(['state', 'district'])['groundwater_level'].shift(1)
    df['depletion_rate'] = df['groundwater_level'] - df['prev_level']   # +ve = going deeper
    return df

def get_top_depleted_districts(df, n=10):
    df = compute_depletion_rate(df)
    agg = df.groupby(['state', 'district'])['depletion_rate'].mean().reset_index()
    return agg.nlargest(n, 'depletion_rate')

def seasonal_trend(df):
    if 'season' not in df.columns:
        return pd.DataFrame()
    return df.groupby(['season', 'year'])['groundwater_level'].mean().reset_index()

def long_term_trend(df, state=None, district=None):
    """Returns yearly mean + moving average for trend line."""
    if state:    df = df[df['state'] == state]
    if district: df = df[df['district'] == district]
    grouped = df.groupby('year')['groundwater_level'].mean().reset_index()
    grouped['ma3'] = grouped['groundwater_level'].rolling(3, min_periods=1).mean()
    grouped['ma5'] = grouped['groundwater_level'].rolling(5, min_periods=1).mean()
    return grouped

def pre_post_monsoon_comparison(df):
    """Compare Pre-Monsoon vs Post-Monsoon levels if season column exists."""
    if 'season' not in df.columns:
        return pd.DataFrame()
    seasons = ['Pre-Monsoon', 'Post-Monsoon']
    filtered = df[df['season'].isin(seasons)]
    if filtered.empty:
        return pd.DataFrame()
    return filtered.groupby(['state', 'season'])['groundwater_level'].mean().unstack('season').reset_index()

def generate_insights(df):
    insights = []
    if df.empty:
        return insights

    df_dep = compute_depletion_rate(df)
    df_risk = add_risk_classification(df)

    yr_min, yr_max = int(df['year'].min()), int(df['year'].max())
    insights.append(f"Dataset spans {yr_min} to {yr_max} ({yr_max - yr_min + 1} years).")

    avg_level = round(df['groundwater_level'].mean(), 2)
    insights.append(f"National average groundwater depth: {avg_level} m below ground level.")

    state_dep = df_dep.groupby('state')['depletion_rate'].mean().dropna()
    if not state_dep.empty:
        worst = state_dep.idxmax()
        rate  = round(state_dep.max(), 2)
        insights.append(f"{worst} has the highest depletion rate ({rate} m/yr on average).")
        best = state_dep.idxmin()
        insights.append(f"{best} shows the most stable groundwater levels.")

    over = df_risk[df_risk['risk_category'] == 'Over-Exploited']['district'].unique()
    if len(over):
        insights.append(f"{len(over)} district(s) are Over-Exploited (>60 m depth): {', '.join(over[:5])}{'...' if len(over)>5 else ''}.")

    safe_pct = round((df_risk['risk_category'] == 'Safe').sum() / len(df_risk) * 100, 1)
    insights.append(f"{safe_pct}% of records fall in the Safe category (<20 m depth).")

    if 'season' in df.columns:
        pre  = df[df['season'] == 'Pre-Monsoon']['groundwater_level'].mean()
        post = df[df['season'] == 'Post-Monsoon']['groundwater_level'].mean()
        if not (pd.isna(pre) or pd.isna(post)):
            diff = round(pre - post, 2)
            insights.append(
                f"Pre-Monsoon avg depth ({round(pre,2)} m) is {'deeper' if diff>0 else 'shallower'} "
                f"than Post-Monsoon ({round(post,2)} m) by {abs(diff)} m."
            )

    top = get_top_depleted_districts(df)
    if not top.empty:
        d = top.iloc[0]
        insights.append(f"Most depleted district: {d['district']} ({d['state']}) at {round(d['depletion_rate'],2)} m/yr.")

    return insights
