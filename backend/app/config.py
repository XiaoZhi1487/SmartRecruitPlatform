"""全局配置模块"""
import os
from datetime import timedelta

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))


class Config:
    """应用基础配置"""
    # ---------- 安全 ----------
    SECRET_KEY = os.environ.get("SECRET_KEY", "job-ai-platform-dev-secret-key-2026")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", SECRET_KEY)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"

    # 登录失败锁定策略
    LOGIN_MAX_ATTEMPTS = 5
    LOGIN_LOCK_MINUTES = 15

    # 敏感字段加密密钥（为空时自动生成并持久化到 instance 目录）
    DATA_ENCRYPTION_KEY = os.environ.get("DATA_ENCRYPTION_KEY", "")

    # ---------- 数据库 ----------
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "job_ai.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------- 文件上传 ----------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_RESUME_EXT = {".pdf", ".doc", ".docx", ".txt"}

    # ---------- DeepSeek AI ----------
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "***REDACTED***")
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    AI_TIMEOUT = 60
    AI_MAX_RETRIES = 3

    # ---------- 爬虫配置 ----------
    # real: 真实爬取；mock: 仅模拟数据；auto: 真实失败后自动降级为模拟数据
    CRAWL_MODE = os.environ.get("CRAWL_MODE", "auto")
    CRAWL_THREADS = int(os.environ.get("CRAWL_THREADS", 3))
    CRAWL_DELAY_MIN = float(os.environ.get("CRAWL_DELAY_MIN", 6))
    CRAWL_DELAY_MAX = float(os.environ.get("CRAWL_DELAY_MAX", 10))
    CRAWL_HEADLESS = os.environ.get("CRAWL_HEADLESS", "1") == "1"
    CRAWL_CAPTCHA_WAIT = int(os.environ.get("CRAWL_CAPTCHA_WAIT", 60))
    CRAWL_PROXY_LIST = os.environ.get("CRAWL_PROXY_LIST", "").split(",") if os.environ.get("CRAWL_PROXY_LIST") else []

    # Boss直聘 URL 模板与页面结构选择器基线（用于结构变更监测）
    CRAWL_URL_TEMPLATE = "https://www.zhipin.com/web/geek/job?query={query}&city={city}&page={page}"
    CRAWL_SELECTORS = {
        "job_list": ".job-list-box > li",
        "job_title": ".job-name",
        "job_area": ".job-area",
        "salary": ".salary",
        "job_tags": ".tag-list li",
        "company": ".company-info .company-name a",
        "company_tags": ".company-tag-list li",
        "job_link": "a[href*='/job_detail/']",
    }
    CRAWL_DETAIL_SELECTORS = {
        "job_desc": ".job-sec-text, [class*='job-detail'] p, .job-detail-section",
        "job_bonus": ".job-banner .labels li, .job-banner .tag-list li",
        "company_name": ".name, .company-name",
    }
    CRAWL_STRUCTURE_CHECK_URL = "https://www.zhipin.com/web/geek/job?query=Python&city=101010100&page=1"
    # 定时爬取关键字（每小时任务）
    CRAWL_SCHEDULE_KEYWORDS = ["Python", "Java", "前端", "数据分析"]
    CRAWL_SCHEDULE_CITY = "101010100"  # 北京
    CRAWL_SCHEDULE_PAGES = 3

    # ---------- 分页 ----------
    DEFAULT_PAGE_SIZE = 10
    MAX_PAGE_SIZE = 50

    # ---------- 邮件(SMTP)配置，未配置时验证邮件输出到控制台 ----------
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 465))
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "")
