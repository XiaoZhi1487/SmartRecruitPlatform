"""招聘市场数据分析服务：基于职位库做就业趋势洞察。

对外提供 build_analysis(jobs) 聚合返回：
  - 岗位需求排行（按岗位类别计数）
  - 薪资趋势（按经验档位折算的月度平均薪资，月/年/天统一折算为 K/月）
  - 学历分布、经验要求分布
  - 基于统计结果的 AI 分析结论
"""
import re

# ---------------- 薪资统一折算为 K/月 ----------------
# 币值单位：万(×10)、千/K(×1)；周期折算：月(×1)、年(÷12)、天(×22，按每月22个工作日)
_PERIOD_FACTOR = {"月": 1.0, "年": 1.0 / 12, "天": 22.0}
_CURRENCY_UNIT = {"万": 10, "千": 1, "k": 1, "K": 1, "w": 10, "W": 10}


def _detect_period(text):
    if "年" in text or "年薪" in text:
        return "年"
    if "天" in text or "日" in text:
        return "天"
    return "月"


def _currency_to_k(num, unit, period):
    """数值 × 币值单位 → 千；无明确单位时：天按 元/天（÷1000），其余视为 千。"""
    num = float(num)
    if unit in _CURRENCY_UNIT:
        return num * _CURRENCY_UNIT[unit]
    if period == "天":
        return num / 1000          # 元/天 换算为 千/天
    if period == "年":
        return num / 1000          # 元/年 换算为 千/年
    return num


def normalize_salary_to_k_month(text):
    """将薪资文本统一折算为 (min_k_month, max_k_month)，返回保留1位小数。"""
    if not text:
        return None, None
    t = str(text).replace("·", " ").strip()
    period = _detect_period(t)
    # 移除周期标识词，避免干扰后续数值提取
    t = re.sub(r"年薪|月薪|/月|/年|/天|/日|\b年\b|\b天\b|\b日\b", " ", t)
    factor = _PERIOD_FACTOR[period]

    def _round_pair(lo, hi):
        if lo is None:
            return None, None
        return round(lo * factor, 1), round(hi * factor, 1)

    # 区间：如 "1.2-2.3万/月"、"30-50万/年"、"300-500元/天"
    m = re.search(r"([\d.]+)\s*(万|千|k|K|w|W)?\s*[-~到至]\s*([\d.]+)\s*(万|千|k|K|w|W)?", t)
    if m:
        u1, u2 = m.group(2) or "", m.group(4) or m.group(2) or ""
        lo = _currency_to_k(m.group(1), u1 or u2, period)
        hi = _currency_to_k(m.group(3), u2 or u1, period)
        return _round_pair(lo, hi)
    # 单值带币值单位：如 "1.2万以上"、"8K以上"
    m2 = re.search(r"([\d.]+)\s*(万|千|k|K|w|W)", t)
    if m2:
        n = _currency_to_k(m2.group(1), m2.group(2), period)
        return _round_pair(n, n)
    # 裸数值："8000-12000"、"15K" 之类兜底
    nums = re.findall(r"\d+\.?\d*", t)
    if len(nums) >= 2:
        lo = _currency_to_k(nums[0], "", period)
        hi = _currency_to_k(nums[1], "", period)
        return _round_pair(lo, hi)
    if len(nums) == 1:
        n = _currency_to_k(nums[0], "", period)
        return _round_pair(n, n)
    return None, None


# ---------------- 岗位分类 ----------------
_CATEGORY_RULES = [
    ("数据分析", ["数据分析", "数据挖掘", "bi", "数分", "商业分析", "数据开发"]),
    ("人工智能", ["人工智能", "ai", "算法", "机器学习", "深度学习", "nlp", "大模型", "cv", "图像识别"]),
    ("前端", ["前端", "vue", "react", "web", "h5", "javascript", "ui设计", "视觉设计"]),
    ("Java", ["java", "spring"]),
    ("Python", ["python", "django", "flask", "爬虫"]),
    ("后端", ["后端", "服务端", "go", "golang", "c++", "php", "网关", "中间件", "嵌入式"]),
    ("运维", ["运维", "devops", "cicd", "sre", "dba"]),
    ("测试", ["测试", "qa", "测开"]),
    ("销售", ["销售", "大客户", "客户经理", "业务员", "推广"]),
    ("运营", ["运营", "新媒体"]),
    ("产品", ["产品", "项目经理", "架构"]),
    ("市场", ["市场", "品牌", "营销", "策划"]),
    ("客服", ["客服", "售后", "热线"]),
    ("行政人力", ["行政", "人事", "hr", "招聘", "前台", "文员"]),
    ("财务", ["财务", "会计", "出纳", "审计"]),
    ("采购物流", ["采购", "物流", "仓库", "供应链"]),
    ("教师", ["教师", "讲师", "培训", "教师招聘", "学管"]),
    ("实习生", ["实习"]),
]


def _categorize_title(title):
    tl = (title or "").lower()
    for name, kws in _CATEGORY_RULES:
        if any(k in tl for k in kws):
            return name
    return "其他"


# ---------------- 学历档位（由低到高排序） ----------------
_EDU_ORDER = ["学历不限", "高中", "中技/中专", "大专", "本科", "硕士", "博士"]

# 6 位城市代码 -> 城市名（与 config.CRAWL_CITY_CODES 保持一致，用于矫正历史落库的代码值）
try:
    from app.config import Config as _Config
    _CODE_TO_CITY = {v: k for k, v in _Config.CRAWL_CITY_CODES.items()}
except Exception:  # pragma: no cover
    _CODE_TO_CITY = {}


def _norm_city(value):
    city = (value or "").strip() or "未知地区"
    if city.isdigit() and len(city) == 6:
        return _CODE_TO_CITY.get(city, city)
    return city


# ---------------- 聚合分析 ----------------
def build_analysis(jobs):
    demand = {}                     # 岗位类别 -> 数量
    education = {}                  # 学历 -> 数量
    salary_by_cat = {}              # 岗位类别 -> {sum, count}
    salary_by_edu = {}              # 学历 -> {sum, count}
    salary_by_city = {}             # 地区 -> {sum, count}

    for j in jobs:
        title = j.get("title") or ""
        cat = _categorize_title(title)
        demand[cat] = demand.get(cat, 0) + 1

        edu = (j.get("education_required") or "学历不限").strip() or "学历不限"
        education[edu] = education.get(edu, 0) + 1

        # 薪资折算为月度 K/月（由 salary_text 折算，缺失时回退到已存结果）
        smin, smax = normalize_salary_to_k_month(j.get("salary_text"))
        if smin is None and j.get("salary_min") is not None:
            smin, smax = j["salary_min"], j["salary_max"] or j["salary_min"]
        if smin is not None and smax is not None and smin <= smax:
            mid_k = (smin + smax) / 2
            c = salary_by_cat.setdefault(cat, {"sum": 0.0, "count": 0})
            c["sum"] += mid_k
            c["count"] += 1
            e = salary_by_edu.setdefault(edu, {"sum": 0.0, "count": 0})
            e["sum"] += mid_k
            e["count"] += 1
            city = _norm_city(j.get("city"))
            r = salary_by_city.setdefault(city, {"sum": 0.0, "count": 0})
            r["sum"] += mid_k
            r["count"] += 1

    # 岗位需求排行（按数量降序）
    demand_rank = sorted(demand.items(), key=lambda x: -x[1])

    # 岗位平均薪资：按类别平均月薪降序 Top5
    cat_salary = [{"category": k, "avg": round(v["sum"] / v["count"], 1)}
                  for k, v in salary_by_cat.items() if v["count"] >= 1]
    cat_salary.sort(key=lambda x: -x["avg"])
    cat_salary = cat_salary[:5]

    # 学历对薪资的影响：按学历档位由低到高
    edu_salary = [{"education": k, "avg": round(v["sum"] / v["count"], 1)}
                  for k, v in salary_by_edu.items() if v["count"] >= 1]
    edu_rank = {x["education"] for x in edu_salary}
    edu_salary = [{"education": k, "avg": dict((x["education"], x["avg"]) for x in edu_salary)[k]}
                  for k in _EDU_ORDER if k in edu_rank]

    # 地区平均薪资排行：按平均月薪降序 Top8
    city_salary = [{"city": k, "avg": round(v["sum"] / v["count"], 1)}
                   for k, v in salary_by_city.items() if v["count"] >= 1]
    city_salary.sort(key=lambda x: -x["avg"])
    city_salary = city_salary[:8]

    education_dist = sorted(education.items(), key=lambda x: -x[1])

    return {
        "demand_rank": [{"category": k, "count": v} for k, v in demand_rank],
        "category_salary": cat_salary,
        "education_salary": edu_salary,
        "city_salary": city_salary,
        "education_dist": [{"name": k, "value": v} for k, v in education_dist],
        "conclusions": _build_conclusions(cat_salary, edu_salary, city_salary,
                                          education_dist),
    }


def _build_conclusions(category_salary, edu_salary, city_salary, education_dist):
    lines = []
    if category_salary:
        top = category_salary[0]
        lines.append(f"平均月薪最高的岗位方向为「{top['category']}」（约{top['avg']}K），技术研发类岗位薪酬更具竞争力。")
    paid_edu = [e for e in edu_salary if e["avg"] > 0]
    if len(paid_edu) >= 2:
        if paid_edu[-1]["avg"] > paid_edu[0]["avg"]:
            lines.append("薪资随学历提升总体上升，本科及以上学历的薪酬优势明显。")
        else:
            lines.append("当前数据下学历与薪资并非严格正相关，实操能力与实际经验同样重要。")
    if city_salary:
        top_city = city_salary[0]
        lines.append(f"平均月薪最高的地区为「{top_city['city']}」（约{top_city['avg']}K），可结合生活成本综合选择就业城市。")
    if education_dist:
        lines.append(f"在招岗位学历要求以「{education_dist[0][0]}」为主，各类学历人才均有就业机会。")
    if not lines:
        lines.append("当前职位数据有限，建议先通过爬虫控制台采集更多岗位后再分析。")
    return lines