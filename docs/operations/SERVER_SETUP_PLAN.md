# [P4] Django 운영 서버 구축 사전 준비 및 Ubuntu 설치 계획

## 1. 목적

Django + PostgreSQL 기반 서비스를 실제 운영 서버에 배포하기 위해 서버 장비 상태, 네트워크 요구사항, Ubuntu 설치 전 사전 준비사항과 이후 구축 절차를 정리한다.

현재 장비에는 Windows 11 Pro가 설치되어 있으며, 최종 운영 환경은 Ubuntu Server 기반으로 구성할 예정이다.

Ubuntu 설치용 USB가 아직 준비되지 않은 상황에서도 네트워크, 배포, 보안, DB, 백업 관련 설계는 먼저 진행하여 일정 지연을 최소화한다.

---

## 2. 현재 서버 상태

| 항목 | 사양 |
|---|---|
| CPU | Intel Core i7-1355U |
| CPU Core | 10 Core / 12 Logical Processor |
| RAM | 16GB |
| Storage | 256GB NVMe SSD |
| 현재 OS | Windows 11 Pro |
| 예정 OS | Ubuntu Server LTS |
| 주요 서비스 | Django + PostgreSQL |
| 예상 사용자 | 약 200명 |

> 사용자 수만으로 서버 부하를 판단하지 않으며, 실제 동시 요청 수, Query 효율, 파일 업로드량, 로그/백업 증가량, 네트워크 대역폭 등을 함께 확인한다.

---

## 3. Ubuntu 설치에 USB가 필요한 이유

USB는 Ubuntu 파일을 단순 저장하기 위한 용도가 아니라, 현재 Windows가 설치된 서버를 **Ubuntu 설치 프로그램으로 부팅하기 위한 설치 미디어**로 사용한다.

```text
Ubuntu Server ISO 다운로드
        ↓
USB에 부팅 이미지 생성
        ↓
서버 재부팅
        ↓
BIOS / Boot Menu에서 USB 부팅
        ↓
Ubuntu 설치 프로그램 실행
        ↓
기존 Windows 파티션 정리
        ↓
Ubuntu Server 설치
```

### USB 권장 사양

- 최소 8GB
- 권장 16GB 이상
- 신규 USB 사용 권장
- 설치 USB 제작 시 USB 내부 데이터는 삭제될 수 있음

USB 지급이 어렵다면 일반 USB를 별도 구매하여 진행 가능하다.

---

## 4. USB 없이도 먼저 진행 가능한 작업

USB가 없으면 Ubuntu 직접 설치와 실제 서버 배포는 진행할 수 없지만, 아래 작업은 선행 가능하다.

- 네트워크 정보 확보
- 고정 IP 확인 및 할당
- MAC Address 등록
- TCP 80/443 포트 사용 가능 여부 확인
- 배포 구조 결정
- 환경변수 정리
- Django 운영 설정 정리
- PostgreSQL 설정 계획
- DB 백업/복구 계획
- 방화벽 정책 수립
- 도메인 및 HTTPS 적용 계획

### 진행 방향

```text
[현재 병렬 진행]
네트워크 확인 ─────────┐
배포 구조 결정 ────────┤
환경변수 정리 ─────────┤
Django 설정 ───────────┤
PostgreSQL 설계 ───────┼─→ 병렬 진행
백업 계획 ─────────────┤
방화벽 계획 ───────────┤
도메인/HTTPS 계획 ─────┘
          +
Ubuntu 설치 USB 확보
          ↓
[USB 확보 후]
Ubuntu 설치 → Docker → Django/PostgreSQL → HTTPS/방화벽 → 외부 접속 테스트
```

---

## 5. 네트워크 준비

### 확인 필요 정보

- [ ] 서버 고정 IP
- [ ] Subnet Mask
- [ ] Default Gateway
- [ ] DNS Server
- [ ] 서버용 유선 LAN 위치
- [ ] 외부 인터넷 접속 가능 여부
- [ ] TCP 80 사용 가능 여부
- [ ] TCP 443 사용 가능 여부

### MAC Address 등록

네트워크 담당자 요청에 따라 서버 장비 MAC Address를 확인하여 전달한다.

Windows 확인 명령어:

```bash
getmac /v /fo list
```

진행 상태:

- [x] Random MAC Address 설정 확인/비활성화
- [x] MAC Address 확인
- [x] 네트워크 담당자 전달
- [ ] 고정 IP 최종 할당 확인

> MAC Address 및 실제 공인 IP 값은 Public Repository 문서에 직접 기록하지 않는다.

---

## 6. 포트 및 방화벽 계획

| Port | 용도 | 기본 정책 |
|---:|---|---|
| 22 | SSH 관리 | 관리자 접근만 제한 허용 권장 |
| 80 | HTTP | 허용 |
| 443 | HTTPS | 허용 |
| 5432 | PostgreSQL | 외부 공개 금지 권장 |

기본 원칙은 **필요한 포트만 허용하고 나머지는 차단**한다.

Ubuntu 설치 후 UFW 적용을 검토한다.

```bash
ufw allow 80/tcp
ufw allow 443/tcp
```

SSH 정책은 실제 네트워크 환경과 관리자 접근 위치 확인 후 확정한다.

---

## 7. 배포 구조

권장 구조:

```text
Internet
   │
   │ HTTPS : 443
   ▼
Reverse Proxy (Caddy 또는 Nginx)
   │
   ▼
Gunicorn
   │
   ▼
Django
   │
   ▼
PostgreSQL
```

Docker Compose 기반으로 서비스 구성을 관리하는 방향을 우선 검토한다.

```text
Ubuntu Server
└── Docker Compose
      ├── Reverse Proxy
      ├── Django
      └── PostgreSQL
```

### Docker Compose를 사용하는 이유

- 서비스별 격리
- 개발/운영 환경 차이 감소
- 배포 재현성 확보
- 이전 및 복구 편의성
- 서비스 단위 재시작 가능

---

## 8. 환경변수 정리

운영 비밀정보는 코드에 직접 작성하지 않는다.

예상 환경변수:

```env
DJANGO_SECRET_KEY=
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=
CSRF_TRUSTED_ORIGINS=

POSTGRES_DB=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_HOST=
POSTGRES_PORT=5432
```

GitHub에 Commit하지 않을 값:

- Django SECRET_KEY
- DB Password
- 관리자 Password
- API Key
- 인증 Token

Repository에는 실제 `.env`가 아닌 `.env.example` 형태만 관리한다.

---

## 9. Django 운영 설정

운영환경에서 최소 확인할 항목:

- [ ] `DEBUG = False`
- [ ] `ALLOWED_HOSTS`
- [ ] `CSRF_TRUSTED_ORIGINS`
- [ ] Static File 처리
- [ ] Media File 처리
- [ ] Gunicorn 설정
- [ ] Logging / Error Logging
- [ ] DB Connection 설정
- [ ] Security Header 설정

개발용 서버 실행 명령인 아래 방식은 운영환경에서 사용하지 않는다.

```bash
python manage.py runserver
```

운영에서는 Reverse Proxy + Gunicorn + Django 구조로 구성한다.

---

## 10. PostgreSQL 설정 계획

초기에는 Django와 PostgreSQL을 동일 서버에서 운영한다.

- [ ] DB 이름 결정
- [ ] DB User 결정
- [ ] DB Password 정책 결정
- [ ] PostgreSQL Volume 설정
- [ ] Encoding 확인
- [ ] Timezone 설정
- [ ] DB Backup Script 작성
- [ ] DB Restore Test 수행

PostgreSQL 데이터는 Container 내부에만 저장하지 않고 별도 Volume으로 유지한다.

```yaml
volumes:
  postgres_data:
```

Container 삭제/재생성 시에도 DB 데이터가 유지되어야 한다.

---

## 11. 백업 계획

최소 백업 대상:

- PostgreSQL DB
- Django Media
- 환경 설정
- Docker Compose 설정

기본 방향:

```text
매일 PostgreSQL pg_dump
        ↓
날짜별 백업 생성
        ↓
일정 기간 보관
        ↓
정기 Restore Test
```

확정 필요 항목:

- [ ] 백업 주기
- [ ] 백업 저장 위치
- [ ] 보관 기간
- [ ] 서버 외부 추가 백업 여부
- [ ] 실제 복구 테스트

> 백업 파일 존재 여부만 확인하지 않고 실제 복구 가능 여부까지 검증한다.

---

## 12. 도메인 / HTTPS 계획

운영 서비스는 가능하면 IP 직접 접속보다 도메인을 사용한다.

```text
Domain
  ↓
DNS
  ↓
고정 IP
  ↓
TCP 443
  ↓
Caddy / Nginx
  ↓
Django
```

확인사항:

- [ ] 사용할 도메인 결정
- [ ] Subdomain 사용 여부
- [ ] DNS 관리 담당자 확인
- [ ] A Record 설정
- [ ] HTTPS 인증서 적용
- [ ] 인증서 자동 갱신

---

## 13. 작업 우선순위

### Phase 1 — USB 없이 즉시 진행

#### Network
- [ ] 고정 IP 확보
- [x] MAC Address 전달
- [ ] Subnet Mask 확보
- [ ] Gateway 확보
- [ ] DNS 확보
- [ ] 80/443 Port 확인
- [ ] LAN 연결 위치 확인

#### Server Design
- [ ] 배포 아키텍처 확정
- [ ] Docker Compose 구조 결정
- [ ] Reverse Proxy 결정
- [ ] 환경변수 목록 작성
- [ ] Django 운영 설정 정리
- [ ] PostgreSQL 설정 정리
- [ ] Volume 구조 결정
- [ ] Backup 정책 결정
- [ ] Firewall 정책 결정
- [ ] Domain/HTTPS 정책 결정

### Phase 2 — USB 확보 후

- [ ] Ubuntu Server ISO 다운로드
- [ ] Ubuntu Boot USB 제작
- [ ] 기존 Windows 데이터 백업 여부 최종 확인
- [ ] BIOS Boot 설정 확인
- [ ] Ubuntu Server 설치
- [ ] Ubuntu Update
- [ ] 고정 IP 적용
- [ ] SSH 설정
- [ ] UFW 설정
- [ ] Docker / Docker Compose 설치
- [ ] Django 배포
- [ ] PostgreSQL 배포
- [ ] Migration 실행
- [ ] Static File 설정
- [ ] Reverse Proxy 구성
- [ ] Domain 연결
- [ ] HTTPS 적용
- [ ] 외부 접속 테스트

### Phase 3 — 운영 검증

#### 기능 검증
- [ ] 로그인
- [ ] 주요 API
- [ ] DB 저장/조회
- [ ] 관리자 기능
- [ ] 파일 업로드
- [ ] 로그 확인

#### 서버 검증
- [ ] 서버 재부팅 후 서비스 자동 실행
- [ ] Docker Container 자동 실행
- [ ] DB 데이터 유지
- [ ] HTTPS 정상 접속
- [ ] 방화벽 확인
- [ ] 외부 접속 확인

#### 장애 대응 검증
- [ ] Django Container 재시작
- [ ] PostgreSQL Container 재시작
- [ ] 서버 재부팅
- [ ] DB Backup
- [ ] DB Restore

#### 사용자 검증
- [ ] 다중 사용자 접속 테스트
- [ ] 주요 화면 응답속도 확인
- [ ] 동시 요청 테스트
- [ ] CPU/RAM 사용량 확인

---

## 14. 역할 분담 예시

| 영역 | 주요 작업 |
|---|---|
| Network | 고정 IP / MAC / Gateway / DNS / Port 확인 |
| Infra | Ubuntu / Docker / Firewall / SSH |
| Backend | Django 운영 설정 / Gunicorn |
| DB | PostgreSQL / Volume / Backup |
| Domain | DNS / Domain / HTTPS |
| QA | 접속 / 장애 / 부하 / 복구 테스트 |

네트워크 확인과 애플리케이션 설정을 병렬로 진행해 전체 구축 시간을 단축한다.

---

## 15. 현재 Blocking 사항

### Blocker 1 — Ubuntu 설치 USB

**상태:** 미확보

**해결 방법:** 8GB 이상 USB 구매 후 Ubuntu Server Boot USB 제작

**영향:** Ubuntu 직접 설치만 대기 상태이며 사전 서버 구성/설계 작업은 진행 가능

### Blocker 2 — 네트워크 정보

**상태:** 담당자 확인 중

필요 정보:

- 고정 IP
- Subnet Mask
- Default Gateway
- DNS
- TCP 80/443
- 서버 LAN 위치

**영향:** Ubuntu 설치 자체는 가능하지만 외부 서비스 연결 및 HTTPS 적용에는 해당 정보가 필요함

---

## 16. 최종 진행 방향

```text
① 네트워크 담당자 정보 확인
         │
         ├───────────────┐
         │               │
         ▼               ▼
② 서버 설계 진행      USB 구매
         │               │
         ├───────────────┘
         ▼
③ Ubuntu 설치
         ↓
④ Docker 구성
         ↓
⑤ Django + PostgreSQL 배포
         ↓
⑥ Network / Domain / HTTPS
         ↓
⑦ Backup / Firewall
         ↓
⑧ 운영 검증
```

USB 확보 대기 때문에 전체 프로젝트를 중단하지 않고, 사전에 결정 가능한 항목을 먼저 완료한 뒤 Ubuntu 설치 직후 실제 설정값을 적용하는 방향으로 진행한다.
