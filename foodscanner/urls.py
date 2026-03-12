from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('scan/', views.scan, name='scan'),
    path('scan-food/', views.scan_food, name='scan_food'),
    path('food/<int:food_id>/', views.food_detail, name='food_detail'),
    path('food/<int:food_id>/rate/', views.rate_food, name='rate_food'),
    path('food/<int:food_id>/review/', views.review_food, name='review_food'),
    path('food/<int:food_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('food/<int:food_id>/generate_video/', views.generate_video, name='generate_video'),
    path('favorites/', views.favorites, name='favorites'),
    path('history/', views.history, name='history'),
    path('ai-assistant/', views.ai_assistant, name='ai_assistant'),
]