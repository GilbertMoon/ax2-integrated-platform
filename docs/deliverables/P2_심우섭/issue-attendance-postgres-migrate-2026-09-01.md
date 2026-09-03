# [근태] attendance 앱 마이그레이션을 원본 DB(Postgres)와 배포 서버에 반영 필요

- **작성자:** tladntjq1-lgtm
- **상태:** Open
- **담당자(Assignee):** P3 김종복 (DB) / GilbertMoon (배포 서버)
- **작성일:** 2026-09-01

## 문제 상황

근태 모듈(`attendance` 앱)을 프로젝트에 통합하고 모델·API·운영 화면까지 구현했으나,
개발 중 `.env`의 `POSTGRES_*` 설정이 주석 처리되어 있어 마이그레이션이
**로컬 sqlite(`db.sqlite3`)에만 적용**된 상태입니다.

- 새 테이블: `attendance_attendancerecord`
- 마이그레이션 파일: `attendance/migrations/0001_initial.py` (DB 종류와 무관, 이미 커밋 대상)
- 원본 개발 DB(Postgres `ax_evaluation`)와 배포 서버에는 아직 이 테이블이 없음
  → 해당 환경에서 `/attendance/` 접근 시 `ProgrammingError: relation "attendance_attendancerecord" does not exist` 발생

## 확인 방법

```bash
# 현재 접속 DB 확인
python -c "import os,django;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings');django.setup();from django.db import connection;print(connection.settings_dict['NAME'])"

# 적용 여부 확인
python manage.py showmigrations attendance
#  [ ] 0001_initial   ← 미적용
#  [X] 0001_initial   ← 적용됨
```

## 요청 사항

### 1. 원본 개발 DB(Postgres)에 반영 — P3

1. `.env`에서 `POSTGRES_*` 5줄 주석 해제 + 실제 비밀번호 입력
2. 접속 DB가 Postgres인지 확인 (`showmigrations`)
3. `python manage.py migrate` 실행 → `attendance.0001_initial` 적용
4. `python manage.py showmigrations attendance` 로 `[X]` 확인
5. 데이터 이관 불필요 — 로컬 sqlite의 근태/`seed_data.py` 데이터는 개발용 픽스처이므로 복사하지 않음

### 2. 배포 서버(Windows 11 Pro)에 반영 — 배포 담당

- 코드 배포 후 `python manage.py migrate` 1회 실행
- MASTER_TODO PHASE 5 "서버 재부팅 후 서비스 기동 확인"에 근태 화면 접근 확인 포함

## 참고

- 코드 변경 범위(커밋 대상):
  - 신규: `attendance/`, `templates/attendance/board.html`
  - 수정: `config/settings.py`, `config/urls.py`, `templates/includes/sidebar.html`
- 관련 산출물: `docs/deliverables/P2_심우섭/2026-09-01_근태_UI_및_앱_통합.md`
- 관련 기준: `docs/deliverables/P2_심우섭/근태_얼굴인식_연결기준_20260827.md`
- 관련 TODO: `docs/01_MASTER_TODO.md` PHASE 4 / PHASE 5

## 진행 상황

| 시각 | 내용 |
|---|---|
| 이슈 생성 | tladntjq1-lgtm이 이슈 작성 |
