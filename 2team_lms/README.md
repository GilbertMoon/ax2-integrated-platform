# 2조 LMS 통합 검증 결과 — 2026-09-08

브랜치: integration/team2-lms-full. 원본: KANT-2/assignment-lms develop, e8f21d66e1c1afe96b664ac8b7485cbaf7d0dbd7.

## 반영 내용
- 2team_lms/lms_modules에 원본 학생·튜터·GitHub 기능을 이식하고 기존 lms/lms_client 이동을 유지했다.
- Core 로그인 및 User/Team/Round 참조를 유지하며 LMS 업무 데이터는 assignment_lms DB로 라우팅한다. LMS 트랜잭션과 커밋 후 GitHub 처리도 같은 DB에 연결했다.
- 강의·과제·제출·재제출·튜터 평가·회차 마감·AI/GitHub 서비스 코드를 연결했다. 템플릿과 정적 파일 경로를 분리했다.
- Core 메뉴에 LMS 진입 링크, LMS 메뉴에 Core 복귀 링크를 추가했다. GitHub 콜백 /github/callback/을 유지했다.
- Slack 전송은 Core 공통 서비스에 위임하며 전송 실패로 제출이 실패하지 않도록 했다.
- 기존 LMS 미디어 폴더를 재사용한다. Core Django 버전을 유지하고 필요한 패키지 파일만 추가했다.
- 승인된 results.0008, rounds.0007, github_sync.0002를 적용했다. 기존 데이터 삭제·초기화와 migration 이력 위조는 하지 않았다. 기존 Core VIEW 2개가 유지됨을 확인했다.

## 검증
| 항목 | 사전 조건/방법 | 예상 | 실제 | 판정 |
|---|---|---|---|---|
| Core 및 LMS 회귀 | 독립 메모리 DB 2개, 외부 HTTP 차단 | 기존 동작 및 통합 동작 유지 | 463개 중 462 통과, 기존 skip 1 | PASS/일부 SKIP |
| 제출·재제출·평가 저장 | 테스트 DB, 사용자/팀 VIEW 조회 모의 처리 | 사용자 ID 유지, 평가 후 재제출 제한 | 기대값 충족 | PASS |
| 실제 DB 화면 조회 | 읽기 전용 트랜잭션, 학생/튜터 RequestFactory 요청 | 정상 렌더링/이동 | 12개 화면 200/302 | PASS |
| Django 검사 | 실제 설정 check | 오류 없음 | 오류 없음 | PASS |
| DB 적용 확인 | migration 이력·컬럼·VIEW 읽기 조회 | 승인한 변경 적용, VIEW 유지 | 확인됨 | PASS |
| Windows 설정 테스트 | config.tests의 Unix 0600 권한 기대 검사 | 0600 | Windows 0666으로 실패 | FAIL |
| 실제 외부 연동 | GitHub OAuth/게시, Slack 발송, Gemini 호출 | 별도 실제 계정 검증 필요 | 외부 호출 안 함 | 미실행 |

화면 검증은 브라우저 시각 검증이나 실제 사용자 로그인 전체 흐름을 대신하지 않는다. 원본의 모든 테스트를 그대로 통과한 것은 아니며, 통합 환경에 맞춘 선정 테스트를 실행했다. 테스트 실행은 별도 Python 3.12 QA 환경이다. 사용자 Python 3.14 실행 파일은 도구 실행 제한으로 직접 검증하지 못했다.

## 다시 실행
프로젝트 루트의 PowerShell에서:

```powershell
.\.venv\Scripts\python.exe -B manage.py test accounts teams rounds results reviews notifications lms.tests lms_modules.tutor.tests lms_modules.github_sync.tests --settings=config.lms_test_settings --noinput
```

이 테스트 설정은 메모리 DB를 사용하고 requests HTTP 호출을 차단한다. 운영 서버에는 사용하지 않는다.

## 향후 DB 작업 주의
기존 LMS DB에는 독립 프로젝트의 admin/auth migration 이력이 있으므로 통합 설정으로 assignment_lms 전체 migrate를 실행하면 이력 불일치가 발생할 수 있다. LMS 전용 migration_settings를 만들었다. 추후 변경 때 먼저 다음처럼 계획을 확인하고 영향 범위를 검토한다:

```powershell
.\.venv\Scripts\python.exe -B manage.py migrate --plan --pythonpath 2team_lms --settings=lms_modules.migration_settings
```

이 설정의 default는 LMS DB를 가리킨다. runserver에는 절대 사용하지 않는다. 이번 3개 변경은 이미 적용했으므로 재적용할 필요 없다.

## 남은 확인
- 사용자 기존 Python 3.14 환경으로 서버 재시작 후 Core 로그인 → LMS 학생/튜터 화면 확인.
- 실제 GitHub OAuth, Slack 발송, Gemini 채점은 테스트 계정·대상과 발송 범위를 정한 뒤 검증.
- 기존 Windows 파일 권한 테스트 실패는 이번 기능 코드와 분리해 처리.
- commit/push는 하지 않았다. 기존 사용자 stash도 유지했다.
