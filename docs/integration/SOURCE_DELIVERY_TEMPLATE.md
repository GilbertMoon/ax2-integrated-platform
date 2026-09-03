# Source Delivery Template

1·2·3조 소스 전달 시 아래 항목을 함께 작성해 주세요.

이 양식은 4조 통합 시 기준 버전, 변경 범위, DB/패키지/환경설정 영향, 테스트 결과를 빠르게 확인하기 위한 공통 제출 기준입니다.

## 기본 정보

- Team:
- Base Branch:
- Base Commit SHA:
- Work Branch:
- Latest Commit SHA:

## Changed Files

- 

## Migration

- 변경 여부: 있음 / 없음
- 관련 Migration 파일:
- 적용/검증 결과:

## requirements

- 변경 여부: 있음 / 없음
- 추가/변경 패키지:

## Environment Variables

- 추가 여부: 있음 / 없음
- 필요한 변수명:

> 실제 비밀값(API Key, Token, Password, Webhook URL 등)은 GitHub에 작성하지 않습니다.

## Test Results

- `python manage.py check`:
- Migration 확인:
- 기능 테스트:
- 기타 테스트:

## 전달 전 확인

- [ ] 현재 작업 코드가 Work Branch에 commit/push 되어 있음
- [ ] Base Branch와 Base Commit SHA를 확인함
- [ ] Latest Commit SHA를 확인함
- [ ] 변경 파일 목록을 작성함
- [ ] Migration 여부를 확인함
- [ ] requirements 변경 여부를 확인함
- [ ] 추가 환경변수 여부를 확인함
- [ ] 테스트 결과를 작성함

## 통합 원칙

- 1·2·3조는 `develop`에 직접 commit/merge하지 않습니다.
- 각 조는 본인 작업 Branch에 코드 commit/push 후 위 정보를 4조에 전달합니다.
- 4조는 전달받은 Branch/Commit을 기준으로 `integration/teamX-*` 브랜치에서 통합 및 검증합니다.
- Migration / Regression / Cross Check 완료 후 4조가 `develop` 대상으로 PR을 생성합니다.
