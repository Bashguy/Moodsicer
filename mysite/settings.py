# settings.py

from dotenv import load_dotenv
import os
from pathlib import Path  

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=os.path.join(BASE_DIR, 'backend', '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  
DEBUG = True
ALLOWED_HOSTS = []  

# Installed apps (we only need basic apps for rendering templates)
INSTALLED_APPS = [
    'django.contrib.contenttypes',  # Minimal app required for template rendering
    'frontend',  # Your frontend app
]

MIDDLEWARE = []  # No middleware required for this basic app

ROOT_URLCONF = 'mysite.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],  # Pointing to the frontend templates
        'APP_DIRS': True,  # Ensure it looks in app-specific template directories
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

# Optional: If you don't need the database, remove it completely
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',  # Dummy backend for no database usage
    }
}
