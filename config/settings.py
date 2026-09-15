import os
import sys
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# Keep existing LMS imports working from the grouped app directory.
sys.path.insert(0, str(BASE_DIR / "2team_lms"))
load_dotenv(BASE_DIR / ".env")


def env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ImproperlyConfigured(f"{name} must be a boolean value")


def env_int(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError as error:
        raise ImproperlyConfigured(f"{name} must be an integer") from error


def env_list(name, default=()):
    value = os.getenv(name)
    if value is None:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


RUNNING_TESTS = "test" in sys.argv
DEBUG = env_bool("DJANGO_DEBUG", True)
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "unsafe-local-development-key")
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", ["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env_list("DJANGO_CSRF_TRUSTED_ORIGINS")

SITE_URL = os.getenv("DJANGO_SITE_URL", "").strip().rstrip("/") or (
    CSRF_TRUSTED_ORIGINS[0].rstrip("/") if CSRF_TRUSTED_ORIGINS else "http://127.0.0.1:8000"
)

INSTALLED_APPS = [
    "bug_reports.apps.BugReportsConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "allauth.socialaccount.providers.kakao",
    "axes",
    "accounts.apps.AccountsConfig",
    "attendance.apps.AttendanceConfig",
    "teams.apps.TeamsConfig",
    "rounds.apps.RoundsConfig",
    "reviews.apps.ReviewsConfig",
    "results.apps.ResultsConfig",
    "audit.apps.AuditConfig",
    "notices.apps.NoticesConfig",
    "notifications.apps.NotificationsConfig",
    "lms.apps.LmsConfig",
    "lms_client.apps.LmsClientConfig",
    "widget_tweaks",
    "lms_modules.core",
    "lms_modules.accounts_client",
    "lms_modules.common",
    "lms_modules.student",
    "lms_modules.tutor",
    "lms_modules.github_sync",
    # 3조 Idea Developer 도메인. 인증은 기존 accounts.User를 그대로 사용한다.
    "apps.common",
    "apps.integration",
    "apps.jobs",
    "apps.brainstorm",
    "apps.prds",
    "apps.ai",
]

MIDDLEWARE = [
    "accounts.middleware.TrustedProxyMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "axes.middleware.AxesMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "accounts.middleware.AccountAccessMiddleware",
]

ROOT_URLCONF = "config.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "lms_modules.common.context_processors.nav",
            ],
        },
    }
]
WSGI_APPLICATION = "config.wsgi.application"

POSTGRES_KEYS = (
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "POSTGRES_HOST",
    "POSTGRES_PORT",
)
if all(os.getenv(key) for key in POSTGRES_KEYS):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ["POSTGRES_DB"],
            "USER": os.environ["POSTGRES_USER"],
            "PASSWORD": os.environ["POSTGRES_PASSWORD"],
            "HOST": os.environ["POSTGRES_HOST"],
            "PORT": os.environ["POSTGRES_PORT"],
            "CONN_MAX_AGE": env_int("POSTGRES_CONN_MAX_AGE", 60),
        },
        "assignment_lms": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("LMS_DB_NAME", "assignment_lms"),
            "USER": os.getenv("LMS_DB_USER", "postgres"),
            "PASSWORD": os.getenv("LMS_DB_PASSWORD", ""),
            "HOST": os.getenv("LMS_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("LMS_DB_PORT", "5432"),
            "OPTIONS": {
                "options": "-c default_transaction_read_only=on",
            },
        },
    }
elif DEBUG:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
        "assignment_lms": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("LMS_DB_NAME", "assignment_lms"),
            "USER": os.getenv("LMS_DB_USER", "postgres"),
            "PASSWORD": os.getenv("LMS_DB_PASSWORD", ""),
            "HOST": os.getenv("LMS_DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("LMS_DB_PORT", "5432"),
            "OPTIONS": {
                "options": "-c default_transaction_read_only=on",
            },
        },
    }
else:
    raise ImproperlyConfigured("Production requires all POSTGRES_* settings")

DATABASE_ROUTERS = ["lms.db_router.LmsDatabaseRouter"]

AUTH_USER_MODEL = "accounts.User"
AUTHENTICATION_BACKENDS = (
    "axes.backends.AxesStandaloneBackend",
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)
SITE_ID = 1

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*"]
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_UNIQUE_EMAIL = True
SOCIALACCOUNT_ADAPTER = "accounts.adapters.CustomSocialAccountAdapter"
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_LOGIN_TIMEOUT = 300
SOCIALACCOUNT_STORE_TOKENS = False

GOOGLE_OAUTH_REQUESTED = env_bool("GOOGLE_OAUTH_ENABLED", False)
GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "").strip()
GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "").strip()
GOOGLE_OAUTH_ENABLED = GOOGLE_OAUTH_REQUESTED and bool(
    GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET
)
KAKAO_OAUTH_REQUESTED = env_bool("KAKAO_OAUTH_ENABLED", False)
KAKAO_OAUTH_CLIENT_ID = os.getenv("KAKAO_OAUTH_CLIENT_ID", "").strip()
KAKAO_OAUTH_CLIENT_SECRET = os.getenv("KAKAO_OAUTH_CLIENT_SECRET", "").strip()
KAKAO_OAUTH_ENABLED = KAKAO_OAUTH_REQUESTED and bool(
    KAKAO_OAUTH_CLIENT_ID and KAKAO_OAUTH_CLIENT_SECRET
)
SOCIALACCOUNT_PROVIDERS = {}
if GOOGLE_OAUTH_ENABLED:
    SOCIALACCOUNT_PROVIDERS["google"] = {
        "APPS": [
            {
                "client_id": GOOGLE_OAUTH_CLIENT_ID,
                "secret": GOOGLE_OAUTH_CLIENT_SECRET,
                "key": "",
            }
        ],
        "SCOPE": ["openid", "email", "profile"],
        "AUTH_PARAMS": {"access_type": "online"},
        "OAUTH_PKCE_ENABLED": True,
    }
if KAKAO_OAUTH_ENABLED:
    SOCIALACCOUNT_PROVIDERS["kakao"] = {
        "APPS": [
            {
                "client_id": KAKAO_OAUTH_CLIENT_ID,
                "secret": KAKAO_OAUTH_CLIENT_SECRET,
                "key": "",
            }
        ]
    }
SOCIALACCOUNT_REQUESTS_TIMEOUT = env_int("SOCIALACCOUNT_REQUESTS_TIMEOUT", 5)

EMAIL_BACKEND = os.getenv(
    "DJANGO_EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend"
).strip()
EMAIL_HOST = os.getenv("DJANGO_EMAIL_HOST", "").strip()
EMAIL_PORT = env_int("DJANGO_EMAIL_PORT", 587)
EMAIL_HOST_USER = os.getenv("DJANGO_EMAIL_HOST_USER", "").strip()
EMAIL_HOST_PASSWORD = os.getenv("DJANGO_EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = env_bool("DJANGO_EMAIL_USE_TLS", False)
EMAIL_USE_SSL = env_bool("DJANGO_EMAIL_USE_SSL", False)
EMAIL_TIMEOUT = env_int("DJANGO_EMAIL_TIMEOUT", 10)
DEFAULT_FROM_EMAIL = os.getenv("DJANGO_DEFAULT_FROM_EMAIL", "webmaster@localhost").strip()
ACCOUNT_EMAIL_SUBJECT_PREFIX = os.getenv("DJANGO_ACCOUNT_EMAIL_SUBJECT_PREFIX", "[AX Console] ")

LOGIN_URL = "/accounts/login/"
LOGIN_REDIRECT_URL = "/accounts/dashboard/"
LOGOUT_REDIRECT_URL = "/accounts/login/"
SESSION_ENGINE = "django.contrib.sessions.backends.db"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 14
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = "Lax"

SECURE_SSL_REDIRECT = env_bool("DJANGO_SECURE_SSL_REDIRECT", not DEBUG and not RUNNING_TESTS)
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_HSTS_SECONDS = env_int("DJANGO_HSTS_SECONDS", 0 if DEBUG else 31_536_000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("DJANGO_HSTS_INCLUDE_SUBDOMAINS", False)
SECURE_HSTS_PRELOAD = env_bool("DJANGO_HSTS_PRELOAD", False)
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
TRUST_PROXY_HEADERS = env_bool("DJANGO_TRUST_PROXY_HEADERS", False)
TRUSTED_PROXY_IPS = env_list("DJANGO_TRUSTED_PROXY_IPS")
TRUSTED_PROXY_HOPS = env_int("DJANGO_TRUSTED_PROXY_HOPS", 0)
HTTPS_READY = env_bool("DJANGO_HTTPS_READY", False)

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 6},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AXES_ENABLED = True
AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_RESET_ON_SUCCESS = True
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False
AXES_LOCKOUT_PARAMETERS = ["username", "ip_address"]
AXES_USERNAME_CALLABLE = "accounts.security.canonicalize_axes_username"
AXES_CLIENT_IP_CALLABLE = "accounts.security.get_direct_client_ip"
AXES_LOCKOUT_CALLABLE = "accounts.security.axes_lockout_response"
AXES_HTTP_RESPONSE_CODE = 429
AXES_SENSITIVE_PARAMETERS = ["username", "email", "password"]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "media/"
MEDIA_ROOT = Path(os.environ.get("DJANGO_MEDIA_ROOT") or BASE_DIR / "media")
PROFILE_IMAGE_MAX_BYTES = 2 * 1024 * 1024

# 얼굴인식(출석 키오스크)이 호출하는 임베딩/라이브니스 서비스.
# 로컬에서는 기본값을 쓰고, 운영 환경은 DJANGO_FACE_SERVICE_URL로 실제 호스트를 지정한다.
FACE_SERVICE_URL = os.getenv("DJANGO_FACE_SERVICE_URL", "http://127.0.0.1:5001").strip().rstrip("/")
FACE_SERVICE_TIMEOUT = env_int("DJANGO_FACE_SERVICE_TIMEOUT", 15)
BUG_REPORT_UPLOAD_ROOT = Path(
    os.getenv("DJANGO_BUG_REPORT_UPLOAD_ROOT") or BASE_DIR / "private_uploads" / "bug_reports"
)
STORAGES = {
    "bug_reports": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
        "OPTIONS": {"location": BUG_REPORT_UPLOAD_ROOT},
    },
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if RUNNING_TESTS
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        )
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "structured": {
            "format": "{levelname} {name} request_id={request_id} event={message}",
            "style": "{",
            "defaults": {"request_id": "-"},
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "structured",
        }
    },
    "loggers": {
        "accounts.security": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

# LMS uses the existing domain database; Core authentication stays unchanged.
LMS_DATABASE_WRITE_ENABLED = env_bool("LMS_DATABASE_WRITE_ENABLED", False)
if LMS_DATABASE_WRITE_ENABLED:
    DATABASES["assignment_lms"]["OPTIONS"].pop("options", None)
AX_ROUND_ID = os.getenv("AX_ROUND_ID") or None
DEV_SKIP_AUTH = False
LMS_MEDIA_ROOT = Path(os.getenv("LMS_MEDIA_ROOT") or BASE_DIR / "media_lms")
LMS_MEDIA_URL = "/lms-media/"
STORAGES["lms"] = {
    "BACKEND": "django.core.files.storage.FileSystemStorage",
    "OPTIONS": {"location": LMS_MEDIA_ROOT, "base_url": LMS_MEDIA_URL},
}
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")
GEMINI_FALLBACK_MODELS = env_list("GEMINI_FALLBACK_MODELS", ["gemini-flash-latest"])
# 3조 Idea Developer는 2조 LMS의 Gemini 자격 증명과 분리한다.
PRD_GEMINI_API_KEY = os.getenv("PRD_GEMINI_API_KEY", "")
GITHUB_OAUTH_CLIENT_ID = os.getenv("GITHUB_OAUTH_CLIENT_ID")
GITHUB_OAUTH_CLIENT_SECRET = os.getenv("GITHUB_OAUTH_CLIENT_SECRET")
GITHUB_TOKEN_ENC_KEY = os.getenv("GITHUB_TOKEN_ENC_KEY")
GITHUB_SUBMISSION_REPO_NAME = os.getenv("GITHUB_SUBMISSION_REPO_NAME", "lms-assignments")
GITHUB_API_TOKEN = os.getenv("GITHUB_API_TOKEN")
SLACK_NOTIFY_SYNC = env_bool("SLACK_NOTIFY_SYNC", False)

# 3조 Idea Developer 연동 설정. 공용 사용자/회차/팀 VIEW는 같은 DB에서 읽는다.
INTEGRATION_DB_ALIAS = "default"
INTEGRATION_ACTIVE_ROUND_STATUSES = frozenset(
    env_list("INTEGRATION_ACTIVE_ROUND_STATUSES", ["IN_PROGRESS"])
)
INTEGRATION_APPROVED_USER_STATUS = os.getenv("INTEGRATION_APPROVED_USER_STATUS", "approved")
INTEGRATION_CONTEXT_RESOLVER_CLASS = "apps.integration.context.StandaloneSessionContextResolver"
PARENT_ROLE_PARTICIPANT_MAP = {
    "student": "editor",
    "tutor": "tutor",
    "admin": "owner",
}
PARENT_STAFF_PARTICIPANT_ROLE = "tutor"
PARENT_SUPERUSER_PARTICIPANT_ROLE = "owner"

API_VERSION = "v1"
POLLING_INTERVAL_MS = env_int("POLLING_INTERVAL_MS", 2000)
POLLING_MIN_INTERVAL_MS = env_int("POLLING_MIN_INTERVAL_MS", 2000)
POLLING_MAX_INTERVAL_MS = env_int("POLLING_MAX_INTERVAL_MS", 5000)
HOME_PAGE_SIZE = env_int("HOME_PAGE_SIZE", 12)
HOME_MAX_PAGE_SIZE = env_int("HOME_MAX_PAGE_SIZE", 50)
PRD_DETAIL_PAGE_SIZE = env_int("PRD_DETAIL_PAGE_SIZE", 20)
PRD_DETAIL_MAX_PAGE_SIZE = env_int("PRD_DETAIL_MAX_PAGE_SIZE", 100)
USER_SEARCH_MIN_LENGTH = env_int("USER_SEARCH_MIN_LENGTH", 2)
USER_SEARCH_PAGE_SIZE = env_int("USER_SEARCH_PAGE_SIZE", 20)
USER_SEARCH_MAX_PAGE_SIZE = env_int("USER_SEARCH_MAX_PAGE_SIZE", 100)

JOB_WORKER_POLL_SECONDS = float(os.getenv("JOB_WORKER_POLL_SECONDS", "5"))
JOB_RUNNER_CLASS = "apps.ai.worker.AiJobRunner"
AI_PROVIDER_CLASS = "apps.ai.gemini.GeminiAiProvider"
AI_RESULT_PROCESSOR_CLASS = "apps.ai.brainstorm.BrainstormAiResultRouter"
AI_EVALUATION_DEMO_CACHE = env_bool("AI_EVALUATION_DEMO_CACHE", False)
AI_JOB_TIMEOUT_SECONDS = env_int("AI_JOB_TIMEOUT_SECONDS", 30)
AI_JOB_MAX_ATTEMPTS = env_int("AI_JOB_MAX_ATTEMPTS", 3)
AI_JOB_RETRY_BASE_SECONDS = env_int("AI_JOB_RETRY_BASE_SECONDS", 5)
AI_DAILY_REQUEST_LIMIT = env_int("AI_DAILY_REQUEST_LIMIT", 50)
AI_DAILY_TOKEN_LIMIT = env_int("AI_DAILY_TOKEN_LIMIT", 200000)
AI_DAILY_COST_LIMIT_USD = Decimal(os.getenv("AI_DAILY_COST_LIMIT_USD", "20.00"))
AI_DUPLICATE_WINDOW_SECONDS = env_int("AI_DUPLICATE_WINDOW_SECONDS", 10)
AI_CHAT_MESSAGE_MAX_LENGTH = env_int("AI_CHAT_MESSAGE_MAX_LENGTH", 4000)
AI_CONTEXT_MAX_CHARS = env_int("AI_CONTEXT_MAX_CHARS", 20000)
AI_RESPONSE_MAX_LENGTH = env_int("AI_RESPONSE_MAX_LENGTH", 12000)
AI_DRAFT_MAX_LENGTH = env_int("AI_DRAFT_MAX_LENGTH", 12000)
AI_CHAT_RECENT_TURNS = env_int("AI_CHAT_RECENT_TURNS", 3)
AI_TTL_DELETE_BATCH_SIZE = env_int("AI_TTL_DELETE_BATCH_SIZE", 500)
AI_PREVIEW_RETENTION_DAYS = env_int("AI_PREVIEW_RETENTION_DAYS", 7)
AI_CHAT_PAYLOAD_RETENTION_DAYS = env_int("AI_CHAT_PAYLOAD_RETENTION_DAYS", 30)
AI_BRAINSTORM_MAX_NODES = env_int("AI_BRAINSTORM_MAX_NODES", 500)
AI_BRAINSTORM_MAX_CHARS = env_int("AI_BRAINSTORM_MAX_CHARS", 50000)
AI_CONTRIBUTION_MAX_COMMENTS = env_int("AI_CONTRIBUTION_MAX_COMMENTS", 500)
AI_CONTRIBUTION_MAX_CHARS = env_int("AI_CONTRIBUTION_MAX_CHARS", 50000)
BRAINSTORM_NOTE_MAX_LENGTH = env_int("BRAINSTORM_NOTE_MAX_LENGTH", 4000)
BRAINSTORM_ALLOWED_COLORS = tuple(
    env_list(
        "BRAINSTORM_ALLOWED_COLORS",
        ["yellow", "blue", "gray", "green", "pink", "purple", "orange"],
    )
)
BRAINSTORM_DELETE_RETENTION_DAYS = env_int("BRAINSTORM_DELETE_RETENTION_DAYS", 30)
PRD_TRASH_RETENTION_DAYS = env_int("PRD_TRASH_RETENTION_DAYS", 30)
BACKGROUND_CLEANUP_BATCH_SIZE = env_int("BACKGROUND_CLEANUP_BATCH_SIZE", 500)
REACT_VERSION = "18.3.1"
REACT_CDN_URL = f"https://cdn.jsdelivr.net/npm/react@{REACT_VERSION}/umd/react.production.min.js"
REACT_DOM_CDN_URL = (
    f"https://cdn.jsdelivr.net/npm/react-dom@{REACT_VERSION}/umd/react-dom.production.min.js"
)
