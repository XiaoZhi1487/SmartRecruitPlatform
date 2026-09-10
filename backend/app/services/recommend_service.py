"""智能推荐算法：基于多维匹配度打分
维度：技能匹配 / 薪资匹配 / 地点匹配 / 经验匹配 / 学历匹配
"""
import json
import re
from datetime import datetime

from app.extensions import db
from app.models.job import Job
from app.models.user import User
from app.models.profile import UserProfile, Skill

# 权重配置
WEIGHTS = {
    "skill": 0.40,
    "salary": 0.20,
    "location": 0.15,
    "experience": 0.15,
    "education": 0.10,
}

EDUCATION_RANK = {"高中": 1, "大专": 2, "本科": 3, "硕士": 4, "博士": 5}
EXPERIENCE_YEARS = {"在校/应届": 0, "1年以内": 1, "1-3年": 2, "3-5年": 4, "5-10年": 7, "10年以上": 10}


def parse_salary(job) -> tuple:
    """返回 (min_k, max_k)；解析失败返回 (None, None)"""
    if job.salary_min is not None:
        return job.salary_min, job.salary_max
    text = job.salary_text or ""
    nums = re.findall(r"\d+", text)
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
    return None, None


def get_user_context(user_id) -> dict:
    """聚合用户画像上下文（技能/薪资/地点/经验/学历）"""
    profile = UserProfile.query.filter_by(user_id=user_id).first()
    if not profile:
        return {"skills": [], "salary_min": None, "salary_max": None,
                "city": None, "experience_years": None, "education_level": None,
                "expected_position": None}
    return {
        "skills": [s.name.lower() for s in profile.skills],
        "salary_min": profile.salary_min,
        "salary_max": profile.salary_max,
        "city": profile.expected_city or profile.city,
        "experience_years": profile.experience_years,
        "education_level": profile.education_level,
        "expected_position": profile.expected_position,
    }


def get_job_tags(job) -> list:
    try:
        return json.loads(job.job_tags) if job.job_tags else []
    except Exception:
        return []


def _skill_score(job, ctx) -> float:
    tags = [t.lower() for t in get_job_tags(job)]
    title = (job.title or "").lower()
    user_skills = set(ctx.get("skills") or [])
    if not user_skills:
        return 0.5  # 无技能信息时取中性分
    pool = set(tags) | {w for w in re.findall(r"[a-z0-9+#.]+", title) if len(w) > 1}
    if not pool:
        return 0.5
    hit = user_skills & pool
    return min(1.0, len(hit) * 0.35 + 0.15)


def _salary_score(job, ctx) -> float:
    jmin, jmax = parse_salary(job)
    umin, umax = ctx.get("salary_min"), ctx.get("salary_max")
    if jmin is None or umin is None:
        return 0.6
    jmax = jmax or jmin
    umax = umax or umin
    # 区间重叠率
    overlap = min(jmax, umax) - max(jmin, umin)
    if overlap >= 0:
        union = max(jmax, umax) - min(jmin, umin)
        return min(1.0, overlap / union + 0.3) if union else 1.0
    # 无重叠：根据距离衰减
    dist = min(abs(jmin - umax), abs(jmax - umin))
    return max(0.0, 1.0 - dist / 20)


def _location_score(job, ctx) -> float:
    city = ctx.get("city")
    if not city:
        return 0.6
    if job.city == city:
        return 1.0
    # 支持“北京/上海”等并列城市
    if job.city and city in job.city:
        return 1.0
    return 0.2


def _experience_score(job, ctx) -> float:
    years = ctx.get("experience_years")
    if years is None:
        return 0.6
    req = EXPERIENCE_YEARS.get(job.experience_required, 2)
    diff = years - req
    if diff >= 0:
        return min(1.0, 0.7 + diff * 0.05)
    return max(0.2, 0.7 + diff * 0.15)


def _education_score(job, ctx) -> float:
    user_edu = EDUCATION_RANK.get(ctx.get("education_level"))
    job_edu = EDUCATION_RANK.get(job.education_required)
    if not user_edu:
        return 0.6
    if not job_edu:
        return 0.8
    diff = user_edu - job_edu
    if diff >= 0:
        return min(1.0, 0.8 + diff * 0.1)
    return max(0.2, 0.8 + diff * 0.2)


def score_job(job, ctx) -> dict:
    """计算单职位综合评分与维度明细"""
    scores = {
        "skill": _skill_score(job, ctx),
        "salary": _salary_score(job, ctx),
        "location": _location_score(job, ctx),
        "experience": _experience_score(job, ctx),
        "education": _education_score(job, ctx),
    }
    total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
    return {"total": round(total * 100, 1), "dimensions": scores}


def recommend_jobs_for_user(user_id, limit=10, exclude_ids=None) -> list:
    """为用户推荐岗位，返回带评分与原因的列表"""
    ctx = get_user_context(user_id)
    query = Job.query.filter_by(is_active=True)
    if exclude_ids:
        query = query.filter(~Job.id.in_(exclude_ids))
    jobs = query.order_by(Job.created_at.desc()).limit(500).all()
    scored = []
    for job in jobs:
        s = score_job(job, ctx)
        if s["total"] >= 20:
            scored.append((s["total"], job, s["dimensions"]))
    scored.sort(key=lambda x: x[0], reverse=True)
    result = []
    for total, job, dims in scored[:limit]:
        d = job.to_dict(brief=True)
        d["match_score"] = total
        d["dimensions"] = {k: round(v * 100) for k, v in dims.items()}
        d["reason"] = _reason_text(job, ctx, dims)
        result.append(d)
    return result


def match_candidates_for_job(job_id, limit=20) -> list:
    """企业端：按岗位要求匹配候选人（多维度筛选）"""
    job = db.session.get(Job, job_id)
    if not job:
        return []
    job_ctx = {
        "skills": [t.lower() for t in get_job_tags(job)],
        "salary_min": None, "salary_max": None,
        "city": job.city,
        "experience_years": EXPERIENCE_YEARS.get(job.experience_required, 2),
        "education_level": job.education_required,
    }
    profiles = UserProfile.query.all()
    scored = []
    for p in profiles:
        u = db.session.get(User, p.user_id)
        if not u or not u.is_active:
            continue
        ctx = get_user_context(p.user_id)
        # 反转为“候选人对岗位”的匹配度
        scores = {
            "skill": _skill_score(job, ctx),
            "salary": 1.0,
            "location": _location_score(job, ctx),
            "experience": _experience_score(job, ctx),
            "education": _education_score(job, ctx),
        }
        total = sum(scores[k] * WEIGHTS[k] for k in WEIGHTS)
        scored.append((total, p, u, scores))
    scored.sort(key=lambda x: x[0], reverse=True)
    result = []
    for total, p, u, scores in scored[:limit]:
        result.append({
            "user_id": u.id,
            "username": u.username,
            "real_name": p.real_name,
            "education_level": p.education_level,
            "experience_years": p.experience_years,
            "city": p.expected_city,
            "expected_position": p.expected_position,
            "skills": [s["name"] for s in p.skills][:8],
            "match_score": round(total * 100, 1),
            "dimensions": {k: round(v * 100) for k, v in scores.items()},
        })
    return result


def _reason_text(job, ctx, dims) -> str:
    parts = []
    if dims["skill"] >= 0.7:
        parts.append("技能匹配度高")
    if dims["salary"] >= 0.7:
        parts.append("薪资符合期望")
    if dims["location"] >= 0.7:
        parts.append(f"地点{job.city}合适")
    if dims["experience"] >= 0.7:
        parts.append("经验要求匹配")
    if dims["education"] >= 0.7:
        parts.append("学历要求匹配")
    return "、".join(parts) if parts else "综合条件较合适"
