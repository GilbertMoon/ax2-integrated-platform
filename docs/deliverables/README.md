# Daily Deliverables Guide

## 제출 원칙
오늘부터 모든 담당자는 **매일 작업 종료 전** `docs/deliverables/P번호/` 폴더에 당일 산출물을 Markdown 파일로 제출합니다.

산출물은 작성자 본인만 이해하는 메모가 아니라, **다른 팀원이 처음 읽어도 작업 목적·수행 내용·결과·검증 방법을 이해할 수 있는 보고서 형태**로 작성합니다.

### 파일명 규칙
`YYYY-MM-DD_업무명.md`

예시:
- `2026-08-28_baseline_report.md`
- `2026-08-28_user_student_role_analysis.md`
- `2026-08-28_db_baseline_report.md`
- `2026-08-28_lms_analysis.md`

### 작성 기준
각 산출물에는 최소한 아래 내용을 포함합니다.

- 작업 목적
- 실제 수행 내용
- 최종 결과
- 관련 Issue / PR / Commit / 문서
- 다른 사람이 확인할 수 있는 검증 방법
- 본인 검증 결과
- Cross Check 결과
- 미해결 사항
- 다음 작업

## 제출 위치
- P1: `docs/deliverables/P1/`
- P2: `docs/deliverables/P2/`
- P3: `docs/deliverables/P3/`
- P4: `docs/deliverables/P4/`
- P5: `docs/deliverables/P5/`
- P6: `docs/deliverables/P6/`

## 매일 제출 순서
1. 오늘 TODO 확인
2. 업무 수행
3. 결과를 담당자 폴더의 MD 파일로 작성
4. 관련 Issue / PR / Commit / 문서 경로 기록
5. 본인 검증
6. 다른 담당자 Cross Check
7. 보완사항 반영
8. 검증 통과 후 GREEN 처리
9. 필요한 경우 Notion에 GitHub 산출물 링크 연결

## GREEN 기준
아래 조건을 **모두** 만족해야 GREEN으로 처리합니다.

- [ ] 당일 TODO가 완료되었다.
- [ ] GitHub에 당일 산출물 파일이 존재한다.
- [ ] 다른 사람이 문서만 읽어도 목적과 결과를 이해할 수 있다.
- [ ] 재현 또는 확인 방법이 작성되어 있다.
- [ ] 관련 Issue / PR / Commit / 문서가 연결되어 있다.
- [ ] 본인 검증이 PASS다.
- [ ] 다른 담당자의 Cross Check가 PASS다.
- [ ] 필요한 경우 Notion에도 GitHub 산출물 링크가 반영되어 있다.

> 단순 체크박스 완료, 구두 보고, 로컬 파일만 존재하는 상태는 GREEN으로 처리하지 않습니다.

## 공통 산출물 형식
```md
# [날짜] [업무명]

## 1. 목적
- 왜 이 작업을 했는지

## 2. 오늘 수행 내용
- 실제로 한 작업

## 3. 결과
- 확인된 결과
- 결정된 사항

## 4. 산출물 / 근거
- Issue:
- PR:
- Commit:
- 관련 문서:

## 5. 검증 방법
1. 다른 사람이 확인할 첫 번째 단계
2. 두 번째 단계
3. 예상되는 정상 결과

## 6. 본인 검증
- 결과: PASS / FAIL
- 확인 내용:

## 7. Cross Check
- 검증자:
- 결과: PASS / FAIL
- 확인 내용:
- 보완사항:

## 8. 미해결 / 다음 작업
- 남은 일:
- 이유:
- 다음 담당자:
- 다음 작업:
```

## 운영 기준
- GitHub의 `docs/deliverables/`를 **산출물 기준 원본(Source of Truth)** 으로 사용합니다.
- Notion에는 산출물 내용을 별도로 다시 관리하기보다 GitHub 산출물 링크를 연결하는 것을 기본으로 합니다.
- Issue는 업무 진행을 추적하고, 실제 완료 결과는 해당 날짜의 Deliverable 문서에서 확인합니다.

---

## 2026-11-19 보강 — Issue와 Daily Deliverable의 역할 분리

과거에는 Daily 계획·Daily 결과도 GitHub Issue로 생성되어 Open Issue가 누적되었다. 이후에는 다음 기준으로 역할을 분리한다.

### Issue를 만드는 경우

- 여러 Commit/PR에 걸칠 수 있는 실제 기능 또는 버그
- 다른 담당자 Review/Cross Check가 필요한 작업
- Blocker, 의사결정, 외부 의존성이 있는 작업
- 완료 조건을 추적해야 하는 통합/배포/QA 작업

### Issue를 만들지 않는 경우

- 오늘 할 일 목록
- 단순 작업일지
- 이미 Active Issue 안에서 수행하는 세부 단계
- 완료 결과 보고만을 위한 기록

위 항목은 해당 날짜의 Deliverable 문서에 기록하고, 관련 Active Issue가 있으면 번호만 연결한다.

### 권장 기록 흐름

`Active Issue → 작업 수행 → PR/Commit → Daily Deliverable → Cross Check → Issue Close`

같은 목적의 Daily Issue를 날짜별로 반복 생성하지 않는다.
