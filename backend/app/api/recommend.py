"""智能推荐接口：岗位推荐 / 候选人匹配 / 数据概览"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.job import Job
from app.services.recommend_service import (
    recommend_jobs_for_user, match_candidates_for_job, get_user_context,
)
from app.utils.response import ok, fail

bp = Blueprint("recommend", __name__)


@bp.get("/jobs")
@jwt_required()
def recommend_jobs():
    """基于用户画像的智能岗位推荐"""
    user_id = int(get_jwt_identity())
    limit = min(int(request.args.get("limit", 10)), 30)
    try:
        result = recommend_jobs_for_user(user_id, limit=limit)
    except Exception as e:
        return fail(f"推荐计算失败: {e}", http_status=500)
    return ok({"items": result, "total": len(result)})


@bp.get("/candidates")
@jwt_required()
def match_candidates():
    """企业端：为指定职位匹配候选人"""
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return fail("用户不存在", http_status=404)
    if user.role not in ("enterprise", "admin"):
        return fail("仅企业用户可使用候选人匹配功能", http_status=403)
    job_id = request.args.get("job_id", type=int)
    if not job_id:
        return fail("请指定职位 ID")
    limit = min(int(request.args.get("limit", 20)), 50)
    result = match_candidates_for_job(job_id, limit=limit)
    return ok({"items": result, "total": len(result)})


@bp.get("/overview")
@jwt_required(optional=True)
def overview():
    """推荐总览：用户画像匹配概况 + 热门技能"""
    identity = get_jwt_identity()
    ctx = get_user_context(int(identity)) if identity else {}
    # 热门技能统计（从职位标签中提取）
    import json
    from collections import Counter
    from app.extensions import db
    jobs = Job.query.filter_by(is_active=True).limit(300).all()
    counter = Counter()
    for j in jobs:
        if j.job_tags:
            try:
                for t in json.loads(j.job_tags):
                    counter[t] += 1
            except Exception:
                pass
    hot_skills = [{"name": k, "count": v} for k, v in counter.most_common(15)]
    return ok({
        "user_context": ctx,
        "hot_skills": hot_skills,
        "suggestion": _suggestion(ctx),
    })


def _suggestion(ctx):
    if not ctx.get("skills"):
        return "请先在【个人中心】完善技能标签与求职期望，推荐会更为精准。"
    return "已根据你的技能与期望生成个性化推荐，可前往【智能推荐】查看。"
