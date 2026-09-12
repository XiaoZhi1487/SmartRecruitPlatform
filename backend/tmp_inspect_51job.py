"""临时检查19：jobId 解析 + fetch_job_detail 计时（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from selenium import webdriver
from selenium.webdriver.edge.options import Options
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By

from app.services.crawler.job51_crawler import extract_job_card, fetch_job_detail
from app import create_app

app = create_app()
cfg = app.config

opts = Options()
opts.add_argument("--headless=new")
opts.add_argument("--no-sandbox")
opts.add_argument("--disable-gpu")
driver = webdriver.Edge(options=opts, service=Service(r"drivers\msedgedriver.exe"))
try:
    driver.get("https://we.51job.com/m/search?keyword=Python&jobarea=000000,000000&pageNum=1")
    time.sleep(8)
    cards = driver.find_elements(By.CSS_SELECTOR, ".joblist")
    print("CARDS:", len(cards))
    if cards:
        it = extract_job_card(cards[0], cfg["CRAWL_SELECTORS"])
        print("ITEM:", {k: it[k] for k in ("title", "salary_text", "city", "district",
                                           "experience_required", "education_required",
                                           "company_name", "source_job_id", "link")})
        t0 = time.time()
        desc = fetch_job_detail(driver, it["link"], cfg["CRAWL_DETAIL_SELECTORS"], timeout=12)
        print("DESC_LEN:", len(desc), "耗时 %.1fs" % (time.time() - t0))
        print("DESC_PREVIEW:", desc[:120].replace("\n", " | "))
finally:
    driver.quit()
