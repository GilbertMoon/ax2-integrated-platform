# 2026-09-16 2조 LMS Core UI 통일 및 GA4·GitHub OAuth 서버 연동 QA

## 1. 목적

* 2조 LMS 학생/튜터 화면을 4조 Core UI 기준에 맞게 정리한다.

* LMS 상단바, breadcrumb, 사이드바, 사용자 표시 방식 등 공통 UI를 Core 스타일과 통일한다.

* 4조 Core 공지를 LMS 학생/튜터 대시보드에서 공통으로 조회할 수 있도록 연동한다.

* LMS에 Google Analytics 4(GA4) 추적 구조를 추가하여 운영환경에서 페이지 사용 현황을 측정할 수 있도록 구성한다.

* UI 및 공지/GA 연동 이후 기존 LMS 과제·제출·평가·점수·GitHub·Slack 기능에 Regression이 발생하지 않았는지 확인한다.

* 통합 Merge 이후 서버 환경에서 GitHub OAuth 연결 상태를 점검하고, callback 주소가 localhost로 복귀하는 현상을 재현하여 원인 범위를 분석한다.

---

## 2. 오늘 수행 내용

### 2.1 LMS 상단바 및 본문 UI Core 기준 통일

2조 LMS 학생/튜터 화면의 상단 공통 영역을 4조 Core 기준으로 정리하였다.

### 적용 내용

* LMS 상단바를 Core 스타일 기준으로 수정

* breadcrumb 구조를 Core와 유사하게 변경

    AX Console
        >
    현재 페이지

* breadcrumb Home 아이콘 적용

* 학생/튜터 화면 본문 시작 위치 및 좌우 여백 조정

* LMS 사용자 표시를 이메일 기준이 아닌 Core와 동일한 사용자 이름 기준으로 변경

기존에는 이메일이 사용자 정보 영역에 노출될 수 있었으나 수정 이후 Core와 동일하게 사용자 이름을 우선 표시하도록 정리하였다.

예시:

    기존
    beyonce@example.com

    변경
    비욘세

* 기존 기능 URL 및 권한 구조는 변경하지 않음

---

## 3. LMS 사이드바 Core UI 기준 정리

기존 2조 LMS 사이드바를 4조 Core 스타일과 비교하여 공통 UI 요소를 통일하였다.

### 적용 내용

* LMS 사이드바 브랜드를 `AX Console`로 통일

* 브랜드 클릭 시 Core 대시보드로 이동하도록 연결

* 메뉴별 Bootstrap Icon 적용

* active 메뉴 스타일을 Core 기준으로 수정

* hover 스타일을 Core 기준으로 수정

* 메뉴 간격 및 padding 조정

* 폰트 크기 및 weight 조정

* border-radius 조정

* Core/LMS 사이드바 폭 비교

    Core sidebar : 240px
    LMS sidebar  : 240px

두 화면의 실제 sidebar width가 동일함을 확인하였다.

또한 LMS에서 항상 세로 스크롤 영역이 잡히던 부분과 Core의 동작 차이를 확인하여 스크롤 및 breakpoint 동작을 보정하였다.

---

## 4. 튜터 사이드바 구조 비교 및 적용 범위 판단

4조 Core 튜터/운영 화면과 2조 LMS 튜터 화면의 사이드바 구조를 비교하였다.

### Core 튜터/운영 화면 특징

* 운영
* 설정
* 시스템
* 기획
* 학습
* 계정

등 여러 카테고리와 다수의 기능 메뉴가 존재한다.

반면 LMS 튜터 화면은 다음 기능을 사용한다.

    튜터

    대시보드
    학생 관리
    점수집계
    과제 관리
    강의 및 교안 관리

따라서 4조 Core와 2조 LMS의 메뉴 개수 및 카테고리 구조 자체가 다르기 때문에, 단순히 화면을 동일하게 보이게 하기 위해 사용하지 않는 메뉴나 카테고리를 임의로 추가하는 것은 적용하지 않았다.

### 적용 기준

* sidebar width 통일

* 메뉴 font 통일

* 메뉴 icon 통일

* active / hover 스타일 통일

* 메뉴 간격 통일

* 브랜드 영역 통일

* 기존 LMS 기능 및 URL 구조 유지

즉 기능 구조는 LMS 기준을 유지하고 공통 UI 스타일만 Core 기준으로 맞추는 방향으로 적용하였다.

---

## 5. Core 공지 → LMS 학생/튜터 대시보드 연동

기존 LMS 학생 대시보드에서 별도로 표시되던 공지 구조를 Core 공지 데이터 기준으로 통합하였다.

### 변경 구조

    Core Notice
        ↓
    공지 조회 Service
        ↓
    LMS 공통 Notice Client
        ↓
    학생 / 튜터 Dashboard

### 적용 내용

* Core `Notice`를 LMS 공지 Source of Truth로 사용

* `is_published=True` 공지만 LMS 화면에 노출

* 학생 대시보드 공지 연동

* 튜터 대시보드 공지 연동

* 공지 배너 UI를 Core 스타일 기준으로 수정

* LMS 전용 공지 테이블 추가 없음

* DB Model 변경 없음

* Migration 추가 없음

* 공지 수정 시 최신 내용 조회

* 공지 삭제 시 LMS에서도 제거

* 공개상태 변경 시 LMS 노출 상태 반영

이를 통해 공지 데이터가 Core와 LMS에 중복 저장되지 않고 Core 데이터를 공통으로 사용하는 구조로 정리되었다.

---

## 6. Google Analytics 4 연동

LMS 사용 현황을 운영환경에서 확인할 수 있도록 Google Analytics 4 연동 구조를 추가하였다.

### 설정 구조

    .env
        ↓
    GA_MEASUREMENT_ID
        ↓
    Django settings
        ↓
    LMS context processor
        ↓
    base.html
        ↓
    gtag.js

### 적용 내용

* `GA_MEASUREMENT_ID` 환경변수 추가

* Django settings에서 환경변수 조회

* LMS 공통 context processor에 Analytics 정보 전달

* LMS 공통 `base.html`에 GA 스크립트 연동

* GA Measurement ID가 설정된 경우에만 `gtag.js` 적용

* GA Measurement ID가 비어 있을 경우 기존 화면에 영향 없이 동작하도록 no-op 처리

* `.env.example`에 관련 환경변수 안내 반영

### 동작 기준

    GA_MEASUREMENT_ID 있음
        ↓
    GA4 활성화

    GA_MEASUREMENT_ID 없음
        ↓
    GA 코드 미적용
        ↓
    기존 LMS 기능 정상 동작

이를 통해 로컬/테스트 환경에서는 GA 설정 없이 기존 기능을 유지하고 운영환경에서 필요한 경우 GA 추적 기능을 활성화할 수 있도록 구성하였다.

---

## 7. 자동 테스트 및 Regression 확인

UI / 공지 / GA 연동 이후 Django 기본 검사 및 전체 테스트를 실행하였다.

### Django System Check

    python manage.py check

    System check identified no issues

### 전체 테스트 결과

    706 tests

    OK

    skipped = 1
    failed = 0
    error = 0

### 확인 내용

* LMS 학생 대시보드 렌더링

* LMS 튜터 대시보드 렌더링

* 상단바 표시

* breadcrumb 표시

* 사용자 이름 표시

* 사이드바 메뉴 표시

* active 메뉴 상태

* Core 공지 표시

* GA 설정 미사용 환경 동작

* 과제 기능 영향 여부

* 제출 기능 영향 여부

* 평가 기능 영향 여부

* 점수 계산 기능 영향 여부

* GitHub 연동 코드 영향 여부

* Slack 연동 코드 영향 여부

UI / 공지 / GA 관련 변경이 기존 LMS 핵심 비즈니스 로직을 직접 변경하지 않았음을 확인하였다.

---

## 8. Git / PR / Merge 확인

금일 작업사항을 `feature/p5_yejin` 브랜치 기준으로 정리하였다.

### 확인 내용

* 작업 전 최신 `develop` 상태 확인

* `feature/p5_yejin` 브랜치 상태 확인

* 기존 local ahead commit 확인

* 해당 commit이 최신 develop Merge commit임을 확인

확인 commit:

    3218796
    Merge pull request #124 from GilbertMoon/feature/p5_yejin

* UI / 공지 / GA 변경사항 commit

* 원격 feature 브랜치 push

* `feature/p5_yejin → develop` PR 반영

* develop Merge 완료 확인

* Merge 이후 최신화 절차 확인

---

## 9. 서버 GitHub OAuth 연동 QA

Merge 이후 실제 서버 환경에서 GitHub OAuth 연동 상태를 확인하였다.

서버 접속 주소:

    http://10.2.16.254:8000/

### 정상 동작 확인

* 로컬 `runserver` 환경 GitHub 연동 정상

* 서버 주소에서도 GitHub 연결 성공 케이스 확인

### 비정상 동작 확인

일부 시도에서 GitHub 인증 완료 후 callback이 다음 주소로 이동하는 현상을 확인하였다.

    http://localhost:8000/github/callback/

해당 상황에서 다음 오류가 발생하였다.

    ERR_CONNECTION_REFUSED

또는

    GitHub 연결 요청이 유효하지 않습니다.

동일한 GitHub 연결 기능이 테스트 시점에 따라 다음과 같이 다르게 나타나는 현상을 확인하였다.

    정상 연결

    또는

    GitHub 연결 요청이 유효하지 않습니다.

    또는

    ERR_CONNECTION_REFUSED

---

## 10. GitHub OAuth callback 원인 분석

GitHub OAuth callback 생성 관련 코드 및 환경설정을 확인하였다.

### 확인 구조

    GITHUB_OAUTH_REDIRECT_URI
        ↓
    값이 있으면 해당 값 사용

    값이 없으면
        ↓
    SITE_URL

    또는
        ↓
    현재 request host

`GITHUB_OAUTH_REDIRECT_URI`는 필수 환경변수가 아니며 빈 값으로 사용할 수 있도록 구성되어 있음을 확인하였다.

로컬 `.env` 확인 결과:

    DJANGO_SITE_URL=http://localhost:8000

값이 존재하였다.

또한 서버 주소에서 OAuth 연동을 시작한 이후 일부 callback이 localhost 주소로 이동하는 사례를 직접 확인하였다.

### 오류 발생 흐름

    서버에서 OAuth 시작
            ↓
    GitHub 로그인 및 인증
            ↓
    callback
            ↓
    localhost:8000

이 경우 로컬 Django 실행 여부에 따라 결과가 달라질 수 있다.

### 로컬 Django 실행 중

    localhost callback
            ↓
    로컬 Django 접근
            ↓
    서버에서 생성한 session/state와 불일치 가능
            ↓
    GitHub 연결 요청이 유효하지 않습니다.

### 로컬 Django 미실행

    localhost callback
            ↓
    접속 대상 없음
            ↓
    ERR_CONNECTION_REFUSED

반면 callback이 서버 주소 기준으로 생성되는 경우 정상적으로 GitHub 연동이 완료되는 것을 확인하였다.

---

## 11. GitHub OAuth 문제 범위 판단

현재 확인된 현상은 GitHub OAuth 기능 자체가 완전히 동작하지 않는 문제로 판단하지 않았다.

### 확인 결과

* 로컬 OAuth 정상

* 서버 OAuth 정상 연결 케이스 존재

* GitHub 인증 자체 정상

* OAuth callback 이후 문제 발생

* localhost callback 사례 확인

따라서 문제 범위를 다음과 같이 분리하였다.

    GitHub OAuth 인증 문제
            X

    callback 주소 생성 / 서버 실행환경 문제
            O

현재 서버 실제 실행환경의 `SITE_URL`, `.env`, 실행 프로세스 적용 상태와 callback 주소가 일치하는지 확인이 필요한 상태로 판단하였다.

---

## 12. 오늘 완료 항목

* [x] LMS 상단바 Core 스타일 적용

* [x] LMS breadcrumb Core 스타일 적용

* [x] LMS 사용자 표시 방식 Core 기준 통일

* [x] LMS 본문 여백 및 시작 위치 조정

* [x] LMS 사이드바 브랜드 `AX Console` 적용

* [x] LMS 사이드바 메뉴 아이콘 적용

* [x] sidebar active / hover 스타일 통일

* [x] Core/LMS sidebar 폭 비교 및 동일 여부 확인

* [x] breakpoint 및 스크롤 동작 보정

* [x] 튜터 sidebar 구조 차이 분석

* [x] 기존 LMS 튜터 메뉴 구조 유지 결정

* [x] Core Notice → LMS 학생 대시보드 연동

* [x] Core Notice → LMS 튜터 대시보드 연동

* [x] LMS 공지 UI Core 스타일 적용

* [x] LMS 공지 Source of Truth Core 기준 통일

* [x] Google Analytics 4 연동 구조 적용

* [x] `GA_MEASUREMENT_ID` 환경변수 기반 적용

* [x] GA 미설정 환경 no-op 처리

* [x] Django System Check 통과

* [x] 전체 자동 테스트 706개 통과

* [x] 기존 LMS 기능 Regression 없음 확인

* [x] 작업 브랜치 commit / push

* [x] PR 반영

* [x] develop Merge 완료 확인

* [x] 로컬 GitHub OAuth 정상 확인

* [x] 서버 GitHub OAuth 정상 연결 케이스 확인

* [x] localhost callback 재현

* [x] `ERR_CONNECTION_REFUSED` 확인

* [x] `GitHub 연결 요청이 유효하지 않습니다.` 오류 확인

* [x] GitHub OAuth callback 문제 범위 분석

---

## 13. QA 판단

### 현재 상태

**YELLOW**

### 판단 근거

2조 LMS의 상단바, breadcrumb, 사용자 표시 방식, 사이드바 등 주요 공통 UI를 4조 Core 기준으로 정리하였다.

Core 공지를 LMS 학생/튜터 대시보드에 연동하여 공지 데이터 Source of Truth를 Core로 통일하였으며, 별도 LMS 공지 테이블이나 Migration 없이 기존 구조를 유지하였다.

Google Analytics 4 연동 구조도 추가하여 `GA_MEASUREMENT_ID`가 설정된 환경에서만 추적 기능이 활성화되도록 구성하였다.

전체 자동 테스트 706개가 정상 통과하였으며 UI / 공지 / GA 변경으로 인해 기존 과제·제출·평가·점수·GitHub·Slack 기능에 직접적인 Regression이 발생하지 않았음을 확인하였다.

또한 작업사항의 PR 반영 및 develop Merge까지 완료하였다.

다만 서버 환경에서 GitHub OAuth 인증 후 callback이 간헐적으로 `localhost:8000`으로 이동하는 현상이 확인되었다.

해당 현상은 OAuth 인증 자체의 장애가 아니라 서버의 callback 생성 기준 및 실행환경 설정과 관련된 문제로 범위를 좁혀 확인하였다.

따라서 LMS UI 및 공지/GA 통합 작업은 완료되었으나 서버 GitHub OAuth callback 환경 확인이 필요한 상태이므로 현재 QA 상태는 **YELLOW**로 판단한다.

---

## 14. 작업 결과

2조 LMS의 공통 UI를 4조 Core 스타일 기준으로 정리하고, Core 공지를 LMS 학생/튜터 대시보드에서 공통으로 사용할 수 있도록 연동하였다.

LMS 튜터 사이드바는 Core와 실제 기능 메뉴 수가 다르기 때문에 구조를 임의로 동일하게 변경하지 않고, 기존 LMS 기능 구성은 유지하면서 공통 UI 스타일만 통일하였다.

Google Analytics 4 연동 구조를 추가하여 운영환경에서 LMS 사용 데이터를 수집할 수 있도록 구성하였으며, 측정 ID가 설정되지 않은 환경에서는 기존 기능에 영향을 주지 않도록 처리하였다.

전체 자동 테스트 706개가 통과하여 UI / 공지 / GA 변경 이후 기존 LMS 기능의 Regression 여부를 확인하였다.

서버 GitHub OAuth 테스트 과정에서는 정상 연결과 localhost callback 오류가 혼재하는 현상을 확인하였으며, 이를 서버 환경의 callback 주소 생성 및 설정 적용 문제로 분리하여 원인 범위를 특정하였다.

---

## 15. 산출물

* LMS 상단바 / breadcrumb Core UI 통일 결과

* LMS 사이드바 Core UI 통일 결과

* 튜터 sidebar 구조 비교 및 적용 범위 정리

* Core Notice → LMS 학생/튜터 공지 연동

* Google Analytics 4 연동 구조

* 전체 자동 Regression 결과

* GitHub OAuth 서버 callback QA 결과

* GitHub Issue #127

    [P5][전예진][2026-09-16] LMS Core UI·GA4 연동 및 GitHub OAuth 서버 QA