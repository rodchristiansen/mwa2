# Django settings for munkiwebadmin project - Development with YAML Support

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'dev-key-for-yaml-testing-not-for-production'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # our apps
    'api',
    'catalogs',
    'manifests',
    'pkgsinfo',
    'process',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'munkiwebadmin.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'munkiwebadmin.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'munkiwebadmin', 'static'),
]

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'test_repo', 'icons')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'mwa2_dev.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'munkiwebadmin': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# APPNAME is user-visible web app name
APPNAME = 'MunkiWebAdmin2 (YAML Development)'

# MUNKI_REPO_DIR holds the local filesystem path to the Munki repo
MUNKI_REPO_DIR = os.path.join(BASE_DIR, 'test_repo')

# Icons URL for development
ICONS_URL = MEDIA_URL

# Path to the makecatalogs binary (optional for development)
MAKECATALOGS_PATH = '/usr/local/munki/makecatalogs'

# Git path (optional for development)
#GIT_PATH = '/usr/bin/git'

# ================================
# YAML Support Settings
# ================================

# Set to True to prefer YAML format for new files when extension is ambiguous
PREFER_YAML_FORMAT = True

# Set to True to show format information in the UI
SHOW_FILE_FORMAT_INFO = True

# Default file extension for new manifests/pkginfo when no extension specified
DEFAULT_MANIFEST_EXTENSION = '.yaml'
DEFAULT_PKGINFO_EXTENSION = '.yaml'

print(f"🚀 MWA2 Development Settings Loaded")
print(f"📁 Munki Repo: {MUNKI_REPO_DIR}")
print(f"🎯 YAML Support: Enabled (Prefer YAML: {PREFER_YAML_FORMAT})")
print(f"🔍 Format Info: {'Enabled' if SHOW_FILE_FORMAT_INFO else 'Disabled'}")
