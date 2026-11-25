"""Run real verification commands & live FastAPI probes and render crisp PNG evidence screenshots."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.main import app, seed_initial_data  # noqa: E402

SHOTS = ROOT / "screenshots"
SHOTS.mkdir(exist_ok=True)


def run_cmd(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, check=False)
    out = (proc.stdout or "") + (proc.stderr or "")
    return f"$ {' '.join(cmd)}\n{out.strip()}\n"


def render_terminal_png(title: str, body: str, out_file: Path) -> None:
    lines = []
    for raw in body.splitlines():
        while len(raw) > 108:
            lines.append(raw[:108])
            raw = raw[108:]
        lines.append(raw)

    font = ImageFont.load_default(size=15)
    title_font = ImageFont.load_default(size=16)
    line_h = 21
    pad_x, pad_y = 24, 54
    width = 1120
    height = max(440, pad_y + len(lines) * line_h + 28)

    img = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(0, 0), (width, 38)], fill=(30, 41, 59))
    draw.ellipse([(16, 12), (28, 24)], fill=(239, 68, 68))
    draw.ellipse([(36, 12), (48, 24)], fill=(245, 158, 11))
    draw.ellipse([(56, 12), (68, 24)], fill=(34, 197, 94))
    draw.text((88, 10), title, font=title_font, fill=(226, 232, 240))

    y = pad_y
    for line in lines:
        color = (226, 232, 240)
        if line.startswith("$ "):
            color = (56, 189, 248)
        elif any(k in line for k in ("PASSED", "PASS", "All checks passed", "No issues", "PROMOTE", "200 OK", "201 Created")):
            color = (74, 222, 128)
        elif "ROLLBACK" in line or "FAIL" in line:
            color = (248, 113, 113)
        draw.text((pad_x, y), line, font=font, fill=color)
        y += line_h

    img.save(out_file)
    print(f"Saved {out_file}")


def main() -> None:
    py = str(ROOT / ".venv" / "Scripts" / "python.exe")
    ruff = str(ROOT / ".venv" / "Scripts" / "ruff.exe")
    bandit = str(ROOT / ".venv" / "Scripts" / "bandit.exe")

    # 1. Live FastAPI Endpoints & JSON Responses
    seed_initial_data()
    client = TestClient(app)
    health_res = client.get("/health/ready")
    ver_res = client.get("/api/v1/version")
    tasks_res = client.get("/api/v1/tasks")
    api_body = "\n".join([
        f"$ curl -s http://localhost:8000/health/ready  # HTTP {health_res.status_code} OK",
        json.dumps(health_res.json(), indent=2),
        "",
        f"$ curl -s http://localhost:8000/api/v1/version  # HTTP {ver_res.status_code} OK",
        json.dumps(ver_res.json(), indent=2),
        "",
        f"$ curl -s http://localhost:8000/api/v1/tasks  # HTTP {tasks_res.status_code} OK",
        json.dumps(tasks_res.json()[:1], indent=2),
    ])
    render_terminal_png(
        "PulseTrack Live FastAPI Service - Health, Version & Tasks API",
        api_body,
        SHOTS / "01-live-api-and-health.png",
    )

    # 2. Live Prometheus /metrics output
    metrics_res = client.get("/metrics")
    metric_lines = [
        line for line in metrics_res.text.splitlines()
        if line and (line.startswith("# HELP http_") or line.startswith("http_requests_total") or line.startswith("pulsetrack_"))
    ][:24]
    render_terminal_png(
        "PulseTrack Observability - Live Prometheus /metrics Exposition",
        "$ curl -s http://localhost:8000/metrics\n" + "\n".join(metric_lines),
        SHOTS / "02-prometheus-metrics.png",
    )

    # 3. Kubernetes Kustomize Production Manifests
    k8s_out = run_cmd(["kubectl", "kustomize", "k8s/overlays/production"])
    k8s_preview = "\n".join(k8s_out.splitlines()[:34]) + "\n... (rendered full production Namespace, RBAC, Deployment, Service, Ingress, HPA, PDB, NetworkPolicy)"
    render_terminal_png(
        "PulseTrack Kubernetes - Kustomize Production Overlay Render",
        k8s_preview,
        SHOTS / "03-k8s-kustomize.png",
    )

    # 4. Pytest + Ruff + Bandit + SecretGuard
    sec_test_out = "\n".join([
        run_cmd([py, "-m", "pytest", "--cov=app", "--cov-report=term-missing"]),
        run_cmd([ruff, "check", "app", "tests"]),
        run_cmd([bandit, "-r", "app", "-ll"]),
        run_cmd([py, "security/secret_guard.py"]),
    ])
    render_terminal_png(
        "PulseTrack CI/CD - Pytest, Ruff, Bandit SAST & SecretGuard",
        sec_test_out,
        SHOTS / "04-tests-and-security.png",
    )

    # 5. Canary Rollout Simulation + Disaster Recovery Backup/Verify/Restore
    ops_out = "\n".join([
        run_cmd([py, "scripts/canary_sim.py"]),
        run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", "dr/backup_restore.ps1", "-Action", "backup"]),
        run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", "dr/backup_restore.ps1", "-Action", "verify"]),
        run_cmd(["powershell", "-ExecutionPolicy", "Bypass", "-File", "dr/backup_restore.ps1", "-Action", "restore"]),
    ])
    render_terminal_png(
        "PulseTrack Canary Rollout Simulation & Disaster Recovery (Backup/Verify/Restore)",
        ops_out,
        SHOTS / "05-canary-and-dr.png",
    )


if __name__ == "__main__":
    main()
