# 2026-09-01 Core VIEW 및 공통 연동 규칙 정리

## 1. 목적
- Issue #56의 P1 작업 내용을 Daily Deliverable로 기록한다.
- P2 인증·권한 기준과 P3 DB·ERD 기준의 충돌 여부를 확인하기 위한 기준을 정리한다.
- 통합 DB의 공통 VIEW 반영 상태와 검증 결과를 기록한다.
- 개인 브랜치, `develop`, PR 및 통합 DB 사용 기준을 팀 공통 작업 규칙으로 정리한다.

## 2. 오늘 수행 내용
- 개인 작업 이력 관리를 위한 `feature/p1-summer` 브랜치 생성
- 통합 DB의 공통 VIEW 존재 및 조회 상태 확인
- `user_round_team_view` 직접 조회 수행
- `ax_user_team_login_view`, `user_round_team_view`의 검증 항목 정리
- P2 인증·권한 / P3 DB·ERD 간 충돌 확인 항목 정리
- `develop` 중심의 브랜치 / PR / 통합 테스트 규칙 정리
- 각 담당자가 개별 로컬/DB 환경에서 먼저 검증한 뒤 통합 DB에 반영하는 기준 정리

## 3. VIEW 검증 결과

### 검증 목적
통합 DB에서 사용자·팀 조회 기준을 하나로 통일하기 위해 만든 공통 VIEW가 실제 DB에 반영되어 있고 정상적으로 조회되는지 확인한다.

### 대상 DB
- PostgreSQL: `ax_evaluation`

### 확인 대상
- `public.ax_user_team_login_view`
- `public.user_round_team_view`

### 현재 확인 결과
| VIEW | 존재 여부 | SELECT 조회 | 데이터 검증 | 현재 상태 |
|---|---|---|---|---|
| `user_round_team_view` | 확인 | 정상 | 최종 확인 필요 | 부분 PASS |
| `ax_user_team_login_view` | 확인 필요 | 확인 필요 | 확인 필요 | 대기 |

### 확인 SQL
```sql
SELECT * FROM user_round_team_view;
```

### VIEW 검증 기준
1. VIEW가 실제 통합 DB에 존재하는지 확인한다.
2. `SELECT` 조회가 오류 없이 정상 수행되는지 확인한다.
3. 조회 결과 데이터가 기대한 구조와 값으로 나오는지 확인한다.

## 4. VIEW 용도 및 사용 기준

### `user_round_team_view`
- 목적: 사용자와 기수(Round), 팀(Team) 관계를 공통 기준으로 조회하기 위한 VIEW
- 현재 확인: 실제 DB 존재 및 직접 조회 정상
- 사용 범위: 사용자-기수-팀 관계가 필요한 통합 기능에서 공통 조회 기준으로 사용
- 추가 확인: 실제 조회 데이터가 기대 구조와 일치하는지 최종 검증 필요

### `ax_user_team_login_view`
- 목적: 로그인 사용자와 팀 관련 정보를 공통 기준으로 조회하기 위한 VIEW
- 사용 범위: 인증/권한 또는 로그인 이후 사용자·팀 정보가 필요한 기능에서 공통 조회 기준 후보
- 추가 확인: 실제 DB 존재 여부, SELECT 정상 여부, 실제 사용 팀/기능 확인 필요

## 5. P2 / P3 확인 기준

### P2 — 인증·권한
확인 대상:
- User / Student / Role 기준
- 로그인 및 권한 처리 기준
- 공통 User / Team 조회 시 VIEW 사용 여부

### P3 — DB·ERD
확인 대상:
- DB / ERD / FK / Migration 기준
- 공통 User / Student / Team 데이터 연결 구조
- VIEW 정의 및 통합 DB 반영 상태

### P1 충돌 확인 항목
- User 기준이 P2와 P3에서 동일한가
- Student 관계가 동일한가
- Team / TeamMember 연결 기준이 동일한가
- Role / 권한 구조가 DB 구조와 충돌하지 않는가
- FK / Migration에 Critical 충돌이 없는가
- 공통 VIEW가 인증/통합 기능에서 같은 기준으로 사용되는가

## 6. 형상관리 및 통합 개발 규칙

### 개인 브랜치
- 개인 작업 History 관리를 위해 `feature/p1-summer` 브랜치 생성 완료
- 개인 작업 브랜치는 `develop`에서 생성한다.

### PR 기준
1. 내 로컬을 최신 상태로 맞춘다.
2. 서버 정상 실행 여부를 확인한다.
3. `develop`을 체크아웃하고 최신화한다.
4. `develop`에서 개인 작업 브랜치를 생성한다.
5. 작업 완료 후 PR base는 `develop`으로 한다.
6. `develop`에서 통합 / Regression Test를 수행한다.
7. 안정화가 끝난 뒤 `develop → main` PR을 진행한다.
8. `main` / `develop` 직접 push는 하지 않는다.

### DB 개발 기준
- 각 조 담당자는 자신의 로컬/개별 DB 환경에서 먼저 기능을 개발하고 검증한다.
- 검증 전부터 공용 통합 DB를 직접 수정 대상으로 사용하지 않는다.
- 개별 환경에서 일정 수준 이상 실행 및 검증이 완료된 뒤 P3 DB 기준에 맞춰 통합한다.
- 통합 DB에 반영하기 전 FK / Migration / 기존 데이터 영향 여부를 확인한다.

### 문서 관리 기준
- 코드와 문서를 별도 흐름으로 관리하지 않고 `develop` 기준으로 함께 반영한다.
- Daily Issue / Daily Deliverable도 실제 개발 및 통합 상태와 동일한 기준으로 최신화한다.

## 7. 산출물 / 근거
- Issue: `#56 [P1][9/1] 김여름 — P2 인증·권한 / P3 DB·ERD 충돌 확인 및 VIEW·공통 연동 기준 정리`
- 개인 브랜치: `feature/p1-summer`
- 대상 DB: PostgreSQL `ax_evaluation`
- 확인 VIEW:
  - `public.ax_user_team_login_view`
  - `public.user_round_team_view`
- 선행 Issue: `#35 [P1][8/31] 김여름[EPIC] — 1·2·3·4조 기능 비교 및 통합/분리 기준 확정`

## 8. 본인 검증
- `feature/p1-summer` 개인 브랜치 생성: **PASS**
- `user_round_team_view` 실제 DB 존재 확인: **PASS**
- `user_round_team_view` 직접 조회: **PASS**
- 브랜치 / PR / develop 중심 운영 규칙 문서화: **PASS**
- Daily Deliverable 작성 및 반영: **PASS**

## 9. 남은 확인 사항
- `ax_user_team_login_view` 실제 통합 DB 존재 여부 확인
- `ax_user_team_login_view` SELECT 정상 여부 확인
- 두 VIEW 조회 데이터의 최종 정상 여부 확인
- 두 VIEW의 실제 사용 팀 / 기능 / 사용 위치 확정
- P2 인증·권한 기준과 P3 DB·ERD 기준의 실제 충돌 여부 확인
- 전체 확인 완료 후 Cross Check PASS 기록

## 10. 현재 판단
- Daily Deliverable 작성 및 반영은 완료되었다.
- 다만 Issue #56 전체 GREEN 처리는 VIEW 전체 검증과 P2/P3 충돌 확인이 끝난 뒤 진행한다.
