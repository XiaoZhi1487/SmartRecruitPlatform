"""临时验证：PC 版柳州城市代码（用后即删，逐次容错）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from selenium.webdriver.common.by import By
from app.services.crawler.anti_detect import create_driver, close_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    for code in ["140100", "140200", "140500", "140400", "140600", "140800"]:
        try:
            driver.get(f"https://we.51job.com/pc/search?jobArea={code}&keyword=Python&searchType=2&pageNum=1")
            time.sleep(8)
            cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
            areas = []
            for c in cards[:6]:
                a = ""
                for sel in ["[class*=location]", "[class*=area]", ".address", ".s"]:
                    try:
                        els = c.find_elements(By.CSS_SELECTOR, sel)
                        if els and els[0].text.strip():
                            a = els[0].text.strip()
                            break
                    except Exception:
                        pass
                if a:
                    areas.append(a)
            print(f"code={code} cards={len(cards)} areas={areas[:4]}")
        except Exception as e:
            print(f"code={code} ERR {type(e).__name__}: {str(e)[:80]}")
            try:
                driver.quit()
            except Exception:
                pass
            driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
finally:
    close_driver(driver)
