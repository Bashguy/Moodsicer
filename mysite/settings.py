# settings.py

from dotenv import load_dotenv
import os
from pathlib import Path  

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(dotenv_path=os.path.join(BASE_DIR, 'backend', '.env'))

SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')  
DEBUG = True
ALLOWED_HOSTS = []  

INSTALLED_APPS = [
    'django.contrib.contenttypes',  
    'frontend',  
]

MIDDLEWARE = []  

ROOT_URLCONF = 'mysite.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'frontend' / 'templates'],  
        'APP_DIRS': True,  
    },
]

WSGI_APPLICATION = 'mysite.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',  
    }
}
