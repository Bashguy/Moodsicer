# mysite/urls.py

from django.urls import path, include

urlpatterns = [
    path('', include('frontend.urls')),  # Include frontend URLs that will call views from backend
]
