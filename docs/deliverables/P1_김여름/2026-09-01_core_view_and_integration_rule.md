# 2026-09-01 Core VIEW 및 공통 연동 규칙 정리

## 1. 목적
- Issue #56의 P1 작업 결과를 Daily Deliverable로 기록한다.
- P2 인증·권한 기준과 P3 DB·ERD 기준의 충돌 여부를 문서 기준으로 확인하고 공통 연동 기준을 정리한다.
- 통합 DB의 공통 VIEW 반영 여부, 조회 결과, 사용 목적과 대상 팀을 검증한다.
- VIEW의 **사용 대상 확정**과 **실제 애플리케이션 적용 완료**를 구분하여 기록한다.
- 개인 브랜치와 `develop` 중심의 브랜치 / PR / 통합 테스트 규칙을 문서화한다.

## 2. 오늘 수행 내용
- 개인 작업 History 관리를 위한 `feature/p1-summer` 브랜치 생성
- 통합 DB의 공통 VIEW 존재 여부 확인
- `ax_user_team_login_view`, `user_round_team_view` 직접 조회 및 데이터 검증
- VIEW별 용도와 사용 대상 팀 최종 정리
- 1·2·3조의 실제 VIEW 적용 상태 구분
- P2 인증·권한 / P3 DB·ERD 기준을 Issue 및 산출물 기준으로 비교
- 관련 PR의 base=`develop` 여부 확인
- `develop` 기준 개인 브랜치 / PR / 통합 테스트 규칙 정리

## 3. VIEW 검증 결과

### 검증 목적
통합 DB에서 사용자·팀 조회 기준을 하나로 통일하기 위해 만든 공통 VIEW가 실제 DB에 반영되어 있고 정상적으로 조회되는지 확인한다.

### 대상 DB
- PostgreSQL: `ax_evaluation`

### 확인 대상 및 결과
| VIEW | 존재 여부 | SELECT 조회 | 데이터 검증 | 결과 |
|---|---|---|---|---|
| `public.ax_user_team_login_view` | 확인 완료 | 정상 | 정상 확인 | **PASS** |
| `public.user_round_team_view` | 확인 완료 | 정상 | 정상 확인 | **PASS** |

### VIEW 검증 기준
1. VIEW가 실제 통합 DB에 존재하는지 확인한다.
2. `SELECT` 조회가 오류 없이 정상 수행되는지 확인한다.
3. 조회 결과 데이터가 기대한 구조와 값으로 나오는지 확인한다.

## 4. VIEW 용도 및 사용 대상 최종 결정

| VIEW | 최종 용도 | 사용 대상 | 현재 상태 |
|---|---|---|---|
| `public.ax_user_team_login_view` | 사용자 기본정보 + 대표/현재 팀 정보 조회 | **1·2·3조 공통** | 사용 기준 확정 / 실제 코드 적용은 조별 통합 시 검증 |
| `public.user_round_team_view` | 사용자별 Round/Team History 조회 | **3조 중심**, Round별 팀 이력이 필요한 기능 | 사용 기준 확정 / 3조 현재 실제 기능에서는 미사용 확인 |

### `ax_user_team_login_view`
- 목적: 전체 조에서 공통적으로 필요한 사용자 기본정보와 대표/현재 팀 정보를 일관된 형식으로 조회한다.
- 사용 대상: 1·2·3조 공통.
- 사용 예: 로그인 이후 사용자 정보, Role, User/Team 공통 조회.
- 정책: 각 조가 원본 Core 테이블을 개별적으로 중복 JOIN하기보다 공통 VIEW를 우선 사용한다.

### `user_round_team_view`
- 목적: 특정 사용자가 각 Round에서 어느 팀에 소속되어 있었는지 조회한다.
- 사용 대상: 3조 중심. 단, 다른 조에서도 Round별 Team History가 필요한 경우 사용할 수 있다.
- 사용 예: 과거 팀 소속 이력, Round별 팀 변경, 팀원 중복 여부 확인.
- 정책: `user_id + round_id`를 주요 조회 기준으로 사용한다.

## 5. 팀별 실제 적용 상태

### 1조
- 통합 DB VIEW 자료 전달: **확인 완료**
- VIEW 사용 기준: **확정**
- 실제 1조 코드 적용: **통합 시 검증 필요**

### 2조
- 공통 User / Team / Round 데이터를 VIEW로 조회하는 방향: **확인 완료**
- 관련 PR #47 base=`develop`: **PASS**
- 실제 2조 코드 적용: **코드 전달 후 검증 필요**

### 3조
- `user_round_team_view`를 Round별 Team History 조회용 주요 VIEW로 지정: **확정**
- 현재 개발 단계의 실제 User View 사용: **미사용 확인**
- 실제 적용 시 컬럼/조회 방식: **재검증 필요**

> **중요:** `사용 대상`과 `실제 적용 완료`는 같은 의미가 아니다. 현재 단계에서는 VIEW 사용 정책과 대상 팀은 확정했지만, 각 조 애플리케이션에서 실제 적용됐는지는 통합 단계에서 별도로 확인한다.

## 6. P2 / P3 결정사항 비교

### 비교 근거
- P2 Issue #13 — 로그인 / 회원 / 학생 / 권한 / 근태 연계
- P3 Issue #32 / #42 / #54 — Core ERD / DB / Migration / VIEW 검증
- `docs/erd/VIEW_GUIDE.md`
- 관련 Deliverable / PR

### 비교 결과
| 항목 | P2 기준 | P3 기준 | 판단 |
|---|---|---|---|
| User | `accounts_user.id` 공통 Master | `accounts_user.id` 공통 Master | 문서 기준 일치 |
| Student | 별도 Student 테이블 없이 User 기준 | `accounts_user` 기준, `RoundParticipant`는 참가 이력 | 문서 기준 일치 |
| Team | 4조 Core Team 정보 사용 | `teams_team` / `teams_teammembership` 기준 | 문서 기준 일치 |
| Role | `accounts_user.role` | Core User 권한 구조 유지 | 문서 기준 일치 |
| FK | 일반 User 참조는 `accounts_user.id` | 동일 기준 | 문서 기준 일치 |
| Team/User 조회 | API 또는 공통 조회 계층 필요 | VIEW 제공 | VIEW 사용 범위 별도 확정 |

### 최종 판단
- 현재 문서 기준 Core 데이터 구조상 **Critical 충돌은 확인되지 않음**.
- User / Student / Team / Role / FK 기본 기준은 문서상 일치한다.
- 이는 실제 코드/통합 DB 연동 완료를 의미하지 않는다.
- 각 조 코드 통합 시 Model / FK / Migration / VIEW 사용 여부를 다시 검증한다.

## 7. 검수 결과

| 검수 항목 | 판정 | 근거/조치 |
|---|---|---|
| Issue ↔ 문서 정합성 | PASS | VIEW 용도/대상 팀을 동일 기준으로 반영 |
| VIEW DB 존재/조회 | PASS | 두 VIEW 존재·SELECT·데이터 검증 완료 |
| VIEW 목적 정의 | PASS | `VIEW_GUIDE.md` 기준 |
| 사용 팀 정의 | PASS | 공통 VIEW / Team History VIEW 대상 확정 |
| 1조 실제 코드 적용 | 보완필요 | 통합 시 확인 |
| 2조 실제 코드 적용 | 보완필요 | 코드 전달 후 확인 |
| 3조 실제 코드 적용 | 보완필요 | 현재 실제 기능에서는 미사용 |
| PR base=`develop` | PASS | 확인 가능한 관련 PR #47 기준 |
| 전체 팀장 판정 | **조건부 PASS** | 정책/기준 승인 가능, 실제 코드 적용은 후속 검증 |

### 과장 완료 체크 방지
- P3 #54에는 VIEW 관련 체크박스와 본문 설명 사이에 상충되는 기록이 확인되어, 해당 Issue의 체크박스만으로 최종 PASS 근거를 삼지 않는다.
- P1 최종 판단은 직접 확인한 VIEW 조회 결과 + `VIEW_GUIDE.md` + 팀별 Issue / Deliverable / PR 근거를 기준으로 한다.

## 8. 형상관리 및 통합 개발 규칙

### 개인 브랜치
- 개인 작업 History 관리를 위해 `feature/p1-summer` 브랜치 생성 완료
- 개인 작업 브랜치는 `develop`에서 생성한다.

### PR / 통합 기준
1. 로컬 최신화
2. 서버 정상 실행 확인
3. `develop` 체크아웃 및 최신화
4. `develop`에서 개인 브랜치 생성
5. 작업 완료 후 PR base=`develop`
6. `develop`에서 통합 / Regression Test
7. 안정화 후 `develop → main` PR
8. `main` / `develop` 직접 push 금지

### DB 개발 기준
- 각 조 담당자는 자신의 로컬/개별 DB 환경에서 먼저 기능을 개발하고 검증한다.
- 검증 전부터 공용 통합 DB를 직접 수정 대상으로 사용하지 않는다.
- 개별 환경에서 실행 및 검증이 완료된 뒤 P3 DB 기준에 맞춰 통합한다.
- 통합 전 FK / Migration / 기존 데이터 영향 여부를 확인한다.

### 문서 관리 기준
- 코드와 문서는 `develop` 기준으로 함께 관리한다.
- Daily Issue / Daily Deliverable도 실제 개발 및 통합 상태와 동일하게 최신화한다.

## 9. 산출물 / 근거
- Issue: `#56 P1 — P2 인증·권한 / P3 DB·ERD 충돌 확인 및 VIEW·공통 연동 기준 정리`
- 선행 Issue: `#35 P1 — 1·2·3·4조 기능 비교 및 통합/분리 기준 확정`
- P2 근거: Issue #13
- P3 근거: Issue #32 / #42 / #54
- VIEW 문서: `docs/erd/VIEW_GUIDE.md`
- 관련 PR: #47 (`feature/p5_yejin` → `develop`)
- 개인 브랜치: `feature/p1-summer`
- 대상 DB: PostgreSQL `ax_evaluation`

## 10. 본인 검증
- 개인 브랜치 생성: **PASS**
- 두 VIEW 실제 DB 존재 확인: **PASS**
- 두 VIEW 직접 조회: **PASS**
- 조회 데이터 이상 여부 확인: **PASS**
- VIEW 용도 / 사용 대상 정리: **PASS**
- P2 / P3 문서 기준 충돌 여부 확인: **PASS**
- 브랜치 / PR / develop 운영 규칙 문서화: **PASS**
- Daily Deliverable 반영: **PASS**

## 11. 현재 판단
- VIEW 자체의 DB 반영/조회 검증은 완료했다.
- VIEW의 용도와 사용 대상 팀은 최종 확정했다.
- P2/P3는 문서 기준으로 Critical 충돌이 확인되지 않았다.
- 각 조의 실제 애플리케이션 VIEW 적용 여부는 아직 전체 완료가 아니므로 조별 통합 단계에서 별도 검증한다.
- 현재 단계의 팀장 판정은 **조건부 PASS / 정책 승인 가능**이며 Critical Blocker는 없다.
