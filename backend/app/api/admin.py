"""管理员接口：用户管理 / 系统统计 / 数据管理"""
from datetime import datetime

from flask import Blueprint, request

from app.extensions import db
from app.models.user import User
from app.models.job import Job, Company
from app.models.resume import Resume
from app.models.interaction import ChatSession, CrawlTask
from app.utils.response import ok, fail, page_result
from app.utils.decorators import admin_required
from app.utils.validators import is_valid_username, is_valid_email, check_password_strength

bp = Blueprint("admin", __name__)


@bp.get("/stats")
@admin_required
def stats():
    return ok({
        "users": User.query.count(),
        "jobs": Job.query.count(),
        "active_jobs": Job.query.filter_by(is_active=True).count(),
        "companies": Company.query.count(),
        "resumes": Resume.query.count(),
        "chat_sessions": ChatSession.query.count(),
        "crawl_tasks": CrawlTask.query.count(),
    })


@bp.get("/users")
@admin_required
def list_users():
    args = request.args
    page = max(1, int(args.get("page", 1)))
    page_size = min(int(args.get("page_size", 10)), 50)
    query = User.query
    kw = (args.get("keyword") or "").strip()
    if kw:
        like = f"%{kw}%"
        query = query.filter(db.or_(User.username.like(like), User.email.like(like)))
    query = query.order_by(User.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(page_result([u.to_dict() for u in items], total, page, page_size))


@bp.patch("/users/<int:user_id>")
@admin_required
def update_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return fail("用户不存在", http_status=404)
    data = request.get_json(silent=True) or {}
    if "is_active" in data:
        user.is_active = bool(data["is_active"])
    if "role" in data:
        if data["role"] not in ("user", "enterprise", "admin"):
            return fail("角色不合法")
        user.role = data["role"]
    if "email_verified" in data:
        user.email_verified = bool(data["email_verified"])
    db.session.commit()
    return ok(user.to_dict(), "用户已更新")


@bp.post("/users")
@admin_required
def create_user():
    """管理员创建用户（含企业用户）"""
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or "user"

    if not is_valid_username(username):
        return fail("用户名格式不正确")
    if not is_valid_email(email):
        return fail("邮箱格式不正确")
    ok_flag, msg = check_password_strength(password)
    if not ok_flag:
        return fail(msg)
    if User.query.filter(db.or_(User.username == username, User.email == email)).first():
        return fail("用户名或邮箱已存在", http_status=409)
    user = User(username=username, email=email, role=role, email_verified=True)
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return ok(user.to_dict(), "用户创建成功")


@bp.delete("/jobs/<int:job_id>")
@admin_required
def delete_job(job_id):
    job = db.session.get(Job, job_id)
    if not job:
        return fail("职位不存在", http_status=404)
    db.session.delete(job)
    db.session.commit()
    return ok(None, "职位已删除")


@bp.post("/jobs/cleanup")
@admin_required
def cleanup_jobs():
    """清理无效职位（按 source 或关键字）"""
    data = request.get_json(silent=True) or {}
    source = data.get("source")
    query = Job.query
    if source:
        query = query.filter_by(source=source)
    deleted = query.delete(synchronize_session=False)
    db.session.commit()
    return ok({"deleted": deleted}, f"已清理 {deleted} 条职位数据")


@bp.get("/crawl-tasks")
@admin_required
def crawl_tasks():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(int(request.args.get("page_size", 10)), 50)
    query = CrawlTask.query.order_by(CrawlTask.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(page_result([t.to_dict() for t in items], total, page, page_size))
