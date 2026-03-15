from django.urls import path

from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportIndexView.as_view(), name='report_index'),
    path('production/', views.ProductionReportView.as_view(), name='production'),
    path('commissions/', views.CommissionReportView.as_view(), name='commissions'),
    path('insurer-portfolio/', views.InsurerPortfolioReportView.as_view(), name='insurer_portfolio'),
    path('type-portfolio/', views.InsuranceTypePortfolioReportView.as_view(), name='type_portfolio'),
    path('claims/', views.ClaimsReportView.as_view(), name='claims'),
    path('loss-ratio/', views.LossRatioReportView.as_view(), name='loss_ratio'),
    path('renewals/', views.RenewalReportView.as_view(), name='renewals'),
    path('clients-by-broker/', views.ClientsByBrokerReportView.as_view(), name='clients_by_broker'),
    path('crm-funnel/', views.CRMFunnelReportView.as_view(), name='crm_funnel'),
    path('endorsements/', views.EndorsementReportView.as_view(), name='endorsements'),
]
