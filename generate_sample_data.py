"""
Generates a realistic CGWB-format groundwater level dataset and auto-loads into MongoDB.
Run: python generate_sample_data.py
"""
import pandas as pd
import numpy as np
import os

np.random.seed(42)

STATES_DISTRICTS = {
    'Punjab':            ['Ludhiana', 'Amritsar', 'Jalandhar', 'Patiala', 'Bathinda', 'Sangrur', 'Moga'],
    'Haryana':           ['Gurugram', 'Faridabad', 'Hisar', 'Rohtak', 'Karnal', 'Panipat', 'Sirsa'],
    'Rajasthan':         ['Jaipur', 'Jodhpur', 'Bikaner', 'Kota', 'Udaipur', 'Barmer', 'Nagaur'],
    'Gujarat':           ['Ahmedabad', 'Surat', 'Vadodara', 'Rajkot', 'Gandhinagar', 'Mehsana', 'Banaskantha'],
    'Maharashtra':       ['Pune', 'Nashik', 'Nagpur', 'Aurangabad', 'Solapur', 'Ahmednagar', 'Latur'],
    'Uttar Pradesh':     ['Lucknow', 'Kanpur', 'Agra', 'Varanasi', 'Meerut', 'Allahabad', 'Bareilly'],
    'Bihar':             ['Patna', 'Gaya', 'Muzaffarpur', 'Bhagalpur', 'Darbhanga', 'Nalanda', 'Saran'],
    'West Bengal':       ['Kolkata', 'Howrah', 'Durgapur', 'Asansol', 'Siliguri', 'Bardhaman', 'Murshidabad'],
    'Tamil Nadu':        ['Chennai', 'Coimbatore', 'Madurai', 'Salem', 'Tiruchirappalli', 'Vellore', 'Tirunelveli'],
    'Karnataka':         ['Bengaluru', 'Mysuru', 'Hubli', 'Mangaluru', 'Belagavi', 'Kalaburagi', 'Tumkur'],
    'Madhya Pradesh':    ['Bhopal', 'Indore', 'Gwalior', 'Jabalpur', 'Ujjain', 'Sagar', 'Rewa'],
    'Andhra Pradesh':    ['Visakhapatnam', 'Vijayawada', 'Guntur', 'Nellore', 'Kurnool', 'Kadapa', 'Anantapur'],
    'Telangana':         ['Hyderabad', 'Warangal', 'Nizamabad', 'Karimnagar', 'Khammam', 'Nalgonda', 'Medak'],
    'Odisha':            ['Bhubaneswar', 'Cuttack', 'Rourkela', 'Berhampur', 'Sambalpur', 'Puri', 'Balasore'],
    'Jharkhand':         ['Ranchi', 'Jamshedpur', 'Dhanbad', 'Bokaro', 'Hazaribagh', 'Giridih', 'Deoghar'],
    'Chhattisgarh':      ['Raipur', 'Bhilai', 'Bilaspur', 'Korba', 'Durg', 'Rajnandgaon', 'Jagdalpur'],
    'Himachal Pradesh':  ['Shimla', 'Dharamshala', 'Mandi', 'Solan', 'Kullu', 'Hamirpur', 'Una'],
    'Uttarakhand':       ['Dehradun', 'Haridwar', 'Roorkee', 'Haldwani', 'Rishikesh', 'Nainital', 'Almora'],
    'Kerala':            ['Thiruvananthapuram', 'Kochi', 'Kozhikode', 'Thrissur', 'Kollam', 'Palakkad', 'Malappuram'],
    'Assam':             ['Guwahati', 'Dibrugarh', 'Silchar', 'Jorhat', 'Nagaon', 'Tezpur', 'Bongaigaon'],
}

# Realistic base depth (m bgl) — stressed states start deeper
BASE_DEPTH = {
    'Punjab': 52, 'Haryana': 45, 'Rajasthan': 60, 'Gujarat': 35,
    'Maharashtra': 28, 'Uttar Pradesh': 22, 'Bihar': 10, 'West Bengal': 8,
    'Tamil Nadu': 32, 'Karnataka': 26, 'Madhya Pradesh': 20, 'Andhra Pradesh': 30,
    'Telangana': 34, 'Odisha': 12, 'Jharkhand': 14, 'Chhattisgarh': 16,
    'Himachal Pradesh': 6, 'Uttarakhand': 7, 'Kerala': 5, 'Assam': 5,
}

# Annual depletion rate (m/yr) — higher for over-exploited states
DEPLETION_RATE = {
    'Punjab': 1.6, 'Haryana': 1.4, 'Rajasthan': 1.8, 'Gujarat': 1.0,
    'Maharashtra': 0.7, 'Uttar Pradesh': 0.6, 'Bihar': 0.3, 'West Bengal': 0.2,
    'Tamil Nadu': 0.9, 'Karnataka': 0.8, 'Madhya Pradesh': 0.5, 'Andhra Pradesh': 0.7,
    'Telangana': 0.8, 'Odisha': 0.3, 'Jharkhand': 0.3, 'Chhattisgarh': 0.4,
    'Himachal Pradesh': 0.1, 'Uttarakhand': 0.1, 'Kerala': 0.1, 'Assam': 0.1,
}

YEARS   = list(range(2000, 2024))
SEASONS = ['Pre-Monsoon', 'Post-Monsoon', 'Rabi', 'Kharif']
AQUIFER_TYPES = ['Alluvial', 'Hard Rock', 'Coastal', 'Semi-Arid']

SEASONAL_OFFSET = {
    'Pre-Monsoon':  3.5,   # deeper before rains
    'Post-Monsoon': -3.0,  # shallower after rains
    'Rabi':          1.0,
    'Kharif':       -1.5,
}

rows = []
well_counter = 1000

for state in STATES_DISTRICTS:
    for district in STATES_DISTRICTS[state]:
        base_depth  = BASE_DEPTH[state] + np.random.uniform(-4, 4)
        depl_rate   = DEPLETION_RATE[state] + np.random.uniform(-0.2, 0.2)
        lat_base    = np.random.uniform(8.5, 34.5)
        lon_base    = np.random.uniform(68.5, 96.5)
        aquifer     = np.random.choice(AQUIFER_TYPES)

        for year in YEARS:
            trend = (year - 2000) * depl_rate
            for season in SEASONS:
                s_offset = SEASONAL_OFFSET[season]
                noise    = np.random.normal(0, 1.2)
                level    = base_depth + trend + s_offset + noise
                rows.append({
                    'state':             state,
                    'district':          district,
                    'year':              year,
                    'season':            season,
                    'groundwater_level': round(max(0.5, level), 2),
                    'latitude':          round(lat_base + np.random.uniform(-0.3, 0.3), 4),
                    'longitude':         round(lon_base + np.random.uniform(-0.3, 0.3), 4),
                    'well_id':           f'CGWB-{well_counter:05d}',
                    'aquifer_type':      aquifer,
                })
                well_counter += 1

df = pd.DataFrame(rows)
os.makedirs('sample_data', exist_ok=True)
df.to_csv('sample_data/cgwb_groundwater_levels.csv', index=False)
print(f"cgwb_groundwater_levels.csv  -- {len(df):,} rows")
print(f"States: {df['state'].nunique()} | Districts: {df['district'].nunique()} | Years: {df['year'].min()}-{df['year'].max()}")

# ── Auto-load into MongoDB ─────────────────────────────────────────────────────
try:
    import django, os as _os
    _os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'groundwater_system.settings')
    django.setup()
    from analytics.mongo import get_collection
    from analytics.utils.data_cleaning import clean_and_prepare

    cleaned = clean_and_prepare(df.copy(), 'mean')
    col = get_collection('groundwater_levels')
    col.delete_many({})
    col.insert_many(cleaned.to_dict('records'))
    print(f"\n[OK] {len(cleaned):,} CGWB records loaded into MongoDB.")
    print("Run: python manage.py runserver")
except Exception as e:
    print(f"\nMongoDB auto-load skipped: {e}")
    print("Upload sample_data/cgwb_groundwater_levels.csv manually via /upload-data/")
