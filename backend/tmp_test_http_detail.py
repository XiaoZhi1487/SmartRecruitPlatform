"""一次性：测试用纯 requests 抓取 msearch 详情页（服务端渲染，免浏览器）"""
import sys
import re

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.job import Job
from app.services.crawler.user_agents import get_random_ua

import requests

app = create_app()
with app.app_context():
    rows = Job.query.filter(Job.source == "crawler",
                            Job.description.isnot(None),
                            Job.description != "").limit(3).all()
    links = [j.link for j in rows]
    print("带详情的链接示例:", links[:3], flush=True)

session = requests.Session()
ua = get_random_ua()
session.headers.update({
    "User-Agent": ua,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://m.51job.com/",
})

for url in links[:3]:
    try:
        r = session.get(url, timeout=15)
        txt = r.text
        print(f"\n=== {url}", flush=True)
        print(f"  status={r.status_code} ct={r.headers.get('Content-Type','')} len={len(txt)}", flush=True)
        # 是否包含职位描述关键字
        for kw in ("职位描述", "任职要求", "job_msg", "jobinfoDesModule", "description"):
            if kw in txt:
                i = txt.find(kw)
                print(f"  找到[{kw}] idx={i} ctx={txt[i:i+120]!r}", flush=True)
        # 提取一段 job_msg 内容
        m = re.search(r'job_msg[^>]*>(.*?)</div>', txt, re.S)
        if m:
            seg = re.sub(r"<[^>]+>", " ", m.group(1))
            seg = re.sub(r"\s+", " ", seg).strip()
            print(f"  job_msg 提取: {seg[:200]}", flush=True)
    except Exception as e:
        print(f"=== {url} 异常 {type(e).__name__}: {str(e)[:100]}", flush=True)
