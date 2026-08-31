# 2026-08-28 2조 LMS 통합 사전 협의 및 Core Mapping

## 1. 목적

* 2조 LMS와 4조 AX2 평가 플랫폼의 통합을 위한 사전 협의 진행
* 2조 고유 기능과 4조 AX2 Core 공통 데이터 영역 구분
* 공통 데이터의 Source of Truth 및 VIEW/FK 연동 기준 확인
* 코드 전달 이후 통합 작업을 위한 일정 및 후속 확인 사항 정리

## 2. 오늘 수행 내용

* 2조 LMS 개발 현황 및 PRD 기준 기능 범위 확인
* 2조 ERD를 기준으로 User / Student / Team / TeamMember / Round 구조 확인
* 2조에 별도 Student 테이블이 존재하지 않는 것을 확인
* 공통 User / Student / Team / TeamMember / Round 데이터는 4조 AX2 Core를 기준으로 사용하는 방향 확인
* 2조 LMS에서 공통 데이터를 VIEW를 통해 조회하는 방향 확인
* 주요 FK 연결 기준 확인
* 2조 고유 LMS 데이터와 4조 Core 공통 데이터 영역 구분
* PRD와 실제 구현에 일부 차이가 있을 수 있음을 확인
* 2조 코드 전달 일정 및 통합 작업 시작 시점 확인

## 3. 최종 결과

### 3-1. 공통 데이터 기준

| 데이터                         | 통합 기준       |
| --------------------------- | ----------- |
| User                        | 4조 AX2 Core |
| Student / Round Participant | 4조 AX2 Core |
| Team                        | 4조 AX2 Core |
| TeamMember                  | 4조 AX2 Core |
| Round                       | 4조 AX2 Core |

### 3-2. 2조 LMS 고유 데이터

* Lecture
* Lesson
* LessonMaterial
* Assignment
* Submission
* SubmissionFile
* AiEvaluation
* Evaluation
* Todo

### 3-3. VIEW 연동 기준

* 공통 User / Team / Round 데이터는 4조 AX2 Core를 기준으로 사용
* 2조 LMS가 공통 데이터를 별도로 소유하지 않음
* 공통 데이터 조회 시 제공된 VIEW를 사용하는 방향으로 확인
* AX2 Core 데이터는 2조 LMS에서 직접 수정하지 않는 방향으로 확인

### 3-4. 주요 FK 기준

* `Assignment.created_by` → `accounts_user`
* `Submission.student_id` → `accounts_user`
* `Submission.team_id` → `teams_team`
* `Todo.student_id` → `accounts_user`

주요 공통 데이터 FK는 4조 AX2 Core를 기준으로 연결하는 방향을 확인하였다.

## 4. 통합 범위 및 일정

### 통합 범위

* 2조 LMS 고유 기능은 2조 영역으로 유지
* 공통 User / Student / Team / TeamMember / Round 데이터는 4조 AX2 Core 사용
* PRD를 기준으로 통합 범위를 검토하되, 실제 구현과 일부 차이가 있을 수 있으므로 최종 범위는 코드 확인 후 확정

### 일정

* 2조 코드 전달 예정: **2026-09-02(수)까지**
* 통합 작업 시작: **코드 전달 후 바로 진행 가능**

## 5. 산출물 / 근거

* Issue: `#8`
* PR: 해당 없음
* Commit: 해당 없음
* 관련 자료:

  * 2조 LMS PRD
  * 2조 LMS ERD
  * 2조 개발 현황 공유 자료
  * 4조 AX2 Core 관련 자료
  * 공통 VIEW 관련 자료

## 6. 검증 방법

1. 2조 ERD에서 Student 별도 테이블 존재 여부를 확인한다.
2. User / Team / TeamMember / Round가 4조 AX2 Core 기준으로 사용되는지 확인한다.
3. 2조 ERD의 주요 FK 연결 대상을 확인한다.
4. 2조 개발 현황 자료에서 Core DB / VIEW 연동 방향을 확인한다.
5. 2조와 협의한 코드 전달 일정 및 통합 시작 가능 시점을 확인한다.

### 예상 결과

* Student 별도 테이블 없음
* 공통 데이터는 4조 AX2 Core 기준
* 공통 데이터 조회는 VIEW 사용
* 주요 FK는 Core 데이터 기준
* 코드 전달 예정일은 2026-09-02(수)까지

## 7. 본인 검증

* 결과: **PASS**
* 확인 내용:

  * 2조 ERD 및 개발 현황을 기준으로 공통 데이터 구조를 확인하였다.
  * 2조 고유 LMS 데이터와 4조 Core 데이터를 구분하였다.
  * VIEW 및 FK 연결 기준을 확인하였다.
  * 2조와 코드 전달 일정 및 통합 시작 시점을 확인하였다.

## 8. Cross Check

* 검증자: 2조 담당자
* 결과: **PASS**
* 확인 내용:

  * Core 데이터 사용 기준 및 VIEW 연동 방향을 확인하였다.
  * 주요 FK 연결 기준을 확인하였다.
  * PRD와 실제 구현에 일부 차이가 있을 수 있음을 확인하였다.
  * 코드 전달 예정일을 확인하였다.
* 보완사항:

  * 실제 Model / FK / Migration 수정 범위는 코드 전달 후 확인 필요
  * 실제 구현 기준 QA 체크리스트는 코드 확인 후 작성 필요

## 9. 미해결 / 다음 작업

* 실제 2조 코드 확인
* 실제 Django Model / FK 구조 확인
* Migration 수정 필요 여부 확인
* PRD와 실제 구현 차이 확인
* 최종 통합 기능 범위 확정
* 실제 구현 기준 QA 체크리스트 작성

### 다음 작업

**2026-09-02(수)까지 2조 코드를 전달받은 후**

1. 실제 코드 구조 확인
2. PRD / ERD / 실제 구현 비교
3. Model / FK / Migration 영향 범위 확인
4. 최종 통합 범위 확정
5. QA 체크리스트 작성
6. 통합 작업 진행
