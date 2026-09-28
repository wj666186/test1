"""汇总结果并生成 Markdown 评估报告。"""

from collections import Counter

from .metrics import METRICS, WEIGHTS


def build_report(rows: list, human_ref: dict) -> str:
    n = len(rows)
    metric_keys = list(METRICS.keys())

    # 整体与各指标均值
    overall_mean = sum(r["overall"] for r in rows) / n
    means = {
        k: sum(r["judge"][k]["score"] for r in rows) / n for k in metric_keys
    }

    # 分布：每个指标 1~5 各多少条
    dist = {
        k: Counter(r["judge"][k]["score"] for r in rows) for k in metric_keys
    }

    passed = sum(1 for r in rows if r["overall"] >= 60)
    gated = [r for r in rows if r["overall"] == 40]  # 触发了 groundedness 封顶

    # 最差 3 条
    worst = sorted(rows, key=lambda r: (r["overall"], r["judge"]["helpfulness"]["score"]))[:3]

    L = []
    L.append("# 客服自动回复质量评估报告\n")
    L.append(f"- 样本量：{n} 条")
    L.append(f"- 整体加权得分：**{overall_mean:.1f} / 100**")
    L.append(f"- 及格线（≥60）以上：{passed}/{n}（{passed/n*100:.0f}%）")
    L.append(f"- 触发「疑似编造」硬门槛：{len(gated)} 条\n")

    L.append("## 一、指标权重与各指标均分\n")
    L.append("| 指标 | 含义 | 权重 | 均分(1-5) | 折合百分制 |")
    L.append("|---|---|---|---|---|")
    for k in metric_keys:
        L.append(
            f"| {k} | {METRICS[k]['name']} | {WEIGHTS[k]:.2f} | "
            f"{means[k]:.2f} | {means[k]*20:.1f} |"
        )

    L.append("\n## 二、各指标分数分布（1-5 分各多少条）\n")
    L.append("| 指标 | 1分 | 2分 | 3分 | 4分 | 5分 |")
    L.append("|---|---|---|---|---|---|")
    for k in metric_keys:
        c = dist[k]
        L.append(
            f"| {METRICS[k]['name']} | {c.get(1,0)} | {c.get(2,0)} | "
            f"{c.get(3,0)} | {c.get(4,0)} | {c.get(5,0)} |"
        )

    L.append("\n## 三、逐条得分一览\n")
    L.append("| ID | 用户问题 | 准确 | 有用 | 不瞎编 | 语气 | 总分 |")
    L.append("|---|---|---|---|---|---|---|")
    for r in sorted(rows, key=lambda x: x["id"]):
        j = r["judge"]
        q = r["user_question"]
        q = q if len(q) <= 18 else q[:18] + "…"
        L.append(
            f"| {r['id']} | {q} | {j['accuracy']['score']} | "
            f"{j['helpfulness']['score']} | {j['groundedness']['score']} | "
            f"{j['tone']['score']} | **{r['overall']}** |"
        )

    L.append("\n## 四、最差 3 条 case 分析\n")
    for i, r in enumerate(worst, 1):
        j = r["judge"]
        hr = human_ref.get(r["id"], {})
        L.append(f"### 最差 #{i}：{r['id']}（总分 {r['overall']}）\n")
        L.append(f"- **用户问题**：{r['user_question']}")
        L.append(f"- **自动回复**：{r['auto_reply']}")
        L.append(f"- **规则特征**：推卸自助短语 {r['features']['deflection_count']} 处，"
                 f"主动揽办 {r['features']['proactive_count']} 处，"
                 f"共情词 {r['features']['empathy_count']} 处")
        L.append("- **分项裁判理由**：")
        for k in metric_keys:
            L.append(f"  - {METRICS[k]['name']}={j[k]['score']}：{j[k]['rationale']}")
        if hr:
            L.append(f"- **人工参考回复**：{hr.get('human_reference','')}")
            L.append(f"- **人工标注备注**：{hr.get('annotator_notes','')}")
        L.append("")

    L.append("## 五、结论与改进方向\n")
    L.append(
        f"- 整体 **{overall_mean:.0f}/100**，"
        f"**{METRICS['accuracy']['name']}（{means['accuracy']:.2f}）与 "
        f"{METRICS['groundedness']['name']}（{means['groundedness']:.2f}）得分高**，"
        f"说明事实层面基本可靠、没有明显瞎编；"
        f"**最弱项是 {METRICS['helpfulness']['name']}（{means['helpfulness']:.2f}）和 "
        f"{METRICS['tone']['name']}（{means['tone']:.2f}）**。"
    )
    L.append(
        "- 高频问题模式：自动回复倾向给「通用规则 + 让用户自己查/自己操作」，"
        "而人工客服会**主动代查订单/物流/商品**并承接情绪。"
        "改进优先级：① 接入订单/物流/商品查询工具，让回复能代查；"
        "② 投诉/焦虑场景增加共情话术，去掉「加强培训」类内部话术；"
        "③ 对用户明说操作困难的场景，先问「卡在哪一步」而不是重复流程。"
    )
    return "\n".join(L)
