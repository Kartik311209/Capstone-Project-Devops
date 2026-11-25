"""Automated unit and integration tests for PulseTrack."""

from fastapi.testclient import TestClient

from app.main import TASKS_DB, INCIDENTS_DB, app, seed_initial_data


def get_client() -> TestClient:
    TASKS_DB.clear()
    INCIDENTS_DB.clear()
    seed_initial_data()
    return TestClient(app)


def test_health_endpoints():
    client = get_client()
    live = client.get("/health/live")
    assert live.status_code == 200
    assert live.json()["status"] == "alive"

    ready = client.get("/health/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
    assert "version" in ready.json()


def test_version_and_dashboard():
    client = get_client()
    ver = client.get("/api/v1/version")
    assert ver.status_code == 200
    assert ver.json()["service"] == "pulsetrack"

    dash = client.get("/")
    assert dash.status_code == 200
    assert "PulseTrack Telemetry Platform" in dash.text


def test_metrics_endpoint():
    client = get_client()
    client.get("/api/v1/version")
    metrics = client.get("/metrics")
    assert metrics.status_code == 200
    assert "http_requests_total" in metrics.text
    assert "pulsetrack_active_tasks" in metrics.text


def test_task_crud_lifecycle():
    client = get_client()
    initial = client.get("/api/v1/tasks")
    assert initial.status_code == 200
    assert len(initial.json()) == 2

    created = client.post(
        "/api/v1/tasks",
        json={
            "title": "Enable Trivy container scan",
            "description": "Fail CI on CRITICAL vulnerabilities",
            "priority": "high",
            "owner": "secops",
        },
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "open"

    updated = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"})
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    deleted = client.delete(f"/api/v1/tasks/{task_id}")
    assert deleted.status_code == 204

    missing = client.patch(f"/api/v1/tasks/{task_id}", json={"status": "open"})
    assert missing.status_code == 404


def test_incident_reporting():
    client = get_client()
    res = client.post(
        "/api/v1/incidents",
        json={
            "service": "checkout-api",
            "severity": "critical",
            "summary": "Elevated 5xx latency on canary pods",
        },
    )
    assert res.status_code == 201
    assert res.json()["resolved"] is False

    listed = client.get("/api/v1/incidents")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
