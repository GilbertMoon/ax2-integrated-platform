# 이슈 #34 진행 상황 코멘트 — 2026-09-01

> GitHub 이슈 [P2][심우섭][2026-08-31] 로그인/회원/학생/권한/근태 실제 구현 시작 (#34) 에
> 붙일 진행 코멘트 초안. 아래 내용을 그대로 이슈 코멘트로 붙여넣으면 됩니다.
> (이 파일 자체는 로컬 산출물 기록용 — 커밋/푸시는 별도)

---

## 2026-09-01 진행 (P2 심우섭)

근태 모듈을 실제 코드로 구현했습니다. 오늘은 **작업 3(권한)**, **작업 4(근태 테이블·화면)** 를 진행했습니다.

### 오늘 완료 → 체크한 항목

- [x] **작업 3 · 근태 조회/수정 API에 튜터 권한 제한 적용**
  - `attendance/views.py`의 `attendance_board`(화면), `user_attendance_view`, `update_attendance_view` 모두
    `accounts/permissions.py`의 `is_operations_user`로 제한 (튜터 또는 관리자, `is_active`·`approval_status` 포함 검증)
- [x] **작업 3 · 튜터/학생 계정 각각으로 접근 테스트 (튜터 허용, 학생 거부)**
  - Django 테스트 클라이언트 확인 결과:
    - 튜터 `GET /attendance/?date=2026-09-01` → 200, 수강생 표 정상
    - 학생 `GET /attendance/` → 403
    - 학생 `GET /attendance/me/` → 200 (본인 기록만)
- [x] **작업 4 · 근태 기록 테이블(AttendanceRecord) 설계 및 마이그레이션 (accounts_user.id 참조)**
  - `attendance/models.py` `AttendanceRecord`: `user`(FK→accounts_user) + `date` + `status`(present/late/absent)
    + `checked_by_face_recognition` + `memo`, `UniqueConstraint(user, date)`
  - `attendance/migrations/0001_initial.py` 생성, `manage.py check` 0 issues
  - ⚠️ 로컬 sqlite에만 적용됨. **Postgres/배포 서버 반영은 별도 이슈** (`issue-attendance-postgres-migrate-2026-09-01.md`)
- [x] **작업 4 · 근태 기록 화면에서 이름으로 표시되는지 확인 (id 노출 없음)**
  - 화면·API 모두 `first_name`(없으면 email)으로 표시, 숫자 id는 사용자에게 노출 안 됨 (`User.__str__`와 동일 패턴)
- [x] **DONE 기준 · 근태 조회/수정 권한이 튜터 계정에서만 정상 동작**

### 참고 — role 기반 권한 함수

- 새 권한 클래스를 만들지 않고 기존 `is_operations_user` / `is_student_user`(함수) 재사용.
- 이유: 두 함수가 `is_active`·`approval_status`까지 이미 검증하고 있어 더 정확함.
  근태 앱은 이걸 import만 해서 사용.

### 산출물

- 코드(미커밋, `feature/p2_wooseob`):
  - 신규 `attendance/`, `templates/attendance/board.html`
  - 수정 `config/settings.py`, `config/urls.py`, `templates/includes/sidebar.html`
- 산출물 문서: `docs/deliverables/P2_심우섭/2026-09-01_근태_UI_및_앱_통합.md`
- 후속 이슈: `docs/deliverables/P2_심우섭/issue-attendance-postgres-migrate-2026-09-01.md`

### 아직 미완 (내일 이후)

- 작업 1 — AUTH_USER_MODEL/DB 연결 통일, 각 조 `request.user` 테스트
- 작업 2 — 팀 정보 API(`/api/teams/me/`, `/api/teams/user/{id}/`) 미착수
- 작업 4 — 얼굴인식 저장 방식 결정 → 매칭 로직 (참고란대로 결정 전까지 보류)
- 커밋·PR(`feature/p2_wooseob` → `develop`), Postgres 마이그레이션, `attendance/tests.py`, Cross Check

→ 다음 작업은 `[P2][심우섭][2026-09-02]` 이슈에서 이어감.
