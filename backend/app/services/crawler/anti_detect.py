"""反爬绕过策略：Selenium 驱动工厂（Edge/Chrome 双引擎、CDP 反检测、随机 UA、随机操作）"""
import os
import random
import socket
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from app.services.crawler.user_agents import get_random_ua
from app.utils.logger import get_logger

logger = get_logger()

# 通过 CDP 注入的反检测脚本（Edge/Chrome 均为 Chromium 内核，脚本通用）
_ANTI_DETECT_JS = """
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
window.chrome = window.chrome || {runtime: {}};
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en']});
Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
Object.defineProperty(navigator, 'hardwareConcurrency', {get: () => 8});
"""

# 两种引擎通用的启动参数
_COMMON_ARGS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-gpu",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--lang=zh-CN",
    "--window-size=1920,1080",
]

# 常见浏览器安装路径（按顺序探测）
_EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
]
_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def _find_browser(engine):
    """按引擎探测浏览器可执行文件路径，未找到返回 None"""
    candidates = _EDGE_PATHS if engine != "chrome" else _CHROME_PATHS
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def _build_options(engine, ua, proxy, headless, browser_path=None):
    """按引擎构建 Options，返回 (options, service_cls, driver_cls)"""
    if engine == "chrome":
        options = ChromeOptions()
        service_cls = ChromeService
        driver_cls = webdriver.Chrome
    else:  # 默认 Edge
        options = EdgeOptions()
        service_cls = EdgeService
        driver_cls = webdriver.Edge

    options.add_argument(f"user-agent={ua}")
    for arg in _COMMON_ARGS:
        options.add_argument(arg)
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # eager：DOM 解析完成即返回，避免 51job 的 WAF 挑战页长期不触发 load 事件导致 driver.get() 卡死
    options.page_load_strategy = "eager"
    # 显式指定浏览器二进制，避免 Selenium Manager 探测失败
    browser_path = browser_path or _find_browser(engine)
    if browser_path and os.path.exists(browser_path):
        options.binary_location = browser_path
    if proxy:
        options.add_argument(f"--proxy-server={proxy}")
    if headless:
        options.add_argument("--headless=new")
    return options, service_cls, driver_cls


def create_driver(ua=None, proxy=None, headless=True, engine="edge",
                  browser_path=None, driver_path=None,
                  wait_timeout=15, attach_port=None):
    """创建带反检测配置的浏览器驱动（默认 Edge，可通过 engine 指定 chrome）
    browser_path: 浏览器可执行文件路径（留空自动探测）
    driver_path:  WebDriver 可执行文件路径（留空由 Selenium Manager 自动管理）
    attach_port:  CDP 附加端口。>0 且该端口存在浏览器调试实例时，直接附加到已运行的
                  浏览器（新开标签页、复用其登录态/Cookie，不新开浏览器进程）；
                  附加失败自动回退为独立启动。
    """
    if attach_port and _port_open(attach_port):
        try:
            driver = _attach_driver(engine, attach_port, driver_path, wait_timeout)
            logger.info("已附加到运行中的 %s(端口 %s)，复用其登录状态", engine, attach_port)
            return driver
        except Exception as e:
            logger.warning("CDP 附加到 %s 失败(%s)，回退为独立启动", engine, e)

    ua = ua or get_random_ua()
    options, service_cls, driver_cls = _build_options(engine, ua, proxy, headless,
                                                      browser_path)
    service = service_cls(executable_path=driver_path) if driver_path else None

    try:
        driver = driver_cls(options=options, service=service) if service else driver_cls(options=options)
    except Exception as e:
        # 兼容旧版本 headless 参数
        logger.warning("%s headless=new 启动失败(%s)，回退为 headless", engine, e)
        options.add_argument("--headless")
        driver = driver_cls(options=options) if not service else driver_cls(options=options, service=service)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument",
                           {"source": _ANTI_DETECT_JS})
    # 隐式等待设小：列表已用显式 sleep 等待渲染，避免 find_elements 长时间阻塞拖慢流程
    driver.implicitly_wait(2)
    return driver


def _port_open(port) -> bool:
    """探测本机端口是否有服务在监听（用于判断浏览器调试实例是否已启动）"""
    try:
        with socket.create_connection(("127.0.0.1", int(port)), timeout=0.5):
            return True
    except OSError:
        return False


def _attach_driver(engine, port, driver_path=None, wait_timeout=15):
    """通过 CDP(debuggerAddress) 附加到已启动的浏览器实例。
    不新开浏览器进程，而是复用其实例：新建标签页访问目标页面，可直接使用该浏览器
    已登录的账号与 Cookie。通过 driver.attach_mode=True 标记，关闭时只关标签页。
    """
    options = EdgeOptions() if engine == "edge" else ChromeOptions()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
    options.page_load_strategy = "eager"
    service = None
    if driver_path and os.path.exists(driver_path):
        service = (EdgeService(executable_path=driver_path) if engine == "edge"
                   else ChromeService(executable_path=driver_path))
    driver = (webdriver.Edge(options=options, service=service) if engine == "edge"
              else webdriver.Chrome(options=options, service=service))
    driver.attach_mode = True
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(2)
    # 立即切换到专属爬虫标签页：附加模式下驱动默认控制浏览器"当前活动标签页"，
    # 若不加处理，后续 driver.get() 会直接导航用户正在看的页面。这里新建一个
    # 专属标签页并切过去，之后所有爬取操作都只发生在该标签页（及逐页新建的标签页）上。
    try:
        driver.switch_to.new_window("tab")
        driver.crawler_handle = driver.current_window_handle
    except Exception as e:
        logger.warning("附加后新建专属标签页失败: %s", e)
        driver.crawler_handle = None
    return driver


def close_driver(driver):
    """释放驱动。附加模式下只关闭爬虫专属标签页，绝不退出用户的浏览器实例。"""
    if driver is None:
        return
    try:
        if getattr(driver, "attach_mode", False):
            try:
                crawler = getattr(driver, "crawler_handle", None)
                handles = driver.window_handles
                # 只关爬虫自己的专属标签页（逐页临时标签页由调用方负责关闭）
                if crawler and crawler in handles:
                    driver.switch_to.window(crawler)
                    driver.close()
            except Exception as e:
                logger.warning("关闭附加标签页失败: %s", e)
            return
        driver.quit()
    except Exception:
        pass


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
