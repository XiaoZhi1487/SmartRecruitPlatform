"""临时验证：PC 版 jobArea 参数 + 手机版区域弹层（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver
from selenium.webdriver.common.by import By

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    # 1) PC 版带 jobArea 参数
    driver.get("https://we.51job.com/pc/search?jobArea=020000&keyword=Python&searchType=2&pageNum=1")
    time.sleep(8)
    print("PC_URL:", driver.current_url)
    body = driver.find_element(By.TAG_NAME, "body").text[:150].replace("\n", " | ")
    print("PC_BODY:", body)
    cards = driver.find_elements(By.CSS_SELECTOR, ".joblist-item")
    areas = []
    for c in cards[:5]:
        try:
            a = c.find_element(By.CSS_SELECTOR, ".location, .area, [class*=area]").text.strip()
        except Exception:
            a = ""
        if a:
            areas.append(a)
    print("PC_CARDS:", len(cards), "areas:", areas[:4])
finally:
    close_driver(driver)
