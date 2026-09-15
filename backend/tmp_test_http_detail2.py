"""一次性：检查 msearch 详情页返回的实际内容结构"""
import sys

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.job import Job
from app.services.crawler.user_agents import get_random_ua

import requests

app = create_app()
with app.app_context():
    row = Job.query.filter(Job.source == "crawler",
                           Job.description.isnot(None),
                           Job.description != "").first()
    url = row.link
    print("url:", url, flush=True)

session = requests.Session()
session.headers.update({
    "User-Agent": get_random_ua(),
    "Accept": "text/html,application/xhtml+xml,*/*",
    "Accept-Language": "zh-CN,zh;q=0.9",
})
r = session.get(url, timeout=15)
raw = r.content
print(f"status={r.status_code} len={len(raw)}", flush=True)
# 探测编码
for enc in ("utf-8", "gbk", "gb18030"):
    try:
        t = raw.decode(enc)
        print(f"[{enc}] 可解码，含'职位描述'={('职位描述' in t)}, 含'任职要求'={('任职要求' in t)}, 含'工作内容'={('工作内容' in t)}", flush=True)
    except Exception as e:
        print(f"[{enc}] 解码失败 {e}", flush=True)

t = raw.decode("utf-8", errors="replace")
# 输出一些文本片段看看页面结构
import re
txt = re.sub(r"<script[\s\S]*?</script>", " ", t)
txt = re.sub(r"<style[\s\S]*?</style>", " ", txt)
txt = re.sub(r"<[^>]+>", " ", txt)
txt = re.sub(r"\s+", " ", txt).strip()
print("正文片段:", txt[:600], flush=True)
print("---tail---", flush=True)
print(txt[-400:], flush=True)
