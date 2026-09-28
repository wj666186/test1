"""流水线主流程：加载数据 -> 提取特征 -> LLM 裁判打分 -> 汇总 -> 落盘。"""

import json
import os

from . import heuristics, report
from .judge import LLMJudge
from .metrics import METRICS, overall_score

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(BASE, "data", name), "r", encoding="utf-8") as f:
        return json.load(f)


def run(mode: str = "mock"):
    replies = _load("auto_replies.json")
    human_ref_list = _load("human_ref.json")
    human_ref = {h["id"]: h for h in human_ref_list}

    judge = LLMJudge(mode=mode)
    rows = []
    for case in replies:
        feats = heuristics.extract_features(
            case["user_question"], case["auto_reply"]
        )
        verdict = judge.evaluate(case, feats)
        metric_scores = {k: verdict[k]["score"] for k in METRICS}
        rows.append({
            "id": case["id"],
            "user_question": case["user_question"],
            "auto_reply": case["auto_reply"],
            "features": feats,
            "judge": verdict,
            "overall": overall_score(metric_scores),
        })

    # 落盘 scores.json
    out_dir = os.path.join(BASE, "results")
    os.makedirs(out_dir, exist_ok=True)
    with open(os.path.join(out_dir, "scores.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    md = report.build_report(rows, human_ref)
    with open(os.path.join(out_dir, "report.md"), "w", encoding="utf-8") as f:
        f.write(md)

    # 终端摘要
    overall_mean = sum(r["overall"] for r in rows) / len(rows)
    print(f"[done] mode={mode}, cases={len(rows)}, overall={overall_mean:.1f}/100")
    for r in sorted(rows, key=lambda x: x["overall"])[:5]:
        print(f"  low  {r['id']}: {r['overall']}  ({r['user_question'][:20]})")
    print(f"report -> {os.path.join(out_dir, 'report.md')}")
    return rows
