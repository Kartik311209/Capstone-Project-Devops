# DevOps Capstone Project Report
## PulseTrack: End-to-End DevOps Automation Platform

**Course:** DevOps Engineering Capstone (120 Marks)  
**Project Name:** PulseTrack — Cloud-Native Task & Incident Telemetry Platform  
**Repository:** `Capstone_devops`  

---

## 1. Problem Statement
Modern software delivery requires rapid, repeatable, and safe releases without sacrificing security or observability. Manual builds, ad-hoc server configuration, unmonitored deployments, and all-at-once cutovers lead to configuration drift, undetected vulnerabilities, slow incident detection, and high-blast-radius outages.

**Objective:** Design and implement a complete, reproducible, end-to-end DevOps automation platform for a chosen microservice (**PulseTrack**) that automates the full lifecycle from `git push` to production Canary rollout, with built-in infrastructure automation, security gates, centralized logging, metrics/alerting, and automated rollback.

---

## 2. System Design & Architecture

### 2.1 End-to-End Delivery Flow
1. **Version Control (Git):** Feature-branch workflow with structured commits, `.gitignore`, and protected `main` branch.
2. **CI/CD Pipeline (GitHub Actions):**
   - `.github/workflows/ci-cd.yml`: Automated linting (`ruff`), SAST (`bandit`), secret scanning (`gitleaks`), unit/integration testing (`pytest` + coverage), multi-stage Docker build, and filesystem/image vulnerability scanning (`trivy` on `CRITICAL,HIGH`).
   - `.github/workflows/terraform-validate.yml`: Automated `terraform fmt -check` and `terraform validate` on infrastructure PRs.
3. **Application Layer (`app/main.py`):**
   - Python **FastAPI** microservice exposing REST endpoints (`/api/v1/tasks`, `/api/v1/incidents`, `/api/v1/version`), Kubernetes probes (`/health/live`, `/health/ready`), Prometheus metrics (`/metrics`), and a built-in live status dashboard (`/`).
   - Emits **structured JSON logs** with `request_id`, `track`, `status_code`, and `latency_ms`.
4. **Containerization (`Dockerfile`, `docker-compose.yml`):**
   - Multi-stage `python:3.12-slim` build, non-root user (`appuser`, UID `10001`), OCI labels, and container `HEALTHCHECK`.
5. **Kubernetes Orchestration (`k8s/`):**
   - Kustomize base + `staging` & `production` overlays.
   - Includes `Namespace` (with `pod-security.kubernetes.io/enforce: restricted`), `Deployment`, `Service`, `Ingress`, `HorizontalPodAutoscaler`, `PodDisruptionBudget`, `RBAC` (`ServiceAccount`, `Role`, `RoleBinding`), and `NetworkPolicy`.
6. **Advanced Deployment Strategy (`k8s/canary/rollout.yaml` & `observability/nginx/canary.conf`):**
   - **Argo Rollouts Canary** (`10% -> 50% -> 100%`) gated by a Prometheus `AnalysisTemplate` (`success-rate >= 0.98`) for automated rollback.
   - Local **Blue-Green / Weighted Canary** router via Nginx (`80%` Blue v1.0.0 / `20%` Green v1.1.0-canary) controlled by `scripts/canary-switch.ps1`.
7. **Infrastructure Automation (`infra/`):**
   - **Terraform (`infra/terraform/`):** Provisions AWS VPC, private subnets across AZs, immutable ECR repository with scan-on-push & AES256 encryption, and worker security groups.
   - **Ansible (`infra/ansible/`):** Hardens Linux nodes (`ufw` default-deny, `fail2ban`, dedicated `pulsetrack` user) and deploys Prometheus `node-exporter`.
8. **Observability (`observability/`):**
   - **Prometheus:** Scrapes `/metrics` every 15s and evaluates SLO alert rules (`PulseTrackInstanceDown`, `PulseTrackHighErrorRate`, `PulseTrackHighLatencyP95`).
   - **Grafana:** Auto-provisioned Prometheus & Loki datasources plus a 4-panel `PulseTrack - DevOps Capstone Observability` dashboard.
   - **Loki + Promtail:** Aggregates and indexes structured JSON application logs.

---

## 3. Implementation Evidence

| Component | Key Files | Purpose |
| :--- | :--- | :--- |
| Application & Tests | `app/main.py`, `tests/test_app.py` | FastAPI telemetry service, `/metrics`, JSON logs, 5 automated tests |
| Containerization | `Dockerfile`, `docker-compose.yml`, `.dockerignore` | Multi-stage non-root image + 7-container local observability stack |
| CI/CD Pipelines | `.github/workflows/ci-cd.yml`, `terraform-validate.yml` | Automated lint, SAST, secret scan, tests, Trivy scan, Canary deploy |
| Kubernetes | `k8s/base/*`, `k8s/overlays/*`, `k8s/canary/rollout.yaml` | Production-hardened K8s manifests + Argo Rollouts Canary |
| IaC & Config Mgmt | `infra/terraform/*.tf`, `infra/ansible/site.yml` | Cloud network/registry provisioning & OS/monitoring automation |
| Observability | `observability/prometheus/*`, `grafana/*`, `loki/*`, `promtail/*` | Metrics, SLO alerts, dashboards, and centralized log pipeline |
| Sample Data & Logs | `samples/app-sample.log`, `samples/sample-payloads.json` | Reproducible JSON log lines and API test payloads |

---

## 4. Security Controls Built-In
- **Supply Chain & Code:** `ruff` linting, `bandit` SAST, `gitleaks` secret detection, `trivy` vulnerability & IaC scanning.
- **Container Hardening:** Multi-stage build (no build tools in runtime), non-root UID `10001`, `.dockerignore` excluding secrets/docs.
- **Kubernetes Hardening:** Pod Security `restricted` enforcement, `runAsNonRoot: true`, `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, dropped capabilities (`ALL`), `automountServiceAccountToken: false`, least-privilege `Role`, and default-restricted `NetworkPolicy`.
- **Host & Cloud Hardening:** Ansible `ufw` + `fail2ban`; Terraform immutable ECR tags, AES256 encryption, and `scan_on_push = true`.

---

## 5. Testing, Verification & Live Screenshots
- **Automated Unit & Integration Tests (`pytest`):** All 5 test suites (`test_health_endpoints`, `test_version_and_dashboard`, `test_metrics_endpoint`, `test_task_crud_lifecycle`, `test_incident_reporting`) verified passing with **95% coverage**.
- **Static Analysis & Security (`ruff`, `bandit`, `secret_guard.py`):** Zero lint errors, zero medium/high security findings, and zero hardcoded secrets.
- **Kubernetes Manifest Validation (`kubectl kustomize`):** `k8s/base`, `k8s/overlays/staging`, and `k8s/overlays/production` render cleanly with zero schema/overlay errors.
- **Live Application Screenshots (`screenshots/`):**
  - `screenshots/01-live-dashboard.png` — Live PulseTrack Web Dashboard (`/`)
  - `screenshots/02-swagger-api-docs.png` — Live Interactive Swagger / OpenAPI 3.1 UI (`/docs`)
  - `screenshots/03-prometheus-metrics.png` — Live Prometheus `/metrics` Exposition
  - `screenshots/04-tasks-api-json.png` — Live Tasks REST API JSON Response (`/api/v1/tasks`)
  - `screenshots/05-powershell-tests-security.png` — Real PowerShell Execution: Pytest Suite & 95% Coverage
  - `screenshots/06-powershell-canary-dr.png` — Real PowerShell Execution: Canary Rollout, SecretGuard & DR Backup

---

## 6. Conclusion
PulseTrack successfully unifies every core DevOps pillar—version control, automated CI/CD, containerization, Kubernetes orchestration, Infrastructure as Code, observability, security, and progressive Canary/Blue-Green delivery—into a single, reproducible, production-ready platform.
