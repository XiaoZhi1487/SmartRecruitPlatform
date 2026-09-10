"""验证码检测与处理策略
1. 检测页面是否出现验证码/安全验证
2. 轮换代理、清空 Cookie、等待人工/打码平台处理
"""
import time

from app.utils.logger import get_logger

logger = get_logger()

CAPTCHA_KEYWORDS = ["安全验证", "验证码", "滑动验证", "captcha", "geetest", "人机验证"]
CAPTCHA_URL_MARKERS = ["verify", "captcha", "geetest", "security"]


def detect_captcha(driver) -> bool:
    """检测当前页面是否命中验证码"""
    try:
        url = (driver.current_url or "").lower()
        if any(m in url for m in CAPTCHA_URL_MARKERS):
            return True
        body = driver.find_element("tag name", "body").text[:2000] if _body_exists(driver) else ""
        return any(k in body for k in CAPTCHA_KEYWORDS)
    except Exception:
        return False


def _body_exists(driver) -> bool:
    try:
        driver.find_element("tag name", "body")
        return True
    except Exception:
        return False


def handle_captcha(driver, wait_seconds, proxy_pool, callback=None):
    """处理验证码。
    返回 True 表示已解除；False 表示持续被拦截。
    策略：等待人工处理 → 轮换代理 → 清空 Cookie 重载
    """
    logger.warning("检测到验证码，进入处理流程（最多等待 %s 秒）", wait_seconds)
    if callback:
        callback("captcha")

    waited = 0
    step = 5
    while waited < wait_seconds:
        time.sleep(step)
        waited += step
        if not detect_captcha(driver):
            logger.info("验证码已解除（等待 %s 秒后）", waited)
            return True
        # 每 20 秒尝试一次代理轮换
        if waited % 20 == 0 and proxy_pool and not proxy_pool.is_empty():
            proxy = proxy_pool.get()
            try:
                driver.quit()
            except Exception:
                pass
            logger.info("轮换代理 %s 以绕过验证码", proxy)
            return "rotate"
    return False
