"""一次性：观察 msearch 详情页加载流程（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.services.crawler.anti_detect import create_driver, close_driver

app = create_app()
cfg = app.config
link = "https://msearch.51job.com/jobs/all/171307301.html"

driver = create_driver(headless=False, engine=cfg["CRAWL_BROWSER"],
                       browser_path=cfg["CRAWL_BROWSER_PATH"],
                       driver_path=cfg["CRAWL_DRIVER_PATH"])
try:
    driver.set_page_load_timeout(15)
    t0 = time.time()
    try:
        driver.get(link)
        print(f"[{time.time()-t0:.1f}s] get 返回", flush=True)
    except Exception as e:
        print(f"[{time.time()-t0:.1f}s] get 异常 {type(e).__name__}: {str(e)[:80]}", flush=True)
    for i in range(20):
        time.sleep(2)
        try:
            cur = driver.current_url
            body = driver.find_elements("css selector", "body")
            blen = len((body[0].text or "").strip()) if body else -1
            has_desc = len(driver.find_elements("css selector", cfg["CRAWL_DETAIL_SELECTORS"]["job_desc"].split(",")[0]))
            print(f"[{time.time()-t0:.1f}s] url={cur[:60]} body_len={blen} "
                  f"jobinfoDesModule={has_desc}", flush=True)
            if has_desc:
                print(">>> 描述容器出现", flush=True)
                break
            if cur.startswith("data:") or cur == "about:blank":
                print(">>> 空页", flush=True)
                break
        except Exception as e:
            print(f"[{time.time()-t0:.1f}s] 异常 {type(e).__name__}: {str(e)[:80]}", flush=True)
            break
finally:
    close_driver(driver)
print("DONE", flush=True)
