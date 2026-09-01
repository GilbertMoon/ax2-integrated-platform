# 2026-08-28 DB Migration 준비 및 공통 VIEW 정리

## 1. 목적
- 4개 조의 DB 구조를 통합 기준에 맞춰 정리하고, PostgreSQL Migration을 안전하게 진행하기 위한 기준을 마련한다.
- 공통 User / Round / Student / Team 관계를 명확히 하고, 사용자별 Round 및 Team History를 조회할 수 있는 VIEW를 제공한다.

## 2. 오늘 수행 내용
- 4개 조 ERD를 비교하여 공통 Core 데이터와 조별 도메인 데이터의 유지·통합·분리 방향을 정리했다.
- 공통 User Owner를 `accounts_user`로 정리했다.
- Round별 학생 정보를 `rounds_roundparticipant`로 관리하는 구조를 정리했다.
- Team Owner를 `teams_team`으로 정리하고 `teams_teammembership`를 통해 Round Participant와 Team을 연결하는 구조를 확정했다.
- 사용자와 Round별 Team 이력을 조회하기 위한 `user_round_team_view`를 설계했다.
- 전체 조에서 사용할 사용자/팀 조회용 `ax_user_team_login_view`를 설계했다.
- PostgreSQL DB Migration 전 백업 및 Migration 절차를 정리했다.
- TO-BE ERD 산출물 위치를 `docs/erd/TO_BE_ERD.png`로 정리했다.

## 3. 결과
- 공통 데이터 Owner를 다음과 같이 정리했다.
  - User: `accounts_user`
  - Student / Round Participant: `rounds_roundparticipant`
  - Team: `teams_team`
  - Team Membership: `teams_teammembership`
- 사용자별 Round별 Team History를 다음 관계로 조회할 수 있도록 했다.
  - `accounts_user → rounds_roundparticipant → teams_teammembership → teams_team`
- 공통 VIEW 2종을 제공 대상으로 확정했다.
  - `public.ax_user_team_login_view`
  - `public.user_round_team_view`
- DB Migration은 Backup → 구조/데이터 Migration → 제약조건 적용 → VIEW 적용 순으로 진행하는 기준을 정리했다.
- DB 백업 파일은 GitHub에 직접 업로드하지 않고 별도 안전한 저장소에 보관하는 방향으로 정리했다.

## 4. 산출물 / 근거
- Issue: [#16 — DB Migration 준비 및 공통 VIEW 정리](https://github.com/GilbertMoon/ax2-integrated-platform/issues/16)
- ERD 비교 및 설계 문서:
  - [TO-BE ERD 초안 범위 정의](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/TO_BE_ERD_DRAFT.md)
  - [1·2·3·4조 ERD 비교표](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/ERD_COMPARISON_4TEAMS.md)
- 관련 ERD 산출물:
  - [TO-BE ERD — PNG](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/TO_BE_ERD.png)
  - [TO-BE ERD — Mermaid](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/TO_BE_ERD.mmd)
  - [VIEW Guide — ax_user_team_login_view / user_round_team_view](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/VIEW_GUIDE.md)

## 5. 검증 방법
1. Django 프로젝트에서 `python manage.py check`를 실행한다.
2. `python manage.py showmigrations`로 현재 Migration 적용 상태를 확인한다.
3. `python manage.py makemigrations`로 Model과 Migration의 차이를 확인한다.
4. PostgreSQL DB에서 Core 테이블 및 FK 관계를 확인한다.
5. `ax_user_team_login_view`, `user_round_team_view`의 존재 여부와 조회 결과를 확인한다.
6. 실제 Migration이 필요한 경우 Backup 후 개발/검증 DB에 적용하고 `showmigrations`로 재확인한다.

## 6. 2026-09-01 Migration 점검 결과

### 실행 결과

```text
python manage.py check
System check identified no issues (0 silenced).

python manage.py showmigrations
현재 출력된 모든 Migration이 [X] 상태

python manage.py makemigrations
No changes detected
```

### 판정

**Django Migration 점검 PASS**

- Django System Check: PASS
- 현재 표시된 Migration 적용 상태: PASS
- 미적용 Migration: 없음
- 신규 Migration 생성: 없음
- 신규 Migration SQL 검토: 신규 Migration이 없어 대상 없음

따라서 2026-09-01 현재 Model 변경에 따른 추가 Migration은 필요하지 않은 상태이다.

## 7. 2026-09-01 VIEW 검증 결과

문서상 VIEW SQL 및 JOIN 구조는 확인되었다. 그러나 현재 확보된 실행 결과에는 PostgreSQL에서 두 VIEW를 실제 `SELECT`한 결과가 포함되어 있지 않으므로 실제 DB 존재/조회 검증은 완료로 판정하지 않는다.

| VIEW | 문서 정의 | 실제 DB 존재 | 실제 조회 | 판정 |
|---|---|---|---|---|
| `public.ax_user_team_login_view` | 확인 | 미확인 | 미확인 | ⚠️ 후속 검증 |
| `public.user_round_team_view` | 확인 | 미확인 | 미확인 | ⚠️ 후속 검증 |

## 8. 2026-09-01 DB Migration 실행 결과

이번 실행에서 `makemigrations` 결과가 `No changes detected`였으므로 새로 생성할 Migration이 없었다. 따라서 신규 Migration에 대한 `migrate` 및 `sqlmigrate` 실행 결과는 생성되지 않았다.

또한 현재 문서 갱신 시점에는 PostgreSQL Backup 완료 및 실제 개발/검증 DB `migrate` 실행 결과도 확보되지 않았다.

따라서 본 산출물에서는 **Migration 점검은 PASS**, **실제 DB Migration 실행은 후속 작업**으로 명확히 구분한다.

## 9. 산출물 업데이트

- `docs/erd/ERD_FINAL_CHECKLIST.md`
  - 2026-09-01 Django Migration 점검 결과 반영
  - ERD 69개 테이블 / FK 검증 PASS 유지
- `docs/erd/VIEW_GUIDE.md`
  - 2026-09-01 VIEW 실제 DB 검증 상태 반영
  - 실제 SELECT 결과 확보 전까지 미검증으로 관리
- `docs/deliverables/P3_김종복/2026-08-28_DB_Migration_준비.md`
  - Migration 점검 및 VIEW 검증 상태 업데이트
- `docs/deliverables/P3_김종복/2026-09-01_Migration_SQL_검토_결과.md`
  - 명령 실행 결과와 SQL 검토 판단 기록

## 10. 미해결 / 다음 작업
- [ ] Migration 전 DB Backup 확인
- [ ] 실제 PostgreSQL 스키마와 ERD 대조
- [ ] Core FK 및 고아 FK 검증
- [ ] `public.ax_user_team_login_view` 존재/조회 검증
- [ ] `public.user_round_team_view` 존재/조회 검증
- [ ] 필요 시 기존 Migration의 `sqlmigrate` SQL 검토
- [ ] 개발/검증 DB에서 필요한 Migration 적용
- [ ] `showmigrations` 최종 재확인
- [ ] 검증 결과를 Issue #54에 완료보고

## 11. 완료보고 기준

```text
[완료보고 - P3 김종복]
완료 여부: 완료 / 부분완료 / 미완료

1. Branch
- Branch: feature/p3-jb
- Commit:

2. Migration
- makemigrations: No changes detected
- sqlmigrate 검토: 신규 Migration 없음
- migrate 적용: 후속 DB 검증 단계
- showmigrations: 현재 표시 Migration 모두 [X]

3. DB 정합성
- Core FK:
- 고아 FK:
- 주요 데이터 건수 비교:
- 중복 데이터:

4. VIEW 검증
- user_round_team_view: 실제 DB 검증 필요
- ax_user_team_login_view: 실제 DB 검증 필요

5. 산출물
- 변경 문서: ERD_FINAL_CHECKLIST.md / VIEW_GUIDE.md / 본 문서
- SQL/검증 결과: 2026-09-01_Migration_SQL_검토_결과.md

6. Blocker / 후속 Action
- 실제 PostgreSQL Backup 및 DB Schema/VIEW 검증 필요
```
