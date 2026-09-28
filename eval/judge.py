"""
LLM-as-judge 打分器。

两种模式：
- real  ：调用 OpenAI 兼容的 /chat/completions 接口（环境变量 OPENAI_API_KEY /
          OPENAI_BASE_URL / JUDGE_MODEL），让裁判模型按 rubric 输出 JSON。
- mock  ：离线可复现，加载 judge_fixtures/mock_verdicts.json。
          该文件是「裁判模型」（本项目开发时由 Doubao 作为裁判）对 20 条样本
          逐条按 rubric 打出的分数与理由，固化为 fixture，保证流水线任何人
          克隆下来都能跑出同样结果。

裁判输出统一结构：
{
  "accuracy":    {"score": 1-5, "rationale": "..."},
  "helpfulness": {"score": 1-5, "rationale": "..."},
  "groundedness":{"score": 1-5, "rationale": "..."},
  "tone":        {"score": 1-5, "rationale": "..."}
}
"""

import json
import os
import urllib.request

from .metrics import METRICS

FIXTURE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "judge_fixtures",
    "mock_verdicts.json",
)


def _build_prompt(case: dict, features: dict) -> str:
    metric_desc = "\n".join(
        f"- {k}（{v['name']}，权重见指标表）：{v['question']}\n"
        f"    5分={v['rubric']['5']}\n    3分={v['rubric']['3']}\n    1分={v['rubric']['1']}"
        for k, v in METRICS.items()
    )
    return f"""你是一名严格、公正的电商客服回复质量裁判。请按 rubric 给自动回复打分。

【用户问题】{case['user_question']}
【自动回复】{case['auto_reply']}
【文本特征】{json.dumps(features, ensure_ascii=False)}

请对以下 4 个指标分别打 1~5 的整数分，并各写一句不超过 40 字的理由：
{metric_desc}

只输出 JSON，不要任何多余文字，结构：
{{"accuracy":{{"score":int,"rationale":""}},"helpfulness":{{"score":int,"rationale":""}},
"groundedness":{{"score":int,"rationale":""}},"tone":{{"score":int,"rationale":""}}}}
"""


class LLMJudge:
    def __init__(self, mode: str = "mock"):
        assert mode in ("mock", "real")
        self.mode = mode
        self._fixture = None
        if mode == "mock":
            with open(FIXTURE_PATH, "r", encoding="utf-8") as f:
                self._fixture = json.load(f)

    def evaluate(self, case: dict, features: dict) -> dict:
        if self.mode == "mock":
            return self._fixture[case["id"]]
        return self._evaluate_real(case, features)

    def _evaluate_real(self, case: dict, features: dict) -> dict:
        api_key = os.environ["OPENAI_API_KEY"]
        base_url = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
        model = os.environ.get("JUDGE_MODEL", "gpt-4o-mini")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "你是客服回复质量裁判，只输出 JSON。"},
                {"role": "user", "content": _build_prompt(case, features)},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            f"{base_url.rstrip('/')}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}",
                     "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return json.loads(data["choices"][0]["message"]["content"])
