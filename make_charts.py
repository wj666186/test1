"""从 results/scores.json 出图：各指标均分、逐条总分、分数分布。"""
import json
import os
from collections import Counter

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

# Windows 中文字体
for fp in [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]:
    if os.path.exists(fp):
        font_manager.fontManager.addfont(fp)
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=fp).get_name()
        break
plt.rcParams["axes.unicode_minus"] = False

BASE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(BASE, "results", "scores.json"), encoding="utf-8") as f:
    rows = json.load(f)

NAMES = {"accuracy": "准确性", "helpfulness": "有用性",
         "groundedness": "不瞎编", "tone": "语气共情"}
COLORS = {"accuracy": "#4C78A8", "helpfulness": "#E45756",
          "groundedness": "#54A24B", "tone": "#F58518"}

keys = ["accuracy", "helpfulness", "groundedness", "tone"]

# ---- 图1：各指标均分（折百分制）+ 整体分 ----
means = {k: sum(r["judge"][k]["score"] for r in rows) / len(rows) for k in keys}
overall_mean = sum(r["overall"] for r in rows) / len(rows)

fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
vals = [means[k] * 20 for k in keys]
bars = ax.bar([NAMES[k] for k in keys], vals,
              color=[COLORS[k] for k in keys], width=0.55)
ax.axhline(overall_mean, color="#333", ls="--", lw=1.2,
           label=f"整体加权分 {overall_mean:.1f}")
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width() / 2, v + 1.2, f"{v:.0f}",
            ha="center", fontsize=11, fontweight="bold")
ax.set_ylim(0, 100)
ax.set_ylabel("得分（百分制）")
ax.set_title("各指标均分 vs 整体加权分（n=20）")
ax.legend(loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "results", "chart_metric_means.png"))
plt.close(fig)

# ---- 图2：逐条总分排序（最差3标红）----
ordered = sorted(rows, key=lambda r: r["overall"])
worst3_ids = {ordered[0]["id"], ordered[1]["id"], ordered[2]["id"]}
fig, ax = plt.subplots(figsize=(8, 7), dpi=150)
ys = [r["id"] for r in ordered]
vs = [r["overall"] for r in ordered]
cs = ["#E45756" if r["id"] in worst3_ids else "#4C78A8" for r in ordered]
bars = ax.barh(ys, vs, color=cs)
for b, v in zip(bars, vs):
    ax.text(v + 0.6, b.get_y() + b.get_height() / 2, f"{v:.0f}",
            va="center", fontsize=9)
ax.axvline(60, color="#888", ls=":", lw=1)
ax.set_xlim(0, 100)
ax.set_xlabel("加权总分（百分制）")
ax.set_title("20 条自动回复逐条得分（红=最差3条）")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "results", "chart_per_case.png"))
plt.close(fig)

# ---- 图3：各指标 1~5 分分布 ----
fig, ax = plt.subplots(figsize=(8, 4.6), dpi=150)
import numpy as np
x = np.arange(5)
w = 0.2
for i, k in enumerate(keys):
    c = Counter(r["judge"][k]["score"] for r in rows)
    heights = [c.get(s, 0) for s in range(1, 6)]
    ax.bar(x + (i - 1.5) * w, heights, w, label=NAMES[k], color=COLORS[k])
ax.set_xticks(x)
ax.set_xticklabels([f"{s}分" for s in range(1, 6)])
ax.set_ylabel("样本条数")
ax.set_title("各指标分数分布（1=最差，5=最好）")
ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.08))
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(os.path.join(BASE, "results", "chart_distribution.png"))
plt.close(fig)

print("charts written to results/")
