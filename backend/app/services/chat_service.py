"""AI 结果持久化：将职位深度解读 / 简历优化等 AI 产物写入「AI 职业助手」新建对话"""
from app.extensions import db
from app.models.interaction import ChatSession, ChatMessage

# 与 chat.py 保持一致的消息长度约束
MAX_USER_LEN = 2000
MAX_ASSISTANT_LEN = 8000


def save_ai_exchange(user_id: int, title: str, user_content: str, assistant_content: str):
    """新建一条对话并写入 user 问题 + assistant 回答，返回会话对象。"""
    session = ChatSession(user_id=user_id, title=(title or "AI分析")[:64])
    db.session.add(session)
    db.session.flush()
    db.session.add(ChatMessage(session_id=session.id, role="user",
                               content=user_content[:MAX_USER_LEN]))
    db.session.add(ChatMessage(session_id=session.id, role="assistant",
                               content=assistant_content[:MAX_ASSISTANT_LEN]))
    db.session.commit()
    return session


def format_job_analysis(result: dict) -> str:
    """将 AI 岗位解读 dict 格式化为对话可读文本"""
    lines = []
    if result.get("core_skills"):
        lines.append("核心技能：" + "、".join(result["core_skills"]))
    if result.get("suitability_advice"):
        lines.append("适配建议：" + str(result["suitability_advice"]))
    if result.get("career_growth"):
        lines.append("成长路径：" + str(result["career_growth"]))
    if result.get("interview_tips"):
        lines.append("面试提示：" + str(result["interview_tips"]))
    return "\n\n".join(lines) or "（AI 未返回结构化解读内容）"


def format_resume_optimize(result: dict) -> str:
    """将 AI 简历优化 dict 格式化为对话可读文本"""
    lines = []
    if result.get("score") is not None:
        lines.append(f"简历评分：{result['score']}/100")
    if result.get("overall"):
        lines.append("总体评价：" + str(result["overall"]))
    for s in (result.get("suggestions") or []):
        if isinstance(s, dict) and s.get("dimension"):
            lines.append(f"【{s['dimension']}】{s.get('advice', '')}")
    return "\n\n".join(lines) or "（AI 未返回优化建议）"