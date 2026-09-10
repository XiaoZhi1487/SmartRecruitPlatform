"""反爬绕过策略：Selenium 驱动工厂（CDP 反检测、随机 UA、随机操作）"""
import random
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from app.services.crawler.user_agents import get_random_ua
from app.utils.logger import get_logger

logger = get_logger()

# 通过 CDP 注入的反检测脚本
_ANTI_DETECT_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || {runtime: {}};
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
"""


def create_driver(ua=None, proxy=None, headless=True, wait_timeout=15):
    """创建带反检测配置的 Chrome 驱动"""
    ua = ua or get_random_ua()
    options = Options()
    options.add_argument(f"user-agent={ua}")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--lang=zh-CN")
    options.add_argument("--window-size=1920,1080")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if headless:
        options.add_argument("--headless=new")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        # 兼容旧版 Chrome headless 参数
        logger.warning("Chrome headless=new 启动失败(%s)，回退为 headless", e)
        options.add_argument("--headless")
        driver = webdriver.Chrome(options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                           {"source": _ANTI_DETECT_JS})
    driver.implicitly_wait(wait_timeout)
    return driver


def humanize(driver, delay_min=0.3, delay_max=1.0):
    """模拟人类行为：随机滚动 + 随机停顿"""
    try:
        scrolls = random.randint(1, 3)
        for _ in range(scrolls):
            driver.execute_script(
                f"window.scrollBy(0, {random.randint(200, 600)});")
            time.sleep(random.uniform(0.2, 0.6))
        # 随机轻微鼠标移动
        try:
            ActionChains(driver).move_by_offset(
                random.randint(-20, 20), random.randint(-20, 20)).perform()
        except Exception:
            pass
    except Exception:
        pass
    time.sleep(random.uniform(delay_min, delay_max))


def random_delay(config):
    """按配置返回随机延迟"""
    return random.uniform(config["CRAWL_DELAY_MIN"], config["CRAWL_DELAY_MAX"])
