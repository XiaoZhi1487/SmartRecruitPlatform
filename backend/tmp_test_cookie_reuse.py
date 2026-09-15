"""一次性：验证【浏览器完成WAF挑战→导出Cookie→requests复用批量抓详情】方案"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.job import Job
from app.services.crawler.anti_detect import create_driver, close_driver
from app.services.crawler.user_agents import get_random_ua

import requests

app = create_app()
DRIVER_PATH = app.config.get("CRAWL_DRIVER_PATH")
BROWSER_PATH = app.config.get("CRAWL_BROWSER_PATH")
with app.app_context():
    # 找一批没有详情的职位
    rows = Job.query.filter(Job.source == "crawler",
                            Job.description.isnot(None),
                            Job.description != "").limit(2).all()
    ok_links = [j.link for j in rows]
    rows2 = Job.query.filter(Job.source == "crawler",
                             (Job.description.is_(None)) | (Job.description == "")).limit(5).all()
    empty_links = [j.link for j in rows2]
    print("已成功详情链接:", ok_links, flush=True)
    print("待补详情链接:", empty_links, flush=True)

# 步骤1：用浏览器访问一个详情页，完成 WAF 挑战
ua = get_random_ua()
driver = create_driver(ua=ua, headless=True, engine="edge",
                       driver_path=DRIVER_PATH, browser_path=BROWSER_PATH)
try:
    driver.set_page_load_timeout(15)
    target = ok_links[0]
    print(f"\n[1] 浏览器访问 {target}", flush=True)
    driver.get(target)
    # 轮询等待真实内容渲染（WAF 挑战完成后跳转）
    desc_found = False
    for i in range(15):
        time.sleep(2)
        try:
            url = driver.current_url or ""
            txt = ""
            els = driver.find_elements("css selector", ".jobinfoDesModule, .job_msg, .bmsg")
            for e in els:
                if e.text.strip():
                    txt = e.text.strip()
                    break
            if txt:
                print(f"[1] 第{i+1}轮: 已渲染出描述 len={len(txt)}, url={url[:60]}", flush=True)
                desc_found = True
                break
            print(f"[1] 第{i+1}轮: url={url[:60]} 无描述, txt='{txt[:40]}'", flush=True)
        except Exception as e:
            print(f"[1] 第{i+1}轮异常: {type(e).__name__} {str(e)[:80]}", flush=True)
            break
    # 导出 cookies
    cookies = driver.get_cookies()
    print(f"[1] 导出 cookies {len(cookies)} 个:", flush=True)
    for c in cookies:
        print(f"    {c['name']}={c['value'][:40]}... domain={c.get('domain')}", flush=True)
    cookie_str = "; ".join(f"{c['name']}={c['value']}" for c in cookies)
finally:
    close_driver(driver)

# 步骤2：用 requests + 浏览器 cookie 抓取无详情职位
if cookie_str:
    session = requests.Session()
    session.headers.update({
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Referer": "https://msearch.51job.com/",
    })
    session.headers["Cookie"] = cookie_str
    print(f"\n[2] 用浏览器Cookie请求{len(empty_links)}条无详情职位:", flush=True)
    for url in empty_links:
        try:
            r = session.get(url, timeout=15)
            t = r.text
            has = ("职位描述" in t or "任职要求" in t or "工作内容" in t
                   or "job_msg" in t or "岗位职责" in t)
            print(f"    {url[:70]} status={r.status_code} len={len(t)} 含描述关键字={has}", flush=True)
        except Exception as e:
            print(f"    {url[:70]} 异常 {type(e).__name__}: {str(e)[:60]}", flush=True)
