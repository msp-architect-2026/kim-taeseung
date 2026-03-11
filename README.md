# 🔮 Kube-Fortune 

<div align="center">
  <img src="https://capsule-render.vercel.app/api?type=soft&color=0f172a&height=250&section=header&text=Kube-Fortune&fontSize=70&animation=fadeIn&fontColor=a8a2f8&desc=개발자를%20위한%20AI%20운세%20및%20인프라%20무드등%20대시보드&descSize=20&descAlignY=75" alt="header" />
</div>
<br>
<div align="center">

> **개발자를 위한 AI 운세 & 실시간 인프라 상태 모니터링 대시보드**
>
> 온프레미스 Kubernetes(ARM64) 환경에서 MSA 기반 웹 애플리케이션을 구축하고, GitOps 파이프라인, 외부 AI API(Gemini), 그리고 **데이터 영속성(Persistent Volume)** 연동을 직접 시연하기 위해 구축한 프로젝트입니다.

</div>

<br>

## 🛠️ Tech Stack

<div align="center">
  <img src="https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB"> 
  <img src="https://img.shields.io/badge/Vite-646CFF?style=for-the-badge&logo=vite&logoColor=white"> 
  <img src="https://img.shields.io/badge/Tailwind_CSS-38B2AC?style=for-the-badge&logo=tailwind-css&logoColor=white"> 
  <br>
  
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white"> 
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white"> 
  <img src="https://img.shields.io/badge/Gunicorn-499848?style=for-the-badge&logo=gunicorn&logoColor=white"> 
  <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google&logoColor=white"> 
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white"> 
  <img src="https://img.shields.io/badge/DBUtils-4479A1?style=for-the-badge&logo=python&logoColor=white">
  <br>
  
  <img src="https://img.shields.io/badge/Ubuntu_22.04-E95420?style=for-the-badge&logo=ubuntu&logoColor=white"> 
  <img src="https://img.shields.io/badge/Kubernetes-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white"> 
  <img src="https://img.shields.io/badge/MetalLB-326CE5?style=for-the-badge&logo=kubernetes&logoColor=white"> 
  <img src="https://img.shields.io/badge/Helm-0F1689?style=for-the-badge&logo=helm&logoColor=white"> 
  <img src="https://img.shields.io/badge/NGINX-009639?style=for-the-badge&logo=nginx&logoColor=white"> 
  <br>
  
  <img src="https://img.shields.io/badge/GitLab-FC6D26?style=for-the-badge&logo=gitlab&logoColor=white"> 
  <img src="https://img.shields.io/badge/ArgoCD-EF7B4D?style=for-the-badge&logo=argo&logoColor=white"> 
  <img src="https://img.shields.io/badge/Ansible-EE0000?style=for-the-badge&logo=ansible&logoColor=white"> 
  <img src="https://img.shields.io/badge/k6-7D64FF?style=for-the-badge&logo=k6&logoColor=white">
</div>

<br>

---

## 💡 프로젝트 개요 (Overview)

Kube-Fortune은 표면적으로는 클러스터의 상태를 시각화하여 개발자들에게 소소한 즐거움을 제공하는 애플리케이션입니다. 하지만 이를 지탱하는 인프라는 클라우드 관리형 서비스(EKS, GKE)에 의존하지 않고, 제한된 온프레미스 자원 안에서 **고가용성, 무중단 배포, 데이터 영속성** 등 실제 엔터프라이즈 환경의 요구사항을 밑바닥부터 구현하고 검증하는 데 목적을 두었습니다.

---

## ✨ 핵심 기능 (Features & UI)

* 🔮 **AI 사주풀이 (Gemini 연동):** 이름, 직군 등을 입력하면 AI가 '버그, 배포, 커밋' 등 개발자 친화적인 용어를 섞어 맞춤형 운세를 제공합니다.
* 🚥 **인프라 무드등 (Observability):** K8s 파드의 실시간 CPU 사용량(millicores)을 측정해 대시보드 상단의 이모지와 색상이 💤 idle → 👨‍💻 normal → 🔥 hot 상태로 변화합니다.
* 💾 **사주 보관함 (Stateful DB):** K8s PV(Persistent Volume)와 MySQL을 연동하여, 파드가 예기치 않게 종료되거나 재시작되어도 사용자의 사주 데이터가 절대 유실되지 않습니다.
* ⚖️ **로드밸런싱 배지:** 화면 하단에 현재 응답을 처리한 실제 백엔드 파드의 호스트명(Hostname)을 실시간으로 출력하여 K8s의 트래픽 라우팅을 시각적으로 증명합니다.

---

## 🚀 기술적 핵심 성과 (Architecture Highlights)

단순한 기능 구현을 넘어, 인프라 아키텍트 관점에서 시스템의 신뢰성과 성능을 극대화했습니다.

1. **완전한 GitOps 파이프라인 (CI/CD)**
   * `git push` 한 번으로 GitLab CI가 ARM64 호환 도커 이미지를 자체 빌드합니다. 
   * ArgoCD가 변경 사항을 감지해 K8s 클러스터에 사람의 개입 없이 무중단으로 자동 배포합니다.
2. **애플리케이션 레벨 성능 최적화 (TPS 95% 향상)**
   * k6를 활용한 500명 동시 접속 부하 테스트 중 DB 커넥션 경합으로 인한 병목을 발견했습니다.
   * DBUtils 커넥션 풀을 도입하여 인프라 확장 없이 **TPS를 95% 향상(932 → 1,817 req/s)**시키고, p90 응답시간을 절반(802ms → 403ms)으로 단축했습니다.
3. **온프레미스 고가용성 (HA) 및 자동 복구**
   * 클라우드 환경 없이 MetalLB를 도입하여 노드 장애 시에도 유지되는 단일 진입점(VIP)을 구축했습니다.
   * 노드 셧다운 테스트 결과, 파드 장애 시 K8s의 Self-Healing 메커니즘을 통해 약 10초 내에 트래픽 중단 없이 서비스가 자동 복구됨을 검증했습니다.

---
## 🎮 Quick Start (Local Demo)

> K8s 클러스터 없이 Docker Compose만으로 Kube-Fortune을 로컬에서 체험할 수 있습니다.

<details>
<summary>📖 설치 및 실행 가이드 펼치기</summary>

### 사전 준비

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) 설치 (Mac / Windows 공통)
- [Google Gemini API Key](https://aistudio.google.com/) 발급

### 1단계. 저장소 클론

```bash
git clone https://github.com/msp-architect-2026/kim-taeseung.git
cd kube-fortune
```

### 2단계. 환경변수 설정

> ⚠️ **이 단계를 건너뛰면 운세 생성 기능이 동작하지 않습니다.**

**Mac / Linux**
```bash
cp .env.example .env
```

**Windows**
```bash
copy .env.example .env
```

이후 `.env` 파일을 열어 발급받은 Gemini API Key를 입력합니다.

```
GEMINI_API_KEY=여기에_실제_API_Key_입력
```

### 3단계. 실행

```bash
docker compose -f docker-compose.local.yml up --build
```

> MySQL 초기화가 완료될 때까지 약 30~60초 소요됩니다.

### 4단계. 브라우저 접속

```
http://localhost:5173
```

### 종료

```bash
docker compose -f docker-compose.local.yml down
```

데이터(MySQL 볼륨)까지 완전히 삭제하려면:

```bash
docker compose -f docker-compose.local.yml down -v
```

### 포트 사용 현황

| 서비스 | 포트 |
| :--- | :--- |
| Frontend (React) | 5173 |
| Backend (Flask) | 5001 |
| MySQL | 3306 |

> 위 포트가 이미 사용 중이라면 `docker-compose.local.yml`에서 포트 번호를 변경하세요.

</details>

---

## 📚 상세 문서 및 회고 (Wiki)

아키텍처 도면부터 부하 테스트 리포트까지, 프로젝트의 모든 의사결정과 엔지니어링 기록은 아래 Wiki에 상세히 문서화되어 있습니다. 관심 있는 주제의 링크를 클릭하여 상세한 내용을 확인해 보세요.

* **[🏠 Home (프로젝트 위키 홈)](https://github.com/msp-architect-2026/kim-taeseung/wiki)**
  * 전체 위키 문서의 네비게이션 허브 역할을 하며, 각 엔지니어링 단계별 상세 문서로 바로 이동할 수 있는 인덱스를 제공합니다.

* **[🎯 Project Story & Features (기획 의도 및 서비스 소개)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Project-Story-and-Features)**
  * 단순한 새로고침(F5)을 막기 위한 인프라 무드등부터, 트래픽 라우팅을 증명하는 LB 배지까지 Kube-Fortune이 탄생하게 된 기획 의도와 6대 핵심 기술 목표를 소개합니다.

* **[🛠️ Tech Stack & Decisions (기술 선정 배경)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Tech-Stack-and-Decisions)**
  * 왜 클릭 몇 번으로 가능한 관리형 클라우드를 두고 온프레미스 `kubeadm`을 선택했는지, 무거운 Docker Engine 대신 `containerd`를 도입한 이유가 무엇인지 등 각 기술 스택의 트레이드오프(Trade-offs)와 엄밀한 선정 배경을 다룹니다.

* **[🏛️ Architecture (아키텍처 설계 및 트래픽 흐름)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Architecture)**
  * 시스템 토폴로지 도면을 바탕으로 Inbound/Outbound 네트워크 트래픽 흐름, RESTful API 명세, 동적으로 초기화되는 DB 스키마, 그리고 상태(Stateful) 관리 전략의 진화 과정을 설명합니다.

* **[🖥️ Infrastructure Setup (클러스터 구성 및 환경 명세)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Infrastructure-Setup)**
  * 클라우드 의존 없이 UTM 가상화(ARM64) 환경에서 마스터/워커 노드를 직접 분리 구축한 과정과 containerd 런타임, Flannel CNI 등 온프레미스 K8s 클러스터를 바닥부터 프로비저닝한 상세 명세가 담겨 있습니다.

* **[🚀 CI/CD Pipeline (GitLab & ArgoCD 파이프라인)](https://github.com/msp-architect-2026/kim-taeseung/wiki/CI-CD-Pipeline)**
  * ARM64 호환 이미지를 구워내는 GitLab Runner(DinD) 기반의 CI 자동화와, Kubeconfig 노출 위험을 원천 차단한 ArgoCD의 Pull 방식 GitOps 무중단 배포(CD) 파이프라인 구조를 설명합니다.
  
* **[📈 Scenario & Testing (HA 시나리오 검증 및 k6 부하 테스트)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Scenario-and-Testing)**
  * 동시 접속자 500명을 가정한 k6 부하 테스트(HPA 자동 스케일 아웃 검증) 결과와, 파드 삭제부터 워커 노드 셧다운에 이르는 4단계의 K8s 고가용성(HA) 장애 복구 시나리오를 정량적으로 검증한 리포트입니다.
  
* **[⚡ Performance Improvement (DB 커넥션 풀 등 성능 개선 기록)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Performance-Improvement)**
  * 부하 테스트 중 발견된 애플리케이션 병목을 DB 커넥션 풀 도입으로 해결하여 TPS를 95% 향상시킨 사례, 그리고 StatefulSet의 재배치 지연 현상을 자동화하여 복구 시간을 단축한 성능 최적화 과정을 기록했습니다.
  
* **[🔥 Troubleshooting (문제 해결 및 회고)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Troubleshooting)**
  * AI 프롬프트 누수로 인한 UI 렌더링 실패, 온프레미스 DinD 환경의 BuildKit 인증 장애, 노드 재부팅 시 발생한 CNI(Flannel) 데드락 및 연쇄 통신 장애 등 인프라 구축 과정에서 겪은 치열한 문제 해결(Troubleshooting) 과정을 아키텍트의 시선으로 풀어냈습니다.
  
* **[📝 Meetings & Feedback (멘토링 회의록)](https://github.com/msp-architect-2026/kim-taeseung/wiki/Meetings-and-Feedback)**
  * 주간 회의 및 멘토링을 통해 도출된 K8s 재해 복구(DR) 대비책, 부하 테스트 타겟 재조정 등 날카로운 피드백과 이를 실제 아키텍처에 반영하며 프로젝트를 고도화해 나간 성장 기록입니다.
