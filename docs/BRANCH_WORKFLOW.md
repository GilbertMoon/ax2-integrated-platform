# AX2 통합 플랫폼 브랜치 운영 정책

작성일: 2026-08-31

## 1. 목적

개인/기능 브랜치에서 개발한 내용을 `develop`에 먼저 통합하여 테스트하고, 검증이 끝난 변경만 `main`에 반영하는 표준 흐름을 정의한다.

## 2. 브랜치 역할

| 브랜치 | 역할 | 직접 Push |
|---|---|---|
| `feature/*`, `team*/기능명` | 개인/기능 개발 | 허용 |
| `develop` | 기능 통합 및 통합 테스트 | 금지 |
| `main` | 배포 가능한 안정 버전 | 금지 |

## 3. 표준 작업 흐름

```text
feature/* 또는 team*/기능명
        ↓ Pull Request
     develop
        ↓ 통합 테스트 / 회귀 테스트
        ↓ Pull Request
       main
        ↓
       배포
```

## 4. Pull Request 기준

- 일반 기능 PR의 기본 대상(base)은 `develop`으로 한다.
- `develop`에 반영된 기능은 통합 테스트와 회귀 테스트를 수행한다.
- `main`에는 `develop → main` Pull Request만 원칙적으로 반영한다.
- `develop`, `main`에는 직접 Push하지 않는다.
- CI가 실패한 Pull Request는 병합하지 않는다.
- Core 영역(`accounts`, `teams`, `rounds`, `reviews`, `results`, `config`, `.github/workflows`) 변경은 4조 담당자의 확인을 거친다.

## 5. GitHub Repository 설정 기준

Repository Settings에서 다음 정책을 적용한다.

### Default branch

- Default branch: `develop`
- 목적: 새 Pull Request 생성 시 기본 base를 `develop`으로 설정하여 `main` 대상 PR 실수를 줄인다.

### Branch protection

`develop`, `main` 두 브랜치 모두 최소 다음 규칙을 적용한다.

- Require a pull request before merging
- 직접 Push 금지
- 가능하면 필수 CI Status Check 통과 후 Merge
- 운영 여건이 허용하면 최소 1명 Review 승인 후 Merge

### `main` 추가 원칙

- 최종 배포 기준 브랜치로 유지한다.
- 통합 테스트를 통과한 `develop`의 변경만 Pull Request를 통해 반영한다.

## 6. 팀 공통 원칙

> 개발은 기능 브랜치에서, 통합 검증은 `develop`에서, 배포 기준은 `main`에서 관리한다.

새 작업은 가능한 한 Issue와 연결하고, 작업 브랜치 → PR → Review/Test → Merge 순서를 지킨다.
