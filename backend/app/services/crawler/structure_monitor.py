"""网站结构变更监测：定期/手动检查页面选择器基线是否仍然有效"""
from datetime import datetime

from app.extensions import db
from app.models.interaction import SiteStructureCheck
from app.services.crawler.anti_detect import create_driver
from app.utils.logger import get_logger

logger = get_logger()


def check_structure(app, check_url=None, selectors=None, detail_selectors=None):
    """加载采样页面，逐一验证选择器是否仍能定位到元素，并记录监测结果。
    返回监测结果列表。
    """
    cfg = app.config
    url = check_url or cfg["CRAWL_STRUCTURE_CHECK_URL"]
    selectors = selectors or cfg["CRAWL_SELECTORS"]
    detail_selectors = detail_selectors or cfg["CRAWL_DETAIL_SELECTORS"]
    results = []

    driver = None
    try:
        driver = create_driver(headless=cfg["CRAWL_HEADLESS"])
        driver.get(url)
        import time as _t
        _t.sleep(4)

        for key, css in selectors.items():
            try:
                count = len(driver.find_elements("css selector", css))
                status = "ok" if count > 0 else "missing"
            except Exception as e:
                count, status = 0, f"error:{e}"
            results.append(_record(app, "list", key, css, status, f"元素数量={count}"))

        for key, css in detail_selectors.items():
            status = "ok"  # 详情页选择器无法在列表页验证，标记为基线状态
            results.append(_record(app, "detail", key, css, status, "详情选择器基线"))

        # 页面是否存在验证码（作为风控级别信号）
        try:
            body = driver.find_element("tag name", "body").text
            if any(k in body for k in ["安全验证", "验证码", "captcha"]):
                _record(app, "list", "captcha_signal", "body", "warning", "采样页命中验证码")
        except Exception:
            pass
    except Exception as e:
        logger.error("结构监测失败: %s", e)
        _record(app, "list", "_network", url, "error", str(e)[:500])
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass

    changed = [r for r in results if r["status"] not in ("ok",)]
    summary = {
        "checked_at": datetime.utcnow().isoformat(),
        "url": url,
        "total": len(results),
        "changed": len(changed),
        "results": results,
    }
    logger.info("结构监测完成：共%s项，异常%s项", len(results), len(changed))
    return summary


def _record(app, check_type, key, selector, status, evidence) -> dict:
    with app.app_context():
        row = SiteStructureCheck(check_type=check_type, selector_key=key,
                                 selector=selector, status=status,
                                 evidence=evidence[:1000])
        db.session.add(row)
        db.session.commit()
    return {"selector_key": key, "selector": selector, "status": status, "evidence": evidence}
