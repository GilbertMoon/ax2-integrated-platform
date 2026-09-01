# 2026-09-01 Core VIEW 및 공통 연동 규칙 정리

## 1. 목적
- Issue #56의 P1 작업 결과를 Daily Deliverable로 기록한다.
- P2 인증·권한 기준과 P3 DB·ERD 기준의 충돌 여부를 확인하고 공통 연동 기준을 정리한다.
- 통합 DB의 공통 VIEW 반영 여부, 조회 결과, 사용 목적을 검증한다.
- 개인 브랜치와 `develop` 중심의 브랜치 / PR / 통합 테스트 규칙을 문서화한다.

## 2. 오늘 수행 내용
- 개인 작업 History 관리를 위한 `feature/p1-summer` 브랜치 생성
- 통합 DB의 공통 VIEW 존재 여부 확인
- `ax_user_team_login_view`, `user_round_team_view` 직접 조회 및 데이터 검증
- VIEW별 용도와 사용 범위 정리
- P2 인증·권한 / P3 DB·ERD 기준 충돌 여부 확인
- `develop` 기준 개인 브랜치 / PR / 통합 테스트 규칙 정리
- 각 담당자가 개별 로컬/DB 환경에서 먼저 검증한 뒤 통합하는 기준 정리

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

### 확인 SQL 예시
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
- 용도: 사용자-기수-팀 관계가 필요한 통합 기능의 공통 조회 기준
- 검증 결과: 존재 / 조회 / 데이터 확인 **PASS**

### `ax_user_team_login_view`
- 목적: 로그인 사용자와 팀 관련 정보를 공통 기준으로 조회하기 위한 VIEW
- 용도: 인증·권한 및 로그인 이후 사용자·팀 정보가 필요한 기능의 공통 조회 기준
- 검증 결과: 존재 / 조회 / 데이터 확인 **PASS**

## 5. P2 / P3 충돌 확인

### P2 — 인증·권한 영역
- User / Student / Role 기준
- 로그인 및 권한 처리 기준
- 공통 User / Team 조회 시 VIEW 사용 기준

### P3 — DB·ERD 영역
- DB / ERD / FK / Migration 기준
- 공통 User / Student / Team 데이터 연결 구조
- VIEW 정의 및 통합 DB 반영 기준

### P1 확인 결과
- User / Student / Team / Role 기준 비교 완료
- FK / Migration 영향 여부 확인 완료
- VIEW 사용 기준 확인 완료
- P2 인증·권한 ↔ P3 DB·ERD 충돌 여부 정리 완료

> 세부 기술 결정은 각 담당 영역의 Issue / ERD / 인증 기준을 따르고, P1은 공통 통합 기준과 충돌 여부를 관리한다.

## 6. 형상관리 및 통합 개발 규칙

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

## 7. 산출물 / 근거
- Issue: `#56 P1 — P2 인증·권한 / P3 DB·ERD 충돌 확인 및 VIEW·공통 연동 기준 정리`
- 선행 Issue: `#35 P1 — 1·2·3·4조 기능 비교 및 통합/분리 기준 확정`
- 개인 브랜치: `feature/p1-summer`
- 대상 DB: PostgreSQL `ax_evaluation`
- 검증 VIEW:
  - `public.ax_user_team_login_view`
  - `public.user_round_team_view`

## 8. 본인 검증
- 개인 브랜치 생성: **PASS**
- 두 VIEW 실제 DB 존재 확인: **PASS**
- 두 VIEW 직접 조회: **PASS**
- 조회 데이터 이상 여부 확인: **PASS**
- VIEW 용도 / 사용 기준 정리: **PASS**
- P2 / P3 충돌 여부 확인: **PASS**
- 브랜치 / PR / develop 운영 규칙 문서화: **PASS**
- Daily Deliverable 반영: **PASS**

## 9. Cross Check
- 결과: **PASS**
- 확인 내용: VIEW 검증 결과, 공통 연동 기준, P2/P3 확인 결과 및 형상관리 기준

## 10. 최종 판단
- Issue #56에서 요구한 Daily Deliverable 반영을 완료했다.
- VIEW 검증 결과와 공통 연동 규칙, 브랜치/PR 운영 기준이 문서화되었다.
- 본 산출물을 기준으로 `Daily Deliverable 반영 완료` 항목을 완료 처리한다.
