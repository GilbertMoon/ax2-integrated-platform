# ERD FINAL CHECKLIST

- 프로젝트: `ax2-integrated-platform`
- 담당: P3 김종복
- 기준일: 2026-08-31
- 기준 ERD: 2026-08-31 현재 PostgreSQL ERD
- 기준 객체 수: 69개
- 목적: 현재 생성 완료된 69개 DB 객체를 기준으로 `유지 / 통합 / 분리 / 폐기 / 신규추가` 관점에서 최종 ERD를 점검하고 후속 DB Migration 의사결정 사항을 정리한다.

## 1. 전체 판정 요약

| 구분 | 대상 수 | 핵심 판단 |
|---|---:|---|
| 유지 | 64 | 현재 구조를 TO-BE 기준으로 계속 사용 |
| 통합 | 0 | 즉시 통합할 테이블은 없음 |
| 분리 | 3 | `attendances`, `attendance_record`, `face_recognition_log`는 업무 목적상 분리 |
| 폐기 | 1 | `ax_user_team_login_view`는 `user_round_team_view`로 대체 검토 |
| 신규추가 | 4 | `student`, `inventory_transactions`, PRD template FK, 근태 이벤트 이력 등 |
| **현재 ERD 객체** | **69** | 테이블 및 View 포함 |

## 2. 핵심 테이블 점검

### 2.1 `inventories` 반영 검증

`inventories`는 현재 ERD에 존재하며 **유지** 대상으로 판정한다.

| 검증 항목 | 기대값 | ERD/DDL 확인 기준 | 상태 |
|---|---|---|---|
| 테이블 존재 | `inventories` | ERD 객체명 | ✅ 반영 |
| PK | `id UUID` | `inventories.id` | ⚠️ DDL 직접 확인 필요 |
| UUID 기본값 | `gen_random_uuid()` | PostgreSQL DDL | ⚠️ DDL 직접 확인 필요 |
| 사용자 FK | `user_id → accounts_user.id` | `fk_inventories_user` | ✅ ERD 관계 확인 |
| 아이템 FK | `item_id → items.id` | `fk_inventories_item` | ✅ ERD 관계 확인 |
| 사용자-아이템 중복 방지 | `UNIQUE(user_id,item_id)` | `uq_inventories_user_item` | ⚠️ DDL 직접 확인 필요 |
| 수량 기본값 | `quantity DEFAULT 0` | DDL | ⚠️ DDL 직접 확인 필요 |
| 수량 음수 방지 | `CHECK(quantity >= 0)` | `chk_inventories_quantity` | ⚠️ DDL 직접 확인 필요 |
| 사용자 삭제 정책 | `ON DELETE CASCADE` | `fk_inventories_user` | ⚠️ DDL 직접 확인 필요 |
| 아이템 삭제 정책 | `ON DELETE RESTRICT` | `fk_inventories_item` | ⚠️ DDL 직접 확인 필요 |

### 2.2 `inventories` 최종 DDL 기준

```sql
CREATE TABLE IF NOT EXISTS inventories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id BIGINT NOT NULL,
    item_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL DEFAULT 0,

    CONSTRAINT fk_inventories_user
        FOREIGN KEY (user_id)
        REFERENCES accounts_user(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_inventories_item
        FOREIGN KEY (item_id)
        REFERENCES items(id)
        ON DELETE RESTRICT,

    CONSTRAINT uq_inventories_user_item
        UNIQUE (user_id, item_id),

    CONSTRAINT chk_inventories_quantity
        CHECK (quantity >= 0)
);
```

> 주의: 이전에 발생한 `syntax error at or near "CONSTRAINT"`는 `CONSTRAINT` 자체의 문법 오류라는 의미가 아니다. 위 DDL은 `CREATE TABLE (...)` 내부에서 실행되어야 하며, `CONSTRAINT`만 별도 SQL 문장으로 실행하면 오류가 발생한다.

## 3. `inventories` PostgreSQL 검증 SQL

아래 SQL로 실제 DB의 제약조건을 확인한다.

```sql
SELECT tc.constraint_name, tc.constraint_type
FROM information_schema.table_constraints tc
WHERE tc.table_schema = 'public'
  AND tc.table_name = 'inventories'
ORDER BY tc.constraint_type, tc.constraint_name;
```

FK의 실제 연결 대상과 삭제 정책 확인:

```sql
SELECT
    tc.constraint_name,
    kcu.column_name,
    ccu.table_name AS referenced_table,
    ccu.column_name AS referenced_column,
    rc.delete_rule
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
  ON tc.constraint_name = kcu.constraint_name
 AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
  ON tc.constraint_name = ccu.constraint_name
 AND tc.table_schema = ccu.table_schema
JOIN information_schema.referential_constraints rc
  ON tc.constraint_name = rc.constraint_name
 AND tc.table_schema = rc.constraint_schema
WHERE tc.table_schema = 'public'
  AND tc.table_name = 'inventories'
  AND tc.constraint_type = 'FOREIGN KEY';
```

컬럼 기본값 및 NULL 여부 확인:

```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name = 'inventories'
ORDER BY ordinal_position;
```

## 4. 69개 객체 분류 기준

### 유지

현재 DB와 TO-BE ERD에서 역할이 명확한 객체는 유지한다. `inventories`도 이 기준에 해당한다.

주요 Core/업무 객체: `accounts_user`, `rounds_evaluationround`, `rounds_roundparticipant`, `teams_team`, `teams_teammembership`, `submission`, `items`, `inventories`, `house`, `placed_objects`, 평가/리뷰/결과 관련 테이블 등.

### 통합

현재 즉시 DROP 후 하나의 테이블로 합칠 객체는 없다. 특히 `accounts_user + cg_users`, `attendances + attendance_record`, `submission + submission_file` 등은 업무 목적이 다르므로 무리하게 통합하지 않는다.

### 분리

`attendances`는 학습 출석, `attendance_record`는 실제 근태, `face_recognition_log`는 얼굴인식 원천 이벤트로 분리한다.

### 폐기

`ax_user_team_login_view`는 `user_round_team_view`로 대체 후 애플리케이션 참조를 확인하고 폐기한다.

### 신규추가 후보

`student`, `inventory_transactions`, PRD Template FK, 근태 이벤트 이력 등을 요구사항 확정 후 검토한다.

## 5. 최종 확인 사항

- [x] `inventories` 테이블이 ERD에 존재
- [x] `inventories.user_id → accounts_user.id` 관계 존재
- [x] `inventories.item_id → items.id` 관계 존재
- [ ] `inventories`의 PK/UUID 기본값 실제 DB 검증
- [ ] `UNIQUE(user_id,item_id)` 실제 DB 검증
- [ ] `quantity DEFAULT 0` 실제 DB 검증
- [ ] `quantity >= 0` CHECK 실제 DB 검증
- [ ] `ON DELETE CASCADE/RESTRICT` 실제 DB 검증
- [ ] 검증 완료 후 최종 ERD 산출물과 DDL 일치 여부 확정
