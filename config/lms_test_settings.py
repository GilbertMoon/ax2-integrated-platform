import os
from unittest.mock import patch

from django.test.runner import DiscoverRunner

from config.settings import *  # noqa: F403 - inherit base settings before QA overrides
from config.settings import BASE_DIR

# Prevent real notifications in this isolated test configuration.
os.environ.pop("SLACK_BOT_TOKEN", None)
os.environ.pop("SLACK_WEBHOOK_URL", None)
os.environ.pop("SLACK_TEST_BOT_TOKEN", None)
os.environ.pop("SLACK_TEST_WEBHOOK_URL", None)
os.environ.pop("SLACK_PROD_BOT_TOKEN", None)
os.environ.pop("SLACK_PROD_WEBHOOK_URL", None)


class OfflineRunner(DiscoverRunner):
    def build_suite(self, test_labels=None, **kwargs):
        labels = list(test_labels or [])
        if not labels or labels == ["."] or labels == [str(BASE_DIR)]:
            labels = labels or ["."]
            labels += [
                "lms",
                "lms_modules.common.tests",
                "lms_modules.github_sync.tests",
                "lms_modules.tutor.tests",
                "lms_modules.student.tests",
            ]
        return super().build_suite(labels, **kwargs)

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
GITHUB_SYNC_SYNC = True
STORAGES = {
    "bug_reports": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
    "lms": {
        "BACKEND": "django.core.files.storage.InMemoryStorage",
        "OPTIONS": {"base_url": "/lms-media/"},
    },
}
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
