"""Boss直聘页面解析与数据入库（含去重与增量更新）"""
import json
import re

from app.extensions import db
from app.models.job import Company, Job
from app.models.interaction import CrawlLog
from app.services.crawler.captcha_handler import detect_captcha
from app.utils.logger import get_logger

logger = get_logger()

SALARY_PATTERN = re.compile(r"(\d+)\s*[-~]\s*(\d+)K")


def extract_job_card(card, selectors) -> dict:
    """从单个职位卡片 li 中提取字段（容错：单个字段失败不影响整体）"""
    item = {"title": "", "salary_text": "", "city": "", "district": "",
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

    item["title"] = _text(selectors["job_title"])
    item["salary_text"] = _text(selectors["salary"])
    # 地点：“北京朝阳区”
    area = _text(selectors["job_area"])
    if area:
        item["city"] = area[:2] if len(area) >= 2 else area
        item["district"] = area[2:] if len(area) > 2 else ""
    item["job_tags"] = _texts(selectors["job_tags"])
    item["company_name"] = _text(selectors["company"])
    item["company_tags"] = _texts(selectors["company_tags"])
    try:
        link_el = card.find_element("css selector", selectors["job_link"])
        href = link_el.get_attribute("href") or ""
        if href and "/job_detail/" in href:
            item["link"] = href if href.startswith("http") else "https://www.zhipin.com" + href
    except Exception:
        pass
    return item


def extract_job_id(link: str) -> str:
    """从链接中提取 boss_job_id 用于去重"""
    m = re.search(r"/job_detail/([\w\-]+)\.html", link or "")
    return m.group(1) if m else None


def parse_salary(text: str) -> tuple:
    """解析薪资文本为 (min_k, max_k)"""
    m = SALARY_PATTERN.search(text or "")
    if m:
        return int(m.group(1)), int(m.group(2))
    nums = re.findall(r"\d+", text or "")
    if len(nums) >= 2:
        return int(nums[0]), int(nums[1])
    if len(nums) == 1:
        return int(nums[0]), int(nums[0])
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
    """批量入库：按 boss_job_id 去重；已存在则增量更新"""
    saved = 0
    with app.app_context():
        for it in items:
            boss_id = it.get("boss_job_id") or extract_job_id(it.get("link", ""))
            if not boss_id:
                boss_id = f"{it.get('title')}-{it.get('company_name')}-{it.get('salary_text')}-{it.get('link','')}"
            salary_min, salary_max = parse_salary(it.get("salary_text"))

            job = Job.query.filter_by(boss_job_id=boss_id).first() if boss_id else None
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
                if it.get("description") and not job.description:
                    job.description = it["description"]
                job.is_active = True
            else:
                job = Job(
                    boss_job_id=boss_id,
                    title=it.get("title") or "未知职位",
                    salary_text=it.get("salary_text"),
                    salary_min=salary_min,
                    salary_max=salary_max,
                    city=it.get("city"),
                    district=it.get("district"),
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
