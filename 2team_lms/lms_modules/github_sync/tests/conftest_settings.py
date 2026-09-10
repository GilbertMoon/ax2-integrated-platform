"""테스트에서 github_sync 를 '설정된' 상태로 만드는 공용 override 값."""

from cryptography.fernet import Fernet


ENABLED_SETTINGS = dict(
    GITHUB_OAUTH_CLIENT_ID="test-client-id",
    GITHUB_OAUTH_CLIENT_SECRET="test-secret",
    GITHUB_TOKEN_ENC_KEY=Fernet.generate_key().decode(),
    GITHUB_SUBMISSION_REPO_NAME="lms-assignments",
    DEV_SKIP_AUTH=False,
)
