# 🔮 Kube-Fortune 

> **개발자를 위한 AI 운세 & 인프라 무드등 대시보드**
> 온프레미스 Kubernetes(ARM64) 환경에서 MSA 기반 웹 애플리케이션을 구축하고, GitOps 파이프라인과 외부 AI API(Gemini) 연동을 시연하기 위한 포트폴리오 프로젝트입니다.

---

## 1. 프로젝트 개요
Kube-Fortune은 단순한 운세 서비스를 넘어, 쿠버네티스 클러스터의 상태를 유머러스하게 시각화하여 보여주는 웹 애플리케이션입니다. 

- **프론트엔드 (React):** 무상태(Stateless) UI 컴포넌트 렌더링 및 Nginx 정적 서빙
- **백엔드 (Flask):** K8s Metrics API 연동 및 Google Gemini API 프롬프트 엔지니어링 처리
- **인프라:** Mac M5(ARM64) 환경 기반의 온프레미스 K8s (kubeadm) 및 GitOps (ArgoCD)

---

## 2. 화면 구성 (Screen Composition)
애플리케이션 화면은 크게 3가지 핵심 기능 영역으로 나뉩니다.

1. **Header [인프라 무드등]:** K8s 파드의 실시간 CPU 사용량(millicores)을 측정하여 상태(쾌적, 보통, 위험)에 따라 이모지와 색상이 변하는 대시보드.
2. **Main [AI 사주풀이]:** 이름, 생년월일, 직군을 입력하면 Gemini AI가 개발자 맞춤형 용어(버그, 배포, 커밋 등)를 섞어 운세를 풀어주는 메인 기능.
3. **Footer [로드밸런싱 배지]:** K8s Service의 라우팅(Round-Robin)을 시각적으로 증명하기 위해, 현재 응답을 처리한 백엔드 파드의 실제 이름(Hostname)을 실시간 출력.

---

## 3. API 명세 (API Specification)
백엔드(`fortune-backend-svc:5000`)에서 제공하는 RESTful API 목록입니다.

| Method | Endpoint | Description | Request Body | Response (Success) |
| :--- | :--- | :--- | :--- | :--- |
| **GET** | `/api/health` | 파드 헬스체크 (Liveness/Readiness) | - | `{"status": "ok", "pod": "..."}` |
| **GET** | `/api/status` | 파드 CPU 메트릭 및 무드등 상태 조회 | - | `{"pod_name": "...", "cpu_millicores": 42.5, "mood": {...}}` |
| **POST** | `/api/fortune` | 사용자 정보 기반 AI 운세 생성 | `{"name": "...", "birthday": "...", "role": "..."}` | `{"fortune": "...", "pod": "..."}` |

---

## 4. 데이터 흐름 및 스키마 (Stateless Data Flow)
본 프로젝트는 시스템의 확장성(Scale-out)을 극대화하기 위해 DB가 없는 무상태(Stateless) 아키텍처로 설계되었습니다. 따라서 전통적인 ERD 대신, 컴포넌트 간의 핵심 데이터 페이로드 스키마를 정의합니다.

- **[Client ➡️ Backend] Fortune Request Payload**
  ```json
  {
    "name": "홍길동",
    "birthday": "1990-01-01",
    "role": "백엔드"
  }
- **[Backend ⬅️ K8s Metrics API]** 파드 리소스(CPU/Memory) 실시간 지표 수집
- **[Backend ↔️ Gemini API]** 개발자 컨텍스트가 주입된 프롬프트 송수신
- **[Backend ➡️ Client] Fortune Response Payload**
{
  "name": "홍길동",
  "role": "백엔드",
  "fortune": "오늘의 배포운: 별 5개! 에러 없는 무결점 커밋이 예상됩니다...",
  "pod": "fortune-backend-5d4f9b-xxxx"
}
---

## 5. 상세 문서 (Wiki)
아키텍처 토폴로지, 인프라 프로비저닝, 그리고 CI/CD 파이프라인의 상세한 구축 과정은 본 리포지토리의 [Wiki] 탭에서 확인할 수 있습니다.

* [🏛️ Architecture (아키텍처 설계 및 트래픽 흐름)](Architecture)
* [🖥️ Infrastructure Setup (클러스터 구성 및 환경 명세)](Infrastructure-Setup)
* [🚀 CI/CD Pipeline (배포 자동화 및 GitOps)](CI-CD-Pipeline)
* [🔥 Troubleshooting (문제 해결 및 회고)](Troubleshooting)
