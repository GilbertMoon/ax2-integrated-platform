"""브라우저 수동 QA 전용 설정.

config.lms_test_settings(자동 테스트 전용, :memory: DB)를 그대로 상속하되
DB만 프로젝트 하위 영속 SQLite 파일로 바꿔서, runserver를 껐다 켜도 데이터가
남아 있도록 한다. DB 라우터(lms.db_router.LmsDatabaseRouter)와
assignment_lms alias 구조는 그대로 유지한다.

운영(config.settings)에는 절대 사용하지 않는다.

사용법 (두 DB 파일에 각각 migrate 해야 실제 테이블이 생긴다 — Django는
--database 로 지정한 alias 하나에만 실물 테이블을 만든다):

    python manage.py migrate --settings=config.lms_manual_qa_settings
    python manage.py migrate --database=assignment_lms --settings=config.lms_manual_qa_settings
    python manage.py runserver --settings=config.lms_manual_qa_settings
"""

from config.lms_test_settings import *  # noqa: F403 - inherit QA runner/offline overrides
from config.lms_test_settings import BASE_DIR

WORK_DIR = BASE_DIR / "work"
WORK_DIR.mkdir(parents=True, exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": WORK_DIR / "manual_qa.sqlite3",
    },
    "assignment_lms": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": WORK_DIR / "manual_qa_lms.sqlite3",
    },
}
