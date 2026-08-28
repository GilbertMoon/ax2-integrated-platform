# TO-BE ERD 초안 범위 정의

- 작성일: 2026-08-28
- 상태: **초안 (오늘은 전체 완성본이 아님)**
- 목적: 1·2·3조 고유 Domain과 4조 Core의 경계를 정하고, 각 Domain이 어떤 Core FK를 참조하는지 합의하기 위한 기준 문서

## 1. 전체 구조

```text
                         ┌──────────────────────────────┐
                         │       4조 CORE 후보          │
                         │                              │
                         │ accounts_user                │
                         │ rounds_roundparticipant      │
                         │ teams_team                   │
                         │ rounds_evaluationround       │
                         │ reviews_* / results_*        │
                         └──────────────┬───────────────┘
                                        │
                 ┌──────────────────────┼──────────────────────┐
                 │                      │                      │
                 ▼                      ▼                      ▼
        ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
        │  1조 학습/게임 │     │ 2조 LMS/과제   │     │ 3조 PRD/AI     │
        │                │     │                │     │                │
        │ TASKS          │     │ LECTURE        │     │ PRDs           │
        │ ATTEMPTS       │     │ LESSON         │     │ PRD_SECTIONS   │
        │ ROOMS          │     │ ASSIGNMENT     │     │ COMMENTS       │
        │ RANKING        │     │ SUBMISSION     │     │ BRAINSTORM     │
        │ ITEMS/CATS     │     │ EVALUATION     │     │ AI_*           │
        └────────────────┘     └────────────────┘     └────────────────┘
                 │                      │                      │
                 └──────────────────────┼──────────────────────┘
                                        ▼
                         ┌──────────────────────────────┐
                         │   4조 근태 / 얼굴인식 영역   │
                         │                              │
                         │ Student FK                   │
                         │ 출석/체크인                   │
                         │ 이미지/촬영                   │
                         │ 예측 학생 / confidence       │
                         │ 성공/실패 / 관리자 검증       │
                         └──────────────────────────────┘
```

---

## 2. Core 후보와 공통 참조 원칙

| Core 후보 | 역할 | 타 조 참조 방식 |
|---|---|---|
| `accounts_user` | 회원/인증/권한 기준 | 모든 조의 사용자 FK 기준 |
| `rounds_roundparticipant` | 특정 평가 회차의 학생 식별 | 학습/과제/PRD/근태의 Student 참조 기준으로 검토 |
| `teams_team` | 회차별 팀 기준 | 1·2·3조의 팀 관련 데이터가 필요할 때 참조 |
| `rounds_evaluationround` | 평가 회차 | PRD/평가/결과가 회차와 연결될 경우 참조 |
| `reviews_*` | 공식 평가 | Core 공식 평가 Domain |
| `results_*` | 최종 계산/결과 | 외부 조 확정 점수를 받아 최종 결과 산출 |

### 공통 원칙

- User의 기준 PK는 `accounts_user.id`로 통일한다.
- 평가 회차에 소속된 학생을 특정해야 하는 데이터는 가능한 한 `rounds_roundparticipant.id`를 FK로 사용한다.
- 팀 데이터는 `teams_team.id`를 기준으로 한다.
- 타 조의 고유 Domain을 Core 테이블에 억지로 흡수하지 않는다.
- 2조/3조에서 확정된 점수는 `results_scoreinput`으로 전달하고 Core가 최종 계산한다.

---

## 3. 1조 고유 데이터 → Core FK 초안

| 1조 데이터 | 업무 목적 | Core FK 후보 | 관계 |
|---|---|---|---|
| `CG_USERS` | 게임용 사용자 확장 프로필 | `accounts_user.id` | 1:1 |
| `ATTENDANCES` | 학습 출석/streak | `accounts_user.id` 또는 `rounds_roundparticipant.id` | **별도 Domain** |
| `TASKS` | 학습 문제 | 없음(자체 Domain) | 독립 |
| `USER_PROFICIENCY` | 학생별 개념 숙련도 | `accounts_user.id` + `CONCEPTS.id` | 사용자 참조 |
| `TASK_ATTEMPTS` | 문제 풀이 시도 | `accounts_user.id` + `TASKS.id` | 사용자/문제 |
| `ROOMS` | 게임 방 | `accounts_user.id` | host FK |
| `ROOM_PARTICIPANTS` | 게임 참가자 | `accounts_user.id` + `teams_team.id`(선택) | 사용자/팀 |
| `ROOM_TASKS` | 방-문제 연결 | `ROOMS.id` + `TASKS.id` | 자체 관계 |
| `RANKING_GROUPS` | 게임 랭킹 그룹 | `accounts_user.id` | owner FK |
| `RANKING_PARTICIPANTS` | 게임 랭킹 참가자 | `accounts_user.id` | 사용자 FK |
| `RANK_CHALLENGES` | 랭킹 도전 | `accounts_user.id` | 사용자 FK |
| `INVENTORIES` | 사용자 아이템 | `accounts_user.id` | 사용자 FK |
| `USER_CATS` | 사용자 고양이 | `accounts_user.id` | 사용자 FK |

> **주의:** `ATTENDANCES`는 4조 근태 테이블과 통합하지 않는다. 1조는 학습 서비스의 출석/streak라는 별도 업무 목적이다.

---

## 4. 2조 고유 데이터 → Core FK 초안

| 2조 데이터 | 업무 목적 | Core FK 후보 | 관계 |
|---|---|---|---|
| `LECTURE` | 강의 | `rounds_evaluationround.id` (필요 시) | 선택 |
| `LESSON` | 강의 차시 | `LECTURE.id` | 자체 관계 |
| `LESSON_MATERIAL` | 교안/자료 | `LESSON.id` | 자체 관계 |
| `ASSIGNMENT` | 튜터가 부여하는 과제 | `accounts_user.id` (`created_by`) | 튜터 FK |
| `SUBMISSION` | 과제 제출 | `accounts_user.id` + `teams_team.id`(팀 과제 시) | 학생/팀 FK |
| `SUBMISSION_FILE` | 제출 파일 | `SUBMISSION.id` | 자체 관계 |
| `AI_EVALUATION` | 과제 AI 1차 평가 | `SUBMISSION.id` | 자체 관계 |
| `EVALUATION` | 과제 튜터 공식 평가 | `SUBMISSION.id` | 자체 관계 |
| `TODO` | 개인 할 일 | `accounts_user.id` | 학생 FK |

### 2조 점수 연결

```text
SUBMISSION
    │
    └── EVALUATION.score (확정)
              │
              │ PUSH / Snapshot
              ▼
       results_scoreinput
              │
              ▼
       results_calculationrun
              │
              ▼
       results_evaluationresult
```

`EVALUATION`을 4조 `reviews_*`와 통합하지 않는다. 2조 평가의 평가 대상은 **과제 제출물**, 4조 평가의 대상은 **평가 회차의 공식 팀/개인 평가**이기 때문이다.

---

## 5. 3조 고유 데이터 → Core FK 초안

| 3조 데이터 | 업무 목적 | Core FK 후보 | 관계 |
|---|---|---|---|
| `Templates` | PRD 템플릿 | 없음 | 독립 |
| `Template_Sections` | 템플릿 섹션 | `Templates.id` | 자체 관계 |
| `Template_Questions` | 템플릿 질문 | `Template_Sections.id` | 자체 관계 |
| `PRDs` | 제품 요구사항 문서 | `accounts_user.id` + `rounds_roundparticipant.id` + `teams_team.id`(선택) | 소유자/회차/팀 |
| `PRD_Permissions` | PRD 접근 권한 | `accounts_user.id` | 사용자 FK |
| `PRD_Sections` | PRD 섹션 | `PRDs.id` | 자체 관계 |
| `PRD_Questions` | PRD 질문 | `PRD_Sections.id` | 자체 관계 |
| `PRD_Comments` | PRD 의견 | `accounts_user.id` + `PRDs.id`/`PRD_Sections.id` | 작성자/대상 |
| `Brainstorm_Boards` | 아이디어 보드 | `PRDs.id` | PRD FK |
| `Brainstorm_Categories` | 보드 분류 | `Brainstorm_Boards.id` | 자체 관계 |
| `Post_its` | 아이디어 포스트잇 | `accounts_user.id` + `Brainstorm_Boards.id` | 작성자/보드 |
| `AI_Usage_Logs` | AI API 사용 기록 | `accounts_user.id` + `PRDs.id`(선택) | 사용자/PRD |
| `AI_Prompts` | AI 프롬프트 버전 | 없음 | 독립 |
| `PRD_Member_Evaluations` | PRD 활동 평가 | `accounts_user.id` + `PRDs.id` | 평가 대상/PRD |
| `PRD_Edit_Histories` | PRD 수정 이력 | `PRD_Sections.id` | 자체 관계 |
| `AI_Chat_Histories` | PRD AI 대화 | `accounts_user.id` + `PRDs.id` + `PRD_Sections.id`(선택) | 사용자/PRD |

### 3조 점수 연결

```text
PRD_Member_Evaluations.total_score
              │
              │ PUSH / Snapshot
              ▼
       results_scoreinput
              │
              ▼
       results_calculationrun
              │
              ▼
       results_evaluationresult
```

---

## 6. 4조 신규 근태 / 얼굴인식 영역

이번 초안에서는 **테이블을 확정하지 않고 Domain과 저장 데이터 후보만 정의**한다.

### 데이터 후보

| 데이터 | 저장 필요성 | 비고 |
|---|---|---|
| Student FK | 필수 | Core 학생 식별자 참조 |
| 출석일 | 필수 | 날짜 단위 출석 판정 |
| 체크인 시각 | 필수 | 실제 인식/출석 시각 |
| 근태 상태 | 필수 | 예: 정상/지각/결석/오인식 등. 최종 enum은 추후 확정 |
| 이미지 저장 경로 | 권장 | DB에 이미지 binary를 직접 저장하지 않고 object/file storage 경로 저장 검토 |
| 촬영 시각 | 필수 | 카메라 캡처 시각 |
| 얼굴인식 예측 학생 | 필수 | 모델이 예측한 학생 식별자 |
| confidence | 필수 | 모델 예측 신뢰도 |
| 인식 성공/실패 | 필수 | inference 결과 |
| 실제 정답 학생 | 검토 | 모델 평가/오인식 분석에 필요 |
| 관리자 검증값 | 검토 | 사후 수정/검증 결과 저장 필요 |
| 검증 시각 | 검토 | 관리자 검증 이력 |
| 검증자 | 검토 | `accounts_user.id` 후보 |

### 핵심 관계 초안

```text
accounts_user
     │
     └── rounds_roundparticipant (Student)
                  │
                  ▼
          [근태/얼굴인식 영역]
                  │
          ┌───────┴────────┐
          ▼                ▼
      출석/근태        얼굴인식 이벤트
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       이미지 경로    예측 학생       confidence
                         │
                         ▼
                    성공/실패
                         │
                         ▼
              실제 정답 / 관리자 검증
```

### 관리자 검증 가능성에 대한 설계 방향

**가능하도록 설계한다.** 모델 예측값과 실제 확정값을 동일 컬럼에 덮어쓰지 않고 구분할 수 있어야 한다.

- `predicted_student_id`: 모델 예측값
- `confidence`: 모델 confidence
- `recognition_status`: 성공/실패
- `verified_student_id`: 사후 검증된 실제 학생
- `verified_by`: 검증 관리자
- `verified_at`: 검증 시각

이렇게 하면 최초 모델 결과를 보존하면서 나중에 관리자 검증값을 추가할 수 있고, 오인식률/모델 성능 분석에도 활용할 수 있다.

---

## 7. 현재 초안의 FK 방향 요약

```text
[4조 Core]
accounts_user
   │
   ├── rounds_roundparticipant (Student)
   │       │
   │       └── teams_team
   │
   ├──────────────────────────────────────────┐
   │                                          │
   ▼                                          ▼
[1조]                                      [2조]
CG_USERS ──► accounts_user              ASSIGNMENT ──► accounts_user
ATTENDANCES ──► Student/User             SUBMISSION ──► User/Team
TASK_ATTEMPTS ──► User                  TODO ──► User
ROOMS ──► User                           EVALUATION ──► Submission
RANKING ──► User
INVENTORY ──► User
USER_CATS ──► User
   │                                          │
   └──────────────────┐      ┌───────────────┘
                      ▼      ▼
                   results_scoreinput
                          ▲
                          │
[3조]                     │
PRDs ──► User/Student/Team│
PRD_* ──► PRD             │
PRD_Member_Evaluations ───┘

[4조 신규 근태/얼굴인식]
Student ──► Attendance/Recognition Event
Recognition Event ──► Image / Prediction / Confidence / Status
Recognition Event ──► Verified Student / Admin / Verified At (추후)
```

## 8. 초안에서 아직 확정하지 않는 항목

1. `ATTENDANCES`의 최종 FK가 `accounts_user`인지 `rounds_roundparticipant`인지
2. 근태의 정확한 상태값(enum)
3. 얼굴 이미지의 보관 위치와 보존 기간
4. 얼굴인식 이벤트와 실제 출석 레코드의 1:N/1:1 관계
5. `verified_student_id`가 반드시 Student FK인지 여부
6. 2조 `LECTURE`의 회차 FK 필요 여부
7. 3조 `PRDs`의 Student FK를 직접 저장할지 User+Round 조합으로 유도할지
8. Core `results_scoreinput`의 실제 컬럼명 및 제약조건

> 위 항목은 오늘의 작업 범위를 넘어서는 상세 설계이므로 **TO-BE ERD 초안 단계에서는 보류**한다.
