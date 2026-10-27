"""Isolated local verification: never reads production database configuration."""
import os
os.environ['PRODUCTION'] = 'False'
from .settings import *  # noqa: F403
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
MEDIA_ROOT = BASE_DIR / '.test-media'
