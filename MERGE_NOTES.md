# review-system → ax2-integrated-platform 통합 노트

review-system(4조 Core) 레포의 파일 구조를 ax2-integrated-platform으로 옮기면서
실제로 무엇을 가져오고, 무엇을 뺐는지 정리한 문서입니다. 팀원 리뷰용으로 남겨둡니다.

## 1. 그대로 가져온 것 (INSTALLED_APPS에 등록된 8개 앱)

```
accounts/  teams/  rounds/  reviews/
results/   audit/  notices/ notifications/
```
- `manage.py`, `config/` (settings, urls, wsgi, asgi)
- `templates/`, `static/`
- `requirements.txt`, `requirements-dev.txt`, `pyproject.toml`
- `Dockerfile`, `compose.yaml`, `compose.production.yaml`, `deploy/`
- `.gitignore`, `.editorconfig`, `.dockerignore`, `.pre-commit-config.yaml`, `.mailmap`
- `seed_data.py`
- `.github/workflows/` (CI 참고용 — 아래 4번 참고)

기존 ax2 쪽 `README.md`, `docs/`(architecture, erd, deliverables, todo 등)는
**전혀 건드리지 않았습니다.** review-system에는 애초에 이 파일들이 존재하지
않았기 때문에 실제 충돌은 없었습니다.

## 2. 이름만 바꿔서 별도 보관한 것 (충돌 방지)

review-system 자체 문서들은 ax2의 `docs/` 구조(architecture, erd, requirements 등)와
주제가 겹쳐서 그대로 합치면 어떤 게 최신 기준인지 헷갈립니다. 그래서
`docs/legacy-review-system/`으로 이름을 바꿔 별도 보관했습니다.

```
docs/legacy-review-system/
├── README_original.md      (review-system 레포의 원래 README)
├── DESIGN.md
├── REQUIREMENTS.md
├── REFINED-REQUIREMENTS.md
├── DATABASE-DESIGN.md
├── TECHNICAL_DECISIONS.md
├── CODING_CONVENTIONS.md
├── FLOWS.md
├── LAYOUT.md
├── TEAMS_UI_PREVIEW.md
├── CONTINUOUS-DELIVERY.md
├── PROJECT_ANALYSIS_REPORT.md
├── adr/0001-retain-integrated-authentication-paths.md
├── AGENT.md
└── CONTEXT.md
```
→ 필요한 내용만 골라서 팀 `docs/architecture`, `docs/requirements` 등으로
점진적으로 옮기는 걸 추천합니다. 통째로 유지할 필요는 없습니다.

## 3. 아예 제외한 것

| 항목 | 이유 |
|---|---|
| `.venv/` (185MB) | 로컬 파이썬 가상환경. 절대 레포에 올리면 안 됨 |
| `.git/` (review-system 쪽) | 히스토리 없이 파일만 옮기는 방식이라 불필요 |
| `__pycache__/`, `*.pyc` (629개 폴더, 3271개 파일) | 빌드 캐시, `.gitignore`로 이미 차단됨 |
| **`.env`** | ⚠️ **실제 비밀값 포함** (`DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`, Google/Kakao OAuth secret 등). 대신 `.env.example`, `.env.production.example`만 가져왔습니다. **누구도 실제 `.env`를 커밋하면 안 됩니다.** |
| `.claude/launch.json` | 개인 에디터 로컬 설정. review-system `.gitignore`에도 이미 제외되어 있던 파일 |

## 4. 중복·불필요해서 제거를 추천하는 것

`peer_reviews/`, `team_reviews/` 앱은 **`INSTALLED_APPS`에 등록되어 있지 않고**,
내부에 `__init__.py` / `apps.py` / 빈 `migrations/__init__.py`만 있는
스켈레톤 상태입니다. 실제 리뷰 관련 로직은 전부 `reviews/` 앱에 구현되어
있어서 이 두 앱은 초기 스캐폴딩 후 방치된 것으로 보입니다.

→ 이번 통합본에는 아예 포함하지 않았습니다. 혹시 팀 내에서 다른 용도로
쓰고 있었다면 알려주세요, 원본 zip에서 다시 가져올 수 있습니다.

## 5. 통합 후 팀원이 확인해야 할 것

1. **`.env` 새로 생성** — `.env.example`을 복사해서 로컬용 `.env`를 각자 만들어야
   `manage.py runserver`가 실행됩니다. (Postgres 접속 정보, `DJANGO_SECRET_KEY` 등)
2. **`.github/workflows/`** — `delivery.yml`, `quality.yml`은 review-system 자체
   배포 대상(Windows PC 원격 배포 스크립트, GitHub Secrets)을 기준으로 작성되어
   있습니다. ax2 레포 기준으로 시크릿/배포 경로를 다시 세팅하기 전까지는
   Actions 탭에서 비활성화해두는 걸 추천합니다.
3. **의존성 설치** — `pip install -r requirements.txt -r requirements-dev.txt`
   (팀에서 Poetry/uv로 전환하기로 했다면 `pyproject.toml` 기준으로 재설정)
4. **`python manage.py migrate`** 후 `python manage.py runserver`로 4조 Core가
   기존과 동일하게 뜨는지부터 확인 — 이게 이번 통합의 baseline입니다.
