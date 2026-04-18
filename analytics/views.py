from datetime import datetime
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
import pandas as pd
import numpy as np

from .forms import SignupForm, LoginForm, CGWBUploadForm
from .models import UserProfile
from .mongo import get_collection
from .utils.data_cleaning import (load_file, clean_and_prepare,
                                   get_missing_summary, get_descriptive_stats,
                                   remove_outliers_iqr)
from .utils.trend_analysis import (add_risk_classification, compute_depletion_rate,
                                    get_top_depleted_districts, generate_insights,
                                    long_term_trend, pre_post_monsoon_comparison,
                                    seasonal_trend)
from .utils.charts import (groundwater_trend_chart, state_comparison_chart,
                            depletion_bar_chart, risk_pie_chart, seasonal_chart,
                            pre_post_monsoon_chart, multiline_state_chart,
                            histogram_chart, boxplot_chart,
                            depletion_heatmap, district_scatter_chart)
from .utils.report_generator import generate_pdf_report


def is_admin(user):
    try:
        return user.profile.is_admin()
    except Exception:
        return False

def get_cgwb_df():
    docs = list(get_collection('groundwater_levels').find({}, {'_id': 0}))
    return pd.DataFrame(docs) if docs else pd.DataFrame()


# ── Auth ──────────────────────────────────────────────────────────────────────

def home(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'analytics/home.html')

def signup_view(request):
    form = SignupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Account created successfully!")
        return redirect('dashboard')
    return render(request, 'analytics/signup.html', {'form': form})

def login_view(request):
    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = authenticate(request,
                            username=form.cleaned_data['username'],
                            password=form.cleaned_data['password'])
        if user:
            login(request, user)
            return redirect('dashboard')
        messages.error(request, "Invalid credentials.")
    return render(request, 'analytics/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')


# ── Dashboard ─────────────────────────────────────────────────────────────────

@login_required
def dashboard(request):
    df = get_cgwb_df()
    ctx = {
        'total_states': 0, 'total_districts': 0, 'total_records': 0,
        'avg_gw_level': 'N/A', 'highest_depletion': 'N/A',
        'year_range': 'N/A', 'has_season': False,
        'trend_chart': None, 'bar_chart': None, 'pie_chart': None,
        'risk_counts': {}, 'insights': [],
    }
    if not df.empty:
        ctx['total_states']    = df['state'].nunique()
        ctx['total_districts'] = df['district'].nunique()
        ctx['total_records']   = len(df)
        ctx['avg_gw_level']    = round(df['groundwater_level'].mean(), 2)
        ctx['year_range']      = f"{int(df['year'].min())} – {int(df['year'].max())}"
        ctx['has_season']      = 'season' in df.columns

        df_risk = add_risk_classification(df)
        ctx['risk_counts'] = df_risk['risk_category'].value_counts().to_dict()

        top = get_top_depleted_districts(df)
        if not top.empty:
            ctx['highest_depletion'] = f"{top.iloc[0]['district']}, {top.iloc[0]['state']}"

        ctx['trend_chart'] = groundwater_trend_chart(df)
        ctx['bar_chart']   = state_comparison_chart(df)
        ctx['pie_chart']   = risk_pie_chart(df)
        ctx['insights']    = generate_insights(df)[:4]

    return render(request, 'analytics/dashboard.html', ctx)


# ── Upload ────────────────────────────────────────────────────────────────────

@login_required
def upload_data(request):
    if not is_admin(request.user):
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    form    = CGWBUploadForm(request.POST or None, request.FILES or None)
    preview = None
    col_info = None
    record_count = 0

    if request.method == 'POST' and form.is_valid():
        strategy = form.cleaned_data['missing_strategy']
        replace  = form.cleaned_data.get('replace_existing', True)
        file_obj = request.FILES['file']
        try:
            raw_df = load_file(file_obj)
            col_info = get_missing_summary(raw_df)
            df = clean_and_prepare(raw_df.copy(), strategy)
            records = df.to_dict('records')
            col = get_collection('groundwater_levels')
            if replace:
                col.delete_many({})
            col.insert_many(records)
            record_count = len(records)
            preview = df.head(10).to_html(
                classes='table table-sm', index=False, border=0
            )
            messages.success(request, f"Uploaded {record_count:,} CGWB records successfully.")
        except Exception as e:
            messages.error(request, str(e))

    existing = get_collection('groundwater_levels').count_documents({})
    return render(request, 'analytics/upload.html', {
        'form': form, 'preview': preview,
        'col_info': col_info, 'existing': existing,
    })


# ── EDA ───────────────────────────────────────────────────────────────────────

@login_required
def eda_view(request):
    df = get_cgwb_df()
    ctx = {
        'stats': {}, 'missing': [], 'outlier_removed': False,
        'hist_chart': None, 'box_chart': None,
        'depletion_heatmap': None,
        'total_records': 0, 'has_data': False,
    }
    if not df.empty:
        ctx['has_data']      = True
        ctx['total_records'] = len(df)
        ctx['missing']       = get_missing_summary(df)
        ctx['stats']         = get_descriptive_stats(df)

        if request.GET.get('remove_outliers') == '1':
            df = remove_outliers_iqr(df, 'groundwater_level')
            ctx['outlier_removed'] = True
            ctx['total_records']   = len(df)

        ctx['hist_chart']       = histogram_chart(df)
        ctx['box_chart']        = boxplot_chart(df)
        ctx['depletion_heatmap'] = depletion_heatmap(df)

    return render(request, 'analytics/eda.html', ctx)


# ── Trend Analysis ────────────────────────────────────────────────────────────

@login_required
def trend_analysis(request):
    df = get_cgwb_df()

    state    = request.GET.get('state', '')
    district = request.GET.get('district', '')

    states    = sorted(df['state'].unique().tolist()) if not df.empty else []
    districts = (sorted(df[df['state'] == state]['district'].unique().tolist())
                 if state and not df.empty else [])

    ctx = {
        'states': states, 'districts': districts,
        'selected_state': state, 'selected_district': district,
        'trend_chart': None, 'seasonal_chart': None,
        'pre_post_chart': None, 'depletion_chart': None,
        'scatter_chart': None, 'has_data': not df.empty,
        'has_season': 'season' in df.columns if not df.empty else False,
    }

    if not df.empty:
        ctx['trend_chart']    = groundwater_trend_chart(df, state or None, district or None)
        ctx['seasonal_chart'] = seasonal_chart(df)
        ctx['pre_post_chart'] = pre_post_monsoon_chart(df)
        ctx['depletion_chart'] = depletion_bar_chart(df)
        if state:
            ctx['scatter_chart'] = district_scatter_chart(df, state)

    return render(request, 'analytics/trend_analysis.html', ctx)


# ── Critical Zones ────────────────────────────────────────────────────────────

@login_required
def critical_zones(request):
    df = get_cgwb_df()
    state_filter = request.GET.get('state', '')

    states = sorted(df['state'].unique().tolist()) if not df.empty else []
    fdf = df[df['state'] == state_filter].copy() if state_filter and not df.empty else df.copy()

    ctx = {
        'top_districts': [], 'pie_chart': None,
        'risk_counts': {}, 'no_data': df.empty,
        'states': states, 'selected_state': state_filter,
        'depletion_chart': None,
    }

    if not fdf.empty:
        fdf_risk = add_risk_classification(fdf)
        ctx['risk_counts']     = fdf_risk['risk_category'].value_counts().to_dict()
        ctx['pie_chart']       = risk_pie_chart(fdf)
        ctx['depletion_chart'] = depletion_bar_chart(fdf)
        top = get_top_depleted_districts(fdf)
        ctx['top_districts']   = top.to_dict('records')

    return render(request, 'analytics/critical_zones.html', ctx)


# ── Comparison ────────────────────────────────────────────────────────────────

@login_required
def comparison(request):
    df = get_cgwb_df()
    all_states = sorted(df['state'].unique().tolist()) if not df.empty else []
    selected   = request.GET.getlist('states') or all_states[:5]

    ctx = {
        'all_states': all_states, 'selected_states': selected,
        'multiline_chart': None, 'bar_chart': None, 'pie_chart': None,
        'pre_post_chart': None,
    }
    if not df.empty:
        ctx['multiline_chart'] = multiline_state_chart(df, selected)
        ctx['bar_chart']       = state_comparison_chart(df)
        ctx['pie_chart']       = risk_pie_chart(df)
        ctx['pre_post_chart']  = pre_post_monsoon_chart(df)

    return render(request, 'analytics/comparison.html', ctx)


# ── Generate Report ───────────────────────────────────────────────────────────

@login_required
def generate_report(request):
    if not is_admin(request.user):
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    df     = get_cgwb_df()
    states = sorted(df['state'].unique().tolist()) if not df.empty else []

    if request.method == 'POST':
        state_f    = request.POST.get('state', '')
        district_f = request.POST.get('district', '')
        fdf = df.copy()
        if state_f:    fdf = fdf[fdf['state'] == state_f]
        if district_f: fdf = fdf[fdf['district'] == district_f]

        insights = generate_insights(fdf)
        stats_df = fdf.describe() if not fdf.empty else pd.DataFrame()
        pdf_buf  = generate_pdf_report(insights, stats_df, state_f, district_f)

        get_collection('reports').insert_one({
            'generated_date':   datetime.now().isoformat(),
            'state_filter':     state_f,
            'district_filter':  district_f,
            'insights_summary': insights,
            'generated_by':     request.user.username,
        })

        resp = HttpResponse(pdf_buf.read(), content_type='application/pdf')
        resp['Content-Disposition'] = (
            f'attachment; filename="cgwb_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
        )
        return resp

    return render(request, 'analytics/generate_report.html', {
        'states':           states,
        'insights_preview': generate_insights(df) if not df.empty else [],
        'selected_state':   '',
    })


# ── Reports History ───────────────────────────────────────────────────────────

@login_required
def reports_history(request):
    reports = list(
        get_collection('reports').find({}, {'_id': 0})
        .sort('generated_date', -1).limit(50)
    )
    return render(request, 'analytics/reports_history.html', {'reports': reports})


# ── Admin Panel ───────────────────────────────────────────────────────────────

@login_required
def admin_panel(request):
    if not is_admin(request.user):
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    from django.contrib.auth.models import User
    users = User.objects.select_related('profile').all()
    record_count = get_collection('groundwater_levels').count_documents({})

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'clear_dataset':
            get_collection('groundwater_levels').delete_many({})
            messages.success(request, "CGWB dataset cleared.")
        elif action == 'delete_user':
            uid = request.POST.get('user_id')
            try:
                u = User.objects.get(pk=uid)
                if u != request.user:
                    u.delete()
                    messages.success(request, f"User '{u.username}' deleted.")
            except User.DoesNotExist:
                pass
        return redirect('admin_panel')

    return render(request, 'analytics/admin_panel.html', {
        'users': users, 'record_count': record_count,
    })


# ── JSON API ──────────────────────────────────────────────────────────────────

@login_required
def api_gw_trend(request):
    df    = get_cgwb_df()
    state = request.GET.get('state')
    if state: df = df[df['state'] == state]
    grouped = df.groupby('year')['groundwater_level'].mean().reset_index()
    return JsonResponse({
        'years':  grouped['year'].tolist(),
        'levels': grouped['groundwater_level'].round(2).tolist(),
    })

@login_required
def api_districts(request):
    state = request.GET.get('state', '')
    docs  = list(get_collection('groundwater_levels').find(
        {'state': state}, {'_id': 0, 'district': 1}
    ))
    return JsonResponse({'districts': sorted(set(d['district'] for d in docs))})
