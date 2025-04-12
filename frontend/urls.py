# frontend/urls.py
from django.urls import include, path
from django.urls import path
from backend import views  # Make sure views are imported from the backend

urlpatterns = [
    path('', views.welcome, name='welcome'),
    path('login/', views.login_redirect, name='login'),
    path('how-it-works/', views.how_it_works, name='how_it_works'),
    path('window-screen/', views.window_screen, name='window_screen'),  # This should point to the correct view
    path("__reload__/", include("django_browser_reload.urls")),
]
