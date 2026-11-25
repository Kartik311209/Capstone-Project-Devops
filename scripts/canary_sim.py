"""Progressive Canary Rollout & Automated Rollback Simulator."""

from __future__ import annotations

import random


def simulate_stage(weight_canary: int, requests: int = 100, inject_fault: bool = False) -> dict:
    blue_hits = 0
    green_hits = 0
    errors_5xx = 0
    for _ in range(requests):
        is_canary = random.random() * 100 < weight_canary  # noqa: S311
        if is_canary:
            green_hits += 1
            if inject_fault and random.random() < 0.08:  # noqa: S311
                errors_5xx += 1
        else:
            blue_hits += 1
    error_rate = (errors_5xx / requests) * 100
    return {
        "canary_weight": weight_canary,
        "blue_hits": blue_hits,
        "green_hits": green_hits,
        "error_rate_pct": round(error_rate, 2),
        "slo_pass": error_rate <= 2.0,
    }


def main() -> None:
    random.seed(42)
    print("=== PulseTrack Progressive Canary Rollout ===")
    for weight in (10, 50, 100):
        res = simulate_stage(weight_canary=weight, requests=200, inject_fault=False)
        status = "PROMOTE" if res["slo_pass"] else "ROLLBACK"
        print(
            f"[Canary {res['canary_weight']:>3}%] Blue={res['blue_hits']:>3} | "
            f"Green={res['green_hits']:>3} | 5xx={res['error_rate_pct']:>4}% | Gate={status}"
        )

    print("\n=== Fault-Injection Auto-Rollback Verification ===")
    fault_res = simulate_stage(weight_canary=50, requests=200, inject_fault=True)
    status = "PROMOTE" if fault_res["slo_pass"] else "AUTO-ROLLBACK TRIGGERED -> 100% BLUE"
    print(
        f"[Canary {fault_res['canary_weight']:>3}%] Blue={fault_res['blue_hits']:>3} | "
        f"Green={fault_res['green_hits']:>3} | 5xx={fault_res['error_rate_pct']:>4}% | Gate={status}"
    )


if __name__ == "__main__":
    main()
