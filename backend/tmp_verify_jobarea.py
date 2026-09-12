"""临时验证：手机版 jobarea 参数是否生效（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver
from selenium.webdriver.common.by import By

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    cases = [
        ("上海_020000", "https://we.51job.com/m/search?keyword=Python&jobarea=020000,000000&pageNum=1"),
        ("北京_010000", "https://we.51job.com/m/search?keyword=Python&jobarea=010000,000000&pageNum=1"),
        ("上海_单值", "https://we.51job.com/m/search?keyword=Python&jobarea=020000&pageNum=1"),
        ("柳州_140200", "https://we.51job.com/m/search?keyword=Python&jobarea=140200,000000&pageNum=1"),
        ("柳州_140200单", "https://we.51job.com/m/search?keyword=Python&jobarea=140200&pageNum=1"),
    ]
    for name, url in cases:
        driver.get(url)
        time.sleep(6)
        cards = driver.find_elements(By.CSS_SELECTOR, ".joblist")
        areas = []
        for c in cards[:5]:
            try:
                a = c.find_element(By.CSS_SELECTOR, ".area .s").text.strip()
            except Exception:
                a = ""
            if a:
                areas.append(a)
        print(f"{name} cards={len(cards)} areas={areas[:4]}")
finally:
    close_driver(driver)
