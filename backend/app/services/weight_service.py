"""动态推荐权重：基于行为反馈的五维自适应推荐算法
三层：
  第一层 全局权重  W_global：由岗位数据区分度自动产生（区分度越高权重越高）
  第二层 个性权重  W_user  ：由用户历史行为反馈学习（浏览/详情/收藏/投递）
  第三层 动态融合  W_final = alpha*W_global + (1-alpha)*W_user，冷启动 alpha=1
"""
import math
import json
from collections import defaultdict
from datetime import datetime, timedelta

from app.extensions import db
from app.models.job import Job
from app.models.interaction import UserFeedback
from app.models.profile import UserProfile
from app.services import recommend_service

# 维度顺序
DIMS = ["skill", "salary", "location", "experience", "education"]

# 冷启动初始权重（即原固定权重）
DEFAULT_WEIGHTS = {"skill": 0.40, "salary": 0.20, "location": 0.15,
                   "experience": 0.15, "education": 0.10}

# 行为 -> 反馈权重
ACTION_WEIGHT = {"browse": 1, "view": 2, "favorite": 4, "apply": 5}

# 仅强反馈行为参与个性化权重学习（浏览噪音较大，可去抖）
STRONG_ACTIONS = {"view", "favorite", "apply"}

# 行为时间衰减半衰期（天）
HALF_LIFE_DAYS = 14.0


# ---------------------------------------------------------------------------
# 第一层：岗位数据区分度 -> 全局权重
# ---------------------------------------------------------------------------
def _distinctiveness(scores: list) -> float:
    """维度区分度：用标准差归一化为 0~1（区分越明显 → 越大）"""
    n = len(scores)
    if n < 2:
        return 0.0
    mean = sum(scores) / n
    var = sum((x - mean) ** 2 for x in scores) / n
    std = math.sqrt(var)
    return min(1.0, std / 0.5)  # 满分阈 0.5（分数区间 0~1）


def compute_global_weights(jobs, ctx) -> dict:
    """第一层：根据候选岗位库计算每个维度的区分度权重。
    区分度越高 -> 权重越高；反之（大家都差不多）-> 权重降低。
    岗位库区分度微弱时回退到默认权重，保证数值稳定。
    """
    if not jobs:
        return dict(DEFAULT_WEIGHTS)
    # 逐岗位计算各维度分数
    per_dim = {d: [] for d in DIMS}
    for job in jobs:
        s = recommend_service.score_job(job, ctx)["dimensions"]
        for d in DIMS:
            per_dim[d].append(s[d])
    disc = {d: _distinctiveness(per_dim[d]) for d in DIMS}
    total = sum(disc.values())
    if total <= 1e-6:
        return dict(DEFAULT_WEIGHTS)
    weights = {d: disc[d] / total for d in DIMS}
    # 锚定融合权重，避免个别维度被完全压制
    anchored = {d: 0.6 * weights[d] + 0.4 * DEFAULT_WEIGHTS[d] for d in DIMS}
    norm = sum(anchored.values())
    return {d: anchored[d] / norm for d in DIMS}


# ---------------------------------------------------------------------------
# 第二层：用户行为反馈 -> 个性权重
# ---------------------------------------------------------------------------
def _time_decay(ts) -> float:
    """越近的行为权重越高（指数时间衰减）"""
    if not ts:
        return 1.0
    days = max(0.0, (datetime.utcnow() - ts).total_seconds() / 86400.0)
    return math.exp(-days / HALF_LIFE_DAYS)


def load_user_feedback(user_id, within_days=90) -> list:
    """加载用户近期有效行为，返回 [(job, action_weight)]；已去重（每职位取最强行为）"""
    since = datetime.utcnow() - timedelta(days=within_days)
    rows = (
        UserFeedback.query
        .filter_by(user_id=user_id)
        .filter(UserFeedback.created_at >= since)
        .all()
    )
    best = {}
    for r in rows:
        if r.action not in ACTION_WEIGHT:
            continue
        w = ACTION_WEIGHT[r.action] * _time_decay(r.created_at)
        if r.job_id not in best or w > best[r.job_id][0]:
            best[r.job_id] = (w, r.job)
    return [(job, w) for w, job in best.values() if job is not None]


def compute_user_weights(user_id, ctx) -> dict:
    """第二层：由用户行为反馈学习个性权重。
    思路：用户偏好的岗位集合在各维度的区分度反映了用户的“偏好向”。
    行为强度按 浏览1/详情2/收藏4/投递5 加权，近发行为更有效。
    """
    feedback = load_user_feedback(user_id)
    if len(feedback) < 2:
        return None  # 行为不足 -> 冷启动，不启用个性化

    # 按行为强度加权聚合各维度分数
    per_dim = defaultdict(float)
    total_w = 0.0
    for job, w in feedback:
        s = recommend_service.score_job(job, ctx)["dimensions"]
        for d in DIMS:
            per_dim[d] += s[d] * w
        total_w += w
    if total_w <= 0:
        return None

    means = {d: per_dim[d] / total_w for d in DIMS}
    # 用户关注维度：该维度分数均值越高=用户看重（强反馈集中在高分维度）
    total = sum(means.values())
    if total <= 1e-6:
        return None
    weights = {d: means[d] / total for d in DIMS}
    # 与默认权重融合，避免忽冷忽热
    anchored = {d: 0.7 * weights[d] + 0.3 * DEFAULT_WEIGHTS[d] for d in DIMS}
    norm = sum(anchored.values())
    return {d: anchored[d] / norm for d in DIMS}


# ---------------------------------------------------------------------------
# 第三层：动态融合
# ---------------------------------------------------------------------------
def fuse_weights(global_w, user_w, alpha=0.5) -> dict:
    """W_final = alpha*W_global + (1-alpha)*W_user；user_w 为空时退化为全局权重。"""
    if not user_w:
        return dict(global_w)
    fused = {d: alpha * global_w[d] + (1 - alpha) * user_w[d] for d in DIMS}
    norm = sum(fused.values())
    return {d: fused[d] / norm for d in DIMS}


def get_dynamic_weights(user_id, ctx, jobs=None, alpha=0.5) -> dict:
    """对外入口：整合三层，返回最终动态权重 + 说明信息。"""
    if jobs is None:
        jobs = Job.query.filter_by(is_active=True).limit(500).all()
    w_global = compute_global_weights(jobs, ctx)
    w_user = compute_user_weights(user_id, ctx)
    w_final = fuse_weights(w_global, w_user, alpha)
    return {
        "weights": w_final,
        "global_weights": w_global,
        "user_weights": w_user,
        "alpha": alpha,
        "using_personal": w_user is not None,
    }


# ---------------------------------------------------------------------------
# 行为记录
# ---------------------------------------------------------------------------
def record_feedback(user_id, job_id, action) -> UserFeedback:
    """记录一条用户行为反馈（返回模型实例；失败返回 None）"""
    if action not in ACTION_WEIGHT:
        return None
    fb = UserFeedback(user_id=user_id, job_id=job_id,
                      action=action, weight=ACTION_WEIGHT[action])
    db.session.add(fb)
    db.session.commit()
    return fb