# [설정] PR 생성 시 기본 base 브랜치가 develop이 아닌 main으로 되어 있음

- **작성자:** tladntjq1-lgtm
- **상태:** Open
- **담당자(Assignee):** GilbertMoon
- **작성일:** 2026-08-31

## 문제 상황

튜터님과 협의하여 PR을 올릴 때 기본(default)으로 main 브랜치가 아닌
develop 브랜치로 설정하기로 했으나, 실제 저장소 설정에서는
여전히 PR 기본 base 브랜치가 main으로 되어 있는 것을 확인했습니다.

## 확인 방법

- Compare changes 화면(`github.com/GilbertMoon/ax2-integrated-platform/compare`)에서
  base: main / compare: main 으로 기본 표시됨
- develop 브랜치가 default branch로 설정되어 있지 않아
  PR 생성 시 자동으로 main이 base로 잡힘

## 요청 사항

- Settings > Branches 에서 Default branch를 main → develop 으로 변경 부탁드립니다
- 변경 후 새 PR 생성 시 base가 develop으로 자동 설정되는지 확인 필요

## 참고

이 설정이 되어 있지 않으면 팀원들이 PR을 올릴 때마다
base 브랜치를 수동으로 develop으로 바꿔야 하는 번거로움이 있습니다.

---

## 진행 상황

| 시각 | 내용 |
|---|---|
| 이슈 생성 | tladntjq1-lgtm이 이슈 작성, GilbertMoon assign |
| +12분 | GilbertMoon이 확인 및 후속 상황 공유 코멘트 남김 (ChatGPT Codex Connector 연동) |

### GilbertMoon 답변 코멘트 (요약)

**확인 및 후속 상황 공유**

우섭님이 제안한 브랜치 운영 정책 자체는 이미 반영되어 있었음:

- `feature/*` 또는 개인/팀 작업 브랜치 → PR → `develop`
- `develop`에서 통합/취합 후 테스트
- `develop` → `main`
- `main`은 배포 가능한 버전만 유지
- `develop` / `main` 직접 Push 금지 원칙
- 관련 문서: `docs/BRANCH_WORKFLOW.md`
- 관련 PR: `docs: develop 기반 브랜치 운영 정책 명시 #44` (develop 병합 완료)

다만 실제 Repository 설정을 다시 확인한 결과, **Default branch는 여전히 main으로 남아 있음**을 재확인. 따라서 새 PR 생성 시 base가 자동으로 develop으로 잡히는 저장소 설정은 아직 미적용 상태. `develop` / `main`의 Branch Protection 실제 설정도 별도 확인 필요.

**남은 관리자 설정**
1. Repository Settings → General → Default branch 를 main → develop 으로 변경
2. develop, main에 PR 필수 보호 규칙 설정
3. 새 PR 생성 시 기본 base가 develop으로 잡히는지 확인
4. main/develop 직접 Push 제한 여부 확인

현재 연결된 GitHub 작업 권한으로는 코드/PR 변경은 가능하지만 Repository Settings의 Default branch 및 Branch Protection 변경 권한은 제공되지 않음 → 위 관리자 설정은 GilbertMoon님이 GitHub 웹 Settings에서 직접 적용 필요.

설정 완료 후 최종 확인 사항: `base = main/develop`인 PR에 대해 강제 Push 제한 또는 PR 보호가 걸리는지.

> 운영 정책 문서와 실제 Repository 설정이 일치해야 최종 완료. 두 관리자 설정(Default branch, Branch Protection) 확인 후 이슈 close 예정.
