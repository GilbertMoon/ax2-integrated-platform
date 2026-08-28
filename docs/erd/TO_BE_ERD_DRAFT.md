# TO-BE ERD 초안 범위 정의

- 작성일: 2026-08-28
- 상태: **P2 협의 반영본**
- 목적: 1·2·3조 고유 Domain과 4조 Core의 경계를 정하고, User / Student / Team 및 각 Domain의 Core 참조 기준을 명확히 한다.

## 1. 핵심 식별자 결정사항

> **P2 협의 반영 기준**
>
> - `accounts_user.id`: 사용자/학생의 **공통 Master ID**
> - `rounds_roundparticipant.id`: 특정 평가 Round의 **참가 이력 ID**
> - 근태/얼굴인식: **`accounts_user.id` 기준**
> - Round/Team 이력이 필요한 기능만 **`rounds_roundparticipant.id` 참조**

따라서 통합 DB에서 `User`와 `Student`가 중복되거나 충돌하는 경우 **`accounts_user`를 최종 공통 Identity 기준으로 사용**한다.

`Student`라는 업무 개념이 필요한 경우에도 기본 사용자 식별은 `accounts_user.id`로 하고, 특정 평가 Round의 참가 이력과 당시 학생 정보를 보존해야 하는 경우에만 `rounds_roundparticipant`를 사용한다.

## 2. 전체 구조

```text
                         ┌──────────────────────────────┐
                         │       4조 CORE               │
                         │                              │
                         │ accounts_user                │
                         │   └─ 공통 Master ID          │
                         │ rounds_roundparticipant      │
                         │   └─ Round 참가 이력         │
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
                         │ accounts_user.id 기준       │
                         │ 출석/체크인                   │
                         │ 이미지/촬영                   │
                         │ 예측 학생 / confidence       │
                         │ 성공/실패 / 관리자 검증       │
                         └──────────────────────────────┘
```

## 3. Core 식별자 및 참조 원칙

| 식별자 | 의미 | 사용 기준 |
|---|---|---|
| `accounts_user.id` | 사용자/학생 공통 Master ID | 모든 조의 사용자 식별 및 공통 사용자 FK 기준 |
| `rounds_roundparticipant.id` | 특정 평가 Round의 참가 이력 | Round/Team 이력이 필요한 기능에서만 참조 |
| `teams_team.id` | 특정 Round의 팀 | 팀 정보가 필요한 기능에서 참조 |
| `rounds_evaluationround.id` | 평가 Round | 평가/결과 등 Round 단위 기능에서 참조 |

### User / Student 정리 원칙

- `accounts_user.id`를 사용자/학생의 **공통 Master ID**로 확정한다.
- 별도 `Student` 기본정보 테이블을 공통 Identity 용도로 중복 운영하지 않는다.
- `rounds_roundparticipant`는 Student의 공통 Master가 아니라 **특정 평가 Round에 참가한 이력**이다.
- Round/Team 이력이 필요하지 않은 기능은 `accounts_user.id`만 참조한다.
- Round 또는 Team 이력이 필요한 기능만 `rounds_roundparticipant.id`를 참조한다.

### 근태 / 얼굴인식 원칙

- 근태 및 얼굴인식 데이터의 사용자 식별 기준은 **`accounts_user.id`**로 한다.
- 근태/얼굴인식에서 단순 사용자 식별을 위해 `rounds_roundparticipant.id`를 직접 사용하지 않는다.
- 특정 Round/Team별 근태 분석이 필요한 경우에만 `rounds_roundparticipant`를 연결한다.

## 4. 1조 고유 데이터 → Core FK 초안

| 1조 데이터 | 업무 목적 | Core FK 기준 | 관계 |
|---|---|---|---|
| `CG_USERS` | 게임용 사용자 확장 프로필 | `accounts_user.id` | 1:1 |
| `ATTENDANCES` | 학습 출석/streak | `accounts_user.id` | 별도 Domain |
| `TASKS` | 학습 문제 | 없음 | 독립 |
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

> **주의:** `ATTENDANCES`는 4조 실제 근태 테이블과 통합하지 않는다. 1조는 학습 서비스의 출석/streak라는 별도 업무 목적이다.

## 5. 2조 고유 데이터 → Core FK 초안

| 2조 데이터 | 업무 목적 | Core FK 기준 | 관계 |
|---|---|---|---|
| `LECTURE` | 강의 | `rounds_evaluationround.id` (필요 시) | 선택 |
| `LESSON` | 강의 차시 | `LECTURE.id` | 자체 관계 |
| `LESSON_MATERIAL` | 교안/자료 | `LESSON.id` | 자체 관계 |
| `ASSIGNMENT` | 튜터가 부여하는 과제 | `accounts_user.id` (`created_by`) | 튜터 FK |
| `SUBMISSION` | 과제 제출 | `accounts_user.id` + `teams_team.id`(팀 과제 시) | 학생/팀 FK |
| `SUBMISSION_FILE` | 제출 파일 | `SUBMISSION.id` | 자체 관계 |
| `AI_EVALUATION` | 과제 AI 1차 평가 | `SUBMISSION.id` | 자체 관계 |
| `EVALUATION` | 과제 튜터 공식 평가 | `SUBMISSION.id` | 자체 관계 |
| `TODO` | 개인 할 일 | `accounts_user.id` | 사용자 FK |

## 6. 3조 고유 데이터 → Core FK 초안

| 3조 데이터 | 업무 목적 | Core FK 기준 | 관계 |
|---|---|---|---|
| `Templates` | PRD 템플릿 | 없음 | 독립 |
| `Template_Sections` | 템플릿 섹션 | `Templates.id` | 자체 관계 |
| `Template_Questions` | 템플릿 질문 | `Template_Sections.id` | 자체 관계 |
| `PRDs` | 제품 요구사항 문서 | `accounts_user.id` + `teams_team.id`(선택) | 소유자/팀 |
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

## 7. 4조 근태 / 얼굴인식 영역

### 핵심 식별 기준

**근태 및 얼굴인식은 `accounts_user.id`를 기준으로 한다.**

```text
accounts_user.id
       │
       ├──────────────► 근태
       │                  ├─ 출석일
       │                  ├─ 체크인/체크아웃 시각
       │                  └─ 근태 상태
       │
       └──────────────► 얼굴인식
                          ├─ 이미지 저장 경로
                          ├─ 촬영 시각
                          ├─ predicted_student_id
                          ├─ confidence
                          ├─ recognition_status
                          └─ 관리자 검증값
```

### Round/Team 이력이 필요한 경우

```text
accounts_user
      │
      ▼
rounds_roundparticipant
      │
      ▼
teams_teammembership
      │
      ▼
teams_team
```

위 관계는 **Round/Team 이력이 필요한 기능에 한해서만 사용**한다.

### 얼굴인식 데이터 후보

| 데이터 | 기준 | 비고 |
|---|---|---|
| 사용자 ID | `accounts_user.id` | 공통 Master ID |
| 출석일 | - | 날짜 단위 출석 판정 |
| 체크인 시각 | - | 실제 인식/출석 시각 |
| 근태 상태 | - | 정상/지각/결석 등. 최종 enum은 추후 확정 |
| 이미지 저장 경로 | - | DB binary 직접 저장보다 파일/object storage 경로 저장 검토 |
| 촬영 시각 | - | 카메라 캡처 시각 |
| 예측 학생 | `accounts_user.id` | 모델이 예측한 사용자 |
| confidence | - | 모델 예측 신뢰도 |
| 인식 성공/실패 | - | inference 결과 |
| 실제 정답 학생 | `accounts_user.id` | 사후 검증값 |
| 관리자 검증자 | `accounts_user.id` | 검증 관리자 |
| 검증 시각 | - | 관리자 검증 시각 |

### 관리자 검증

모델 예측값과 실제 확정값을 동일 컬럼에 덮어쓰지 않고 구분한다.

- `predicted_student_id` → `accounts_user.id`
- `confidence`
- `recognition_status`
- `verified_student_id` → `accounts_user.id`
- `verified_by` → `accounts_user.id`
- `verified_at`

## 8. 점수 및 결과 연결

2조와 3조의 고유 평가 결과는 각자의 Domain에서 유지하고, Core 최종 결과에 필요한 확정 점수만 `results_scoreinput`으로 전달한다.

```text
2조 EVALUATION.score ──┐
                       ├──► results_scoreinput
3조 PRD_Member_Evaluations ┘          │
                                      ▼
                           results_calculationrun
                                      │
                                      ▼
                           results_evaluationresult
```

## 9. 최종 Core 참조 요약

```text
                         accounts_user
                       [공통 Master ID]
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
          1조 Domain       2조 Domain       3조 Domain
              │               │                │
              └───────────────┼────────────────┘
                              │
                              │ Round/Team 이력이
                              │ 필요한 경우에만
                              ▼
                  rounds_roundparticipant
                     [Round 참가 이력]
                              │
                              ▼
                         teams_team

accounts_user.id
       │
       └──────────────► 근태 / 얼굴인식
```

### 확정 원칙

1. **`accounts_user.id` = 사용자/학생 공통 Master ID**
2. **`rounds_roundparticipant.id` = 특정 평가 Round의 참가 이력**
3. **근태/얼굴인식 = `accounts_user.id` 기준**
4. **Round/Team 이력이 필요한 기능만 `rounds_roundparticipant.id` 참조**
5. 각 조의 고유 Domain은 독립적으로 유지하되 필요한 Core만 FK로 참조한다.
6. 1조 학습 출석과 4조 실제 근태는 업무 목적이 다르므로 분리한다.
7. 중복 User/Student 기본정보 모델은 공통 Core의 `accounts_user` 기준으로 통합한다.

## 10. 관련 산출물

- [ERD 4개 조 비교표](./ERD_COMPARISON_4TEAMS.md)
- [VIEW Guide](./VIEW_GUIDE.md)
- [TO-BE ERD 이미지](./TO_BE_ERD.png)
- [TO-BE ERD Mermaid](./TO_BE_ERD.mmd)
- [P3 DB Migration 준비 문서](../deliverables/P3_김종복/2026-08-28_DB_Migration_준비.md)
