"""职位接口：搜索/筛选/详情/收藏/原文跳转/AI分析"""
import json

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.job import Job
from app.models.user import User
from app.models.interaction import FavoriteJob
from app.utils.response import ok, fail, page_result

bp = Blueprint("jobs", __name__)


def _build_query(args):
    query = Job.query.filter_by(is_active=True)
    keyword = (args.get("keyword") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(db.or_(Job.title.like(like), Job.company_name.like(like),
                                    Job.description.like(like), Job.job_tags.like(like)))
    city = (args.get("city") or "").strip()
    if city:
        query = query.filter(Job.city == city)
    exp = (args.get("experience") or "").strip()
    if exp:
        query = query.filter(Job.experience_required.like(f"%{exp}%"))
    edu = (args.get("education") or "").strip()
    if edu:
        query = query.filter(Job.education_required.like(f"%{edu}%"))
    src = (args.get("source") or "").strip()
    if src:
        query = query.filter_by(source=src)
    return query


@bp.get("")
@jwt_required(optional=True)
def list_jobs():
    args = request.args
    query = _build_query(args)
    sort = args.get("sort", "latest")
    from sqlalchemy import nullslast
    if sort == "salary":
        query = query.order_by(nullslast(Job.salary_max.desc()))
    elif sort == "salary_asc":
        query = query.order_by(nullslast(Job.salary_min.asc()))
    elif sort == "company":
        query = query.order_by(nullslast(Job.company_name.asc()))
    else:
        query = query.order_by(Job.created_at.desc())
    page = max(1, int(args.get("page", 1)))
    page_size = min(int(args.get("page_size", 10)), 50)
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    identity = get_jwt_identity()
    fav_ids = set()
    if identity:
        fav_ids = {f.job_id for f in FavoriteJob.query.filter_by(
            user_id=int(identity)).all()}
    result = []
    for j in items:
        d = j.to_dict(brief=True)
        d["is_favorite"] = j.id in fav_ids
        result.append(d)
    return ok(page_result(result, total, page, page_size))


@bp.get("/cities")
def list_cities():
    cities = [r[0] for r in db.session.query(Job.city).filter(Job.city.isnot(None)).distinct().all()]
    return ok(cities)


@bp.get("/stats")
def job_stats():
    """职位数据统计（供首页/仪表盘可视化）"""
    from sqlalchemy import func
    total = Job.query.filter_by(is_active=True).count()
    # 覆盖城市 = 独立城市数（不依赖薪资是否解析成功，修复统计为0的问题）
    covered_cities = db.session.query(func.count(func.distinct(Job.city))).filter(
        Job.city.isnot(None), Job.city != "").scalar() or 0
    salary_rows = db.session.query(
        func.avg(Job.salary_min), func.avg(Job.salary_max),
        Job.city).filter(Job.salary_min.isnot(None)).group_by(Job.city).all()
    city_stats = [
        {"city": r[2], "avg_min": round(r[0] or 0, 1), "avg_max": round(r[1] or 0, 1)}
        for r in salary_rows
    ]
    top_companies = db.session.query(
        Job.company_name, func.count(Job.id)).filter(
        Job.company_name.isnot(None)).group_by(Job.company_name).order_by(
        func.count(Job.id).desc()).limit(8).all()
    return ok({
        "total_jobs": total,
        "covered_cities": covered_cities,
        "city_salary": city_stats,
        "top_companies": [{"name": c[0], "count": c[1]} for c in top_companies],
    })


@bp.get("/analysis")
def job_analysis():
    """招聘市场数据分析：岗位需求排行/薪资趋势/学历分布/经验要求 + AI 结论

    薪资统一折算为 K/月（万×10、年÷12、天×22），供可视化使用。
    """
    from app.services.analysis_service import build_analysis
    jobs = Job.query.filter_by(is_active=True).all()
    data = build_analysis([j.to_dict(brief=True) for j in jobs])
    return ok(data)


@bp.get("/<int:job_id>")
@jwt_required(optional=True)
def job_detail(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return fail("职位不存在", http_status=404)
    data = job.to_dict()
    data["jump_url"] = job.link or ""
    identity = get_jwt_identity()
    if identity:
        fav = FavoriteJob.query.filter_by(user_id=int(identity), job_id=job.id).first()
        data["is_favorite"] = fav is not None
    else:
        data["is_favorite"] = False
    return ok(data)


@bp.post("/<int:job_id>/favorite")
@jwt_required()
def favorite(job_id):
    user_id = int(get_jwt_identity())
    job = db.session.get(Job, job_id)
    if not job:
        return fail("职位不存在", http_status=404)
    if not FavoriteJob.query.filter_by(user_id=user_id, job_id=job_id).first():
        db.session.add(FavoriteJob(user_id=user_id, job_id=job_id))
        db.session.commit()
    return ok(None, "已收藏")


@bp.delete("/<int:job_id>/favorite")
@jwt_required()
def unfavorite(job_id):
    user_id = int(get_jwt_identity())
    fav = FavoriteJob.query.filter_by(user_id=user_id, job_id=job_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
    return ok(None, "已取消收藏")


@bp.get("/favorites/list")
@jwt_required()
def my_favorites():
    user_id = int(get_jwt_identity())
    favs = FavoriteJob.query.filter_by(user_id=user_id).order_by(
        FavoriteJob.created_at.desc()).all()
    items = []
    for f in favs:
        if f.job:
            d = f.job.to_dict(brief=True)
            d["fav_time"] = f.created_at.isoformat() if f.created_at else None
            items.append(d)
    return ok(items)


@bp.get("/<int:job_id>/redirect")
@jwt_required(optional=True)
def jump_to_source(job_id):
    """一键跳转 前程无忧 原文页面"""
    job = db.session.get(Job, job_id)
    if not job:
        return fail("职位不存在", http_status=404)
    if not job.link:
        return fail("该职位无原文链接", http_status=404)
    return ok({"jump_url": job.link, "title": job.title})


@bp.post("/<int:job_id>/analyze")
@jwt_required(optional=True)
def ai_analyze(job_id):
    """AI 岗位深度解读（已登录时自动写入「AI 职业助手」新对话）"""
    job = db.session.get(Job, job_id)
    if not job:
        return fail("职位不存在", http_status=404)
    from app.services.ai_service import ai_service
    if not ai_service or not ai_service.available:
        return fail("AI服务未配置", http_status=503)
    try:
        result = ai_service.analyze_job(job.to_dict())
        if not result or "_raw" in result:
            return fail("AI 解析失败，请稍后重试")
        identity = get_jwt_identity()
        if identity:
            from app.services.chat_service import save_ai_exchange, format_job_analysis
            try:
                save_ai_exchange(
                    int(identity),
                    title=f"职位解读-{job.title}",
                    user_content=(
                        f"请对职位「{job.title}」（{job.company_name or ''}，"
                        f"{job.salary_text or '薪资面议'}，{job.city or ''}）生成深度解读。"
                    ),
                    assistant_content=format_job_analysis(result),
                )
            except Exception as e:
                db.session.rollback()
                current_app.logger.warning("写入AI对话失败: %s", e)
        return ok(result)
    except Exception as e:
        return fail(f"AI 服务调用失败: {e}", http_status=503)
