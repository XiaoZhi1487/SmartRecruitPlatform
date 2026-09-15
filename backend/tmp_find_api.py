"""一次性：测试 51job 列表 JSON API（用后即删）"""
import json
import sys

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app.services.crawler.user_agents import get_random_ua

import requests

ua = get_random_ua()
headers = {
    "User-Agent": ua,
    "Referer": "https://we.51job.com/",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Origin": "https://we.51job.com",
}
candidates = [
    "https://we.51job.com/api/job/search-pc?keyword=%E9%94%80%E5%94%AE&jobArea=140400&pageNum=1&pageSize=20",
    "https://we.51job.com/api/job/search?keyword=%E9%94%80%E5%94%AE&jobArea=140400&pageNum=1&pageSize=20",
    "https://search.51job.com/list/140400,000000,0000,00,9,99,%25E9%2594%2580%25E5%2594%25AE,2,1.html",
    "https://msearch.51job.com/api/job/search?keyword=%E9%94%80%E5%94%AE&jobarea=140400&pageNum=1",
]
for url in candidates:
    try:
        r = requests.get(url, headers=headers, timeout=12)
        ct = r.headers.get("Content-Type", "")
        txt = r.text
        print(f"\n=== {url[:80]}", flush=True)
        print(f"  status={r.status_code} ct={ct} len={len(txt)}", flush=True)
        has_desc = ("description" in txt.lower() or "jobDesc" in txt or "职位描述" in txt)
        print(f"  has_desc={has_desc}", flush=True)
        if "json" in ct:
            try:
                d = r.json()
                if isinstance(d, dict):
                    print("  top keys:", list(d.keys())[:12], flush=True)
                    for k in ("resultbody", "job", "data"):
                        if k in d:
                            v = d[k]
                            print(f"  {k} type={type(v).__name__}", flush=True)
                            s = json.dumps(v, ensure_ascii=False)
                            print("   sample:", s[:300], flush=True)
                            break
            except Exception as e:
                print(f"  json parse fail: {e}", flush=True)
                print("  raw head:", txt[:200], flush=True)
        elif has_desc:
            idx = txt.lower().find("description")
            print("  ctx:", txt[idx:idx + 200], flush=True)
        else:
            print("  raw head:", txt[:150], flush=True)
    except Exception as e:
        print(f"=== {url[:60]} 异常 {type(e).__name__}: {str(e)[:80]}", flush=True)
