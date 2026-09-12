"""临时验证：手机版页面 区域 筛选交互（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver
from selenium.webdriver.common.by import By

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    url = "https://we.51job.com/m/search?keyword=Python&jobarea=000000,000000&pageNum=1"
    driver.get(url)
    time.sleep(8)
    # 找"区域"按钮
    body = driver.find_element(By.TAG_NAME, "body").text[:200]
    print("BODY:", body.replace("\n", " | "))
    # 查找含"区域"文本的可点击元素
    try:
        el = driver.find_element(By.XPATH, "//*[contains(text(),'区域')]")
        print("FOUND 区域:", el.tag_name, "| class:", el.get_attribute("class"))
        el.click()
        time.sleep(3)
        body2 = driver.find_element(By.TAG_NAME, "body").text[:400]
        print("AFTER_CLICK:", body2.replace("\n", " | ")[:350])
        # 城市选项
        try:
            items = driver.find_elements(By.CSS_SELECTOR, "[class*=city], [class*=area], [class*=item], .tag")
            for it in items[:20]:
                t = it.text.strip()
                if t and len(t) < 10:
                    print("  OPT:", it.tag_name, t, "| class:", (it.get_attribute("class") or "")[:40])
        except Exception:
            pass
    except Exception as e:
        print("CLICK FAIL:", type(e).__name__, str(e)[:120])
        # 尝试所有 button
        try:
            btns = driver.find_elements(By.TAG_NAME, "span")
            for b in btns[:30]:
                t = b.text.strip()
                if t in ("区域", "职能", "筛选", "综合排序"):
                    print("  SPAN:", repr(t), b.get_attribute("class"))
        except Exception:
            pass
finally:
    close_driver(driver)
