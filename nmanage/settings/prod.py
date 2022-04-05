from dj_easy_log import load_loguru

from nmanage.settings.base import *

STATIC_ROOT = BASE_DIR / 'static-compiled'
SECURE_SSL_REDIRECT = True

load_loguru(globals())
