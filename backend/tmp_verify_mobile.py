"""临时验证：手机版全国搜索页结构（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    url = "https://we.51job.com/m/search?keyword=Python&jobarea=000000,000000&pageNum=1"
    driver.get(url)
    time.sleep(10)
    print("URL:", driver.current_url)
    from selenium.webdriver.common.by import By
    cards = driver.find_elements(By.CSS_SELECTOR, ".joblist")
    print("CARDS:", len(cards))
    for i, c in enumerate(cards[:3]):
        try:
            title = c.find_element(By.CSS_SELECTOR, ".jname").text.strip()
        except Exception:
            title = "<none>"
        try:
            area = c.find_element(By.CSS_SELECTOR, ".area .s").text.strip()
        except Exception:
            area = "<none>"
        try:
            sd = c.get_attribute("sensorsdata") or ""
        except Exception:
            sd = ""
        print(f"[{i}] title={title!r} area={area!r} sensorsdata_len={len(sd)}")
    body = driver.find_element(By.TAG_NAME, "body").text[:600]
    print("BODY_PREVIEW:", body.replace("\n", " | ")[:500])
finally:
    close_driver(driver)
