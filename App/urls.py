from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('items/', views.items, name='items'),
    path('feedback/', views.feedback, name='feedback'),
    path('blog/', views.blog, name='blog'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-panel/requests/', views.admin_requests, name='admin_requests'),
    path('admin-panel/blog/', views.admin_blog, name='admin_blog'),
    path('admin-panel/gallery/', views.admin_gallery, name='admin_gallery'),
]