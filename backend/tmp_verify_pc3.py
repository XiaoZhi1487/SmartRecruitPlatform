"""临时验证：PC 版 全国 vs 城市 结果对比 v2（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from selenium.webdriver.common.by import By
from app.services.crawler.anti_detect import create_driver, close_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)


def areas_of(cards):
    out = []
    for c in cards[:8]:
        a = ""
        for sel in ["[class*=area]", "[class*=location]", ".address", ".s"]:
            try:
                els = c.find_elements(By.CSS_SELECTOR, sel)
                if els and els[0].text.strip():
                    a = els[0].text.strip()
                    break
            except Exception:
                pass
        if a:
            out.append(a)
    return out


try:
    for name, code in [("全国000000", "000000"), ("上海020000", "020000"),
                       ("柳州140400", "140400"), ("无参数", None)]:
        u = (f"https://we.51job.com/pc/search?jobArea={code}&keyword=Python&searchType=2&pageNum=1"
             if code else "https://we.51job.com/pc/search?keyword=Python&searchType=2&pageNum=1")
        driver.get(u)
        time.sleep(8)
        cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
        print(f"{name}: cards={len(cards)} areas={areas_of(cards)[:6]}")
finally:
    close_driver(driver)
