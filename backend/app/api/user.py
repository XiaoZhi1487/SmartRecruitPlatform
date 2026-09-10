"""用户资料接口：个人信息、教育背景、工作经历、技能、修改密码"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.extensions import db
from app.models.user import User
from app.models.profile import UserProfile, Education, WorkExperience, Skill
from app.utils.response import ok, fail
from app.utils.validators import check_password_strength, is_valid_phone, clean_text

bp = Blueprint("user", __name__)


def _get_current():
    user = db.session.get(User, int(get_jwt_identity()))
    return user


def _profile_or_fail(user):
    p = UserProfile.query.filter_by(user_id=user.id).first()
    if not p:
        return fail("请先完善个人信息", http_status=404)
    return p


@bp.get("/profile")
@jwt_required()
def get_profile():
    user = _get_current()
    return ok(user.profile.to_dict() if user.profile else None)


@bp.put("/profile")
@jwt_required()
def update_profile():
    user = _get_current()
    p = user.profile or UserProfile(user_id=user.id)
    if not user.profile:
        db.session.add(p)
    data = request.get_json(silent=True) or {}

    text_fields = ["real_name", "gender", "city", "avatar", "self_intro",
                   "expected_position", "expected_city", "education_level"]
    for f in text_fields:
        if f in data:
            setattr(p, f, clean_text(str(data[f] or "")))
    if "birthday" in data and data["birthday"]:
        from datetime import date
        try:
            p.birthday = date.fromisoformat(str(data["birthday"])[:10])
        except ValueError:
            return fail("生日格式错误，应为 YYYY-MM-DD")
    if "phone" in data:
        phone = clean_text(str(data.get("phone") or ""))
        if phone and not is_valid_phone(phone):
            return fail("手机号格式不正确")
        p.phone = phone
    if "salary_min" in data:
        p.salary_min = int(data["salary_min"]) if data["salary_min"] not in (None, "") else None
    if "salary_max" in data:
        p.salary_max = int(data["salary_max"]) if data["salary_max"] not in (None, "") else None
    if "experience_years" in data:
        p.experience_years = int(data["experience_years"]) if data["experience_years"] not in (None, "") else None
    if p.salary_min and p.salary_max and p.salary_min > p.salary_max:
        return fail("期望薪资下限不能大于上限")
    db.session.commit()
    return ok(p.to_dict(), "资料已更新")


@bp.post("/profile/educations")
@jwt_required()
def add_education():
    user = _get_current()
    p = _profile_or_fail(user)
    data = request.get_json(silent=True) or {}
    school = clean_text(str(data.get("school") or ""))
    if not school:
        return fail("学校名称不能为空")
    edu = Education(profile_id=p.id, school=school,
                    major=clean_text(str(data.get("major") or "")),
                    degree=data.get("degree"), start_date=data.get("start_date"),
                    end_date=data.get("end_date"),
                    description=clean_text(str(data.get("description") or "")))
    db.session.add(edu)
    db.session.commit()
    return ok(edu.to_dict(), "教育经历已添加")


@bp.put("/profile/educations/<int:edu_id>")
@jwt_required()
def update_education(edu_id):
    user = _get_current()
    p = _profile_or_fail(user)
    edu = Education.query.filter_by(id=edu_id, profile_id=p.id).first()
    if not edu:
        return fail("教育经历不存在", http_status=404)
    data = request.get_json(silent=True) or {}
    if "school" in data:
        edu.school = clean_text(str(data["school"]))
    for f in ["major", "degree", "start_date", "end_date", "description"]:
        if f in data:
            setattr(edu, f, clean_text(str(data[f] or "")))
    db.session.commit()
    return ok(edu.to_dict(), "已更新")


@bp.delete("/profile/educations/<int:edu_id>")
@jwt_required()
def delete_education(edu_id):
    user = _get_current()
    p = _profile_or_fail(user)
    edu = Education.query.filter_by(id=edu_id, profile_id=p.id).first()
    if not edu:
        return fail("教育经历不存在", http_status=404)
    db.session.delete(edu)
    db.session.commit()
    return ok(None, "已删除")


@bp.post("/profile/works")
@jwt_required()
def add_work():
    user = _get_current()
    p = _profile_or_fail(user)
    data = request.get_json(silent=True) or {}
    company = clean_text(str(data.get("company") or ""))
    position = clean_text(str(data.get("position") or ""))
    if not company or not position:
        return fail("公司和职位不能为空")
    work = WorkExperience(profile_id=p.id, company=company, position=position,
                          start_date=data.get("start_date"), end_date=data.get("end_date"),
                          description=clean_text(str(data.get("description") or "")))
    db.session.add(work)
    db.session.commit()
    return ok(work.to_dict(), "工作经历已添加")


@bp.put("/profile/works/<int:work_id>")
@jwt_required()
def update_work(work_id):
    user = _get_current()
    p = _profile_or_fail(user)
    work = WorkExperience.query.filter_by(id=work_id, profile_id=p.id).first()
    if not work:
        return fail("工作经历不存在", http_status=404)
    data = request.get_json(silent=True) or {}
    if "company" in data:
        work.company = clean_text(str(data["company"]))
    if "position" in data:
        work.position = clean_text(str(data["position"]))
    for f in ["start_date", "end_date", "description"]:
        if f in data:
            setattr(work, f, clean_text(str(data[f] or "")))
    db.session.commit()
    return ok(work.to_dict(), "已更新")


@bp.delete("/profile/works/<int:work_id>")
@jwt_required()
def delete_work(work_id):
    user = _get_current()
    p = _profile_or_fail(user)
    work = WorkExperience.query.filter_by(id=work_id, profile_id=p.id).first()
    if not work:
        return fail("工作经历不存在", http_status=404)
    db.session.delete(work)
    db.session.commit()
    return ok(None, "已删除")


@bp.post("/profile/skills")
@jwt_required()
def add_skill():
    user = _get_current()
    p = _profile_or_fail(user)
    data = request.get_json(silent=True) or {}
    name = clean_text(str(data.get("name") or ""))
    if not name:
        return fail("技能名称不能为空")
    skill = Skill(profile_id=p.id, name=name,
                  level=max(1, min(5, int(data.get("level") or 3))),
                  category=data.get("category"))
    db.session.add(skill)
    db.session.commit()
    return ok(skill.to_dict(), "技能已添加")


@bp.put("/profile/skills/<int:skill_id>")
@jwt_required()
def update_skill(skill_id):
    user = _get_current()
    p = _profile_or_fail(user)
    skill = Skill.query.filter_by(id=skill_id, profile_id=p.id).first()
    if not skill:
        return fail("技能不存在", http_status=404)
    data = request.get_json(silent=True) or {}
    if "name" in data:
        skill.name = clean_text(str(data["name"]))
    if "level" in data:
        skill.level = max(1, min(5, int(data["level"])))
    if "category" in data:
        skill.category = data["category"]
    db.session.commit()
    return ok(skill.to_dict(), "已更新")


@bp.delete("/profile/skills/<int:skill_id>")
@jwt_required()
def delete_skill(skill_id):
    user = _get_current()
    p = _profile_or_fail(user)
    skill = Skill.query.filter_by(id=skill_id, profile_id=p.id).first()
    if not skill:
        return fail("技能不存在", http_status=404)
    db.session.delete(skill)
    db.session.commit()
    return ok(None, "已删除")


@bp.post("/change-password")
@jwt_required()
def change_password():
    user = _get_current()
    data = request.get_json(silent=True) or {}
    old = data.get("old_password", "")
    new = data.get("new_password", "")
    if not user.check_password(old):
        return fail("原密码错误", http_status=401)
    ok_flag, msg = check_password_strength(new)
    if not ok_flag:
        return fail(msg)
    user.set_password(new)
    db.session.commit()
    return ok(None, "密码修改成功")
