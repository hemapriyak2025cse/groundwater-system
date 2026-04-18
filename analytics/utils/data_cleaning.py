import pandas as pd
import numpy as np

# Real CGWB dataset column mappings (flexible aliases)
CGWB_REQUIRED = ['state', 'district', 'year', 'groundwater_level']

CGWB_COLUMN_ALIASES = {
    'state':             ['state', 'state_name', 'statename', 'st_name'],
    'district':          ['district', 'district_name', 'districtname', 'dist_name', 'dist'],
    'year':              ['year', 'yr', 'data_year'],
    'groundwater_level': ['groundwater_level', 'gw_level', 'water_level', 'level_mbgl',
                          'depth_to_water_level', 'water_level_mbgl', 'gwl', 'wl_mbgl',
                          'pre_monsoon_gwl', 'post_monsoon_gwl', 'level'],
    'season':            ['season', 'period', 'monitoring_period', 'season_name'],
    'latitude':          ['latitude', 'lat'],
    'longitude':         ['longitude', 'lon', 'long'],
    'well_id':           ['well_id', 'well_no', 'station_id', 'wid'],
    'aquifer_type':      ['aquifer_type', 'aquifer', 'aq_type'],
}

def load_file(file_obj):
    name = file_obj.name.lower()
    if name.endswith('.csv'):
        return pd.read_csv(file_obj)
    elif name.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_obj)
    raise ValueError("Unsupported format. Use CSV or Excel.")

def normalize_columns(df):
    """Normalize column names and map CGWB aliases to standard names."""
    df.columns = [c.strip().lower().replace(' ', '_').replace('-', '_') for c in df.columns]
    rename_map = {}
    for standard, aliases in CGWB_COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in df.columns and standard not in df.columns:
                rename_map[alias] = standard
                break
    return df.rename(columns=rename_map)

def validate_cgwb(df):
    missing = [c for c in CGWB_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(
            f"Missing required CGWB columns: {missing}. "
            f"Required: state, district, year, groundwater_level"
        )
    return df

def handle_missing(df, strategy='mean'):
    if strategy == 'drop':
        return df.dropna(subset=['groundwater_level'])
    for col in df.columns:
        if df[col].isnull().any():
            if pd.api.types.is_numeric_dtype(df[col]):
                fill = df[col].mean() if strategy == 'mean' else df[col].median()
                df[col] = df[col].fillna(fill)
            else:
                mode = df[col].mode()
                df[col] = df[col].fillna(mode[0] if not mode.empty else 'Unknown')
    return df

def remove_outliers_iqr(df, col='groundwater_level'):
    Q1, Q3 = df[col].quantile(0.25), df[col].quantile(0.75)
    IQR = Q3 - Q1
    return df[(df[col] >= Q1 - 1.5 * IQR) & (df[col] <= Q3 + 1.5 * IQR)]

def get_missing_summary(df):
    total = len(df)
    return [{
        'column':  col,
        'missing': int(df[col].isnull().sum()),
        'percent': round(df[col].isnull().sum() / total * 100, 2) if total else 0,
        'dtype':   str(df[col].dtype),
    } for col in df.columns]

def get_descriptive_stats(df):
    numeric = df.select_dtypes(include=[np.number])
    if numeric.empty:
        return {}
    return numeric.describe().round(3).to_dict()

def clean_and_prepare(df, missing_strategy='mean'):
    df = normalize_columns(df)
    df = validate_cgwb(df)
    df = handle_missing(df, missing_strategy)
    df['year']              = pd.to_numeric(df['year'], errors='coerce').fillna(0).astype(int)
    df['groundwater_level'] = pd.to_numeric(df['groundwater_level'], errors='coerce')
    df['state']             = df['state'].astype(str).str.strip().str.title()
    df['district']          = df['district'].astype(str).str.strip().str.title()
    if 'season' in df.columns:
        df['season'] = df['season'].astype(str).str.strip().str.title()
    df = df.dropna(subset=['groundwater_level'])
    return df
