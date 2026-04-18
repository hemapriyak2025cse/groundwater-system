import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io, base64

PLOTLY_THEME = 'plotly_white'

def fig_to_html(fig):
    return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'responsive': True})

def mpl_to_base64():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=110)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    return b64

# ── Trend: line + moving averages ─────────────────────────────────────────────
def groundwater_trend_chart(df, state=None, district=None):
    from analytics.utils.trend_analysis import long_term_trend
    grouped = long_term_trend(df, state, district)
    if grouped.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=grouped['year'], y=grouped['groundwater_level'],
        mode='lines+markers', name='Yearly Avg',
        line=dict(color='#2563eb', width=2.5),
        marker=dict(size=5)
    ))
    fig.add_trace(go.Scatter(
        x=grouped['year'], y=grouped['ma3'],
        mode='lines', name='3-yr MA',
        line=dict(color='#f59e0b', dash='dash', width=2)
    ))
    fig.add_trace(go.Scatter(
        x=grouped['year'], y=grouped['ma5'],
        mode='lines', name='5-yr MA',
        line=dict(color='#ef4444', dash='dot', width=2)
    ))
    title = f"Groundwater Level Trend — {district or state or 'All India'}"
    fig.update_layout(
        title=title, xaxis_title='Year',
        yaxis_title='Depth (m below ground level)',
        yaxis_autorange='reversed',
        template=PLOTLY_THEME, height=400,
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    return fig_to_html(fig)

# ── State-wise bar chart ───────────────────────────────────────────────────────
def state_comparison_chart(df):
    grouped = df.groupby('state')['groundwater_level'].mean().reset_index()
    grouped = grouped.sort_values('groundwater_level', ascending=False)
    fig = px.bar(
        grouped, x='state', y='groundwater_level',
        color='groundwater_level', color_continuous_scale='RdYlGn_r',
        labels={'groundwater_level': 'Avg Depth (m bgl)', 'state': 'State'},
        title='Average Groundwater Depth by State (CGWB)'
    )
    fig.update_layout(template=PLOTLY_THEME, height=400, xaxis_tickangle=-40,
                      coloraxis_colorbar=dict(title='Depth (m)'))
    return fig_to_html(fig)

# ── Depletion rate bar ─────────────────────────────────────────────────────────
def depletion_bar_chart(df):
    from analytics.utils.trend_analysis import get_top_depleted_districts
    top = get_top_depleted_districts(df)
    if top.empty:
        return None
    top['label'] = top['district'] + ', ' + top['state']
    fig = px.bar(
        top, x='label', y='depletion_rate',
        color='depletion_rate', color_continuous_scale='Reds',
        labels={'depletion_rate': 'Avg Depletion (m/yr)', 'label': 'District'},
        title='Top 10 Most Depleted Districts (CGWB)'
    )
    fig.update_layout(template=PLOTLY_THEME, height=400, xaxis_tickangle=-30)
    return fig_to_html(fig)

# ── Risk pie chart ─────────────────────────────────────────────────────────────
def risk_pie_chart(df):
    from analytics.utils.trend_analysis import add_risk_classification
    df = add_risk_classification(df.copy())
    counts = df['risk_category'].value_counts().reset_index()
    counts.columns = ['category', 'count']
    color_map = {
        'Safe': '#10b981', 'Semi-Critical': '#f59e0b',
        'Critical': '#f97316', 'Over-Exploited': '#ef4444'
    }
    colors = [color_map.get(c, '#94a3b8') for c in counts['category']]
    fig = go.Figure(go.Pie(
        labels=counts['category'], values=counts['count'],
        marker=dict(colors=colors), hole=0.4,
        textinfo='label+percent'
    ))
    fig.update_layout(title='CGWB Risk Category Distribution', template=PLOTLY_THEME, height=360)
    return fig_to_html(fig)

# ── Seasonal comparison ────────────────────────────────────────────────────────
def seasonal_chart(df):
    if 'season' not in df.columns:
        return None
    grouped = df.groupby(['season', 'year'])['groundwater_level'].mean().reset_index()
    fig = px.line(
        grouped, x='year', y='groundwater_level', color='season',
        labels={'groundwater_level': 'Avg Depth (m bgl)', 'year': 'Year'},
        title='Seasonal Groundwater Level Trend (Pre/Post Monsoon)'
    )
    fig.update_layout(template=PLOTLY_THEME, height=400,
                      yaxis_autorange='reversed',
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig_to_html(fig)

# ── Pre vs Post Monsoon grouped bar ───────────────────────────────────────────
def pre_post_monsoon_chart(df):
    if 'season' not in df.columns:
        return None
    seasons = ['Pre-Monsoon', 'Post-Monsoon']
    filtered = df[df['season'].isin(seasons)]
    if filtered.empty:
        return None
    grouped = filtered.groupby(['state', 'season'])['groundwater_level'].mean().reset_index()
    fig = px.bar(
        grouped, x='state', y='groundwater_level', color='season',
        barmode='group', color_discrete_map={'Pre-Monsoon': '#ef4444', 'Post-Monsoon': '#2563eb'},
        labels={'groundwater_level': 'Avg Depth (m bgl)', 'state': 'State'},
        title='Pre-Monsoon vs Post-Monsoon Groundwater Depth by State'
    )
    fig.update_layout(template=PLOTLY_THEME, height=420, xaxis_tickangle=-40)
    return fig_to_html(fig)

# ── Multi-state comparison ─────────────────────────────────────────────────────
def multiline_state_chart(df, states):
    filtered = df[df['state'].isin(states)]
    grouped  = filtered.groupby(['state', 'year'])['groundwater_level'].mean().reset_index()
    fig = px.line(
        grouped, x='year', y='groundwater_level', color='state',
        labels={'groundwater_level': 'Avg Depth (m bgl)', 'year': 'Year'},
        title='Groundwater Level Comparison Across States'
    )
    fig.update_layout(template=PLOTLY_THEME, height=420, yaxis_autorange='reversed',
                      legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1))
    return fig_to_html(fig)

# ── EDA: Histogram ────────────────────────────────────────────────────────────
def histogram_chart(df, col='groundwater_level'):
    if col not in df.columns:
        return None
    fig = px.histogram(
        df, x=col, nbins=40,
        color_discrete_sequence=['#2563eb'],
        labels={col: 'Depth (m bgl)'},
        title=f'Distribution of Groundwater Depth (CGWB)'
    )
    fig.update_layout(template=PLOTLY_THEME, height=360)
    return fig_to_html(fig)

# ── EDA: Box plot by state ────────────────────────────────────────────────────
def boxplot_chart(df, col='groundwater_level'):
    if col not in df.columns:
        return None
    fig = px.box(
        df, x='state', y=col,
        color='state',
        labels={col: 'Depth (m bgl)', 'state': 'State'},
        title='Groundwater Depth Distribution by State (Outlier Detection)'
    )
    fig.update_layout(template=PLOTLY_THEME, height=420,
                      xaxis_tickangle=-40, showlegend=False)
    return fig_to_html(fig)

# ── Depletion heatmap: state x year ───────────────────────────────────────────
def depletion_heatmap(df):
    pivot = df.groupby(['state', 'year'])['groundwater_level'].mean().unstack('year')
    if pivot.empty:
        return None
    plt.figure(figsize=(14, 7))
    sns.heatmap(pivot, cmap='RdYlGn_r', linewidths=0.3,
                cbar_kws={'label': 'Avg Depth (m bgl)'}, annot=False)
    plt.title('Groundwater Depth Heatmap — State × Year (CGWB)', fontsize=13, pad=12)
    plt.xlabel('Year')
    plt.ylabel('State')
    plt.tight_layout()
    return mpl_to_base64()

# ── Year-wise district scatter ─────────────────────────────────────────────────
def district_scatter_chart(df, state):
    fdf = df[df['state'] == state]
    if fdf.empty:
        return None
    grouped = fdf.groupby(['district', 'year'])['groundwater_level'].mean().reset_index()
    fig = px.scatter(
        grouped, x='year', y='groundwater_level', color='district',
        size='groundwater_level', hover_name='district',
        labels={'groundwater_level': 'Depth (m bgl)', 'year': 'Year'},
        title=f'District-wise Groundwater Depth — {state}'
    )
    fig.update_layout(template=PLOTLY_THEME, height=420, yaxis_autorange='reversed')
    return fig_to_html(fig)
