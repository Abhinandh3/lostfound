from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('profile/', views.profile, name='profile'),
    path('items/', views.items, name='items'),
    path('feedback/', views.feedback, name='feedback'),
    path('blog/', views.blog, name='blog'),
    path('admin-page/', views.admin_page, name='admin_page'),
]