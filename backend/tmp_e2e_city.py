"""临时自测：真实爬取指定城市（柳州）验证城市参数生效（用后即删）"""
import json
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

import urllib.request

API = "http://127.0.0.1:5000/api"


def http_json(path, data=None, token=None, timeout=10):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(API + path, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def main():
    token = http_json("/auth/login", {"account": "admin", "password": "Admin@123456"})["data"]["tokens"]["access_token"]
    print("[1] 登录成功")

    # 启动：关键字 Python、城市柳州、1 页、1 线程、真实模式、无头
    resp = http_json("/crawl/start", {"keywords": "Python", "city": "柳州",
                                      "pages": 1, "threads": 1, "mode": "real",
                                      "headless": True}, token=token)
    print("[2] 启动响应:", resp)

    last_ids = set()
    start = time.time()
    while time.time() - start < 180:
        st = http_json("/crawl/status").get("data", {})
        running = st.get("running")
        stats = st.get("stats", {})
        logs = http_json("/crawl/logs?page=1&page_size=30").get("data", {}).get("items", [])
        for l in logs:
            if l["id"] not in last_ids:
                last_ids.add(l["id"])
                if l.get("task_id") == st.get("current_task_id"):
                    print(f"    LOG [{l['level']}] {l['message'][:130]}")
        print(f"    [t={int(time.time()-start)}s] running={running} found={stats.get('found')} saved={stats.get('saved')}")
        if not running and time.time() - start > 15:
            break
        time.sleep(5)

    # 验证任务
    tasks = http_json("/crawl/tasks?page=1&page_size=2", token=token).get("data", {}).get("items", [])
    for t in tasks[:1]:
        print(f"[3] 任务#{t['id']} mode={t['mode']} status={t['status']} "
              f"found={t['total_found']} saved={t['total_saved']} msg={t.get('message','')}")

    # 验证最新爬取职位的城市分布（应全是柳州）
    import sqlite3
    con = sqlite3.connect(r"e:\Allcode\毕业设计\backend\instance\job_ai.db")
    rows = con.execute(
        "select title, city, district, company_name from jobs "
        "where source='crawler' and created_at >= datetime('now','localtime','-20 minutes') "
        "order by id desc limit 12").fetchall()
    cities = set()
    print("[4] 最近爬取的职位：")
    for r in rows:
        cities.add(r[1])
        print(f"     {r[0][:22]} | {r[1]}/{r[2]} | {r[3][:16]}")
    print("[5] 覆盖城市:", sorted(c for c in cities if c))
    con.close()


if __name__ == "__main__":
    main()
