"""临时自测2：真实爬取（默认全国）+ 验证结果（用后即删）"""
import json
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

import urllib.request
from selenium.webdriver.common.by import By
from app.services.crawler.anti_detect import create_driver, close_driver

BASE = "http://localhost:5173"
API = "http://127.0.0.1:5000/api"


def http_json(path, data=None, token=None, timeout=10):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(API + path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def set_input(driver, css, value):
    driver.execute_script(
        f"""
        const el = document.querySelector({json.dumps(css)});
        if(!el) return;
        const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        setter.call(el, {json.dumps(value)});
        el.dispatchEvent(new Event('input', {{bubbles: true}}));
        el.dispatchEvent(new Event('change', {{bubbles: true}}));
        el.dispatchEvent(new Event('blur', {{bubbles: true}}));
        """
    )


def main():
    token = http_json("/auth/login", {"account": "admin", "password": "Admin@123456"})["data"]["tokens"]["access_token"]
    print("[1] 登录成功")

    opts = None
    driver = create_driver(headless=True, engine="edge", driver_path=r"drivers\msedgedriver.exe")
    try:
        driver.get(BASE + "/login")
        time.sleep(2)
        driver.execute_script(
            f"localStorage.setItem('access_token', {json.dumps(token)}); location.href='/crawler';")
        time.sleep(4)
        print("[2] 进入 /crawler:", driver.current_url)

        # 表单：1 个关键字、1 页、1 线程、真实模式、无头；城市保持默认（全国）
        set_input(driver, ".crawl-form .form-item.full .el-input input", "Python")
        time.sleep(0.5)
        set_input(driver, ".crawl-form .el-input-number input", "1")
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//label[contains(.,'真实')]").click()
        time.sleep(0.5)
        chk = driver.find_element(By.XPATH, "//label[contains(.,'显示浏览器')]")
        if "is-checked" in chk.get_attribute("class"):
            chk.click()
        time.sleep(0.5)
        driver.find_element(By.XPATH, "//button[contains(.,'启动爬取')]").click()
        print("[3] 已点击 启动爬取（默认全国）")
        time.sleep(3)

        # 轮询
        last_ids = set()
        start = time.time()
        while time.time() - start < 240:
            st = http_json("/crawl/status").get("data", {})
            running = st.get("running")
            stats = st.get("stats", {})
            logs = http_json("/crawl/logs?page=1&page_size=30").get("data", {}).get("items", [])
            for l in logs:
                if l["id"] not in last_ids:
                    last_ids.add(l["id"])
                    print(f"    LOG [{l['level']}] {l['message'][:130]}")
            print(f"    [t={int(time.time()-start)}s] running={running} found={stats.get('found')} saved={stats.get('saved')}")
            if not running and time.time() - start > 15:
                break
            time.sleep(5)

        # 任务结果
        tasks = http_json("/crawl/tasks?page=1&page_size=3", token=token).get("data", {}).get("items", [])
        for t in tasks[:2]:
            print(f"[4] 任务#{t['id']} mode={t['mode']} status={t['status']} "
                  f"found={t['total_found']} saved={t['total_saved']} msg={t.get('message','')}")

        # 验证保存的职位城市分布（全国性）
        with open(r"e:\Allcode\毕业设计\backend\instance\job_ai.db", "rb"):
            pass
        import sqlite3
        con = sqlite3.connect(r"e:\Allcode\毕业设计\backend\instance\job_ai.db")
        rows = con.execute(
            "select title, city, district, company_name from jobs where source='crawler' order by id desc limit 15").fetchall()
        print("[5] 最近爬取的职位：")
        cities = set()
        for r in rows:
            cities.add(r[1])
            print(f"     {r[0][:20]} | {r[1]}/{r[2]} | {r[3][:18]}")
        print("[6] 覆盖城市:", sorted(c for c in cities if c))
        con.close()
    finally:
        close_driver(driver)


if __name__ == "__main__":
    main()
