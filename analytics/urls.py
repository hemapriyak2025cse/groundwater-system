from django.urls import path
from . import views

urlpatterns = [
    path('',                    views.home,             name='home'),
    path('signup/',             views.signup_view,      name='signup'),
    path('login/',              views.login_view,       name='login'),
    path('logout/',             views.logout_view,      name='logout'),
    path('dashboard/',          views.dashboard,        name='dashboard'),
    path('upload-data/',        views.upload_data,      name='upload_data'),
    path('eda/',                views.eda_view,         name='eda'),
    path('trend-analysis/',     views.trend_analysis,   name='trend_analysis'),
    path('critical-zones/',     views.critical_zones,   name='critical_zones'),
    path('comparison/',         views.comparison,       name='comparison'),
    path('generate-report/',    views.generate_report,  name='generate_report'),
    path('reports-history/',    views.reports_history,  name='reports_history'),
    path('admin-panel/',        views.admin_panel,      name='admin_panel'),
    # JSON API
    path('api/gw-trend/',       views.api_gw_trend,     name='api_gw_trend'),
    path('api/districts/',      views.api_districts,    name='api_districts'),
]
