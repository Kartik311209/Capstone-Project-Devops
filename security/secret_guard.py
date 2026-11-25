"""Secret Guard: scans repository files for accidental secrets and masks sensitive values in logs."""

from __future__ import annotations

import re
import sys
from pathlib import Path

SECRET_PATTERNS = [
    ("AWS Access Key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("GitHub Token", re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}")),
    ("Private Key Block", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Generic Hardcoded Secret", re.compile(r"(?i)(api_key|secret_key|password)\s*=\s*['\"][^'\"]{8,}['\"]")),
]

IGNORE_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "screenshots", "backups"}
IGNORE_EXTS = {".png", ".pdf", ".zip", ".gz", ".pyc"}


def mask_secret(text: str) -> str:
    """Mask sensitive tokens before writing to logs."""
    masked = text
    for _, pattern in SECRET_PATTERNS:
        masked = pattern.sub("***MASKED***", masked)
    return masked


def scan_repository(root: Path) -> list[tuple[str, int, str]]:
    findings: list[tuple[str, int, str]] = []
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        if path.suffix.lower() in IGNORE_EXTS:
            continue
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        for lineno, line in enumerate(content.splitlines(), start=1):
            for label, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    findings.append((str(path.relative_to(root)), lineno, label))
    return findings


def main() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    print(f"[SecretGuard] Scanning repository: {repo_root}")
    findings = scan_repository(repo_root)
    sample_log = "Connecting with token=ghp_1234567890abcdefghijklmnopqrstuvwxyz"
    print(f"[SecretGuard] Log masking check: {mask_secret(sample_log)}")
    if findings:
        for file_path, line_no, label in findings:
            print(f"  [FAIL] {file_path}:{line_no} -> {label}")
        return 1
    print("[SecretGuard] PASS - 0 hardcoded secrets detected.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
