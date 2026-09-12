"""临时验证：PC 版全国代码 + 卡片结构（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from selenium.webdriver.common.by import By
from app.services.crawler.anti_detect import create_driver, close_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    # 全国代码测试
    for code in ["000000", ""]:
        u = (f"https://we.51job.com/pc/search?jobArea={code}&keyword=Python&searchType=2&pageNum=1"
             if code else "https://we.51job.com/pc/search?keyword=Python&searchType=2&pageNum=1")
        driver.get(u)
        time.sleep(8)
        cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
        areas = []
        for c in cards[:8]:
            try:
                sd = c.get_attribute("sensorsdata") or ""
                import re
                m = re.search(r'"jobArea":"([^"]+)"', sd)
                if m:
                    areas.append(m.group(1))
            except Exception:
                pass
        print(f"jobArea={code or '(none)'} cards={len(cards)} areas={areas[:6]}")

    # 卡片结构详细检查
    driver.get("https://we.51job.com/pc/search?jobArea=000000&keyword=Python&searchType=2&pageNum=1")
    time.sleep(8)
    cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
    if cards:
        c = cards[0]
        html = c.get_attribute("outerHTML")
        print("CARD_LEN:", len(html))
        # 检查各选择器
        for name, sel in [("title", ".jname"), ("sal", ".sal"), ("area", "[class*=area]"),
                          ("company", ".cname"), ("info", ".info"), ("tags", "[class*=tags]"),
                          ("link", "a[href]")]:
            try:
                els = c.find_elements(By.CSS_SELECTOR, sel)
                print(f"  {name}: {len(els)}", end="")
                if els:
                    if name == "link":
                        print(f" href={els[0].get_attribute('href')[:80]}")
                    else:
                        print(f" text={els[0].text.strip()[:40]!r}")
                else:
                    print()
            except Exception as e:
                print(f"  {name}: ERR {e}")
finally:
    close_driver(driver)
