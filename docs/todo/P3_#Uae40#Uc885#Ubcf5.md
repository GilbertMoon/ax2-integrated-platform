# P3 김종복 TODO

- 역할: **ERD / DB / Migration / Backup·Restore**
- 목표 완료일: **2026-09-07 (월)**

## PHASE 0 — DB 기준 확보
### MUST
- [ ] 기존 4조 DB 구조 확인
- [ ] 로컬 DB 복원 테스트
- [ ] 현재 Migration 상태 확인
- [ ] Baseline DB Backup 확보

## PHASE 1 — 통합 ERD
### MUST
- [ ] 1·2·3·4조 ERD 비교
- [ ] 유지 / 통합 / 분리 / 폐기 테이블 분류
- [ ] 공통 FK 기준 정리(User/Student/Team 등)
- [ ] TO-BE ERD 초안 작성
- [ ] 1조 학습 출석과 4조 근태를 별도 Domain으로 반영

## PHASE 2 — DB/Migration 정비
### MUST
- [ ] 필요한 모델 변경사항 정리
- [ ] Migration 생성 및 적용 테스트
- [ ] FK/Unique/NULL 제약조건 점검
- [ ] 운영 DB 직접 ALTER 없이 Migration 기준 유지

## PHASE 4 — 근태/얼굴인식 DB
### MUST
- [ ] 근태 테이블 설계
- [ ] 얼굴 등록/이미지/인식 로그 구조 설계
- [ ] 학생 FK 연결
- [ ] 이미지 경로, 촬영시각, 인식 결과, confidence 저장 항목 검토
- [ ] ML 활용을 위한 실제 정답값/검증값 저장 가능 여부 검토

## PHASE 5 — 운영 검증
### MUST
- [ ] Windows 서버 DB Migration 적용 확인
- [ ] Backup/Restore 1회 실제 검증
- [ ] DB 변경 이력 문서화

## DONE 기준
- TO-BE ERD가 최신 상태임
- 모든 DB 변경이 Migration으로 재현 가능함
- 근태/얼굴인식 데이터 구조가 확정됨
- Backup/Restore가 실제로 성공함
