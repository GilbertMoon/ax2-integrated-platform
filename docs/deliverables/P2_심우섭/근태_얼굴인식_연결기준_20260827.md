# 근태·얼굴인식 연결 기준

작성자: P2 심우섭 | 작성일: 2026-08-28
※ 이 문서는 오늘 확정된 "기준"만 담고 있으며, 실제 구현은 다음 단계에서 진행

## 1. 근태 데이터 연결 기준
- 근태 데이터는 `accounts_user.id`(공통 Master ID)를 참조하도록 연결 (student_number 대신 내부 id 기준으로 확정)
- 1조의 학습 출석(코딩실습 참여 여부)과 4조의 실제 근태(오프라인 출결)는 **별도 데이터로 유지** — 서로 섞이지 않음
- 참고: `rounds_roundparticipant`는 평가 Round 참가 이력용 테이블이며 근태와는 무관 — 근태는 항상 `accounts_user.id` 기준

## 2. 얼굴인식 연결 기준
- 얼굴인식 결과는 `accounts_user.profile_image` 필드와 `accounts_user.id`를 기준으로 매칭
- **매칭(내부)**: 얼굴인식 결과 ↔ `accounts_user.id`로 시스템 내부에서 정확히 매칭
- **표시(화면)**: 튜터 화면에는 id 대신 `first_name` + `last_name`으로 조회해 이름으로 보여줌 — 사용자는 숫자 id를 볼 일 없음
- 저장 방식(원본 사진 vs 임베딩 벡터)은 아직 미정 상태 — 별도 결정 필요

## 3. 권한 기준
- 근태 조회/수정 권한은 `role='tutor'`인 계정에만 부여
- 학생 본인은 자신의 근태만 조회 가능 여부는 추후 확정 필요

## 4. student_number 관련 결정 사항
- ~~student_number 값이 비어있어 선행 작업 필요~~ → **student_number 대신 accounts_user.id로 매칭하는 방식으로 확정**, 학번 데이터를 별도로 채울 필요 없음
- 향후 다른 조에서 학번 기준 기능이 필요해지면 그때 별도로 student_number를 채우는 