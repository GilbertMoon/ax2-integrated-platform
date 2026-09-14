import os
from unittest.mock import patch

from django.test.runner import DiscoverRunner

from config.settings import *  # noqa: F403 - inherit base settings before QA overrides

# Prevent real notifications in this isolated test configuration.
os.environ.pop("SLACK_BOT_TOKEN", None)
os.environ.pop("SLACK_WEBHOOK_URL", None)


class OfflineRunner(DiscoverRunner):
    def run_tests(self, *args, **kwargs):
        with patch(
            "requests.sessions.Session.request",
            side_effect=AssertionError("Live HTTP is forbidden in QA"),
        ):
            return super().run_tests(*args, **kwargs)


TEST_RUNNER = "config.lms_test_settings.OfflineRunner"

DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
    "assignment_lms": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"},
}
GITHUB_OAUTH_CLIENT_ID = None
GITHUB_OAUTH_CLIENT_SECRET = None
GITHUB_TOKEN_ENC_KEY = None
GEMINI_API_KEY = None
PRD_GEMINI_API_KEY = ""
SLACK_NOTIFY_SYNC = True
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "lms": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {"base_url": "/lms-media/"},
    },
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
