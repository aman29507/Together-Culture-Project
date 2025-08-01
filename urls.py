"""
URL configuration for Together Culture CRM app.
"""

from django.urls import path
from . import views

app_name = 'crm'

urlpatterns = [
    # Public pages
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Member area
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Admin area
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('members/', views.member_list, name='member_list'),
    path('member/<int:member_id>/', views.member_detail, name='member_detail'),
    
    # Ajax endpoints
    path('ajax/search-members/', views.ajax_member_search, name='ajax_member_search'),
]