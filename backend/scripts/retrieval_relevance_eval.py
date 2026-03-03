#!/usr/bin/env python3
"""
Retrieval relevance benchmark for backend -> remote_ai citation quality.

Runs 20 single-turn cases via /sessions/{id}/messages and evaluates whether
returned citations match expected topic keywords while avoiding forbidden terms.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, request


ROOT_DIR = Path(__file__).resolve().parents[2]
REPORT_DIR = ROOT_DIR / "backend" / "reports"


@dataclass
class EvalCase:
    case_id: str
    prompt: str
    expected_keywords: List[str]
    forbidden_keywords: List[str]


CASES: List[EvalCase] = [
    EvalCase(
        case_id="C01_throat_pain",
        prompt="我喉咙很痛，晚上卧室更严重，还有鼻塞和咳嗽。",
        expected_keywords=["喉", "咽", "鼻", "上呼吸道", "扁桃体"],
        forbidden_keywords=["高血压", "血压", "心肌", "糖尿病", "胃溃疡"],
    ),
    EvalCase(
        case_id="C02_hypertension",
        prompt="我有高血压，最近血压160/100，应该怎么处理？",
        expected_keywords=["高血压", "血压", "降压", "心血管"],
        forbidden_keywords=["喉", "鼻炎", "湿疹", "皮肤"],
    ),
    EvalCase(
        case_id="C03_chest_pain",
        prompt="走路时胸口发闷发痛，有点心慌，休息后缓解。",
        expected_keywords=["胸痛", "心绞痛", "冠心病", "心血管"],
        forbidden_keywords=["咽喉", "湿疹", "胃炎", "鼻炎"],
    ),
    EvalCase(
        case_id="C04_rash_itch",
        prompt="手臂起红疹很痒，抓了以后更严重。",
        expected_keywords=["皮疹", "瘙痒", "皮肤", "湿疹"],
        forbidden_keywords=["高血压", "胸痛", "心梗", "血压"],
    ),
    EvalCase(
        case_id="C05_wheezing",
        prompt="夜里反复咳嗽和喘，呼吸不太顺畅。",
        expected_keywords=["哮喘", "呼吸", "支气管", "咳嗽"],
        forbidden_keywords=["高血压", "皮疹", "月经", "血糖"],
    ),
    EvalCase(
        case_id="C06_reflux",
        prompt="吃完饭总是反酸烧心，喉咙也有点刺激。",
        expected_keywords=["反酸", "胃食管", "胃", "消化"],
        forbidden_keywords=["高血压", "皮疹", "鼻炎", "甲状腺"],
    ),
    EvalCase(
        case_id="C07_headache",
        prompt="最近偏头痛，伴恶心怕光。",
        expected_keywords=["偏头痛", "头痛", "神经"],
        forbidden_keywords=["高血压", "皮肤", "鼻炎", "胃炎"],
    ),
    EvalCase(
        case_id="C08_knee_pain",
        prompt="膝盖走路就疼，蹲起更明显。",
        expected_keywords=["膝", "关节", "骨科", "骨关节"],
        forbidden_keywords=["高血压", "咽喉", "皮疹", "鼻炎"],
    ),
    EvalCase(
        case_id="C09_eye_red",
        prompt="眼睛发红刺痛，还怕光流泪。",
        expected_keywords=["眼", "结膜", "视力", "眼科"],
        forbidden_keywords=["高血压", "皮疹", "咽喉", "胃炎"],
    ),
    EvalCase(
        case_id="C10_menstrual",
        prompt="月经不规律，伴下腹痛和乏力。",
        expected_keywords=["月经", "妇科", "盆腔", "妇产"],
        forbidden_keywords=["高血压", "咽喉", "皮肤", "鼻炎"],
    ),
    EvalCase(
        case_id="C11_child_fever",
        prompt="孩子发烧咳嗽两天了，精神也差。",
        expected_keywords=["儿童", "小儿", "发热", "上呼吸道"],
        forbidden_keywords=["高血压", "月经", "骨折", "甲状腺"],
    ),
    EvalCase(
        case_id="C12_thyroid",
        prompt="最近心慌怕热、体重下降，怀疑甲状腺有问题。",
        expected_keywords=["甲状腺", "内分泌", "甲亢"],
        forbidden_keywords=["咽喉", "皮疹", "鼻炎", "胃炎"],
    ),
    EvalCase(
        case_id="C13_allergic_rhinitis",
        prompt="最近总打喷嚏流清鼻涕，鼻子很痒。",
        expected_keywords=["鼻炎", "喷嚏", "流涕", "过敏"],
        forbidden_keywords=["高血压", "心梗", "糖尿病", "骨折"],
    ),
    EvalCase(
        case_id="C14_diarrhea",
        prompt="腹泻伴腹痛两天，吃东西后加重。",
        expected_keywords=["腹泻", "腹痛", "肠", "消化"],
        forbidden_keywords=["高血压", "咽喉", "皮疹", "鼻炎"],
    ),
    EvalCase(
        case_id="C15_acne",
        prompt="脸上痘痘反复，皮肤出油很多。",
        expected_keywords=["痤疮", "皮肤", "粉刺", "炎症"],
        forbidden_keywords=["高血压", "胸痛", "鼻炎", "月经"],
    ),
    EvalCase(
        case_id="C16_neck_pain",
        prompt="颈部疼痛，低头久了手臂会发麻。",
        expected_keywords=["颈", "神经", "椎", "骨科"],
        forbidden_keywords=["高血压", "皮疹", "鼻炎", "胃炎"],
    ),
    EvalCase(
        case_id="C17_bp_headache",
        prompt="最近血压高还头晕头痛，担心并发症。",
        expected_keywords=["高血压", "血压", "心血管", "风险"],
        forbidden_keywords=["湿疹", "鼻炎", "咽喉", "月经"],
    ),
    EvalCase(
        case_id="C18_sore_throat_air",
        prompt="开空调后喉咙干痛，说话多会加重。",
        expected_keywords=["喉", "咽", "呼吸道", "鼻咽"],
        forbidden_keywords=["高血压", "血糖", "皮疹", "骨折"],
    ),
    EvalCase(
        case_id="C19_asthma_night",
        prompt="夜间胸闷咳嗽反复，像哮喘发作。",
        expected_keywords=["哮喘", "呼吸", "支气管", "胸闷"],
        forbidden_keywords=["高血压", "月经", "皮疹", "甲状腺"],
    ),
    EvalCase(
        case_id="C20_hyperglycemia",
        prompt="最近口渴多尿，血糖也偏高。",
        expected_keywords=["糖尿病", "血糖", "内分泌", "代谢"],
        forbidden_keywords=["咽喉", "鼻炎", "湿疹", "骨折"],
    ),
]


def post_json(url: str, payload: Dict[str, Any], timeout: float = 30.0) -> Dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(
        url=url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except error.HTTPError as exc:
        text = exc.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {exc.code}: {text[:400]}") from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(str(exc)) from exc


def create_session(base_url: str, agent_type: str = "general") -> str:
    body = post_json(f"{base_url.rstrip('/')}/sessions", {"agent_type": agent_type})
    sid = body.get("session_id")
    if not isinstance(sid, str) or not sid:
        raise RuntimeError(f"invalid session response: {body}")
    return sid


def send_message(base_url: str, session_id: str, content: str) -> Dict[str, Any]:
    return post_json(
        f"{base_url.rstrip('/')}/sessions/{session_id}/messages",
        {"content": content},
    )


def evaluate_case(case: EvalCase, response: Dict[str, Any]) -> Dict[str, Any]:
    agentic = ((response.get("specialty_data") or {}).get("agentic") or {})
    citations = agentic.get("citations") or []
    citation_text = " ".join(str(item.get("snippet") or "") for item in citations).lower()

    expected_hits = [kw for kw in case.expected_keywords if kw.lower() in citation_text]
    forbidden_hits = [kw for kw in case.forbidden_keywords if kw.lower() in citation_text]

    expected_ratio = (len(expected_hits) / len(case.expected_keywords)) if case.expected_keywords else 0.0
    penalty = 0.25 * len(forbidden_hits)
    score = round(expected_ratio - penalty, 3)

    has_error = agentic.get("error") is not None
    strict_pass = (len(expected_hits) > 0) and (len(forbidden_hits) == 0) and (not has_error)
    loose_pass = (len(expected_hits) > 0) and (len(forbidden_hits) == 0)

    retrieval_trace = next(
        (row for row in (agentic.get("tool_trace") or []) if row.get("name") == "subagent.retrieval"),
        {},
    )
    retrieval_ms = int(retrieval_trace.get("latency_ms") or 0)

    return {
        "case_id": case.case_id,
        "prompt": case.prompt,
        "strict_pass": strict_pass,
        "loose_pass": loose_pass,
        "score": score,
        "expected_hits": expected_hits,
        "forbidden_hits": forbidden_hits,
        "citation_count": len(citations),
        "citations": citations,
        "agentic_error": agentic.get("error"),
        "retrieval_latency_ms": retrieval_ms,
        "assistant_message": response.get("message"),
        "risk_level": response.get("risk_level"),
    }


def percentile(values: List[int], p: float) -> int:
    if not values:
        return 0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * p))
    return ordered[max(0, min(idx, len(ordered) - 1))]


def run_benchmark(base_url: str, agent_type: str, pause_ms: int) -> Dict[str, Any]:
    results: List[Dict[str, Any]] = []
    request_failures = 0

    for idx, case in enumerate(CASES, start=1):
        try:
            sid = create_session(base_url, agent_type=agent_type)
            response = send_message(base_url, sid, case.prompt)
            row = evaluate_case(case, response)
            row["session_id"] = sid
            row["request_error"] = None
        except Exception as exc:  # noqa: BLE001
            request_failures += 1
            row = {
                "case_id": case.case_id,
                "prompt": case.prompt,
                "strict_pass": False,
                "loose_pass": False,
                "score": -1.0,
                "expected_hits": [],
                "forbidden_hits": [],
                "citation_count": 0,
                "citations": [],
                "agentic_error": None,
                "retrieval_latency_ms": 0,
                "assistant_message": "",
                "risk_level": None,
                "session_id": None,
                "request_error": str(exc),
            }

        results.append(row)
        print(
            f"[{idx:02d}/{len(CASES)}] {case.case_id}: "
            f"strict={row['strict_pass']} loose={row['loose_pass']} "
            f"cit={row['citation_count']} score={row['score']}"
        )
        if pause_ms > 0:
            time.sleep(pause_ms / 1000.0)

    strict_pass = sum(1 for row in results if row["strict_pass"])
    loose_pass = sum(1 for row in results if row["loose_pass"])
    no_citation = sum(1 for row in results if row["citation_count"] == 0)
    forbidden_hit_cases = sum(1 for row in results if len(row["forbidden_hits"]) > 0)
    latencies = [int(row["retrieval_latency_ms"]) for row in results if int(row["retrieval_latency_ms"]) > 0]
    avg_score = round(sum(float(row["score"]) for row in results) / len(results), 3) if results else 0.0

    return {
        "meta": {
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "base_url": base_url,
            "agent_type": agent_type,
            "case_count": len(CASES),
            "pause_ms": pause_ms,
        },
        "summary": {
            "strict_pass_count": strict_pass,
            "strict_pass_rate": round(strict_pass / len(results), 3) if results else 0.0,
            "loose_pass_count": loose_pass,
            "loose_pass_rate": round(loose_pass / len(results), 3) if results else 0.0,
            "request_failures": request_failures,
            "no_citation_count": no_citation,
            "forbidden_hit_case_count": forbidden_hit_cases,
            "avg_score": avg_score,
            "retrieval_latency_p50_ms": percentile(latencies, 0.5),
            "retrieval_latency_p95_ms": percentile(latencies, 0.95),
        },
        "results": results,
    }


def save_report(report: Dict[str, Any], output_path: str | None) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    if output_path:
        path = Path(output_path)
    else:
        ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        path = REPORT_DIR / f"retrieval_relevance_eval_{ts}.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run retrieval relevance benchmark.")
    parser.add_argument("--base-url", default="http://localhost:8100", help="Backend API base URL.")
    parser.add_argument("--agent-type", default="general", help="Session agent_type.")
    parser.add_argument("--pause-ms", type=int, default=150, help="Pause between cases in ms.")
    parser.add_argument("--output", default="", help="Optional report output path.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = run_benchmark(
        base_url=args.base_url,
        agent_type=args.agent_type,
        pause_ms=max(0, int(args.pause_ms)),
    )
    path = save_report(report, args.output or None)

    summary = report["summary"]
    print("\n=== Retrieval Relevance Summary ===")
    print(f"report: {path}")
    print(f"strict_pass: {summary['strict_pass_count']}/{len(CASES)} ({summary['strict_pass_rate']:.1%})")
    print(f"loose_pass: {summary['loose_pass_count']}/{len(CASES)} ({summary['loose_pass_rate']:.1%})")
    print(f"forbidden_hit_cases: {summary['forbidden_hit_case_count']}")
    print(f"no_citation_cases: {summary['no_citation_count']}")
    print(
        "retrieval_latency_ms: "
        f"p50={summary['retrieval_latency_p50_ms']} "
        f"p95={summary['retrieval_latency_p95_ms']}"
    )


if __name__ == "__main__":
    main()
