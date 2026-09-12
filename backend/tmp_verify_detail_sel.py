"""临时验证：Selenium 抓 msearch 详情耗时（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=True, engine="edge", driver_path=DRIVER)
try:
    url = "https://msearch.51job.com/jobs/all/173487969.html"
    t0 = time.time()
    driver.set_page_load_timeout(15)
    try:
        driver.get(url)
    except Exception as e:
        print("GET_EXC:", type(e).__name__, str(e)[:80], "耗时%.1fs" % (time.time() - t0))
    time.sleep(3)
    body = driver.find_element("tag name", "body").text
    print("BODY_LEN:", len(body), "耗时%.1fs" % (time.time() - t0))
    print("PREVIEW:", body[:300].replace("\n", " | "))
finally:
    close_driver(driver)
