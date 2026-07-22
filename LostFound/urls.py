from django.urls import path
from . import views

urlpatterns = [
    # Public Views
    path('', views.home_view, name='home'),
    path('cases/', views.cases_list_view, name='cases_list'),
    path('case/<int:pk>/', views.case_detail_view, name='case_detail'),
    path('map/', views.map_view, name='map'),
    path('ai-search/', views.ai_search_view, name='ai_search'),
    path('blogs/', views.blog_list_view, name='blog_list'),
    path('blog/<slug:slug>/', views.blog_detail_view, name='blog_detail'),
    
    # Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # User Case Management
    path('create-case/', views.create_case_view, name='create_case'),
    path('case/<int:case_pk>/sighting/', views.submit_sighting_view, name='submit_sighting'),
    path('case/<int:case_pk>/request-detective/', views.request_detective_view, name='request_detective'),
    
    # Detective
    path('apply-detective/', views.apply_detective_view, name='apply_detective'),
    path('detective-dashboard/', views.detective_dashboard_view, name='detective_dashboard'),
    path('add-update/<int:assignment_pk>/', views.add_investigation_update_view, name='add_update'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('approve-detective/<int:app_pk>/', views.approve_detective_view, name='approve_detective'),
    path('assign-detective/<int:case_pk>/', views.assign_detective_view, name='assign_detective'),
    path('create-blog/', views.create_blog_view, name='create_blog'),
    
    # Profile & Dashboard
    path('profile/', views.profile_view, name='profile'),
    path('edit-profile/', views.edit_profile_view, name='edit_profile'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # API Endpoints
    path('api/cases/', views.cases_api, name='cases_api'),
]
