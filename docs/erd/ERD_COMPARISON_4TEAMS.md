# 1·2·3·4조 ERD 비교표

- 작성일: 2026-08-28
- 기준: 기존 4조 평가 시스템을 **Core 기준 시스템**으로 유지하고 1·2·3조 고유 기능을 모듈 단위로 통합
- 분류 기준: 단순 테이블명 유사성이 아니라 **업무 목적(Business Purpose)** 기준

## 1. 판정 기준

| 분류 | 의미 |
|---|---|
| **유지** | 해당 조의 고유 업무 기능으로 필요하므로 그대로 유지 |
| **통합** | Core의 공통 데이터/계산 구조로 합치거나 Core가 대체 |
| **분리** | 이름이나 데이터 성격은 유사하지만 업무 목적이 달라 별도 Domain으로 유지 |
| **폐기** | 중복/캐시/통합 과정에서 더 이상 독립적으로 사용할 필요가 없음 |

> 핵심 원칙: **Core의 User / Student(Participant) / Team / Evaluation Round / Evaluation / Result 구조는 4조를 기준으로 한다.** 다른 조의 고유 업무 데이터는 삭제하지 않고 모듈로 유지하되, 점수처럼 Core 결과 산출에 필요한 값은 `results_scoreinput`으로 수집한다.

---

## 2. Core(4조) 기준 테이블

| 조 | 테이블 | 업무 목적 | 판정 | 통합 기준 / 비고 |
|---|---|---|---|---|
| 4조 | `accounts_user` | 회원·인증·권한의 기준 | **유지** | 모든 조의 User 기준. 별도 User 생성 금지 |
| 4조 | `account_emailaddress` | 이메일 인증/주소 관리 | **유지** | Core 인증 보조 데이터 |
| 4조 | `rounds_evaluationround` | 평가 회차 관리 | **유지** | 전체 평가 결과의 기준 회차 |
| 4조 | `rounds_roundparticipant` | 회차별 학생 참가자/스냅샷 | **유지** | 1·2·3조 학생 식별의 Core 기준 |
| 4조 | `rounds_templatequestion` | 평가 문항 | **유지** | 동료/팀 평가 문항 기준 |
| 4조 | `teams_team` | 평가 회차별 팀 | **유지** | 1·2·3조가 팀을 참조할 때 Core Team 사용 |
| 4조 | `teams_teammembership` | 팀-참가자 관계 | **유지** | 공통 Team Membership 기준 |
| 4조 | `reviews_reviewsubmission` | 팀/동료 평가 제출 | **유지** | Core 평가 Domain |
| 4조 | `reviews_reviewanswer` | 평가 문항별 점수 | **유지** | 최종 점수 계산의 Core 입력 |
| 4조 | `results_calculationrun` | 점수 계산 실행 단위 | **유지** | 모든 점수 집계의 최종 계산 기준 |
| 4조 | `results_evaluationresult` | 최종 팀/개인 결과 | **유지** | 외부 조 점수를 흡수한 최종 결과 |
| 4조 | `notices_notice` | 공지 | **유지** | 공통 서비스 영역 |
| 4조 | `notifications_notification` | 알림 | **유지** | 공통 서비스 영역 |
| 4조 | `audit_auditevent` | 감사 로그 | **유지** | 공통 운영/감사 영역 |
| 4조 | `results_scoreinput` | 2·3조 점수의 Core 계산 입력 스냅샷 | **유지** | `source_type + source_id`로 외부 점수 수집. 물리 FK는 만들지 않음 |

---

## 3. 1조 — 학습 게이미피케이션

| 조 | 테이블 | 업무 목적 | 판정 | 통합 기준 / 비고 |
|---|---|---|---|---|
| 1조 | `CG_USERS` | 게임 서비스용 사용자 확장 프로필 | **통합** | `accounts_user`와 1:1 확장 구조로 전환. 별도 사용자 식별 주체로 사용하지 않음 |
| 1조 | `ATTENDANCES` | 게임 내 학습 출석/연속 학습일(streak) | **분리** | 4조의 실제 출퇴근/근태와 업무 목적이 다름. **학습 출석 Domain 유지** |
| 1조 | `CONCEPTS` | 프로그래밍 개념 분류 | **유지** | 1조 학습 콘텐츠의 고유 기능 |
| 1조 | `TASKS` | 게임형 프로그래밍 학습 문제 | **유지** | 과제(2조)와 목적이 다름. 학습 문제/콘텐츠로 유지 |
| 1조 | `USER_PROFICIENCY` | 개념별 학습 숙련도 | **유지** | 학습 분석/개인화에 필요한 고유 데이터 |
| 1조 | `TASK_ATTEMPTS` | 학습 문제 풀이 시도 및 결과 | **유지** | 2조 `SUBMISSION`과 목적이 다름. 학습 시도 이력으로 유지 |
| 1조 | `ROOMS` | 실시간 게임/배틀 방 | **유지** | 1조 고유 게임 기능 |
| 1조 | `ROOM_PARTICIPANTS` | 게임 방 참가자 | **유지** | Core Team을 참조하되 게임 참가 관계 자체는 1조 Domain |
| 1조 | `ROOM_TASKS` | 게임 방에서 사용할 문제 | **유지** | `TASKS`와 `ROOMS`를 연결하는 고유 기능 |
| 1조 | `RANKING_GROUPS` | 랭킹 그룹 | **유지** | 게임 랭킹 기능 |
| 1조 | `RANKING_PARTICIPANTS` | 랭킹 참가자/점수 | **유지** | Core 평가 점수와 목적이 다른 게임 랭킹 점수 |
| 1조 | `RANK_CHALLENGES` | 랭킹 도전 과제 진행 | **유지** | 게임 도전 기능 |
| 1조 | `RANK_CHALLENGE_TASKS` | 도전 과제의 문제 구성/진행 | **유지** | 게임 챌린지 고유 기능 |
| 1조 | `ITEMS` | 게임 아이템 정의 | **유지** | 게임 경제/꾸미기 기능 |
| 1조 | `INVENTORIES` | 사용자 아이템 보유량 | **유지** | 게임 인벤토리 |
| 1조 | `PLACED_OBJECTS` | 공간 내 배치 아이템 | **유지** | 게임 공간 꾸미기 |
| 1조 | `CATS` | 고양이 캐릭터 정의 | **유지** | 게임 고유 콘텐츠 |
| 1조 | `USER_CATS` | 사용자 보유 고양이 | **유지** | 게임 고유 기능 |
| 1조 | `CAT_MEMORIES` | 고양이 AI 대화/기억 요약 | **유지** | 게임 AI 기능 |

### 1조 핵심 판정

**`CG_USERS`는 통합**, `ATTENDANCES`는 **분리**가 핵심이다.

- `CG_USERS`: 회원 자체를 새로 만드는 테이블이 아니라 `accounts_user`의 게임 확장 프로필이므로 Core User에 종속시킨다.
- `ATTENDANCES`: "학습 서비스를 이용했는가/학습 streak가 이어지는가"를 기록한다. 4조 신규 근태의 "실제 출근·퇴근/근무 상태"와는 업무 목적이 다르므로 하나의 Attendance 테이블로 합치지 않는다.

---

## 4. 2조 — LMS / 강의 / 과제 / 제출

| 조 | 테이블 | 업무 목적 | 판정 | 통합 기준 / 비고 |
|---|---|---|---|---|
| 2조 | `LECTURE` | 강의 단위 관리 | **유지** | LMS 고유 기능 |
| 2조 | `LESSON` | 강의의 수업/차시 | **유지** | LMS 고유 기능 |
| 2조 | `LESSON_MATERIAL` | 교안/파일/링크 | **유지** | LMS 고유 기능 |
| 2조 | `ASSIGNMENT` | 튜터가 부여하는 과제 | **유지** | Core 평가와 다른 "학습 과제" Domain |
| 2조 | `SUBMISSION` | 과제 제출물 | **유지** | 2조의 핵심 고유 기능. Core 결과 계산에는 점수만 `results_scoreinput`으로 PUSH |
| 2조 | `SUBMISSION_FILE` | 제출 파일 첨부 | **유지** | 제출물의 파일 관리 |
| 2조 | `AI_EVALUATION` | 과제 제출물 AI 1차 평가 | **유지** | AI 평가 결과 자체는 2조 기능. 필요 시 최종 확정 점수만 Core로 전달 |
| 2조 | `EVALUATION` | 제출물에 대한 튜터 공식 평가 | **유지** | 이름은 Core 평가와 유사하지만 대상이 "과제 제출물"이므로 별도 Domain 유지. 확정 점수는 Core로 PUSH |
| 2조 | `TODO` | 개인 할 일 관리 | **유지** | 학습 관리 고유 기능. Core 평가와 무관 |

### 2조 핵심 판정

2조의 **과제/제출 기능은 고유 기능으로 확인되므로 통합·폐기하지 않는다.**

특히 `ASSIGNMENT → SUBMISSION → EVALUATION`은 "과제 업무 처리"를 담당하고, 4조 Core의 `reviews_* → results_*`는 "평가 회차의 공식 평가 및 최종 결과 산출"을 담당한다. 따라서 테이블을 이름만 보고 `EVALUATION` 하나로 합치면 업무 경계가 깨진다.

점수 연계는 다음처럼 처리한다.

```text
2조 EVALUATION / 확정 점수
        ↓ PUSH
Core results_scoreinput
        ↓
Core results_calculationrun
        ↓
Core results_evaluationresult
```

`SUBMISSION.final_score`는 원본 제출 Domain의 조회 편의를 위한 캐시 성격이므로 **최종 통합 설계에서 중복 계산 원천으로 사용하지 않는다.**

---

## 5. 3조 — PRD / 아이디어 개발 / AI Coach

| 조 | 테이블 | 업무 목적 | 판정 | 통합 기준 / 비고 |
|---|---|---|---|---|
| 3조 | `Templates` | PRD 템플릿 유형 | **유지** | PRD 고유 기능 |
| 3조 | `Template_Sections` | 템플릿 섹션 | **유지** | PRD 고유 기능 |
| 3조 | `Template_Questions` | 템플릿 질문 | **유지** | PRD 고유 기능 |
| 3조 | `PRDs` | 아이디어/제품 요구사항 문서 | **유지** | 3조 핵심 고유 Domain |
| 3조 | `PRD_Permissions` | PRD 공유/권한 | **유지** | 협업 고유 기능 |
| 3조 | `PRD_Sections` | PRD 문서 섹션 | **유지** | PRD 고유 기능 |
| 3조 | `PRD_Questions` | PRD 질문/답변 | **유지** | PRD 고유 기능 |
| 3조 | `PRD_Comments` | PRD 의견/댓글 | **유지** | 협업 고유 기능 |
| 3조 | `Brainstorm_Boards` | 아이디어 브레인스토밍 보드 | **유지** | 3조 고유 기능 |
| 3조 | `Brainstorm_Categories` | 브레인스토밍 분류 영역 | **유지** | 3조 고유 기능 |
| 3조 | `Post_its` | 브레인스토밍 포스트잇 | **유지** | 3조 고유 기능 |
| 3조 | `AI_Usage_Logs` | AI API 사용 기록 | **유지** | AI 운영/분석 데이터 |
| 3조 | `AI_Prompts` | AI 기능 프롬프트 버전 관리 | **유지** | AI Coach 고유 기능 |
| 3조 | `PRD_Member_Evaluations` | PRD 활동 기반 학생 평가 | **유지** | PRD 활동 평가의 원본 Domain. 확정 점수만 Core로 PUSH |
| 3조 | `PRD_Edit_Histories` | PRD 첨삭/수정 이력 | **유지** | 변경 이력 고유 기능 |
| 3조 | `AI_Chat_Histories` | PRD 관련 AI 대화 이력 | **유지** | AI Coach 고유 기능 |

### 3조 핵심 판정

3조 PRD 관련 테이블은 **고유 기능으로 확인되므로 유지**한다.

`PRDs`, `PRD_Sections`, `PRD_Questions`, `PRD_Permissions`, `PRD_Comments`, 브레인스토밍, AI 사용/대화/수정 이력은 4조 Core의 평가·팀·결과 테이블을 대체하는 구조가 아니다. Core의 `accounts_user`, `rounds_roundparticipant`, `teams_team`을 참조하면서 PRD Domain을 독립적으로 유지한다.

`PRD_Member_Evaluations.total_score`는 PRD Domain의 평가 결과이며, Core 최종 결과와 동일 테이블로 합치지 않는다. 확정 점수만 `results_scoreinput`에 스냅샷으로 전달한다.

---

## 6. 평가 / 점수 계열 비교

| 출처 | 평가 대상 | 점수의 의미 | 판정 | Core 연계 |
|---|---|---|---|---|
| 4조 `reviews_reviewanswer` | 팀/개인 | Core 공식 평가 문항 점수 | **유지** | Core 계산의 직접 입력 |
| 4조 `results_evaluationresult` | 팀/개인 | 최종 계산 결과 | **유지** | 최종 결과 저장 |
| 2조 `AI_EVALUATION` | 과제 제출물 | AI 1차 평가 점수 | **유지** | 확정/채택 점수만 Core로 전달 가능 |
| 2조 `EVALUATION` | 과제 제출물 | 튜터 공식 과제 평가 | **유지** | `source_type=ASSIGNMENT`로 `results_scoreinput`에 PUSH |
| 2조 `SUBMISSION.final_score` | 제출물 | `EVALUATION.score` 캐시 | **폐기(원천 점수로 사용하지 않음)** | 최종 통합 계산의 Source of Truth가 아님 |
| 3조 `PRD_Member_Evaluations` | PRD 활동의 학생 | PRD 활동 평가 점수 | **유지** | `source_type=PRD`로 `results_scoreinput`에 PUSH |
| 1조 `TASK_ATTEMPTS` | 학습 문제 풀이 | 정답/풀이 성공 여부 | **유지** | 일반적으로 Core 공식 평가 점수로 직접 대체하지 않음 |
| 1조 `RANKING_PARTICIPANTS.current_rank_score` | 게임 랭킹 참가자 | 게임 랭킹 점수 | **분리** | Core 공식 평가 점수와 목적이 다름 |
| 1조 `ROOM_PARTICIPANTS.current_score` | 게임 참가자 | 게임 방 진행 점수 | **분리** | Core 공식 평가 점수와 목적이 다름 |

### 점수 통합 원칙

```text
4조 Core 공식 평가 ───────────────┐
                                  │
2조 과제 확정 점수 ── source_type=ASSIGNMENT ─┤
                                  │
3조 PRD 확정 점수 ── source_type=PRD ──────────┤
                                  ↓
                         results_scoreinput
                                  ↓
                         results_calculationrun
                                  ↓
                       results_evaluationresult
```

`results_scoreinput`은 외부 조의 원본 테이블과 물리 FK를 직접 연결하지 않고 `source_type/source_id`와 `raw_score`를 스냅샷으로 보관한다. 따라서 원본 Domain은 독립적으로 유지하면서 Core 결과 계산에 필요한 점수만 안정적으로 흡수한다.

---

## 7. 1조 학습 출석 vs 4조 근태 — 반드시 분리

| 구분 | 1조 `ATTENDANCES` | 4조 신규 근태 |
|---|---|---|
| 업무 목적 | 학습 서비스 이용/학습 연속성 관리 | 실제 출근·퇴근 및 근태 관리 |
| 대표 데이터 | `check_in_date`, `streak_count` | 출퇴근 시각, 근태 상태, 인식 결과 등 |
| 기준 주체 | 게임/학습 사용자 | Core `Student` |
| 얼굴인식 연계 | 직접 연계 대상 아님 | 얼굴 등록/인식 로그와 연계 |
| 판정 | **분리** | **분리** |

따라서 `ATTENDANCES`를 4조 근태 테이블로 이름만 변경하거나 합치지 않는다. 1조 출석은 학습 Domain에 남기고, 4조 근태는 실제 근태 Domain으로 신규 설계한다.

---

## 8. 최종 판정 요약

| 영역 | 최종 판단 |
|---|---|
| 공통 User | **4조 Core `accounts_user`로 통합** |
| 공통 Student 식별 | **4조 `rounds_roundparticipant` 기준으로 통일** |
| 공통 Team | **4조 `teams_team`으로 통합** |
| 1조 `CG_USERS` | **Core User의 1:1 확장으로 통합** |
| 1조 학습 `ATTENDANCES` | **4조 근태와 분리** |
| 1조 학습/게임 기능 | **고유 기능 유지** |
| 2조 강의/LMS | **고유 기능 유지** |
| 2조 과제/제출 | **고유 기능 유지** |
| 2조 과제 평가 | **원본은 유지, 확정 점수만 Core로 PUSH** |
| 3조 PRD | **고유 기능 유지** |
| 3조 AI Coach/브레인스토밍 | **고유 기능 유지** |
| 3조 PRD 평가 | **원본은 유지, 확정 점수만 Core로 PUSH** |
| Core 평가/결과 | **4조 기준 유지** |
| 외부 점수 수집 | **`results_scoreinput`으로 통합** |
| 단순 캐시 점수 | **원천 데이터로 사용하지 않음 / 필요 시 폐기** |

---

## 9. 통합 설계 시 주의사항

1. **이름이 같다는 이유만으로 통합하지 않는다.** `EVALUATION`이라는 이름만 보고 2조 평가와 4조 평가를 하나로 만들면 업무 목적이 충돌한다.
2. **User는 중복 생성하지 않는다.** 1조 `CG_USERS`는 Core User를 확장하는 구조로 바꾼다.
3. **Student 참조 기준을 통일한다.** 2·3조와 근태/얼굴인식 모두 Core Student 식별 기준을 사용한다.
4. **Team은 Core `teams_team`을 사용한다.** 1조 게임 기능이 팀을 참조할 경우에도 별도 Team 마스터를 만들지 않는다.
5. **2조 과제와 4조 공식 평가는 분리한다.** 다만 확정 점수는 Core 계산에 입력할 수 있다.
6. **3조 PRD와 4조 평가 결과는 분리한다.** PRD 자체의 평가 이력을 유지하면서 최종 점수만 Core에 전달한다.
7. **1조 학습 출석과 4조 실제 근태는 반드시 별도 Domain이다.** 이는 통합 대상이 아니라 명시적 `분리` 대상이다.
8. **Core 결과 계산의 Source of Truth를 명확히 한다.** 외부 조 점수는 `results_scoreinput.raw_score`에 스냅샷으로 수신하고, `results_calculationrun`이 최종 계산을 담당한다.

---

## 10. 다음 ERD 작업에 반영할 변경사항

- [ ] `CG_USERS` → `accounts_user` 1:1 확장 구조 명시
- [ ] `ATTENDANCES`와 4조 근태 Domain을 별도 영역으로 배치
- [ ] 2조 `LECTURE / LESSON / ASSIGNMENT / SUBMISSION` 유지
- [ ] 2조 `EVALUATION`의 확정 점수 → `results_scoreinput` 연결 표현
- [ ] 3조 PRD 전체 Domain 유지
- [ ] `PRD_Member_Evaluations` → `results_scoreinput` 연결 표현
- [ ] `results_scoreinput`의 `source_type/source_id` 스냅샷 방식 유지
- [ ] 중복 User / Student / Team 테이블 생성 금지
- [ ] 최종 TO-BE ERD에 위 판정 결과 반영
