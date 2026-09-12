"""临时验证：51job 柳州城市代码（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver
from selenium.webdriver.common.by import By

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    # 候选柳州代码测试
    for code in ["050800", "050600", "051200", "050900", "051100"]:
        url = f"https://we.51job.com/m/search?keyword=Python&jobarea={code},000000&pageNum=1"
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
        # 页面区域标签
        body = ""
        try:
            body = driver.find_element(By.TAG_NAME, "body").text[:80].replace("\n", " ")
        except Exception:
            pass
        print(f"code={code} cards={len(cards)} areas={areas[:3]} top={body[:60]!r}")
        if any("柳州" in a for a in areas):
            print(f"  -> {code} 命中柳州")
            break
finally:
    close_driver(driver)
