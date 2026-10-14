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
    DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
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
    # 浏览器引擎：edge / chrome（默认 Edge，与本地浏览器一致）
    CRAWL_BROWSER = os.environ.get("CRAWL_BROWSER", "edge").lower()
    # 浏览器可执行文件路径（留空时自动探测常见安装位置）
    CRAWL_BROWSER_PATH = os.environ.get("CRAWL_BROWSER_PATH", "")
    # WebDriver 路径（留空时由 Selenium Manager 自动管理；优先使用项目内置驱动）
    _DRIVERS_DIR = os.path.join(BASE_DIR, "drivers")
    CRAWL_DRIVER_PATH = os.environ.get("CRAWL_DRIVER_PATH", "") or os.path.join(_DRIVERS_DIR, "msedgedriver.exe")
    # CDP 附加模式：>0 时优先附加到已运行的 Edge/Chrome（复用登录态，在原有浏览器中新开标签页，
    # 不再新开一个浏览器进程）。需要先用 backend/start_edge_debug.py 以 --remote-debugging-port 启动浏览器；
    # 端口无调试实例时自动回退为独立启动。0 表示禁用。
    try:
        CRAWL_ATTACH_PORT = int(os.environ.get("CRAWL_ATTACH_PORT", "9222"))
    except (TypeError, ValueError):
        CRAWL_ATTACH_PORT = 0
    # 验证码人工处理等待时间（秒）
    CRAWL_CAPTCHA_WAIT = int(os.environ.get("CRAWL_CAPTCHA_WAIT", 180))
    CRAWL_PROXY_LIST = os.environ.get("CRAWL_PROXY_LIST", "").split(",") if os.environ.get("CRAWL_PROXY_LIST") else []

    # 前程无忧 URL 模板与页面结构选择器基线（用于结构变更监测）
    # 说明：使用桌面版 SPA（we.51job.com/pc/search）作为真实爬取源——
    #   1) jobArea 参数真实生效（020000=上海、140400=柳州等），可精确按城市爬取；
    #   2) 未带 jobArea 时页面按账号/IP 地区锁定城市（如账号填柳州则只出柳州职位），
    #      因此「全国」需用 jobarea=000000 的手机版源（we.51job.com/m/search，默认全国）。
    # 城市代码（PC 版 jobArea 参数）：000000全国 010000北京 020000上海 030200广州
    #          040000深圳 030800东莞 060000重庆 070200南京 070300苏州 080200杭州
    #          090200成都 110200福州 120200济南 120300青岛 140200南宁 140400柳州
    #          150200合肥 160200石家庄 170200郑州 180200武汉 190200长沙 200200西安
    #          220200哈尔滨 230200沈阳 240200长春 250200昆明 260200贵阳 280100呼和浩特
    CRAWL_URL_TEMPLATE = ("https://we.51job.com/pc/search?jobArea={jobarea}"
                          "&keyword={query}&searchType=2&pageNum={page}")
    # 全国兜底使用手机版搜索（jobarea 参数不生效但默认即全国，不受账号/IP 地区影响）
    CRAWL_URL_NATIONWIDE = ("https://we.51job.com/m/search?keyword={query}"
                            "&jobarea=000000,000000&pageNum={page}")
    # 城市名称 -> 城市代码（前端传名称时自动换算；直接传 6 位代码则原样使用）
    CRAWL_CITY_CODES = {
        "全国": "000000", "北京": "010000", "上海": "020000", "广州": "030200",
        "深圳": "040000", "东莞": "030800", "重庆": "060000", "南京": "070200",
        "苏州": "070300", "杭州": "080200", "成都": "090200", "福州": "110200",
        "济南": "120200", "青岛": "120300", "南宁": "140200", "柳州": "140400",
        "合肥": "150200", "石家庄": "160200", "郑州": "170200", "武汉": "180200",
        "长沙": "190200", "西安": "200200", "哈尔滨": "220200", "沈阳": "230200",
        "长春": "240200", "昆明": "250200", "贵阳": "260200", "呼和浩特": "280100",
    }
    # PC 版列表卡片结构（.joblist-item 为卡片容器；字段优先取自卡片 sensorsdata 属性，
    # 该属性含 jobId/jobTitle/jobSalary/jobArea/jobYear/jobDegree/companyId 等完整字段）
    CRAWL_SELECTORS = {
        "job_list": ".joblist-item",
        "job_title": ".jname",
        "job_area": ".area, [class*=area]",
        "salary": ".sal",
        "job_limits": ".joblist-item-tags .tag, .tags .tag",
        "job_tags": ".joblist-item-tags .tag, .tags .tag",
        "company": ".cname",
        "company_tags": ".comp .tag, .tags span",
        "job_link": ".joblist-item-job",
    }
    # 详情页选择器：优先 msearch 手机详情（服务端渲染，可免验证码读取）
    # jobinfoDesModule 为 msearch 详情页职位描述容器（已验证有效）
    CRAWL_DETAIL_SELECTORS = {
        "job_desc": ".jobinfoDesModule, .job_msg, .bmsg, .jd-content, "
                    "[class*=job-detail], .job_detail, [class*=jobmsg], "
                    ".tCompany_main .msg",
        "job_bonus": ".job_msg .t1, .bmsg .t1, .welfare",
        "company_name": ".cname, .tCompany_main h1, .c_info .cname",
    }
    CRAWL_STRUCTURE_CHECK_URL = "https://we.51job.com/pc/search?jobArea=000000&keyword=Python&searchType=2&pageNum=1"

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
