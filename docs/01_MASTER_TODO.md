# MASTER TODO

- 초기 목표 완료일: **2026-09-07 (월)**
- 운영 재정비 기준일: **2026-11-19**
- 진행 원칙: **PHASE > Priority > Task > Owner > Status > 완료조건**
- 상태: `TODO / DOING / REVIEW / DONE`
- 우선순위: `MUST / SHOULD / COULD`

## PHASE 0 — 기존 시스템 확인
- [ ] 기존 4조 프로젝트 Clone 및 실행 확인 — 전체
- [ ] DB 복원 및 주요 기능 Smoke Test — P3 중심
- [ ] 기준 버전(Baseline) 고정 — P1

## PHASE 1 — 통합 설계
- [ ] 1·2·3·4조 기능/ERD 비교 — P1, P2, P3
- [ ] 공통 데이터 Owner 확정(User/Student/Team 등) — P2, P3
- [ ] 통합/분리/폐기 테이블 결정 — P3
- [ ] TO-BE ERD 초안 작성 — P3

## PHASE 2 — Core 정비
- [ ] 로그인/회원/학생/권한 기준 정리 — P2
- [ ] DB Migration 정리 — P3
- [ ] 공통 연동 기준 문서화 — P1

## PHASE 3 — 1·2·3조 순차 통합
- [ ] 1조 기능 통합 — P4
- [ ] 1조 통합 후 기존 기능 Regression 확인 — P5
- [ ] 2조 기능 통합 — P5
- [ ] 2조 통합 후 기존 기능 Regression 확인 — P5
- [ ] 3조 기능 통합 — P6
- [ ] 3조 통합 후 기존 기능 Regression 확인 — P5

## PHASE 4 — 4조 신규 기능
- [ ] 근태 모듈 설계/개발 — P2, P3 협업
- [ ] 얼굴등록/얼굴인식 기능 개발 — 별도 주담당 지정, P3/P6 협업
- [ ] 얼굴 이미지/인식 로그 저장 구조 확정 — P3
- [ ] ML 활용을 위한 데이터 항목 점검 — P1, P3

## PHASE 5 — 통합 테스트/배포
- [ ] 전체 E2E 시나리오 점검 — P5
- [ ] Windows 11 Pro 서버 환경 구성 — P6
- [ ] 서버 재부팅 후 서비스 기동 확인 — P6
- [ ] Backup/Restore 1회 검증 — P3, P6
- [ ] README/운영 문서 최신화 — P1

## 최종 완료조건
- [ ] 기존 4조 핵심 기능 정상
- [ ] 1·2·3조 핵심 기능 통합 완료
- [ ] 근태/얼굴인식 신규 기능 동작
- [ ] DB Migration 정상
- [ ] Windows 서버에서 서비스 접속 가능
- [ ] Backup/Restore 검증 완료

---

## 2026-11-19 재정비 기준

기존 Phase 0~5 체크리스트는 **초기 통합 계획의 기준선**으로 유지한다. 2026-11-19 이후 실제 진행 여부는 체크박스를 추측으로 변경하지 않고 GitHub Issue·PR·Deliverable 증거로 판정한다.

### 재정비 순서

- [ ] Open Issue 53건을 담당자별로 재분류
- [ ] 완료 증거가 있는 과거 Issue 종료
- [ ] 후속 Issue로 대체된 Issue는 successor 링크 후 종료
- [ ] 중복 Issue 정리
- [ ] Daily 계획/결과형 Issue를 Deliverable 중심 기록으로 전환
- [ ] 담당자별 ACTIVE Issue 1~2개로 축소
- [ ] 현재 ACTIVE Issue를 기준으로 MASTER TODO 상태 현행화
- [ ] Open PR #142와 관련 Issue 연결 상태 확인
- [ ] 최종적으로 README / 개인 TODO / Deliverable / Issue가 서로 같은 상태를 가리키는지 Cross Check

### 완료 판정 규칙

`DONE`은 단순 체크박스나 구두 보고가 아니라 다음 증거가 있을 때만 반영한다.

`Issue → 구현/문서 변경 → PR/Commit → 실행/테스트 → Deliverable → Cross Check`

상세 Issue 정리 기준은 `docs/ISSUE_MANAGEMENT.md`를 따른다.
