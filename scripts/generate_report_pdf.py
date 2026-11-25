"""Generate a clean, submission-ready PDF version of the DevOps Capstone Report."""

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

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, text)
        self.ln(2)

    def bullet(self, lead: str, text: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(15, 23, 42)
        self.write(5.5, f"- {lead}: ")
        self.set_font("Helvetica", "", 10)
        self.set_text_color(30, 41, 59)
        self.multi_cell(0, 5.5, text)
        self.ln(1)


def main():
    pdf = CapstonePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # Cover Header
    pdf.set_fill_color(15, 23, 42)
    pdf.rect(0, 0, pdf.w, 42, "F")
    pdf.set_y(11)
    pdf.set_font("Helvetica", "B", 19)
    pdf.set_text_color(248, 250, 252)
    pdf.cell(0, 9, "DevOps Engineering Capstone Report (120 Marks)", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(56, 189, 248)
    pdf.cell(0, 7, "PulseTrack: End-to-End DevOps Automation Platform", new_x="LMARGIN", new_y="NEXT")
    pdf.set_y(48)

    pdf.section_title("1. Problem Statement & Objectives")
    pdf.body_text(
        "Modern software delivery demands fast, repeatable, and low-risk releases. Manual builds, "
        "configuration drift, unmonitored services, and all-at-once deployments increase outage risk "
        "and slow incident recovery. PulseTrack addresses this by automating the full software delivery "
        "lifecycle from Git commit to production Canary rollout with built-in security, observability, "
        "and automated rollback."
    )

    pdf.section_title("2. System Design & Architecture")
    pdf.bullet("Version Control", "Structured Git repository with feature-branch workflow and .gitignore hygiene.")
    pdf.bullet("Application Layer", "Python FastAPI service (app/main.py) with REST CRUD APIs, /health/live, /health/ready, /metrics (Prometheus), and structured JSON logging.")
    pdf.bullet("CI/CD Pipeline", "GitHub Actions (.github/workflows/ci-cd.yml) executing Ruff lint, Bandit SAST, Gitleaks secret scan, Pytest with coverage, Docker Buildx, Trivy scan, and Canary rollout.")
    pdf.bullet("Containerization", "Multi-stage Dockerfile (python:3.12-slim) running as non-root UID 10001 with HEALTHCHECK and 7-service docker-compose.yml stack.")
    pdf.bullet("Kubernetes Orchestration", "Kustomize base + staging/production overlays with Pod Security restricted enforcement, RBAC, NetworkPolicy, HPA, and PodDisruptionBudget.")
    pdf.bullet("Advanced Deployment", "Argo Rollouts Canary (10% -> 50% -> 100%) gated by Prometheus AnalysisTemplate (>=98% success rate) plus local Nginx Blue/Green 80/20 weighted router.")
    pdf.bullet("Infrastructure Automation", "Terraform (AWS VPC, private subnets, immutable encrypted ECR, security groups) and Ansible (UFW firewall, fail2ban, non-root deploy user, Node Exporter).")
    pdf.bullet("Monitoring & Logging", "Prometheus scrape & SLO alert rules, pre-provisioned Grafana dashboard, and Loki + Promtail structured JSON log pipeline.")

    pdf.section_title("3. Security Controls")
    pdf.body_text(
        "- Static & Supply Chain: Ruff, Bandit SAST, Gitleaks secret scanning, Trivy CRITICAL/HIGH gates.\n"
        "- Container Hardening: Non-root user (appuser), minimal runtime image, read-only K8s root filesystem, ALL Linux capabilities dropped.\n"
        "- Cluster & Cloud: Least-privilege K8s RBAC, default-restricted NetworkPolicy, UFW default-deny, ECR scan-on-push and AES256 encryption."
    )

    pdf.section_title("4. Testing, Verification & Evidence")
    pdf.body_text(
        "- Automated Pytest Suite: 5/5 tests passing (health probes, version/dashboard, Prometheus /metrics, task CRUD lifecycle, incident reporting).\n"
        "- Static Quality & Security: Ruff check and Bandit SAST pass with zero findings.\n"
        "- Kubernetes Manifests: kubectl kustomize validated cleanly across base, staging, and production overlays.\n"
        "- Sample Data & Logs: Provided in samples/app-sample.log and samples/sample-payloads.json."
    )

    pdf.section_title("5. Conclusion")
    pdf.body_text(
        "PulseTrack delivers a complete, reproducible, production-grade DevOps platform integrating CI/CD, "
        "containerization, Kubernetes, Terraform, Ansible, Prometheus/Grafana/Loki observability, security "
        "hardening, and automated Canary/Blue-Green delivery."
    )

    out_path = Path(__file__).resolve().parent.parent / "docs" / "CAPSTONE_REPORT.pdf"
    pdf.output(str(out_path))
    print(f"Generated PDF: {out_path}")


if __name__ == "__main__":
    main()
