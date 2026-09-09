"""Migration-only settings for the existing standalone LMS database history.

Never use these settings for runserver or deployment. The live service uses
config.settings and accounts.User; the old LMS auth_user tables remain untouched.
"""
from config.settings import *

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'lms_modules.core',
    'lms_modules.accounts_client',
    'lms_modules.tutor',
    'lms_modules.github_sync',
]
AUTH_USER_MODEL = 'auth.User'
DATABASES = {'default': DATABASES['assignment_lms']}


class DomainMigrationRouter:
    def allow_migrate(self, db, app_label, model_name=None, **hints):
        return app_label in {'core', 'tutor', 'github_sync'}


DATABASE_ROUTERS = [DomainMigrationRouter()]
ROOT_URLCONF = 'lms_modules.migration_urls'
MIDDLEWARE = []
