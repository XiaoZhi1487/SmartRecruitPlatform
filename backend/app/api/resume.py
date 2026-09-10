"""简历接口：上传 / 解析 / 查询 / AI优化"""
import os
import uuid

from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.resume import Resume
from app.utils.response import ok, fail
from app.utils.logger import get_logger

bp = Blueprint("resume", __name__)
logger = get_logger()

# 每个用户最多保留的简历数
MAX_RESUMES = 10


@bp.post("/upload")
@jwt_required()
def upload_resume():
    user_id = int(get_jwt_identity())
    file = request.files.get("file")
    if not file or not file.filename:
        return fail("请选择要上传的文件")

    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in current_app.config["ALLOWED_RESUME_EXT"]:
        return fail("仅支持 PDF / Word / TXT 格式")

    if Resume.query.filter_by(user_id=user_id).count() >= MAX_RESUMES:
        return fail(f"最多保留 {MAX_RESUMES} 份简历，请先删除旧简历")

    # 保存文件
    fname = f"{user_id}-{uuid.uuid4().hex[:12]}{ext}"
    fpath = os.path.join(current_app.config["UPLOAD_FOLDER"], fname)
    file.save(fpath)
    fsize = os.path.getsize(fpath)

    resume = Resume(user_id=user_id, file_name=file.filename, file_path=fpath,
                    file_type=ext.lstrip("."), file_size=fsize, parse_status="pending")
    db.session.add(resume)
    db.session.commit()

    # 异步解析，避免阻塞上传响应
    from threading import Thread
    app = current_app._get_current_object()
    Thread(target=_parse_task, args=(resume.id, app), daemon=True).start()
    return ok(resume.to_dict(), "上传成功，正在解析...")


def _parse_task(resume_id, app):
    """后台解析简历：文本抽取 → AI结构化 → 兜底启发式"""
    with app.app_context():
        resume = db.session.get(Resume, resume_id)
        if not resume:
            return
        try:
            from app.services.resume_parser import extract_text, heuristic_extract
            text = extract_text(resume.file_path, resume.file_type)
            resume.raw_text = text
            if not text:
                resume.parse_status = "failed"
                db.session.commit()
                return

            structured = heuristic_extract(text)
            # 尝试 AI 结构化抽取（失败则使用启发式结果）
            from app.services.ai_service import ai_service
            if ai_service and ai_service.available:
                try:
                    ai_result = ai_service.parse_resume(text)
                    if isinstance(ai_result, dict) and ai_result.get("real_name") is not None:
                        _merge_structured(structured, ai_result)
                except Exception as e:
                    logger.warning("AI简历解析失败，使用启发式: %s", e)
            import json
            resume.structured = json.dumps(structured, ensure_ascii=False)
            resume.parse_status = "success"
        except Exception as e:
            logger.exception("简历解析失败 #%s", resume_id)
            resume.parse_status = "failed"
        db.session.commit()


def _merge_structured(target, src):
    """合并 AI 结构化结果到启发式结果"""
    for key in ("real_name", "phone", "email", "city", "education_level",
                "expected_position"):
        if src.get(key):
            target[key] = src[key]
    if src.get("experience_years") not in (None, 0, ""):
        target["experience_years"] = src["experience_years"]
    if src.get("skills") and isinstance(src["skills"], list):
        names = [s["name"] for s in src["skills"] if s.get("name")]
        if names:
            target["skills"] = [{"name": n, "level": 3} for n in names[:20]]
    if src.get("educations") and isinstance(src["educations"], list):
        target["educations"] = src["educations"]
    if src.get("works") and isinstance(src["works"], list):
        target["works"] = src["works"]


@bp.get("")
@jwt_required()
def list_resumes():
    user_id = int(get_jwt_identity())
    resumes = Resume.query.filter_by(user_id=user_id).order_by(
        Resume.created_at.desc()).all()
    return ok([r.to_dict() for r in resumes])


@bp.get("/<int:resume_id>")
@jwt_required()
def get_resume(resume_id):
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
    if not resume:
        return fail("简历不存在", http_status=404)
    return ok(resume.to_dict(include_detail=True))


@bp.delete("/<int:resume_id>")
@jwt_required()
def delete_resume(resume_id):
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
    if not resume:
        return fail("简历不存在", http_status=404)
    try:
        if os.path.exists(resume.file_path):
            os.remove(resume.file_path)
    except OSError:
        pass
    db.session.delete(resume)
    db.session.commit()
    return ok(None, "简历已删除")


@bp.post("/<int:resume_id>/optimize")
@jwt_required()
def optimize_resume(resume_id):
    """AI 简历优化建议"""
    user_id = int(get_jwt_identity())
    resume = Resume.query.filter_by(id=resume_id, user_id=user_id).first()
    if not resume:
        return fail("简历不存在", http_status=404)
    if resume.parse_status != "success" or not resume.raw_text:
        return fail("简历尚未解析完成，请稍后重试")

    from app.services.ai_service import ai_service
    if not ai_service or not ai_service.available:
        return fail("AI服务未配置", http_status=503)
    data = request.get_json(silent=True) or {}
    job_title = data.get("job_title")
    try:
        result = ai_service.optimize_resume(resume.raw_text, job_title)
        if not result or "_raw" in result:
            return fail("AI 优化分析失败，请稍后重试")
        return ok(result)
    except Exception as e:
        return fail(f"AI 服务调用失败: {e}", http_status=503)
