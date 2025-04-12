# backend/views.py

from django.shortcuts import render, redirect

def welcome(request):
    return render(request, 'welcome.html')  # Adjust path to templates

def how_it_works(request):
    return render(request, 'how_it_works.html')  # Adjust path to templates

def window_screen(request):
    return render(request, 'window_screen.html')  # Adjust path to templates

def login_redirect(request):
    return redirect('http://localhost:8001/login')  # Redirect to FastAPI login
