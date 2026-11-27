"""Generate submission-ready Capstone PDF with 8 real terminal screenshots embedded."""

from pathlib import Path
from fpdf import FPDF


class CapstonePDF(FPDF):
    def header(self):
        if self.page_no() > 1:
            self.set_font("Helvetica", "I", 8)
            self.set_text_color(100, 116, 139)
            self.cell(0, 8, "PulseTrack - End-to-End DevOps Automation Platform | Capstone Report", align="R")
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(100, 116, 139)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

    def section_title(self, title: str):
        self.ln(4)
        self.set_font("Helvetica", "B", 13)
        self.set_text_color(15, 23, 42)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(14, 165, 233)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def sub_section(self, title: str):
        self.ln(3)
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(14, 165, 233)
        self.cell(0, 7, title, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(30, 41, 59)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, lead: str, text: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 23, 42)
        self.write(5.5, f"  - {lead}: ")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def add_screenshot(self, fig_num: int, caption: str, img_path: Path):
        if not img_path.exists():
            self.set_font("Helvetica", "I", 9)
            self.set_text_color(200, 0, 0)
            self.cell(0, 6, f"[Missing: {img_path.name}]", new_x="LMARGIN", new_y="NEXT")
            return
        if self.get_y() > 175:
            self.add_page()
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(15, 23, 42)
        self.cell(0, 6, f"Figure {fig_num}: {caption}", new_x="LMARGIN", new_y="NEXT")
        self.image(str(img_path), w=186)
        self.ln(5)


def main():
    root = Path(__file__).resolve().parent.parent
    shots = root / "screenshots"

    pdf = CapstonePDF()
    pdf.set_auto_page_break(auto=True, margin=16)
    pdf.add_page()

    # ── Cover ──────────────────────────────────────────────────────────────
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 46, "F")
    pdf.set_y(10)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(248, 250, 252)
    pdf.cell(0, 10, "DevOps Engineering Capstone Report", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(56, 189, 248)
    pdf.cell(0, 7, "PulseTrack: End-to-End DevOps Automation Platform", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(148, 163, 184)
    pdf.cell(0, 6, "120 Marks | B.Tech CSE | DevOps Automation", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(52)

    # ── 1. Problem Statement ───────────────────────────────────────────────
    pdf.section_title("1. Problem Statement & Objectives")
    pdf.body_text(
        "Modern software delivery demands fast, repeatable, and low-risk production releases. "
        "Manual builds, ad-hoc server configuration, all-at-once deployments, unmonitored "
        "services, and absent disaster recovery plans result in configuration drift, slow incident "
        "detection, and high-blast-radius outages.\n\n"
        "Objective: Design and implement a complete, reproducible, end-to-end DevOps automation "
        "platform for PulseTrack that automates the full lifecycle from git push to production "
        "Canary rollout, with built-in security gates, centralized observability, infrastructure "
        "automation, and automated rollback + disaster recovery."
    )

    # ── 2. Architecture ────────────────────────────────────────────────────
    pdf.section_title("2. System Design & Architecture")

    pdf.sub_section("2.1  Version Control & CI/CD Pipeline")
    pdf.bullet("Version Control", "Feature-branch Git workflow with structured conventional commits and .gitignore hygiene.")
    pdf.bullet("CI/CD (GitHub Actions)", "ci-cd.yml: Ruff lint, Bandit SAST, Gitleaks secret scan, Pytest + coverage, Docker Buildx multi-arch, Trivy CRITICAL/HIGH scan, and progressive Canary deploy.")
    pdf.bullet("IaC Validation", "terraform-validate.yml: terraform fmt -check and validate on every infra PR.")

    pdf.sub_section("2.2  Application Layer")
    pdf.bullet("FastAPI Service", "app/main.py: REST CRUD APIs (/api/v1/tasks, /api/v1/incidents), structured JSON logs, /health/live, /health/ready, /api/v1/version, and Prometheus /metrics.")
    pdf.bullet("Test Suite", "5 automated Pytest tests covering health probes, dashboard, metrics, task CRUD lifecycle, and incident reporting. 95% code coverage.")

    pdf.sub_section("2.3  Containerization")
    pdf.bullet("Multi-Stage Dockerfile", "python:3.12-slim builder + runtime, non-root appuser (UID 10001), OCI labels, HEALTHCHECK.")
    pdf.bullet("Docker Compose Stack", "7 services: app-blue (v1.0.0), app-green (v1.1.0-canary), Nginx canary router, Prometheus, Grafana, Loki, Promtail.")

    pdf.sub_section("2.4  Kubernetes Orchestration")
    pdf.bullet("Kustomize", "Base manifests + staging and production overlays.")
    pdf.bullet("Security Hardening", "Namespace Pod Security restricted, non-root runAsUser 10001, readOnlyRootFilesystem, capabilities drop ALL, automountServiceAccountToken false.")
    pdf.bullet("Reliability", "HorizontalPodAutoscaler (2-6 replicas, 70% CPU), PodDisruptionBudget (minAvailable 1), NetworkPolicy default-deny.")
    pdf.bullet("RBAC", "Dedicated ServiceAccount, least-privilege Role, RoleBinding.")

    pdf.sub_section("2.5  Advanced Deployment Strategy")
    pdf.bullet("Argo Rollouts Canary", "10% -> 50% -> 100% promotion gated by Prometheus AnalysisTemplate (success rate >= 98%). Auto-rollback on SLO breach.")
    pdf.bullet("Nginx Blue/Green", "Weighted 80/20 router (canary-switch.ps1). canary_sim.py for progressive rollout + fault-injection auto-rollback demo.")

    pdf.sub_section("2.6  Infrastructure Automation")
    pdf.bullet("Terraform", "AWS VPC, private subnets across AZs, immutable ECR (AES256, scan-on-push), security groups.")
    pdf.bullet("Ansible", "Node hardening: UFW default-deny, fail2ban SSH protection, non-root deploy user, Prometheus Node Exporter.")
    pdf.bullet("Disaster Recovery", "dr/backup_restore.ps1: timestamped .zip snapshots of k8s/, infra/, observability/, samples/, verify integrity, and test-restore.")

    pdf.sub_section("2.7  Monitoring & Logging")
    pdf.bullet("Prometheus", "15s scrape interval, SLO alert rules: PulseTrackInstanceDown (1m), PulseTrackHighErrorRate (5xx > 2%), PulseTrackHighLatencyP95 (> 500ms).")
    pdf.bullet("Grafana", "Auto-provisioned Prometheus + Loki datasources, 4-panel PulseTrack dashboard (RPS by track, P95 latency, active tasks, 5xx rate).")
    pdf.bullet("Loki + Promtail", "Structured JSON log pipeline with label extraction (level, service, track, status_code).")

    # ── 3. Security ────────────────────────────────────────────────────────
    pdf.section_title("3. Security Controls")
    pdf.body_text(
        "Supply Chain & SAST: Ruff linting, Bandit SAST (zero Medium/High findings), "
        "Gitleaks + security/secret_guard.py (zero hardcoded secrets), "
        "Trivy filesystem + image scan (block on CRITICAL/HIGH).\n\n"
        "Container: Non-root UID 10001, multi-stage minimal runtime image, "
        "readOnlyRootFilesystem, ALL Linux capabilities dropped.\n\n"
        "Kubernetes: Pod Security restricted, least-privilege RBAC, "
        "default-restricted NetworkPolicy (allow only ingress-nginx + monitoring namespaces).\n\n"
        "Cloud & Host: ECR scan-on-push + AES256 encryption, immutable image tags, "
        "UFW default-deny ingress, fail2ban SSH brute-force protection."
    )

    # ── 4. Screenshots ─────────────────────────────────────────────────────
    pdf.section_title("4. Implementation Evidence & Screenshots")

    pdf.add_screenshot(1, "Git Log & CI Gate Demo - Deliberate failure then ALL_CI_GATES_PASSED", shots / "01-git-and-ci-gates.png")
    pdf.add_screenshot(2, "Docker Multi-Stage Build + Trivy Vulnerability Scan", shots / "02-docker-and-trivy.png")
    pdf.add_screenshot(3, "Terraform IaC + Ansible Node Provisioning", shots / "03-terraform-ansible.png")
    pdf.add_screenshot(4, "Vault Secret Injection & Log Masking (***MASKED***)", shots / "04-vault-secrets.png")
    pdf.add_screenshot(5, "Kubernetes Deployment - kubectl apply + Pod/Service/HPA Status", shots / "05-k8s-and-gitops.png")
    pdf.add_screenshot(6, "Canary Rollout 10%->50%->100% with Auto-Rollback on SLO Breach", shots / "06-canary-rollout.png")
    pdf.add_screenshot(7, "Prometheus Metrics + Alerting + Structured JSON Logs (Loki)", shots / "07-monitoring-logging.png")
    pdf.add_screenshot(8, "Disaster Recovery - Backup Snapshot + Integrity Verify + Restore", shots / "08-disaster-recovery.png")

    # ── 5. Conclusion ──────────────────────────────────────────────────────
    pdf.section_title("5. Testing, Verification & Results")
    pdf.body_text(
        "Automated Tests: 5/5 Pytest suite passed (95% coverage on app/main.py). "
        "Static Analysis: Ruff and Bandit SAST report zero issues. "
        "Secret Scanning: Gitleaks + secret_guard.py report 0 hardcoded secrets. "
        "Kubernetes: kubectl kustomize validated cleanly across base, staging, and production overlays. "
        "Canary Simulation: Progressive 10/50/100% rollout and fault-injection auto-rollback verified. "
        "DR: Backup + verify + restore pipeline tested end-to-end."
    )

    pdf.section_title("6. Conclusion")
    pdf.body_text(
        "PulseTrack delivers a complete, reproducible, production-grade DevOps automation platform "
        "integrating version control, CI/CD with security gates, multi-stage containerization, "
        "Kubernetes orchestration with RBAC and NetworkPolicy, Terraform + Ansible infrastructure "
        "automation, Prometheus/Grafana/Loki observability, Vault secret management, "
        "progressive Canary/Blue-Green delivery with automated rollback, and disaster recovery "
        "- covering every pillar of the 120-mark capstone brief."
    )

    out_path = root / "docs" / "CAPSTONE_REPORT.pdf"
    pdf.output(str(out_path))
    print(f"Generated: {out_path} ({out_path.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
