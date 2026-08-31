# ERD FINAL CHECKLIST

- 프로젝트: `ax2-integrated-platform`
- 담당: P3 김종복
- 기준일: 2026-08-31
- 기준 ERD: 2026-08-31 현재 PostgreSQL ERD
- 기준 객체 수: 69개
- 목적: 현재 생성 완료된 69개 DB 객체를 기준으로 `유지 / 통합 / 분리 / 폐기 / 신규추가` 관점에서 최종 ERD를 점검하고 후속 DB Migration 의사결정 사항을 정리한다.

> **판정 원칙**
>
> 1. 현재 DB에 존재하고 통합 TO-BE에서 역할이 명확한 객체는 `유지`를 기본으로 한다.
> 2. 동일한 업무 개념을 중복 저장하는 객체는 `통합` 후보로 표시한다.
> 3. 목적이 서로 다른 원천 데이터는 `분리`하여 유지한다.
> 4. 기존 호환성/조회 목적의 중복 View 등은 신규 View로 대체 후 `폐기` 후보로 관리한다.
> 5. 현재 69개 객체에 없는 기능적 요구사항은 `신규추가`로 관리하되, 즉시 생성하지 않고 업무 확정 후 Migration 대상으로 이동한다.

## 1. 전체 판정 요약

| 구분 | 대상 수 | 핵심 판단 |
|---|---:|---|
| 유지 | 64 | 현재 구조를 TO-BE 기준으로 계속 사용 |
| 통합 | 0 | 즉시 통합할 테이블은 없음. 일부는 논리적 통합 검토 대상 |
| 분리 | 3 | `attendances`, `attendance_record`, `face_recognition_log`는 업무 목적상 분리 |
| 폐기 | 1 | `ax_user_team_login_view`는 `user_round_team_view`로 대체 검토 |
| 신규추가 | 4 | `student` 분리 여부, `inventory_transactions`, PRD template FK 확정, 근태 이벤트 이력 등 |
| **합계(현재 69개)** | **69** | 현재 ERD 객체 기준 |

> `신규추가`는 현재 69개에 없는 향후 후보이므로 현재 69개 합계에는 포함하지 않는다. 분류 수는 최종 의사결정 과정에서 조정될 수 있다.

## 2. 69개 객체 최종 분류

### 2.1 유지

현재 DB와 통합 TO-BE ERD에서 역할이 명확하고 유지하는 것이 적절한 객체이다.

| No | 객체 | 영역 | 판정 | 비고 |
|---:|---|---|---|---|
| 1 | `account_emailaddress` | 인증 | 유지 | Allauth 이메일 계정 |
| 2 | `account_emailconfirmation` | 인증 | 유지 | 이메일 인증 |
| 3 | `accounts_auththrottlebucket` | 인증보안 | 유지 | 인증 요청 제한 |
| 4 | `accounts_emailverificationcode` | 인증 | 유지 | 이메일 인증 코드 |
| 5 | `accounts_scheduledemail` | 알림/메일 | 유지 | 예약 메일 |
| 6 | `accounts_user` | Core | 유지 | 사용자 Master |
| 7 | `accounts_user_groups` | 권한 | 유지 | Django 그룹 연결 |
| 8 | `accounts_user_user_permissions` | 권한 | 유지 | 사용자 권한 연결 |
| 9 | `accounts_whitelistemail` | 인증 | 유지 | 허용 이메일 관리 |
| 10 | `ai_evaluation` | AI 평가 | 유지 | 제출물 AI 평가 |
| 11 | `assignment` | 과제 | 유지 | 과제 정의 |
| 12 | `attendance_record` | 실제 근태 | 유지 | 실제 근태 기록 |
| 13 | `attendances` | 학습 출석 | 유지 | 게임/학습 출석 |
| 14 | `audit_auditevent` | 감사 | 유지 | 감사 이벤트 |
| 15 | `auth_group` | 권한 | 유지 | Django 그룹 |
| 16 | `auth_group_permissions` | 권한 | 유지 | 그룹 권한 |
| 17 | `auth_permission` | 권한 | 유지 | Django Permission |
| 18 | `axes_accessattempt` | 보안 | 유지 | 로그인 접근 시도 |
| 19 | `axes_accessattemptexpiration` | 보안 | 유지 | 접근 제한 만료 |
| 20 | `axes_accessfailurelog` | 보안 | 유지 | 로그인 실패 로그 |
| 21 | `axes_accesslog` | 보안 | 유지 | 접근 로그 |
| 22 | `cg_users` | 게임/학습 | 유지 | `accounts_user` 1:1 확장 |
| 23 | `concepts` | 학습 | 유지 | 학습 개념 |
| 24 | `django_admin_log` | Django | 유지 | 관리자 변경 로그 |
| 25 | `django_content_type` | Django | 유지 | ContentType |
| 26 | `django_migrations` | Django | 유지 | Migration 이력 |
| 27 | `django_session` | Django | 유지 | 세션 |
| 28 | `django_site` | Django/Allauth | 유지 | Site |
| 29 | `evaluation` | 평가 | 유지 | 제출물 평가 |
| 30 | `face_image` | 얼굴인식 | 유지 | 얼굴 이미지 |
| 31 | `face_profile` | 얼굴인식 | 유지 | 사용자 얼굴 프로필 |
| 32 | `face_recognition_log` | 얼굴인식 | 유지 | 얼굴인식 원천 로그 |
| 33 | `house` | 게임 | 유지 | 사용자 하우스 |
| 34 | `inventories` | 게임 | 유지 | 사용자별 아이템 보유량 |
| 35 | `items` | 게임 | 유지 | 아이템 Master |
| 36 | `notices_notice` | 공지 | 유지 | 공지사항 |
| 37 | `notifications_notification` | 알림 | 유지 | 사용자 알림 |
| 38 | `placed_objects` | 게임 | 유지 | 하우스 배치 객체 |
| 39 | `prds` | PRD | 유지 | 프로젝트 요구사항 |
| 40 | `results_calculationrun` | 평가결과 | 유지 | 계산 실행 단위 |
| 41 | `results_evaluationresult` | 평가결과 | 유지 | 최종 평가 결과 |
| 42 | `results_scoreinput` | 통합채점 | 유지 | 개인/팀 점수 입력 |
| 43 | `results_tutornote` | 평가 | 유지 | 튜터 메모 |
| 44 | `reviews_reviewanswer` | 리뷰 | 유지 | 리뷰 문항 답변 |
| 45 | `reviews_reviewfinalsubmission` | 리뷰 | 유지 | 최종 리뷰 제출 |
| 46 | `reviews_reviewsubmission` | 리뷰 | 유지 | 리뷰 제출 |
| 47 | `reviews_tutorreview` | 리뷰 | 유지 | 튜터 리뷰 |
| 48 | `reviews_tutorreviewanswer` | 리뷰 | 유지 | 튜터 리뷰 답변 |
| 49 | `reviews_tutorteamreview` | 리뷰 | 유지 | 튜터 팀 리뷰 |
| 50 | `reviews_tutorteamreviewanswer` | 리뷰 | 유지 | 튜터 팀 리뷰 답변 |
| 51 | `room_participants` | 게임/방 | 유지 | 방 참가자 |
| 52 | `rooms` | 게임/방 | 유지 | 방/세션 |
| 53 | `rounds_evaluationround` | Core | 유지 | 평가 Round |
| 54 | `rounds_questiontemplate` | 평가문항 | 유지 | 질문 Template |
| 55 | `rounds_roundparticipant` | Core | 유지 | Round 참가자 |
| 56 | `rounds_templatequestion` | 평가문항 | 유지 | Template 문항 |
| 57 | `socialaccount_socialaccount` | 소셜인증 | 유지 | 소셜 계정 |
| 58 | `socialaccount_socialapp` | 소셜인증 | 유지 | 소셜 앱 |
| 59 | `socialaccount_socialapp_sites` | 소셜인증 | 유지 | 소셜 앱-Site |
| 60 | `socialaccount_socialtoken` | 소셜인증 | 유지 | 소셜 토큰 |
| 61 | `submission` | 제출 | 유지 | 개인/팀 제출 |
| 62 | `submission_file` | 제출 | 유지 | 제출 파일 |
| 63 | `task_attempts` | 학습 | 유지 | 과제 시도 |
| 64 | `tasks` | 학습 | 유지 | 학습 과제 |
| 65 | `teams_team` | Core | 유지 | 팀 |
| 66 | `teams_teammembership` | Core | 유지 | 팀-참가자 관계 |
| 67 | `user_proficiency` | 학습 | 유지 | 사용자 숙련도 |
| 68 | `user_round_team_view` | 조회 View | 유지 | 최종 사용자-Round-Team 조회 View |

> 현재 ERD의 69번째 객체는 `ax_user_team_login_view`이며 아래 폐기 후보로 분류한다. 따라서 유지 표는 실제 69개 중 68개 객체를 나열한다.

## 3. 통합

현재 69개 객체 중 **즉시 DROP 후 하나로 합칠 테이블은 없음**으로 판단한다.

| 후보 | 검토 내용 | 최종 판단 |
|---|---|---|
| `accounts_user` + `cg_users` | 사용자 Master와 게임 확장 프로필 | 통합하지 않음. `cg_users`를 1:1 확장으로 유지 |
| `attendance_record` + `attendances` | 출결이라는 명칭은 유사 | 통합하지 않음. 실제 근태와 학습 출석의 업무 목적이 다름 |
| `face_profile` + `face_image` | 얼굴 프로필과 이미지 | 통합하지 않음 |
| `submission` + `submission_file` | 제출 메타정보와 첨부파일 | 통합하지 않음 |
| `results_evaluationresult` + `results_scoreinput` | 입력 점수와 최종 결과 | 통합하지 않음 |
| `reviews_*` | 리뷰 유형별 구조 | 통합하지 않음 |

## 4. 분리

### 4.1 출석 / 근태 / 얼굴인식

| 객체 | 업무 목적 | 기준 Key | 판정 |
|---|---|---|---|
| `attendances` | 학습/게임 출석 및 streak | `accounts_user.id` | 분리 |
| `attendance_record` | 실제 근태 기록 | `accounts_user.id` | 분리 |
| `face_recognition_log` | 얼굴인식 시도/결과 원천 로그 | `accounts_user.id` | 분리 |

핵심 원칙은 다음과 같다.

```text
accounts_user.id
   ├── attendances              # 학습 출석
   ├── attendance_record        # 실제 근태
   └── face_recognition_log      # 얼굴인식 원천 이벤트
```

학습 출석과 실제 근태는 이름이 비슷하더라도 업무 목적과 데이터 생명주기가 다르므로 하나의 Attendance 테이블로 통합하지 않는다.

## 5. 폐기

### `ax_user_team_login_view`

| 객체 | 상태 | 대체 객체 | 판정 |
|---|---|---|---|
| `ax_user_team_login_view` | 기존 사용자/팀 조회 View | `user_round_team_view` | 폐기 후보 |
| `user_round_team_view` | 신규 통합 조회 View | - | 유지 |

**폐기 조건**

1. 기존 View의 SQL 및 반환 컬럼 확인
2. 신규 `user_round_team_view` 결과와 비교
3. Django/API/화면의 기존 View 참조 검색
4. 신규 View로 사용처 전환
5. 전환 검증 후 기존 View DROP

즉시 DROP하지 않고 애플리케이션 참조 여부를 먼저 확인한다.

## 6. 신규추가 후보

현재 69개 객체에는 없지만 향후 요구사항에 따라 추가 검토할 항목이다.

| No | 신규 후보 | 필요성 | 우선순위 | 결정 |
|---:|---|---|---|---|
| 1 | `student` | 학생을 `accounts_user`와 별도 도메인 객체로 관리해야 하는 경우 | 중 | 보류 |
| 2 | `inventory_transactions` | 아이템 획득/사용/소비/조정 이력 | 중 | 추가 검토 |
| 3 | PRD Template FK | `prds.template_id`의 참조 대상 확정 | 높음 | 관계 확정 필요 |
| 4 | 근태 이벤트 이력 | 수기 수정/출퇴근 이벤트 원천 이력 보존 | 중 | 요구사항 확인 |

### 6.1 Student

현재 통합 기준은 `accounts_user.id`를 사용자/학생 공통 Master ID로 사용하고, 특정 평가 Round 참가 이력은 `rounds_roundparticipant`로 관리하는 것이다. 따라서 별도 `student` 테이블은 즉시 추가하지 않는다.

### 6.2 inventory_transactions

`inventories`는 사용자별 아이템의 현재 보유량을 관리한다. 향후 획득/구매/보상/사용/소비/회수/관리자 조정 이력이 필요하면 `inventory_transactions`를 추가한다.

### 6.3 prds.template_id

`prds.template_id`는 참조 대상이 확정되기 전까지 FK 생성을 보류한다. 후보가 `rounds_questiontemplate.id`라면 업무 의미와 컬럼 타입을 검증한 뒤 FK를 확정한다.

## 7. 핵심 무결성 체크

### User Master

```text
accounts_user.id = 공통 User Master ID
cg_users.id       = accounts_user의 게임 확장 영역
```

### Round / Team / Participant

```text
accounts_user
      ↓
rounds_roundparticipant
      ↓
teams_teammembership
      ↓
teams_team
```

### 개인/팀 점수

`results_scoreinput`은 개인 또는 팀 중 하나만 대상으로 한다.

```text
개인: participant_id IS NOT NULL AND team_id IS NULL
팀:   participant_id IS NULL AND team_id IS NOT NULL
```

### 제출 대상

`submission`은 개인 제출과 팀 제출을 구분하며 두 대상을 동시에 지정하지 않는다.

## 8. 최종 체크리스트

- [x] `accounts_user` Core User 확정
- [x] `rounds_evaluationround` Core Round 확정
- [x] `rounds_roundparticipant` Round 참가 이력 확정
- [x] `teams_team` / `teams_teammembership` Core Team 관계 확인
- [x] 1조 학습/게임 영역 반영
- [x] 2조 LMS/과제/제출/평가 영역 반영
- [x] 3조 PRD/AI 영역 반영
- [x] 4조 근태/얼굴인식 영역 반영
- [x] 학습 출석과 실제 근태 분리
- [x] 얼굴인식 원천 로그 분리
- [x] `inventories` 반영
- [x] `user_round_team_view` 반영
- [ ] `ax_user_team_login_view` 참조 코드 검색
- [ ] 신규 View와 기존 View 결과 비교
- [ ] `ax_user_team_login_view` 폐기 승인
- [ ] `prds.template_id` FK 대상 확정
- [ ] `student` 별도 테이블 필요 여부 확정
- [ ] `inventory_transactions` 필요 여부 확정
- [ ] 근태 이벤트 이력 필요 여부 확정
- [ ] Migration 전/후 데이터 정합성 검증

## 9. 최종 결론

현재 생성 완료된 69개 ERD 객체는 **User–Round–Team을 Core로 하고, 학습/게임, LMS/과제/제출, PRD/AI, 실제 근태/얼굴인식, 평가/결과 영역을 하나의 PostgreSQL DB 안에서 연결하는 통합 구조**로 정리한다.

- **유지:** 기존 핵심 및 도메인 테이블 중심으로 유지
- **통합:** 현재 즉시 통합할 테이블 없음
- **분리:** 학습 출석 / 실제 근태 / 얼굴인식 원천 로그의 업무 경계를 유지
- **폐기:** `ax_user_team_login_view`는 `user_round_team_view` 대체 검증 후 폐기
- **신규추가:** `student`, `inventory_transactions`, PRD Template FK, 근태 이벤트 이력은 요구사항 확정 후 Migration 대상으로 검토

**ERD 최종 상태: 조건부 완료**

- Core 구조: 완료
- 조별 Domain 반영: 완료
- FK 관계: 확인 완료
- 출결/근태 분리: 완료
- 인벤토리 반영: 완료
- 기존/신규 View 정리: 검증 필요
- PRD Template FK: 결정 필요
- Student 분리 여부: 결정 필요
- Inventory 거래 이력: 결정 필요
