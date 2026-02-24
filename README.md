# 🔮 Kube-Fortune 

> **개발자를 위한 AI 운세 & 인프라 무드등 대시보드**
>
> 온프레미스 Kubernetes(ARM64) 환경에서 MSA 기반 웹 애플리케이션을 구축하고, GitOps 파이프라인과 외부 AI API(Gemini), 그리고 **데이터 영속성(Persistent Volume)** 연동을 시연하기 위한 포트폴리오 프로젝트입니다.

---

## 1. 프로젝트 개요
Kube-Fortune은 단순한 운세 서비스를 넘어, 쿠버네티스 클러스터의 상태를 유머러스하게 시각화하고 사용자 데이터를 안전하게 관리하는 Stateful 웹 애플리케이션입니다. 

- **프론트엔드 (React):** 점진적 정보 공개(Progressive Disclosure) UI 및 Nginx 기반 정적 서빙
- **백엔드 (Flask):** K8s Metrics API 연동, Google Gemini API 프롬프트 엔지니어링 및 MySQL ORM 제어
- **인프라:** ARM64 환경 기반의 온프레미스 K8s, GitOps (ArgoCD) 및 외부 트래픽 라우팅 (Ingress-Nginx)
- **데이터 영속성 (Stateful Architecture):** 초기 PoC 단계의 브라우저 `localStorage` 의존도를 벗어나, 클러스터 내부에 **MySQL** 데이터베이스를 배포했습니다. Kubernetes의 **PV(Persistent Volume) 및 PVC**를 연동하여, 파드가 삭제되거나 재시작되더라도 사용자의 닉네임과 사주 보관함 데이터가 영구적으로 보존되는 엔터프라이즈급 상태 유지(Stateful) 아키텍처를 구현했습니다.



---

## 2. 화면 구성 (Screen Composition)
애플리케이션 화면은 크게 4가지 핵심 기능 영역으로 나뉩니다.

1. **Header [인프라 무드등]:** K8s 파드의 실시간 CPU 사용량(millicores)을 측정하여 상태(쾌적, 보통, 위험)에 따라 이모지와 색상이 변하는 대시보드.
2. **Main [AI 사주풀이]:** 이름, 생년월일, 직군을 입력하면 Gemini AI가 개발자 맞춤형 용어(버그, 배포, 커밋 등)를 섞어 운세를 풀어주는 메인 기능.
3. **Tab [사주 보관함 & 가상 로그인]:** 닉네임 기반의 로그인 시스템을 통해 자신이 조회한 프리미엄 사주를 DB에 영구 저장하고, 언제든 다시 꺼내볼 수 있는 보관함 탭 기능.
4. **Footer [로드밸런싱 배지]:** K8s Service의 라우팅(Round-Robin)을 시각적으로 증명하기 위해, 현재 응답을 처리한 백엔드 파드의 실제 이름(Hostname)을 실시간 출력.

---

## 3. API 명세 (API Specification)
백엔드(`fortune-backend-svc:5000`)에서 프론트엔드와 통신하기 위해 제공하는 RESTful API 목록입니다.

| Method | Endpoint | Description | Request Body / Params |
| :--- | :--- | :--- | :--- |
| **GET** | `/api/health` | 파드 헬스체크 (Liveness/Readiness) | - |
| **GET** | `/api/status` | 파드 CPU 메트릭 및 무드등 상태 조회 | - |
| **POST** | `/api/fortune` | 사용자 정보 기반 AI 운세 생성 | `{"name": "...", "birthday": "...", "role": "..."}` |
| **POST** | `/api/login` | 닉네임 확인 및 신규 사용자 DB 등록 | `{"nickname": "버그킬러"}` |
| **POST** | `/api/fortunes/save` | 운세 결과를 MySQL 보관함에 영구 저장 | `{"nickname": "...", "fortune": "...", ...}` |
| **GET** | `/api/fortunes/<nickname>` | 특정 사용자의 전체 운세 보관함 리스트 조회 | URL Parameter: `nickname` |
| **DELETE**| `/api/fortunes/<nickname>/<id>`| 보관함 내 특정 운세 내역 단건 삭제 | URL Parameter: `nickname`, `id` |

---

## 4. 데이터베이스 스키마 (Database Schema)
데이터 영속성을 보장하기 위해 도입된 K8s 내부 MySQL의 핵심 테이블 구조입니다. (앱 기동 시 백엔드 컨테이너가 10회 재시도 로직을 통해 자동 초기화 및 테이블 생성을 수행합니다.)

* **`users` Table:** 서비스에 접근한 사용자(닉네임) 정보 관리
  * `id` (PK), `nickname` (Unique), `created_at`
* **`fortunes` Table:** 사용자가 저장한 사주 결과 및 메타데이터 관리
  * `id` (PK), `nickname` (Index), `person_name`, `role`, `birthday`, `fortune_text` (LongText), `pod`, `saved_at`

---

## 5. 상세 문서 (Wiki)
아키텍처 토폴로지, 인프라 프로비저닝, DB 볼륨 마운트 그리고 CI/CD 파이프라인의 상세한 구축 과정은 본 리포지토리의 [Wiki] 탭에서 확인할 수 있습니다.

* [🏠 Home (프로젝트 개요)](https://github.com/msp-architect-2026/kim-taeseung/wiki)
* [🛠️ Tech Stack & Decisions (기술 스택 및 선정 배경)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Tech-Stack-and-Decisions)
* [🏛️ Architecture(아키텍처 설계 및 트래픽 흐름)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Architecture)
* [🖥️ Infrastructure Setup(클러스터 구성 및 환경 명세)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Infrastructure-Setup)
* [🚀 CI/CD Pipeline(배포 자동화 및 GitOps)](https://github.com/msp-architect-2026/kim-taeseung/wiki/CI-CD-Pipeline)
* [🔥 Troubleshooting(문제 해결 및 회고)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Troubleshooting)
