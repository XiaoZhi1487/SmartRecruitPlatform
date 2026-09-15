"""一次性：验证详情抓取覆盖率提升（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.services.crawler import crawl_manager
from app.models.job import Job

app = create_app()
with app.app_context():
    task_id = crawl_manager.start(["销售"], "柳州", 1, 1, "real", headless=False)
    print("task_id:", task_id, flush=True)
    t0 = time.time()
    while crawl_manager.running and time.time() - t0 < 240:
        time.sleep(5)
        print(f"[{time.time()-t0:5.0f}s] found={crawl_manager.stats['found']} "
              f"saved={crawl_manager.stats['saved']}", flush=True)
    print("结束 stats:", crawl_manager.stats, flush=True)
    rows = Job.query.filter(Job.source == "crawler").order_by(Job.id.desc()).limit(20).all()
    total = len(rows)
    with_desc = sum(1 for j in rows if j.description)
    print(f"本页最新{total}条, 带描述 {with_desc} 条", flush=True)
    for j in rows:
        print(f"  {'OK ' if j.description else '-- '} {j.title} len={len(j.description or '')}", flush=True)
