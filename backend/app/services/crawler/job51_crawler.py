"""前程无忧(51job)页面解析与数据入库（含去重与增量更新）"""
import json
import re

from app.extensions import db
from app.models.job import Company, Job
from app.models.interaction import CrawlLog
from app.services.crawler.captcha_handler import detect_captcha
from app.utils.logger import get_logger

logger = get_logger()


def _parse_sensorsdata(card):
    """从卡片 sensorsdata 属性解析字段（PC 版含完整职位信息，结构稳定）"""
    data = {}
    try:
        sensor = card.get_attribute("sensorsdata") or ""
        if not sensor:
            # sensorsdata 属性位于卡片内层 .joblist-item-job 元素上，需向下查找
            els = card.find_elements("css selector", "[sensorsdata]")
            sensor = els[0].get_attribute("sensorsdata") if els else ""
        sensor = sensor.replace("&quot;", '"').replace("&amp;", "&")
        m = re.search(r'\{.*\}', sensor)
        if m:
            obj = json.loads(m.group(0))
            for k in ("jobId", "jobTitle", "jobSalary", "jobArea", "jobYear",
                      "jobDegree", "companyId"):
                if obj.get(k):
                    data[k] = str(obj[k]).strip()
    except Exception:
        pass
    return data


def extract_job_card(card, selectors) -> dict:
    """从单个职位卡片中提取字段。

    PC 版卡片结构（.joblist-item）：
      <div class="joblist-item">
        <div class="joblist-item-job" sensorsdata='{"jobId":"173487969","jobTitle":"...",
             "jobSalary":"5-8千","jobArea":"柳州·城中区","jobYear":"1年及以上",
             "jobDegree":"本科","companyId":"10464649"}' ...>
          <div class="joblist-item-jobname"><span class="jname">职位名</span></div>
          <div class="joblist-item-jobinfo"><span class="sal">薪资</span></div>
          <div class="joblist-item-tags"><span class="tag">经验</span><span class="tag">学历</span></div>
          <div class="joblist-item-left">... <div class="area">城市·区</div></div>
          <div class="joblist-item-right"><span class="cname">公司名</span> ...</div>
        </div>
      </div>

    字段优先取自 sensorsdata 属性（结构稳定），CSS 选择器兜底。
    """
    item = {"title": "", "salary_text": "", "city": "", "district": "",
            "experience_required": "", "education_required": "",
            "job_tags": [], "company_name": "", "company_tags": [], "link": ""}

    def _text(css, default=""):
        try:
            els = card.find_elements("css selector", css)
            return els[0].text.strip() if els else default
        except Exception:
            return default

    def _texts(css):
        try:
            return [e.text.strip() for e in card.find_elements("css selector", css) if e.text.strip()]
        except Exception:
            return []

    sensor = _parse_sensorsdata(card)
    item["title"] = sensor.get("jobTitle") or _text(selectors["job_title"])
    item["salary_text"] = sensor.get("jobSalary") or _text(selectors["salary"])
    # 地点：前程无忧格式 "柳州·城中区" / "上海-浦东新区"
    area = sensor.get("jobArea") or _text(selectors["job_area"])
    if area:
        parts = re.split(r"[·\-|]", area)
        item["city"] = parts[0].strip() if parts else area
        item["district"] = parts[1].strip() if len(parts) > 1 else ""
    item["experience_required"] = sensor.get("jobYear") or ""
    item["education_required"] = sensor.get("jobDegree") or ""
    # 标签（福利/技能）与公司标签
    tags = _texts(selectors["job_tags"])
    if tags:
        item["job_tags"] = tags
    item["company_name"] = _text(selectors["company"])
    item["company_tags"] = _texts(selectors["company_tags"])

    # 职位ID与详情链接：优先 sensorsdata 的 jobId；详情用 msearch 服务端渲染页（免验证码）
    job_id = sensor.get("jobId")
    if job_id:
        item["source_job_id"] = job_id
        item["link"] = f"https://msearch.51job.com/jobs/all/{job_id}.html"
    return item


def extract_job_id(link: str) -> str:
    """从链接中提取站点职位ID用于去重（如 msearch.51job.com/jobs/xian-xxxq/173605258.html）"""
    m = re.search(r"/([\w\-]+)\.html", link or "")
    return m.group(1) if m else None


def parse_salary(text: str) -> tuple:
    """解析薪资文本为 (min_k, max_k)，单位统一为 K/月。
    支持：20-30K、1.2-2.3万/月、4-8千/月、15K以上、面议
    """
    text = (text or "").replace("·", " ").strip()
    if not text:
        return None, None
    # 区间格式：数字 - 数字 [万|千]
    m = re.search(r"([\d.]+)\s*[-~]\s*([\d.]+)\s*(万|千)?", text)
    if m:
        lo, hi, unit = float(m.group(1)), float(m.group(2)), m.group(3) or ""
        if unit == "万":       # 1.2-2.3万/月 → 12-23K
            lo, hi = lo * 10, hi * 10
        elif unit == "千":     # 4-8千/月 → 4-8K
            pass
        return int(lo), int(hi)
    nums = re.findall(r"\d+\.?\d*", text)
    if len(nums) >= 2:
        return int(float(nums[0])), int(float(nums[1]))
    if len(nums) == 1:
        n = int(float(nums[0]))
        return n, n
    return None, None


def fetch_job_detail(driver, link: str, detail_selectors, timeout=12):
    """进入职位详情页提取职位描述、任职要求与福利（尽力而为）"""
    try:
        driver.set_page_load_timeout(timeout)
        driver.get(link)
        import time as _t
        _t.sleep(2)
        desc = ""
        for css in detail_selectors.get("job_desc", "").split(","):
            css = css.strip()
            if not css:
                continue
            try:
                els = driver.find_elements("css selector", css)
                if els:
                    desc = "\n".join(e.text.strip() for e in els if e.text.strip())
                    if desc:
                        break
            except Exception:
                continue
        return desc[:10000]
    except Exception as e:
        logger.warning("详情页获取失败 %s: %s", link, e)
        return ""


def save_jobs(app, items, source="crawler") -> int:
    """批量入库：按 source_job_id 去重；已存在则增量更新"""
    saved = 0
    with app.app_context():
        for it in items:
            source_id = it.get("source_job_id") or extract_job_id(it.get("link", ""))
            if not source_id:
                source_id = f"{it.get('title')}-{it.get('company_name')}-{it.get('salary_text')}-{it.get('link','')}"
            salary_min, salary_max = parse_salary(it.get("salary_text"))

            job = Job.query.filter_by(source_job_id=source_id).first() if source_id else None
            company = None
            if it.get("company_name"):
                company = Company.query.filter_by(name=it["company_name"]).first()
                if not company:
                    company = Company(name=it["company_name"])
                    db.session.add(company)
                    db.session.flush()
                it["company_id"] = company.id

            tags = it.get("job_tags") or []
            company_tags = it.get("company_tags") or []
            # 从公司标签中识别行业/规模/融资
            industry = _pick_industry(company_tags)
            scale = _pick_scale(company_tags)

            if job:
                # 增量更新
                if it.get("salary_text"):
                    job.salary_text = it["salary_text"]
                    job.salary_min, job.salary_max = salary_min, salary_max
                if it.get("title"):
                    job.title = it["title"]
                if it.get("job_tags"):
                    job.job_tags = json.dumps(tags, ensure_ascii=False)
                if it.get("experience_required"):
                    job.experience_required = it["experience_required"]
                if it.get("education_required"):
                    job.education_required = it["education_required"]
                if it.get("description") and not job.description:
                    job.description = it["description"]
                if company and not job.company_id:
                    job.company_id = company.id
                job.is_active = True
            else:
                job = Job(
                    source_job_id=source_id,
                    title=it.get("title") or "未知职位",
                    salary_text=it.get("salary_text"),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=it.get("city"),
                    district=it.get("district"),
                    experience_required=it.get("experience_required"),
                    education_required=it.get("education_required"),
                    job_tags=json.dumps(tags, ensure_ascii=False) if tags else None,
                    company_name=it.get("company_name"),
                    company_id=it.get("company_id"),
                    link=it.get("link"),
                    description=it.get("description"),
                    source=source,
                )
                db.session.add(job)
            saved += 1
        db.session.commit()
    return saved


def _pick_industry(tags):
    industries = ["互联网", "电子商务", "金融", "教育", "医疗", "游戏", "人工智能", "大数据", "外包服务", "汽车"]
    return next((t for t in tags if any(k in t for k in industries)), None)


def _pick_scale(tags):
    scales = ["100-499人", "500-999人", "1000-9999人", "10000人以上", "20-99人", "0-20人"]
    return next((t for t in tags if t in scales), None)


def record_log(app, task_id, level, message, keyword=None, page=None):
    with app.app_context():
        db.session.add(CrawlLog(task_id=task_id, level=level, keyword=keyword,
                                page=page, message=message[:2000]))
        db.session.commit()
