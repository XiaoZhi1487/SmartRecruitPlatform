"""一次性：查看最近爬取任务的详情抓取日志，分析失败模式"""
import sys

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.interaction import CrawlLog

app = create_app()
with app.app_context():
    rows = CrawlLog.query.order_by(CrawlLog.id.desc()).limit(40).all()
    for r in rows:
        print(f"[{r.level}] kw={r.keyword} page={r.page} :: {r.message[:120]}")
