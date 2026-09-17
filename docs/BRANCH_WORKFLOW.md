# AX2 통합 플랫폼 브랜치 운영 정책

작성일: 2026-08-31  
최종 수정: 2026-09-01

## 1. 목적

AX2 통합 플랫폼의 소스 변경을 안전하게 관리하고, 1·2·3조에서 개발한 기능을 기존 4조 Core에 순차적으로 통합하기 위한 브랜치 및 Pull Request 운영 기준을 정의한다.

현재 프로젝트는 여러 조의 독립 프로젝트를 하나의 통합 플랫폼으로 결합하는 **PHASE 3 소스 통합 단계**이다.

따라서 현재 통합 기간에는 일반적인 공동 개발 방식과 달리 **1·2·3조의 직접 Pull Request 생성을 제한하고, 4조가 통합 작업과 Pull Request / Merge를 관리한다.**

---

## 2. 기준 Repository / Branch

```text
Repository: GilbertMoon/ax2-integrated-platform
통합 기준 Branch: develop
최종 안정 Branch: main
```

- `develop`: 1·2·3조 코드의 통합 기준 및 통합 테스트 Branch
- `main`: 통합 테스트가 끝난 최종 안정 버전 Branch
- 1·2·3조는 `develop`을 Clone 또는 Pull하여 **로컬 개발/검증 기준**으로 사용한다.
- 1·2·3조는 `develop` 또는 `main`에 직접 Push하지 않는다.

---

## 3. 역할 구분

| 구분 | 역할 |
|---|---|
| 1조 | 1조 기능 개발 및 로컬 검증 |
| 2조 | LMS 등 2조 기능 개발 및 로컬 검증 |
| 3조 | PRD/AI 등 3조 기능 개발 및 로컬 검증 |
| 4조 | Core 관리, 전달 코드 검토, 통합, PR, Merge, Regression Test |
| `develop` | 통합 기준 및 통합 검증 |
| `main` | 최종 안정/배포 기준 |

---

## 4. 브랜치 역할

| 브랜치 | 역할 | 운영 주체 |
|---|---|---|
| `develop` | 기능 통합 및 통합 테스트 | 4조 관리 |
| `main` | 최종 안정/배포 기준 | 4조 관리 |
| `feature/*` | 4조 내부 기능/문서 개발 | 4조 |
| `integration/team1-*` | 1조 코드 통합 | 4조 담당자 |
| `integration/team2-*` | 2조 코드 통합 | 4조 담당자 |
| `integration/team3-*` | 3조 코드 통합 | 4조 담당자 |
| 1·2·3조 Local Branch | 각 조 로컬 개발/검증 | 각 조 로컬 전용 |

---

## 5. PHASE 3 핵심 운영 원칙

### 1·2·3조

1. `develop` 최신 소스를 Clone/Pull한다.
2. 로컬에서 별도 작업 Branch를 만든다.
3. 자신의 기능을 개발하거나 수정한다.
4. 자신의 로컬 환경에서 실행 및 기능 테스트를 수행한다.
5. 변경 파일, Base Commit, Migration, Dependency, 환경변수, 테스트 결과를 정리한다.
6. 변경사항을 각 조별 4조 통합 담당자에게 전달한다.
7. **GilbertMoon/ax2-integrated-platform에 직접 Pull Request를 생성하지 않는다.**
8. `develop`, `main`에 직접 Push하지 않는다.

### 4조

1. 각 조에서 전달받은 변경사항을 검토한다.
2. Core 영역 및 DB 영향 여부를 확인한다.
3. 조별 Integration Branch를 생성한다.
4. 전달받은 코드를 Integration Branch에 반영한다.
5. 기능 테스트, Migration 검토, Regression Test를 수행한다.
6. 검증 완료 후 **4조가 `develop` 대상 Pull Request를 생성한다.**
7. Review / Cross Check 후 `develop`에 Merge한다.
8. 전체 통합 안정화 후 `develop → main` Pull Request를 진행한다.

---

## 6. 1·2·3조가 직접 PR을 생성하지 않는 이유

일반적인 개발 단계에서는 개발자가 직접 PR을 생성하는 방식이 일반적이다.

하지만 현재 AX2 프로젝트는 독립적인 기능 개발 단계가 아니라 **여러 프로젝트를 기존 4조 Core에 순차 통합하는 단계**이다.

### 6.1 Core 파일 충돌 방지

여러 조가 동시에 영향을 줄 수 있는 공통 영역이 존재한다.

```text
accounts/
teams/
rounds/
reviews/
results/
config/
templates/
static/
requirements.txt
Migration
공통 VIEW
```

각 조가 서로 다른 시점의 `develop`을 기준으로 직접 PR을 생성하면 동일 파일에 다른 변경이 겹칠 수 있다.

### 6.2 공통 데이터 중복 방지

통합 프로젝트의 공통 기준은 다음과 같다.

```text
User → accounts_user
Role → accounts_user.role
Team → teams_team
Round → rounds_evaluationround
Round Participant → rounds_roundparticipant
```

1·2·3조가 기존 프로젝트의 User / Student / Team 구조를 그대로 PR에 포함하면 통합 Core와 중복되는 구조가 다시 유입될 수 있다.

### 6.3 Migration 충돌 방지

각 조에서 개별적으로 Migration을 생성/반영하면 다음 문제가 발생할 수 있다.

- Migration Dependency 충돌
- 동일 Table / Column 중복 생성
- FK 불일치
- Unique / Index 충돌
- 기존 데이터 손상 가능성

따라서 DB 변경은 4조와 DB 담당자가 최종 검토한 후 통합한다.

### 6.4 통합 순서 유지

현재 기본 통합 순서는 다음과 같다.

```text
4조 Core
↓
1조 통합
↓
Regression Test
↓
2조 통합
↓
Regression Test
↓
3조 통합
↓
Regression Test
```

각 조가 독립적으로 PR을 생성하면 이 통합 순서와 기준 Commit 관리가 어려워진다.

### 6.5 통합 책임 주체 명확화

각 조는 자신의 기능이 정상 동작하는지 확인할 책임이 있다.

하지만 다음 전체 영향은 4조가 확인한다.

```text
로그인 / 회원 / 권한
Team / Round
공통 DB / VIEW
Migration
Core 기능
각 조 기능 연결
Regression Test
```

따라서 `develop`에 반영되는 변경사항은 4조의 통합 검토를 거친 변경으로 관리한다.

---

## 7. 1·2·3조 표준 작업 흐름

```text
develop 최신화
        ↓
Local Branch 생성
        ↓
개발 / 수정
        ↓
로컬 실행
        ↓
기능 테스트
        ↓
변경사항 정리
        ↓
4조 담당자에게 전달
```

### 최초 Clone

```bash
git clone https://github.com/GilbertMoon/ax2-integrated-platform.git
cd ax2-integrated-platform
git checkout develop
git pull origin develop
```

이미 Clone한 경우:

```bash
git checkout develop
git pull origin develop
```

### 로컬 작업 Branch 예시

```bash
git checkout -b local/team1-garden
```

```bash
git checkout -b local/team2-lms
```

```bash
git checkout -b local/team3-prd
```

위 Branch는 **로컬 개발 및 변경 추적용**이다.

현재 PHASE 3에서는 이 Branch에서 통합 저장소로 PR을 생성하지 않는다.

---

## 8. Base Commit SHA 기록

각 조는 작업 시작 시 반드시 기준 Commit을 기록한다.

```bash
git rev-parse HEAD
```

전달 예시:

```text
Base Branch: develop
Base Commit: abc123456789...
```

Base Commit을 기록하는 이유는 4조가 해당 변경이 **어느 시점의 develop을 기준으로 만들어졌는지** 확인하기 위해서다.

1조가 통합된 뒤 `develop`이 변경되면 2조/3조의 Base Commit과 최신 `develop` 사이에 차이가 발생할 수 있으므로 실제 통합 직전에 다시 비교한다.

---

## 9. 로컬 검증 기준

각 조는 코드 전달 전 최소 다음 내용을 확인한다.

```text
[ ] 최신 develop 기준에서 작업 시작
[ ] 서버 실행 가능
[ ] python manage.py check PASS
[ ] 자신의 핵심 기능 정상 동작
[ ] 기존 로그인 흐름 이상 없음
[ ] accounts.User와 중복 User 생성 없음
[ ] teams.Team과 중복 Team 생성 없음
[ ] Core Role 중복 생성 없음
[ ] Migration 추가/변경 여부 확인
[ ] requirements.txt 변경 여부 확인
[ ] .env 신규 항목 확인
[ ] Secret이 소스에 포함되지 않았는지 확인
[ ] 변경 파일 목록 정리
```

기본 확인 명령:

```bash
python manage.py check
```

변경 파일 확인:

```bash
git status
```

또는:

```bash
git diff --name-status develop
```

---

## 10. 변경사항 Commit 및 전달

각 조는 로컬 Branch에서 변경사항을 Commit하여 변경 이력을 남긴다.

```bash
git add .
git commit -m "feat: team2 LMS integration"
```

이 Commit은 로컬 변경 추적용이며, 현재 PHASE 3에서는 1·2·3조가 직접 PR을 생성하지 않는다.

### 권장 전달 방법: Git Patch

가능하면 변경사항을 Patch로 전달한다.

```bash
git format-patch develop --stdout > team2_lms.patch
```

Patch를 사용하면 다음 정보를 확인하기 쉽다.

- 추가된 코드
- 삭제된 코드
- 변경 파일
- Commit 단위 변경 이력

파일만 전달하는 경우에도 반드시 아래 전달 정보를 함께 제공한다.

---

## 11. 1·2·3조 소스 전달 양식

```text
[소스 전달 정보]

조:
담당자:

Repository:
GilbertMoon/ax2-integrated-platform

Base Branch:
develop

Base Commit SHA:

Local Branch:

작업 내용:

ADDED:

MODIFIED:

DELETED:

Migration:
있음 / 없음

Migration 파일:

DB 구조 변경:
있음 / 없음

requirements.txt 변경:
있음 / 없음

추가 Package:

.env 신규 항목:
있음 / 없음

환경변수 이름:

Core 변경:
있음 / 없음

python manage.py check:
PASS / FAIL

핵심 기능 테스트:
PASS / FAIL

테스트 방법:

알려진 문제:

전달 파일/Patch:
```

---

## 12. 조별 통합 시 주요 확인사항

### 1조

1조 고유 기능은 유지하되 공통 데이터는 Core 기준을 사용한다.

```text
User → accounts_user
Role → accounts_user.role
Team → teams_team
```

특히 다음 구조를 확인한다.

```text
CG_USERS
CG_PROFILE
role
username
ROOM_PARTICIPANTS
Team 관련 모델
ATTENDANCES
```

1조 학습 출석(`ATTENDANCES`)과 4조 실제 근태는 업무 목적이 다르므로 별도 Domain으로 유지한다.

### 2조

2조 LMS의 고유 기능은 유지한다.

```text
강의
과제
제출
GitHub 제출 연동
LMS 기능
```

다음 공통 데이터는 Core 기준을 사용한다.

```text
User
Student
Team
Round
Role
```

실제 코드 수령 후 Model / FK / Migration / Submission / Evaluation / GitHub API / Slack 연동 영향을 확인한다.

### 3조

3조 PRD/AI 기능은 고유 Domain으로 유지한다.

사용자/팀 정보는 Core 기준을 사용한다.

공통 조회가 필요한 경우 다음 VIEW 또는 공통 API 기준을 우선 사용한다.

```text
ax_user_team_login_view
user_round_team_view
```

원본 Core Table을 각 조가 중복 JOIN하기보다 공통 조회 계층을 우선 사용한다.

---

## 13. Core 보호 영역

다음 영역은 통합 Core 보호 영역으로 관리한다.

```text
accounts/
teams/
rounds/
reviews/
results/
config/
.github/
공통 templates/
공통 static/
```

1·2·3조에서 해당 영역 변경이 필요하면 변경 목적과 영향 범위를 4조 담당자에게 전달한다.

### Core 변경 요청 양식

```text
[Core 변경 요청]

요청 조:
담당자:

변경 대상:

변경이 필요한 이유:

현재 막히는 기능:

필요한 필드/API:

DB 영향:

예상 영향:
```

4조가 기존 Core 구조와 다른 조에 대한 영향을 확인한 후 반영 여부를 결정한다.

---

## 14. DB / Migration 관리

다음 Core 구조는 4조와 DB 담당자가 관리한다.

```text
accounts_user
teams_team
teams_teammembership
rounds_evaluationround
rounds_roundparticipant
```

### 금지 사항

- 공용 DB 직접 ALTER
- Migration 파일 임의 삭제
- Migration 번호 임의 재작성
- Core Table 중복 생성
- 기존 FK 임의 변경

### Migration 변경 시 전달 정보

```text
Migration 추가 여부:
Migration 파일명:
신규 Table:
신규 Column:
FK 변경:
Unique 변경:
Index 변경:
기존 데이터 변경:
```

### 통합 단계 검토 순서

```text
Model 변경 확인
↓
Migration 생성/변경 확인
↓
Dependency / SQL 검토
↓
개발·검증 DB 적용
↓
데이터 정합성 확인
↓
통합 승인
```

---

## 15. Dependency / 환경변수 / Secret 관리

새로운 Python Package를 사용하는 경우 반드시 기록한다.

예:

```text
추가 Package: requests
사용 이유: Slack API 호출
```

`requirements.txt` 변경 여부를 함께 전달한다.

다음과 같은 Secret 값은 GitHub에 Commit하지 않는다.

```text
SECRET_KEY
DB_PASSWORD
GOOGLE_CLIENT_SECRET
KAKAO_CLIENT_SECRET
SLACK_TEST_BOT_TOKEN / SLACK_TEST_WEBHOOK_URL
SLACK_PROD_BOT_TOKEN / SLACK_PROD_WEBHOOK_URL
GitHub Token
기타 API Key
```

신규 환경변수가 필요한 경우 실제 값이 아니라 변수 이름만 문서화한다.

---

## 16. 4조 Integration Branch 운영

각 조 변경사항은 바로 `develop`에 반영하지 않는다.

4조 담당자가 최신 `develop`에서 Integration Branch를 만든다.

### 1조

```bash
git checkout develop
git pull origin develop
git checkout -b integration/team1-garden
```

### 2조

```bash
git checkout develop
git pull origin develop
git checkout -b integration/team2-lms
```

### 3조

```bash
git checkout develop
git pull origin develop
git checkout -b integration/team3-prd
```

전달받은 코드/Patch를 해당 Branch에 반영한다.

---

## 17. 4조 통합 검증 기준

4조 담당자는 최소 다음 항목을 확인한다.

```text
[ ] Base Commit 확인
[ ] 변경 파일 확인
[ ] Core 영역 영향 확인
[ ] Migration 확인
[ ] requirements.txt 확인
[ ] .env 변경 확인
[ ] Secret 포함 여부 확인
[ ] python manage.py check PASS
[ ] 해당 조 핵심 기능 테스트
[ ] 기존 로그인/권한 정상
[ ] Core User / Team / Round 정상
[ ] 기존 4조 기능 Regression Test
[ ] DB/FK 정합성 확인
[ ] Cross Check
```

---

## 18. PASS / 보완 필요 / BLOCKER

### PASS

- 기능 정상
- 변경 근거 명확
- Core 충돌 없음
- Migration 검토 완료
- 테스트 결과 있음
- 통합 가능

### 보완 필요

- 기능은 정상이나 테스트 근거 부족
- 변경 파일 목록 누락
- Migration 설명 부족
- 환경변수/Dependency 설명 부족
- 전달 문서 부족

### BLOCKER

- Core User 중복 생성
- Team 중복 생성
- Migration 충돌
- 기존 Core 기능 오류
- DB 데이터 손실 가능성
- Secret Commit
- 로컬 실행 불가
- Base Commit과 최신 develop의 차이가 커서 바로 통합 불가

---

## 19. Pull Request / Merge 기준

### PHASE 3 기간

1·2·3조:

```text
통합 Repository PR 생성하지 않음
```

4조:

```text
integration/team*-*
        ↓ Pull Request
     develop
```

PR에는 최소 다음 내용을 기록한다.

- 대상 조
- Base Commit
- 전달받은 변경 범위
- Core 영향
- Migration 여부
- 테스트 결과
- Regression 결과
- 알려진 제한사항

검증 완료 후 Merge한다.

### 최종 안정화

```text
develop
   ↓ Pull Request
 main
   ↓
배포
```

`main`은 통합 및 Regression Test를 통과한 `develop`만 반영한다.

---

## 20. 통합 상태 관리

```text
DELIVERED
각 조 변경사항 전달 완료

REVIEWING
4조 변경사항 검토 중

INTEGRATING
Integration Branch 반영 중

TESTING
기능/Regression Test 중

PR OPEN
4조가 develop 대상 PR 생성

MERGED
develop Merge 완료

GREEN
Merge 후 재검증 및 Regression 완료
```

코드를 전달받았다는 이유만으로 완료 처리하지 않는다.

---

## 21. 통합 순서 및 최신 develop 재확인

기본적으로 순차 통합한다.

```text
1조
↓
develop
↓
Regression PASS
↓
2조
↓
develop
↓
Regression PASS
↓
3조
↓
develop
↓
Regression PASS
```

앞 단계 통합으로 `develop`이 변경되었을 경우 다음 조 코드는 최신 `develop`과 다시 비교한다.

필요한 경우 전달받은 변경사항을 최신 `develop` 기준으로 재적용한 뒤 테스트한다.

---

## 22. 금지 사항

### 1·2·3조

```text
통합 Repository PR 직접 생성 금지
develop 직접 Push 금지
main 직접 Push 금지
Core 구조 임의 변경 금지
공용 DB 직접 ALTER 금지
Migration 임의 재작성 금지
Secret Commit 금지
```

### 공통

- 테스트하지 않은 변경을 완료 처리하지 않는다.
- 다른 조의 코드까지 임의로 수정한 후 전달하지 않는다.
- 단순 파일 전달만으로 통합 완료라고 판단하지 않는다.

---

## 23. 최종 작업 흐름

```text
                 GilbertMoon/ax2-integrated-platform
                              │
                           develop
                              │
             ┌────────────────┼────────────────┐
             │                │                │
          1조 Clone        2조 Clone        3조 Clone
             │                │                │
       Local Branch      Local Branch      Local Branch
             │                │                │
          개발/수정          개발/수정          개발/수정
             │                │                │
        Local Test       Local Test       Local Test
             │                │                │
       변경사항 전달      변경사항 전달      변경사항 전달
             │                │                │
             └────────────── 4조 ──────────────┘
                              │
                       Integration Branch
                              │
                    Core / Migration 검토
                              │
                         기능 Test
                              │
                     Regression Test
                              │
                         Cross Check
                              │
                        4조 Pull Request
                              │
                           develop
                              │
                       Merge 후 재검증
                              │
                            GREEN
                              │
                     develop → main
```

---

## 24. 최종 원칙

> **1·2·3조는 자신의 기능을 개발하고 로컬에서 검증한다.**

> **1·2·3조는 PHASE 3 통합 기간 동안 통합 Repository에 직접 Pull Request를 생성하지 않는다.**

> **변경사항은 각 조별 4조 담당자에게 전달한다.**

> **4조는 전달받은 코드를 Core 기준으로 검토하고 Integration Branch에서 통합한다.**

> **Pull Request와 Merge는 통합 책임자인 4조가 관리한다.**

> **`develop`은 각 조가 자유롭게 수정하는 Branch가 아니라 검증된 변경을 모으는 통합 기준 Branch이다.**

> **최종 완료는 `develop` Merge 후 Regression Test와 재검증까지 끝난 상태(GREEN)로 판단한다.**
