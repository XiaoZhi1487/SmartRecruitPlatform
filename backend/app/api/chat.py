"""AI 对话接口：会话管理 + 多轮上下文对话"""
from datetime import datetime

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.interaction import ChatSession, ChatMessage
from app.utils.response import ok, fail

bp = Blueprint("chat", __name__)

MAX_CONTEXT_MESSAGES = 20
MAX_MESSAGE_LEN = 2000


def _build_context(session, history, user):
    """组装多轮对话上下文：注入用户画像 + 最近消息"""
    profile = user.profile
    if profile:
        intro = (
            f"当前用户画像：姓名{profile.real_name or '未填写'}，"
            f"期望岗位{profile.expected_position or '未填写'}，"
            f"期望城市{profile.expected_city or '未填写'}，"
            f"薪资期望{profile.salary_min or '?'}-{profile.salary_max or '?'}K，"
            f"工作年限{profile.experience_years or '?'}年，"
            f"学历{profile.education_level or '?'}，"
            f"技能{','.join(s.name for s in profile.skills) or '未填写'}。"
        )
    else:
        intro = "当前用户尚未完善个人画像。"
    messages = [{"role": "system", "content": intro}]
    messages += history
    return messages


@bp.post("/sessions")
@jwt_required()
def create_session():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()[:64] or "新对话"
    session = ChatSession(user_id=user_id, title=title)
    db.session.add(session)
    db.session.commit()
    return ok(session.to_dict(), "会话已创建")


@bp.get("/sessions")
@jwt_required()
def list_sessions():
    user_id = int(get_jwt_identity())
    sessions = ChatSession.query.filter_by(user_id=user_id).order_by(
        ChatSession.updated_at.desc()).all()
    return ok([s.to_dict() for s in sessions])


@bp.get("/sessions/<int:session_id>/messages")
@jwt_required()
def get_messages(session_id):
    user_id = int(get_jwt_identity())
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return fail("会话不存在", http_status=404)
    return ok([m.to_dict() for m in session.messages])


@bp.post("/sessions/<int:session_id>/messages")
@jwt_required()
def send_message(session_id):
    user_id = int(get_jwt_identity())
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return fail("会话不存在", http_status=404)
    user = db.session.get(User, user_id)
    content = (request.get_json(silent=True) or {}).get("content", "").strip()
    if not content:
        return fail("消息内容不能为空")
    content = content[:MAX_MESSAGE_LEN]

    # 保存用户消息
    db.session.add(ChatMessage(session_id=session.id, role="user", content=content))
    session.updated_at = datetime.utcnow()
    if session.title == "新对话":
        session.title = content[:20]
    db.session.commit()

    # 组装历史
    history = [{"role": m.role, "content": m.content[:1500]}
               for m in session.messages[-MAX_CONTEXT_MESSAGES:]]
    messages = _build_context(session, history, user)

    from app.services.ai_service import ai_service
    try:
        if not ai_service or not ai_service.available:
            raise RuntimeError("DeepSeek API Key 未配置")
        reply = ai_service.chat(messages, system_key="chat")
        if not reply or not reply.strip():
            raise RuntimeError("AI 返回空内容")
    except Exception as e:
        current_app.logger.error("AI对话失败: %s", e)
        reply = ("抱歉，AI 服务暂时不可用。你可以先完善个人画像与技能标签，"
                 "系统会根据你的信息进行智能岗位推荐。")

    db.session.add(ChatMessage(session_id=session.id, role="assistant", content=reply))
    session.updated_at = datetime.utcnow()
    db.session.commit()
    return ok({"reply": reply}, "ok")


@bp.delete("/sessions/<int:session_id>")
@jwt_required()
def delete_session(session_id):
    user_id = int(get_jwt_identity())
    session = ChatSession.query.filter_by(id=session_id, user_id=user_id).first()
    if not session:
        return fail("会话不存在", http_status=404)
    db.session.delete(session)
    db.session.commit()
    return ok(None, "会话已删除")
