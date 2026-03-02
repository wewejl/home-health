#!/usr/bin/env python3
"""
Agentic gray rollout smoke + throat-dialogue benchmark runner.

Usage examples:
  python backend/scripts/agentic_gray_eval.py --enable-gray --specialties general
  python backend/scripts/agentic_gray_eval.py --batch-size 3
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import time
import math
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import httpx


ROOT_DIR = Path(__file__).resolve().parents[2]
BACKEND_DIR = ROOT_DIR / "backend"
REPORT_DIR = BACKEND_DIR / "reports"
DEFAULT_ENV_FILE = BACKEND_DIR / ".env.local"


def upsert_env_vars(env_file: Path, updates: Dict[str, str]) -> None:
    env_file.parent.mkdir(parents=True, exist_ok=True)
    lines = env_file.read_text(encoding="utf-8").splitlines() if env_file.exists() else []

    for key, value in updates.items():
        pattern = re.compile(rf"^\s*{re.escape(key)}\s*=")
        replaced = False
        for idx, line in enumerate(lines):
            if pattern.match(line):
                lines[idx] = f"{key}={value}"
                replaced = True
                break
        if not replaced:
            lines.append(f"{key}={value}")

    try:
        env_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
    except IOError as exc:
        raise RuntimeError(f"Failed to write env file {env_file}: {exc}") from exc


def restart_backend() -> None:
    subprocess.run(
        ["docker", "compose", "restart", "backend"],
        cwd=str(ROOT_DIR),
        check=True,
        text=True,
    )


def wait_backend_ready(base_url: str, timeout_sec: int = 90) -> None:
    deadline = time.time() + timeout_sec
    last_err = ""
    with httpx.Client(timeout=5.0) as client:
        while time.time() < deadline:
            try:
                resp = client.get(f"{base_url.rstrip('/')}/health")
                if resp.status_code == 200:
                    return
                last_err = f"status={resp.status_code}"
            except Exception as exc:  # noqa: BLE001
                last_err = str(exc)
            time.sleep(1.5)
    raise RuntimeError(f"backend not ready within {timeout_sec}s: {last_err}")


def create_session(client: httpx.Client, base_url: str, agent_type: str = "general") -> str:
    resp = client.post(f"{base_url.rstrip('/')}/sessions", json={"agent_type": agent_type})
    resp.raise_for_status()
    body = resp.json()
    return body["session_id"]


def send_message(
    client: httpx.Client,
    base_url: str,
    session_id: str,
    content: str,
    debug: bool = True,
    max_retries: int = 0,
) -> Dict[str, Any]:
    suffix = "?debug=true" if debug else ""
    err = ""
    for _ in range(max_retries + 1):
        started = time.perf_counter()
        try:
            resp = client.post(
                f"{base_url.rstrip('/')}/sessions/{session_id}/messages{suffix}",
                json={"content": content},
            )
            resp.raise_for_status()
            body = resp.json()
            body["_latency_ms"] = int((time.perf_counter() - started) * 1000)
            body["_transport_error"] = False
            return body
        except Exception as exc:  # noqa: BLE001
            err = str(exc)
            time.sleep(1.0)
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    return {
        "message": f"[ERROR] 请求失败: {err}",
        "stage": "collecting",
        "progress": 0,
        "quick_options": [],
        "risk_level": "low",
        "specialty_data": {"agentic": {"error": err}},
        "next_state": {},
        "_latency_ms": elapsed_ms,
        "_transport_error": True,
    }


def has_agentic_payload(response: Dict[str, Any]) -> bool:
    return isinstance(response.get("specialty_data"), dict) and "agentic" in response["specialty_data"]


def run_gray_smoke(base_url: str) -> Dict[str, Any]:
    with httpx.Client(timeout=25.0) as client:
        general_sid = create_session(client, base_url, "general")
        general_resp = send_message(
            client,
            base_url,
            general_sid,
            "我喉咙很痛，前天开始，家里通风差，晚上更明显。",
            debug=True,
            max_retries=1,
        )

        derm_sid = create_session(client, base_url, "dermatology")
        derm_resp = send_message(
            client,
            base_url,
            derm_sid,
            "我脸上有红疹和瘙痒，最近三天加重。",
            debug=True,
            max_retries=1,
        )

    general_agentic = has_agentic_payload(general_resp)
    derm_agentic = has_agentic_payload(derm_resp)

    return {
        "general_session_id": general_sid,
        "dermatology_session_id": derm_sid,
        "general_uses_agentic": general_agentic,
        "dermatology_uses_agentic": derm_agentic,
        "gray_smoke_passed": general_agentic and (not derm_agentic),
        "general_message": general_resp.get("message", "")[:180],
        "dermatology_message": derm_resp.get("message", "")[:180],
    }


THROAT_DIALOGUE_TURNS = [
    "我为什么喉咙非常的疼，过年后回来家里一直没有通风，天气暖和后感觉空气很不好，前天开始逐步加重。",
    "刀割样疼痛，灼烧感。",
    "还有鼻塞流涕和咳嗽。",
    "晚上睡觉时在卧室症状更严重。",
    "目前没有做空气质量检测，也没有做医院检查。",
    "没有慢性病史，不吸烟不喝酒。",
]


def analyze_transcript(turn_outputs: List[Dict[str, Any]]) -> Dict[str, Any]:
    question_turns = 0
    agentic_turns = 0
    turn_indexes: List[int] = []

    for row in turn_outputs:
        message = row.get("message", "")
        if "？" in message or "?" in message:
            question_turns += 1
        if has_agentic_payload(row):
            agentic_turns += 1
        next_state = row.get("next_state", {})
        if isinstance(next_state, dict) and isinstance(next_state.get("turn_index"), int):
            turn_indexes.append(next_state["turn_index"])

    final_message = turn_outputs[-1].get("message", "") if turn_outputs else ""
    monotonic = all(x < y for x, y in zip(turn_indexes, turn_indexes[1:])) if len(turn_indexes) > 1 else True

    final_has_reason = any(k in final_message for k in ["原因", "判断", "倾向", "可能"])
    final_has_action = any(k in final_message for k in ["建议", "可以", "下一步", "处理"])
    final_has_escalation = any(k in final_message for k in ["就医", "急诊", "120"])

    passed = (
        agentic_turns == len(turn_outputs)
        and monotonic
        and question_turns >= 2
        and final_has_action
        and final_has_escalation
    )

    return {
        "turn_count": len(turn_outputs),
        "agentic_turns": agentic_turns,
        "question_turns": question_turns,
        "turn_indexes": turn_indexes,
        "turn_index_monotonic": monotonic,
        "final_has_reason": final_has_reason,
        "final_has_action": final_has_action,
        "final_has_escalation": final_has_escalation,
        "acceptance_passed": passed,
    }


def run_throat_benchmark(base_url: str, batch_size: int) -> Dict[str, Any]:
    runs: List[Dict[str, Any]] = []
    all_latencies: List[int] = []
    transport_errors = 0
    timeout_count = 0
    fallback_count = 0

    with httpx.Client(timeout=25.0) as client:
        for idx in range(batch_size):
            print(f"[benchmark] run {idx + 1}/{batch_size} start")
            sid = create_session(client, base_url, "general")
            outputs: List[Dict[str, Any]] = []
            for turn_idx, content in enumerate(THROAT_DIALOGUE_TURNS, start=1):
                print(f"[benchmark] run {idx + 1}/{batch_size} turn {turn_idx}/{len(THROAT_DIALOGUE_TURNS)}")
                outputs.append(send_message(client, base_url, sid, content, debug=True, max_retries=0))

            for row in outputs:
                lat = int(row.get("_latency_ms", 0) or 0)
                all_latencies.append(lat)
                if row.get("_transport_error"):
                    transport_errors += 1
                    fallback_count += 1
                msg = str(row.get("message", "")).lower()
                if "timed out" in msg or "timeout" in msg:
                    timeout_count += 1

            analysis = analyze_transcript(outputs)
            runs.append(
                {
                    "run_index": idx + 1,
                    "session_id": sid,
                    "analysis": analysis,
                    "messages": [
                        {
                            "turn": i + 1,
                            "user": THROAT_DIALOGUE_TURNS[i],
                            "assistant": outputs[i].get("message", ""),
                            "risk_level": outputs[i].get("risk_level"),
                            "quick_options": outputs[i].get("quick_options", []),
                            "latency_ms": outputs[i].get("_latency_ms", 0),
                            "transport_error": outputs[i].get("_transport_error", False),
                        }
                        for i in range(len(outputs))
                    ],
                }
            )

    pass_count = sum(1 for r in runs if r["analysis"]["acceptance_passed"])
    lat_sorted = sorted(all_latencies)
    p95_latency_ms = 0
    if lat_sorted:
        idx = max(0, min(len(lat_sorted) - 1, math.ceil(len(lat_sorted) * 0.95) - 1))
        p95_latency_ms = lat_sorted[idx]

    return {
        "batch_size": batch_size,
        "passed_runs": pass_count,
        "pass_rate": round(pass_count / batch_size, 3) if batch_size else 0.0,
        "summary": {
            "transport_errors": transport_errors,
            "timeouts": timeout_count,
            "fallback_count": fallback_count,
            "p95_latency_ms": p95_latency_ms,
        },
        "runs": runs,
    }


def save_report(payload: Dict[str, Any], output: Path | None = None) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = output or (REPORT_DIR / f"agentic_gray_eval_{ts}.json")
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


@dataclass
class RunOptions:
    base_url: str
    enable_gray: bool
    specialties: str
    engine_mode: str
    batch_size: int
    env_file: Path
    no_restart: bool
    output: Path | None


def parse_args() -> RunOptions:
    parser = argparse.ArgumentParser(description="Run agentic gray rollout + throat benchmark")
    parser.add_argument("--base-url", default="http://localhost:8100")
    parser.add_argument("--enable-gray", action="store_true", help="Enable USE_AGENTIC_ENGINE and whitelist")
    parser.add_argument("--specialties", default="general", help="Gray specialties list")
    parser.add_argument(
        "--engine-mode",
        default="legacy",
        choices=["legacy", "remote_ai", "hybrid_shadow"],
        help="Backend AI engine mode",
    )
    parser.add_argument("--batch-size", type=int, default=3, help="Benchmark run count")
    parser.add_argument("--env-file", default=str(DEFAULT_ENV_FILE))
    parser.add_argument("--no-restart", action="store_true", help="Skip docker compose restart")
    parser.add_argument("--output", default="", help="Optional output report path")
    args = parser.parse_args()

    return RunOptions(
        base_url=args.base_url,
        enable_gray=args.enable_gray,
        specialties=args.specialties,
        engine_mode=args.engine_mode,
        batch_size=args.batch_size,
        env_file=Path(args.env_file),
        no_restart=args.no_restart,
        output=Path(args.output) if args.output else None,
    )


def main() -> None:
    opts = parse_args()

    changes: Dict[str, Any] = {
        "gray_enabled": False,
        "env_file": str(opts.env_file),
        "engine_mode": opts.engine_mode,
    }
    upsert_env_vars(
        opts.env_file,
        {
            "AI_ENGINE_MODE": opts.engine_mode,
        },
    )
    if opts.enable_gray:
        upsert_env_vars(
            opts.env_file,
            {
                "USE_AGENTIC_ENGINE": "true",
                "AGENTIC_ENABLED_SPECIALTIES": opts.specialties,
            },
        )
        changes["gray_enabled"] = True
        changes["specialties"] = opts.specialties

    if not opts.no_restart:
        restart_backend()
    wait_backend_ready(opts.base_url, timeout_sec=90)

    smoke = run_gray_smoke(opts.base_url)
    benchmark = run_throat_benchmark(opts.base_url, opts.batch_size)

    report = {
        "timestamp": datetime.now().isoformat(),
        "base_url": opts.base_url,
        "changes": changes,
        "smoke": smoke,
        "benchmark": benchmark,
    }
    path = save_report(report, opts.output)

    print("=== Agentic Gray Eval Summary ===")
    print(f"report: {path}")
    print(f"smoke_passed: {smoke['gray_smoke_passed']}")
    print(
        "benchmark: "
        f"{benchmark['passed_runs']}/{benchmark['batch_size']} "
        f"(pass_rate={benchmark['pass_rate']})"
    )
    summary = benchmark.get("summary") or {}
    print(
        "stability: "
        f"timeouts={summary.get('timeouts', 0)} "
        f"fallbacks={summary.get('fallback_count', 0)} "
        f"p95_latency_ms={summary.get('p95_latency_ms', 0)}"
    )


if __name__ == "__main__":
    main()
