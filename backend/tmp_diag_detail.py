"""临时诊断：fetch_job_detail 卡住复现（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver, close_driver
from app.services.crawler.job51_crawler import extract_job_card, fetch_job_detail
from app import create_app

app = create_app()
cfg = app.config

driver = create_driver(headless=True, engine="edge", driver_path=r"drivers\msedgedriver.exe")
try:
    driver.get("https://we.51job.com/m/search?keyword=Python&jobarea=000000,000000&pageNum=1")
    time.sleep(8)
    cards = driver.find_elements("css selector", ".joblist")
    print("CARDS:", len(cards))
    if not cards:
        raise SystemExit("no cards")
    it = extract_job_card(cards[0], cfg["CRAWL_SELECTORS"])
    print("LINK:", it.get("link"))
    print("SID:", it.get("source_job_id"))
    t0 = time.time()
    desc = fetch_job_detail(driver, it["link"], cfg["CRAWL_DETAIL_SELECTORS"], timeout=15)
    print("DESC_LEN:", len(desc), "耗时 %.1fs" % (time.time() - t0))
    print("PREVIEW:", desc[:150].replace("\n", " | "))
finally:
    close_driver(driver)
