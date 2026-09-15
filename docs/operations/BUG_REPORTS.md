# 오류 신고

로그인 후 우측 상단 프로필 메뉴의 **마이페이지 → 바로 아래 오류 신고**에서 제목, 오류 내용, 발생 페이지, 캡처(선택)를 제출합니다.
캡처는 파일 선택 또는 Ctrl+V 붙여넣기를 지원하며 PNG/JPEG/WebP, 최대 5MB·2천만 화소로 제한합니다.
사용자는 본인 신고만, 기존 운영 권한을 가진 승인된 튜터·관리자는 전체 신고를 조회합니다.
운영 담당자는 신고 내역에서 접수 / 확인 중 / 해결 완료 상태와 신고자에게 보이는 답변을 저장합니다.

## 저장과 배포

- DB 변경: `python manage.py migrate`
- 기본 첨부 위치: 프로젝트 폴더/private_uploads/bug_reports/screenshots/
- 현재 로컬: C:/Users/hiju2/Documents/ChatGPT/4조 통합/private_uploads/bug_reports/screenshots/
- 운영 경로 설정: DJANGO_BUG_REPORT_UPLOAD_ROOT (절대 경로 권장)
- 공개 MEDIA_ROOT와 분리합니다. 웹 서버의 정적 파일 경로로 노출하지 마세요.
- 첨부는 로그인·신고 접근 권한을 확인하는 다운로드 뷰로만 제공합니다.
- 컨테이너 배포에서는 이 경로에 영구 볼륨을 연결하고 DB와 함께 백업해야 합니다.
- 발생 페이지의 쿼리 문자열과 fragment는 저장하지 않습니다.

## 검증

`python manage.py test bug_reports --settings=config.lms_test_settings`
