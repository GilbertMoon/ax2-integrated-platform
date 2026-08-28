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
- 관련 문서:
  - [TO-BE ERD — PNG](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/TO_BE_ERD.png)
  - [TO-BE ERD — Mermaid](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/TO_BE_ERD.mmd)
  - [VIEW Guide — ax_user_team_login_view / user_round_team_view](https://github.com/GilbertMoon/ax2-integrated-platform/blob/main/docs/erd/VIEW_GUIDE.md)

## 5. 검증 방법
1. PostgreSQL `ax_evaluation` DB에서 `accounts_user`, `rounds_roundparticipant`, `teams_teammembership`, `teams_team` 테이블이 존재하는지 확인한다.
2. `user_round_team_view`를 조회하여 특정 `user_id`의 Round별 Team 정보가 반환되는지 확인한다.
3. 예상되는 정상 결과는 동일 사용자의 Round별 `round_id`, `round_title`, `team_id`, `team_number`, `team_name`이 각각 연결되어 조회되는 것이다.

## 6. 본인 검증
- 결과: PASS
- 확인 내용:
  - 공통 User / Student / Team 관계 및 Team History 조회 구조를 검토했다.
  - `user_round_team_view`의 JOIN 관계가 `accounts_user → rounds_roundparticipant → teams_teammembership → teams_team` 구조와 일치하는 것을 확인했다.
  - TO-BE ERD 파일을 `docs/erd/TO_BE_ERD.png` 위치에 반영했다.

## 7. Cross Check
- 검증자: 미정
- 결과: FAIL
- 확인 내용: 다른 담당자의 Cross Check는 아직 수행되지 않았다.
- 보완사항: P1/P2 또는 관련 담당자가 공통 Owner/FK 및 VIEW 구조를 Cross Check한 후 결과를 갱신한다.

## 8. 미해결 / 다음 작업
- 남은 일:
  - 실제 DB Migration 실행
  - Migration 전/후 데이터 정합성 검증
  - 공통 VIEW SQL을 DB에 적용
  - VIEW 접근 권한 및 사용 방식 확정
  - Cross Check 수행
- 이유:
  - 현재 단계에서는 통합 구조 및 Migration 준비가 중심이며, 실제 운영 DB Migration은 별도 실행 단계가 필요하다.
- 다음 담당자: P3 김종복 및 관련 DB 담당자
- 다음 작업: PostgreSQL 백업 완료 후 Migration 대상 모델 및 데이터 매핑을 적용하고, Migration 이후 VIEW를 생성하여 Team History 조회를 검증한다.
