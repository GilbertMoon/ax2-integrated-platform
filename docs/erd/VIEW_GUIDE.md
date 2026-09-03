# AX2 통합 플랫폼 DB VIEW 제공 안내

## 1. 문서 목적

AX2 통합 플랫폼의 팀 간 데이터 연계를 위해 공통적으로 사용할 수 있는 PostgreSQL VIEW를 제공합니다.

이번 VIEW는 각 팀이 개별 테이블 구조를 직접 조회하지 않고, 통합 DB에서 필요한 사용자, Round 참가, 팀 소속 및 프로젝트 기간 정보를 일관된 형태로 조회할 수 있도록 하는 것을 목적으로 합니다.

현재 제공 VIEW는 다음 2개입니다.

| 구분 | VIEW | 주요 용도 | 사용 팀 |
|---|---|---|---|
| 1 | `ax_user_team_login_view` | 사용자 기본정보, 대표 이메일, Round 참가 및 팀/프로젝트 정보 조회 | 전체 조 |
| 2 | `user_round_team_view` | 사용자의 Round별 팀 소속 및 프로젝트 기간 조회 | 3조 |

> **중요:** 프로젝트 기간(`team_start`, `team_end`)은 `rounds_evaluationround`가 아니라 `project_info`에서 제공합니다. `project_info.evaluationround_id`를 통해 해당 Round와 연결합니다.

---

## 2. DB 접속 환경

| 항목 | 값 |
|---|---|
| Database | `ax_evaluation` |
| User | `ax_evaluation` |
| Host | `10.2.16.91` |
| Port | `5432` |
| Password | 별도 전달 |

> **보안 주의:** DB Password는 GitHub, 문서 저장소, 메신저 공용 채널 등에 평문으로 기록하지 않고 별도 보안 채널을 통해 전달합니다.

PostgreSQL 접속 예시:

```bash
psql -h 10.2.16.91 -p 5432 -U ax_evaluation -d ax_evaluation
```

---

## 3. 사용자 관련 VIEW

### VIEW

`public.ax_user_team_login_view`

### 목적

전체 조에서 공통적으로 사용하는 사용자 기본정보 + 대표 이메일 + Round 참가정보 + 팀 정보 + 프로젝트 기간 정보를 하나의 VIEW에서 조회할 수 있도록 제공합니다.

`DISTINCT ON (u.id)`를 사용하므로 사용자별로 최신 Round 참가정보를 1건 선택합니다. 선택 우선순위는 `evaluation_start_at DESC`, 이후 `rp.created_at DESC`입니다.

### 주요 연결 구조

```text
accounts_user
      │
      ├── account_emailaddress
      │
      └── rounds_roundparticipant
                │
                ├── rounds_evaluationround
                │
                └── teams_teammembership
                           │
                           └── teams_team
                │
                └── project_info
                       └── evaluationround_id = round_id
```

### 제공 컬럼

| 컬럼 | 설명 |
|---|---|
| `user_id` | 사용자 ID |
| `user_email` | 사용자 계정 이메일 |
| `first_name` | 이름 |
| `last_name` | 성 |
| `role` | 사용자 역할 |
| `approval_status` | 승인 상태 |
| `phone_number` | 전화번호 |
| `is_onboarded` | 온보딩 여부 |
| `profile_image` | 프로필 이미지 |
| `last_login` | 마지막 로그인 |
| `is_active` | 활성 사용자 여부 |
| `is_staff` | Staff 여부 |
| `is_superuser` | Superuser 여부 |
| `is_social_account` | 소셜 계정 여부 |
| `date_joined` | 가입일 |
| `primary_email` | 대표 이메일 |
| `participant_id` | Round 참가자 ID |
| `round_id` | Round ID |
| `display_name_snapshot` | 해당 Round 당시 표시 이름 |
| `team_id` | 팀 ID |
| `team_name` | 팀 이름 |
| `project_info_id` | 프로젝트 정보 ID |
| `team_start` | 프로젝트 시작일 (`project_info` 기준) |
| `team_end` | 프로젝트 종료일 (`project_info` 기준) |

### VIEW SQL

```sql
CREATE OR REPLACE VIEW public.ax_user_team_login_view
AS SELECT DISTINCT ON (u.id)
    u.id AS user_id,
    u.email AS user_email,
    u.first_name,
    u.last_name,
    u.role,
    u.approval_status,
    u.phone_number,
    u.is_onboarded,
    u.profile_image,
    u.last_login,
    u.is_active,
    u.is_staff,
    u.is_superuser,
    u.is_social_account,
    u.date_joined,
    ea.email AS primary_email,
    rp.id AS participant_id,
    rp.round_id,
    rp.display_name_snapshot,
    t.id AS team_id,
    t.name AS team_name,
    pi.id AS project_info_id,
    pi.team_start,
    pi.team_end
FROM accounts_user u
LEFT JOIN account_emailaddress ea
    ON ea.user_id = u.id
   AND ea."primary" = true
LEFT JOIN rounds_roundparticipant rp
    ON rp.user_id = u.id
LEFT JOIN rounds_evaluationround er
    ON er.id = rp.round_id
LEFT JOIN teams_teammembership tm
    ON tm.participant_id = rp.id
LEFT JOIN teams_team t
    ON t.id = tm.team_id
LEFT JOIN project_info pi
    ON pi.evaluationround_id = rp.round_id
ORDER BY
    u.id,
    er.evaluation_start_at DESC NULLS LAST,
    rp.created_at DESC;
```

### 조회 예시

전체 사용자:

```sql
SELECT *
FROM public.ax_user_team_login_view;
```

특정 사용자:

```sql
SELECT *
FROM public.ax_user_team_login_view
WHERE user_id = 123;
```

프로젝트 기간까지 확인:

```sql
SELECT
    user_id,
    round_id,
    team_id,
    team_name,
    project_info_id,
    team_start,
    team_end
FROM public.ax_user_team_login_view
WHERE user_id = 123;
```

---

## 4. Team History VIEW

### VIEW

`public.user_round_team_view`

### 사용 팀

**3조**

### 목적

특정 사용자가 **각 Round에서 어느 팀에 소속되어 있었는지**와 해당 Round에 연결된 **프로젝트 시작일/종료일**을 확인하기 위한 VIEW입니다.

동일한 사용자가 Round마다 다른 팀에 배정될 수 있으므로 `user_id`와 `round_id`를 기준으로 팀 소속 정보를 확인할 수 있습니다.

### 주요 연결 구조

```text
accounts_user
      │
      ▼
rounds_roundparticipant
      │
      ├──────────────► rounds_evaluationround
      │
      ├──────────────► teams_teammembership
      │                         │
      │                         ▼
      │                     teams_team
      │
      └──────────────► project_info
                         └── evaluationround_id = round_id
```

### 제공 컬럼

| 컬럼 | 설명 |
|---|---|
| `user_id` | 사용자 ID |
| `email` | 사용자 이메일 |
| `round_id` | 평가 Round ID |
| `round_title` | Round 제목 |
| `round_status` | Round 상태 |
| `participant_id` | Round 참가자 ID |
| `student_number_snapshot` | 해당 Round 당시 학번 |
| `display_name_snapshot` | 해당 Round 당시 표시 이름 |
| `team_id` | 팀 ID |
| `team_number` | 해당 Round의 팀 번호 |
| `team_name` | 팀 이름 |
| `project_info_id` | 프로젝트 정보 ID |
| `team_start` | 프로젝트 시작일 (`project_info` 기준) |
| `team_end` | 프로젝트 종료일 (`project_info` 기준) |

### VIEW SQL

```sql
CREATE OR REPLACE VIEW public.user_round_team_view
AS SELECT
    u.id AS user_id,
    u.email,
    r.id AS round_id,
    r.title AS round_title,
    r.status AS round_status,
    rp.id AS participant_id,
    rp.student_number_snapshot,
    rp.display_name_snapshot,
    t.id AS team_id,
    t.team_number,
    t.name AS team_name,
    pi.id AS project_info_id,
    pi.team_start,
    pi.team_end
FROM accounts_user u
JOIN rounds_roundparticipant rp
    ON rp.user_id = u.id
JOIN rounds_evaluationround r
    ON r.id = rp.round_id
JOIN teams_teammembership tm
    ON tm.participant_id = rp.id
JOIN teams_team t
    ON t.id = tm.team_id
LEFT JOIN project_info pi
    ON pi.evaluationround_id = r.id;
```

---

## 5. Team History VIEW 사용 방법

### 5.1 특정 사용자의 Round별 팀 조회

```sql
SELECT
    user_id,
    round_id,
    round_title,
    round_status,
    participant_id,
    student_number_snapshot,
    display_name_snapshot,
    team_id,
    team_number,
    team_name,
    project_info_id,
    team_start,
    team_end
FROM public.user_round_team_view
WHERE user_id = 123
ORDER BY round_id;
```

예상 결과:

| user_id | round_id | round_title | team_id | team_number | team_name | team_start | team_end |
|---:|---:|---|---:|---:|---|---|---|
| 123 | 1 | 1차 평가 | 10 | 1 | A팀 | 2026-08-07 | 2026-08-10 |
| 123 | 2 | 2차 평가 | 25 | 3 | B팀 | 2026-08-12 | 2026-08-20 |
| 123 | 3 | 3차 평가 | 31 | 2 | C팀 | 2026-08-24 | 2026-09-18 |

### 5.2 프로젝트 기간 기준 사용자/팀 조회

```sql
SELECT
    user_id,
    round_id,
    team_id,
    team_name,
    team_start,
    team_end
FROM public.user_round_team_view
WHERE team_start <= CURRENT_DATE
  AND team_end >= CURRENT_DATE
ORDER BY team_id, user_id;
```

> 위 조회는 현재 날짜가 프로젝트 기간에 포함되는 사용자/팀을 찾는 예시입니다. `team_start`와 `team_end`가 NULL인 경우에는 프로젝트 기간이 정의되지 않은 것으로 취급됩니다.

---

## 6. `project_info`와 Round의 관계

두 VIEW 모두 다음 관계를 사용합니다.

```text
rounds_evaluationround.id
        │
        │ 1 : N 또는 설계상 정의된 관계
        ▼
project_info.evaluationround_id
```

실제 VIEW JOIN 조건은 다음과 같습니다.

```sql
pi.evaluationround_id = rp.round_id
```

또는 `user_round_team_view`에서는:

```sql
pi.evaluationround_id = r.id
```

따라서 프로젝트 기간 정보는 `rounds_evaluationround`에 직접 저장하지 않고 `project_info`에서 관리하며, `evaluationround_id`를 통해 Round와 연결합니다.

### 프로젝트 기간 컬럼의 의미

| 컬럼 | 출처 | 의미 |
|---|---|---|
| `project_info_id` | `project_info.id` | 프로젝트 정보 식별자 |
| `team_start` | `project_info.team_start` | 프로젝트 시작일 |
| `team_end` | `project_info.team_end` | 프로젝트 종료일 |
| `evaluationround_id` | `project_info.evaluationround_id` | 연결된 Evaluation Round ID |

> **설계 원칙:** 평가 기간(`rounds_evaluationround.evaluation_start_at`, `evaluation_end_at`)과 프로젝트 기간(`project_info.team_start`, `team_end`)은 서로 다른 개념으로 취급합니다.

---

## 7. 다른 팀 개발 시 권장사항

다른 팀에서는 통합 DB의 원본 테이블을 직접 JOIN하기보다는 가능한 경우 제공된 VIEW를 사용하는 것을 권장합니다.

사용자별 팀 정보가 필요한 경우:

```sql
SELECT *
FROM public.user_round_team_view
WHERE user_id = ?;
```

사용자의 최신 로그인/대표 팀 정보가 필요한 경우:

```sql
SELECT *
FROM public.ax_user_team_login_view
WHERE user_id = ?;
```

프로젝트 기간이 필요한 경우에도 VIEW에서 제공하는 `team_start`, `team_end`를 사용합니다.

공통 데이터 연결 로직은 VIEW에서 관리하고 각 팀의 애플리케이션은 VIEW를 조회하는 방식으로 통합합니다.

---

## 8. 주의사항

- VIEW는 조회용 인터페이스입니다.
- 동일 사용자가 여러 Round에서 다른 팀에 소속될 수 있으므로 `user_id + round_id`를 주요 조회 기준으로 사용합니다.
- `student_number_snapshot`, `display_name_snapshot`은 해당 Round 당시의 참가자 정보입니다.
- `team_start`, `team_end`는 `project_info`에서 제공되는 프로젝트 기간입니다.
- `rounds_evaluationround.evaluation_start_at`, `evaluation_end_at`은 평가 기간이며 프로젝트 기간과 동일하다고 가정하지 않습니다.
- `project_info`가 존재하지 않으면 `LEFT JOIN` 특성상 `project_info_id`, `team_start`, `team_end`가 NULL로 반환됩니다.
- `user_round_team_view`는 `JOIN`을 사용하므로 참가자와 팀 멤버십 및 팀 정보가 존재하는 경우에만 결과가 반환됩니다.
- `ax_user_team_login_view`는 `LEFT JOIN`을 사용하므로 팀 또는 프로젝트 정보가 없는 사용자도 기본 사용자 정보와 함께 조회될 수 있습니다.
- `ax_user_team_login_view`는 `DISTINCT ON (u.id)`를 사용하므로 사용자당 1개의 행만 반환합니다.
- DB Password는 GitHub에 평문으로 저장하지 않습니다.

---

## 9. 2026-09-03 P3 VIEW 정의 반영

### 반영 내용

| 항목 | 내용 | 판정 |
|---|---|---|
| `ax_user_team_login_view` | `project_info` JOIN 추가 | ✅ |
| `user_round_team_view` | `project_info` JOIN 추가 | ✅ |
| `project_info_id` | 두 VIEW에 추가 | ✅ |
| `team_start` | `project_info.team_start`를 두 VIEW에서 제공 | ✅ |
| `team_end` | `project_info.team_end`를 두 VIEW에서 제공 | ✅ |
| `rounds_evaluationround`의 프로젝트 기간 컬럼 | VIEW에서 직접 사용하지 않음 | ✅ |

### 실제 DB 검증 SQL

VIEW 존재 여부:

```sql
SELECT schemaname, viewname
FROM pg_views
WHERE schemaname = 'public'
  AND viewname IN ('ax_user_team_login_view', 'user_round_team_view')
ORDER BY viewname;
```

`ax_user_team_login_view` 조회 검증:

```sql
SELECT
    user_id,
    round_id,
    team_id,
    team_name,
    project_info_id,
    team_start,
    team_end
FROM public.ax_user_team_login_view
LIMIT 10;
```

`user_round_team_view` 조회 검증:

```sql
SELECT
    user_id,
    round_id,
    round_title,
    team_id,
    team_number,
    team_name,
    project_info_id,
    team_start,
    team_end
FROM public.user_round_team_view
LIMIT 10;
```

컬럼 구조 확인:

```sql
SELECT
    table_schema,
    table_name,
    column_name,
    data_type,
    ordinal_position
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('ax_user_team_login_view', 'user_round_team_view')
ORDER BY table_name, ordinal_position;
```

> 위 SQL은 실제 PostgreSQL 접속 환경에서 실행하여 VIEW 존재 여부와 조회 결과를 최종 확인할 수 있습니다.

---

## 10. 요약

| VIEW | 목적 | 프로젝트 기간 | 대상 |
|---|---|---|---|
| `public.ax_user_team_login_view` | 사용자 기본정보 및 최신 Round/팀 정보 | `project_info.team_start/end` | 전체 조 |
| `public.user_round_team_view` | 사용자의 Round별 팀 소속 및 프로젝트 기간 | `project_info.team_start/end` | 3조 |

두 VIEW 모두 다음 구조로 프로젝트 기간을 제공합니다.

```text
rounds_evaluationround
        │
        │ id = evaluationround_id
        ▼
project_info
   ├── team_start
   └── team_end
```

`user_round_team_view`는 다음 질문에 답하기 위한 VIEW입니다.

> **이 사용자는 각 Round에서 어느 팀에 소속되어 있었으며, 해당 프로젝트의 기간은 언제인가?**
