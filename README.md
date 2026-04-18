# Groundwater Analysis System

## Setup

### 1. Create virtual environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Linux/Mac
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure environment
Edit `.env`:
```
MONGO_URI=mongodb://localhost:27017/
MONGO_DB_NAME=groundwater_db
SECRET_KEY=your-secret-key-here
DEBUG=True
```

### 4. Run migrations (Django auth/sessions)
```bash
python manage.py migrate
```

### 5. Create superuser (optional)
```bash
python manage.py createsuperuser
```

### 6. Generate sample data (optional)
```bash
python generate_sample_data.py
```

### 7. Run server
```bash
python manage.py runserver
```

Visit: http://127.0.0.1:8000

---

## Routes

| URL | Description |
|-----|-------------|
| `/` | Home |
| `/signup/` | Register |
| `/login/` | Login |
| `/dashboard/` | Main dashboard |
| `/upload-data/` | Upload CSV/Excel (Admin) |
| `/eda/` | Exploratory Data Analysis |
| `/trend-analysis/` | Trend & seasonal analysis |
| `/correlation/` | Correlation heatmap & scatter |
| `/critical-zones/` | Risk zone detection |
| `/comparison/` | State/district comparison |
| `/generate-report/` | PDF report generator (Admin) |
| `/reports-history/` | Past reports |
| `/admin-panel/` | User & dataset management (Admin) |

---

## Dataset Column Requirements

| Dataset | Required Columns |
|---------|-----------------|
| groundwater_levels | state, district, year, groundwater_level |
| rainfall_data | state, district, year, rainfall_mm |
| agriculture_usage | state, district, year, water_usage_mcm |
| population_data | state, district, year, population_density |

Optional columns: `season`, `latitude`, `longitude`

---

## Tech Stack
- **Backend**: Django 4.2
- **Database**: MongoDB (PyMongo) + SQLite (auth)
- **Frontend**: Bootstrap 5.3
- **Charts**: Plotly + Matplotlib + Seaborn
- **PDF**: ReportLab
- **Data**: Pandas + NumPy
