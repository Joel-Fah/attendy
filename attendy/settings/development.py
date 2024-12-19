from .base import *
from dotenv import load_dotenv

# Settings overrides for development environment

# Load prod.env file
load_dotenv(
    os.path.join(BASE_DIR, 'dev.env')
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-8_+&c$&g(8+xz=3l5g030jn%rm-grf$(e-bhfko27bu!tgbd@f'

DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
    'test': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': 'localhost',
        'PORT': '5432'
    }
}

# Add compression and caching support for whitenoise

# STORAGES = {
#     "default": {
#         "BACKEND": "django.core.files.storage.FileSystemStorage",
#     },
#     "staticfiles": {
#         "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
#     },
# }

# Tailwind config
NPM_BIN_PATH = "C:/Program Files/nodejs/npm.cmd"

SITE_URL = 'http://127.0.0.1:8000/'
