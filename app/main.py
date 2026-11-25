"""PulseTrack - Cloud-Native Task & Incident Telemetry Service."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
from pydantic import BaseModel, Field

APP_NAME = os.getenv("APP_NAME", "pulsetrack")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
DEPLOYMENT_TRACK = os.getenv("DEPLOYMENT_TRACK", "stable")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


class JsonLogFormatter(logging.Formatter):
    """Structured JSON log formatter for centralized log aggregation (Loki/Promtail)."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": APP_NAME,
            "version": APP_VERSION,
            "track": DEPLOYMENT_TRACK,
            "environment": ENVIRONMENT,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for attr in ("request_id", "method", "path", "status_code", "latency_ms"):
            if hasattr(record, attr):
                payload[attr] = getattr(record, attr)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def configure_logging() -> logging.Logger:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonLogFormatter())
    root = logging.getLogger("pulsetrack")
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    return root


logger = configure_logging()

# Prometheus Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total HTTP requests processed",
    ["method", "path", "status", "track"],
)
HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "path", "track"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)
ACTIVE_TASKS_GAUGE = Gauge(
    "pulsetrack_active_tasks",
    "Current number of non-completed tasks",
    ["priority"],
)
INCIDENTS_TOTAL = Counter(
    "pulsetrack_incidents_reported_total",
    "Total incidents reported",
    ["severity"],
)


class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=2, max_length=120)
    description: str = Field(default="", max_length=500)
    priority: TaskPriority = TaskPriority.MEDIUM
    owner: str = Field(default="devops-team", min_length=2, max_length=60)


class TaskUpdate(BaseModel):
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class TaskRecord(BaseModel):
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    owner: str
    created_at: str
    updated_at: str


class IncidentCreate(BaseModel):
    service: str = Field(..., min_length=2, max_length=80)
    severity: TaskPriority = TaskPriority.HIGH
    summary: str = Field(..., min_length=4, max_length=240)


class IncidentRecord(BaseModel):
    id: str
    service: str
    severity: TaskPriority
    summary: str
    resolved: bool
    reported_at: str


# In-memory store (seeded for immediate demo & observability)
TASKS_DB: Dict[str, TaskRecord] = {}
INCIDENTS_DB: Dict[str, IncidentRecord] = {}
APP_STATE = {"ready": True, "started_at": datetime.now(timezone.utc).isoformat()}


def _refresh_task_gauges() -> None:
    counts = {p.value: 0 for p in TaskPriority}
    for task in TASKS_DB.values():
        if task.status != TaskStatus.DONE:
            counts[task.priority.value] += 1
    for priority, count in counts.items():
        ACTIVE_TASKS_GAUGE.labels(priority=priority).set(count)


def seed_initial_data() -> None:
    if TASKS_DB:
        return
    now = datetime.now(timezone.utc).isoformat()
    sample_tasks = [
        TaskRecord(
            id="tsk-1001",
            title="Configure Prometheus Alertmanager routes",
            description="Route critical SLO alerts to Slack & PagerDuty",
            priority=TaskPriority.HIGH,
            status=TaskStatus.IN_PROGRESS,
            owner="sre-oncall",
            created_at=now,
            updated_at=now,
        ),
        TaskRecord(
            id="tsk-1002",
            title="Verify Canary rollout rollback threshold",
            description="Ensure 5xx rate > 2% triggers automatic rollback",
            priority=TaskPriority.CRITICAL,
            status=TaskStatus.OPEN,
            owner="platform-eng",
            created_at=now,
            updated_at=now,
        ),
    ]
    for t in sample_tasks:
        TASKS_DB[t.id] = t
    _refresh_task_gauges()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    seed_initial_data()
    logger.info("PulseTrack service started")
    yield
    logger.info("PulseTrack service shutting down")


app = FastAPI(
    title="PulseTrack DevOps Platform API",
    version=APP_VERSION,
    description="Cloud-native task & incident telemetry service for End-to-End DevOps Capstone",
    lifespan=lifespan,
)


@app.middleware("http")
async def observability_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    status_code = 500
    try:
        response: Response = await call_next(request)
        status_code = response.status_code
        response.headers["X-Request-ID"] = request_id
        response.headers["X-App-Version"] = APP_VERSION
        response.headers["X-Deployment-Track"] = DEPLOYMENT_TRACK
        return response
    finally:
        elapsed = time.perf_counter() - start
        path = request.url.path
        if path != "/metrics":
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                path=path,
                status=str(status_code),
                track=DEPLOYMENT_TRACK,
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                path=path,
                track=DEPLOYMENT_TRACK,
            ).observe(elapsed)
            logger.info(
                "http_request",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": path,
                    "status_code": status_code,
                    "latency_ms": round(elapsed * 1000, 2),
                },
            )


@app.get("/", response_class=HTMLResponse)
def dashboard() -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>PulseTrack | DevOps Capstone</title>
  <style>
    body {{ font-family: system-ui, -apple-system, sans-serif; background: #0f172a; color: #e2e8f0; margin: 0; padding: 2rem; }}
    .card {{ max-width: 820px; margin: 0 auto; background: #1e293b; border-radius: 12px; padding: 1.5rem 2rem; border: 1px solid #334155; }}
    .badge {{ display: inline-block; padding: 0.25rem 0.7rem; border-radius: 999px; font-size: 0.8rem; font-weight: 600; background: #0ea5e9; color: #0f172a; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin-top: 1.25rem; }}
    .stat {{ background: #0f172a; padding: 1rem; border-radius: 8px; border: 1px solid #334155; }}
    a {{ color: #38bdf8; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>PulseTrack Telemetry Platform <span class="badge">v{APP_VERSION} ({DEPLOYMENT_TRACK})</span></h1>
    <p>Environment: <strong>{ENVIRONMENT}</strong> | Started: <code>{APP_STATE["started_at"]}</code></p>
    <div class="grid">
      <div class="stat"><div>Tasks</div><h2>{len(TASKS_DB)}</h2></div>
      <div class="stat"><div>Incidents</div><h2>{len(INCIDENTS_DB)}</h2></div>
      <div class="stat"><div>Endpoints</div><p><a href="/docs">/docs</a> | <a href="/metrics">/metrics</a> | <a href="/health/ready">/health/ready</a></p></div>
    </div>
  </div>
</body>
</html>"""


@app.get("/health/live")
def liveness():
    return {"status": "alive", "service": APP_NAME}


@app.get("/health/ready")
def readiness():
    if not APP_STATE["ready"]:
        raise HTTPException(status_code=503, detail="Service not ready")
    return {
        "status": "ready",
        "service": APP_NAME,
        "version": APP_VERSION,
        "track": DEPLOYMENT_TRACK,
        "environment": ENVIRONMENT,
    }


@app.get("/api/v1/version")
def get_version():
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "track": DEPLOYMENT_TRACK,
        "environment": ENVIRONMENT,
        "started_at": APP_STATE["started_at"],
    }


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/api/v1/tasks", response_model=List[TaskRecord])
def list_tasks(status: Optional[TaskStatus] = None):
    tasks = list(TASKS_DB.values())
    if status is not None:
        tasks = [t for t in tasks if t.status == status]
    return tasks


@app.post("/api/v1/tasks", response_model=TaskRecord, status_code=201)
def create_task(payload: TaskCreate):
    now = datetime.now(timezone.utc).isoformat()
    task_id = f"tsk-{uuid.uuid4().hex[:6]}"
    record = TaskRecord(
        id=task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=TaskStatus.OPEN,
        owner=payload.owner,
        created_at=now,
        updated_at=now,
    )
    TASKS_DB[task_id] = record
    _refresh_task_gauges()
    logger.info("task_created id=%s priority=%s", task_id, payload.priority.value)
    return record


@app.patch("/api/v1/tasks/{task_id}", response_model=TaskRecord)
def update_task(task_id: str, payload: TaskUpdate):
    task = TASKS_DB.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    updated = task.model_copy(
        update={
            "status": payload.status if payload.status is not None else task.status,
            "priority": payload.priority if payload.priority is not None else task.priority,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    TASKS_DB[task_id] = updated
    _refresh_task_gauges()
    return updated


@app.delete("/api/v1/tasks/{task_id}", status_code=204)
def delete_task(task_id: str):
    if task_id not in TASKS_DB:
        raise HTTPException(status_code=404, detail="Task not found")
    del TASKS_DB[task_id]
    _refresh_task_gauges()
    return Response(status_code=204)


@app.get("/api/v1/incidents", response_model=List[IncidentRecord])
def list_incidents():
    return list(INCIDENTS_DB.values())


@app.post("/api/v1/incidents", response_model=IncidentRecord, status_code=201)
def report_incident(payload: IncidentCreate):
    inc_id = f"inc-{uuid.uuid4().hex[:6]}"
    record = IncidentRecord(
        id=inc_id,
        service=payload.service,
        severity=payload.severity,
        summary=payload.summary,
        resolved=False,
        reported_at=datetime.now(timezone.utc).isoformat(),
    )
    INCIDENTS_DB[inc_id] = record
    INCIDENTS_TOTAL.labels(severity=payload.severity.value).inc()
    logger.warning("incident_reported id=%s service=%s severity=%s", inc_id, payload.service, payload.severity.value)
    return record
