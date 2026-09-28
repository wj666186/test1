"""
规则特征（heuristics）。

这些特征不直接决定最终分数，而是：
1. 作为 LLM-as-judge 的辅助信号，写进 judge prompt；
2. 在报告里做「可解释性」展示——为什么这条回复分低；
3. 在 mock 模式下作为 sanity check（judge 分数应与特征方向一致）。
"""

# 把用户推去自助/推卸责任的短语（出现越多，helpfulness 越可疑）
DEFLECTION_PHRASES = [
    "查看商品详情页", "详情页", "联系客服", "咨询航空", "咨询具体航空",
    "自行", "耐心等待", "请查看", "请检查", "请您查看", "请您检查",
    "查看取件码", "查看物流", "查看订单", "翻详情",
]

# 道歉 / 共情词
EMPATHY_WORDS = [
    "抱歉", "对不起", "不好意思", "久等", "不好的体验", "困扰", "不便",
    "非常抱歉", "高度重视", "重视",
]

# 主动揽办信号
PROACTIVE_PHRASES = [
    "我帮您", "我来", "为您查询", "帮您查", "帮您处理", "帮您申请",
    "帮您联系", "我帮您查", "帮您确认",
]


def extract_features(user_question: str, auto_reply: str) -> dict:
    reply = auto_reply or ""
    deflection_hits = [p for p in DEFLECTION_PHRASES if p in reply]
    empathy_hits = [w for w in EMPATHY_WORDS if w in reply]
    proactive_hits = [p for p in PROACTIVE_PHRASES if p in reply]
    return {
        "reply_len_chars": len(reply),
        "deflection_count": len(deflection_hits),
        "deflection_phrases": deflection_hits,
        "empathy_count": len(empathy_hits),
        "proactive_count": len(proactive_hits),
        "asks_clarifying_question": ("？" in reply) or ("?" in reply),
        "user_emotional": any(
            w in (user_question or "")
            for w in ["差", "生气", "坏", "复杂", "等了", "两次", "敏感", "怕", "?"]
        ),
    }
