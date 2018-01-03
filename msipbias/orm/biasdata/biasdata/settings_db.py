import os

DBHOST = os.environ.get('BIASDB_HOST', '')
DBPORT = os.environ.get('BIASDB_PORT', '')
DBUSER = os.environ.get('BIASDB_USER', '')
DBPASS = os.environ.get('BIASDB_PASS', '')

# Database
# https://docs.djangoproject.com/en/1.8/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'biasdb',
        'USER': DBUSER,
        'PASSWORD': DBPASS,
        'HOST': DBHOST,
        'PORT': DBPORT
    }
}
