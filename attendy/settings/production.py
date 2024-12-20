from .base import *
import dj_database_url
from dotenv import load_dotenv

# Your development specific settings here
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load prod.env file
load_dotenv(
    os.path.join(BASE_DIR, 'prod.env')
)

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv("DEBUG", False) == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS').split(" ")

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.parse(os.getenv('RENDER_POSTGRESQL_URL'))
}

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

SITE_URL = os.getenv('SITE_URL')
