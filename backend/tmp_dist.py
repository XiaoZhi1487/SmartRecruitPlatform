"""一次性：查看带详情职位的分布（用后即删）"""
import sys

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.job import Job

app = create_app()
with app.app_context():
    rows = Job.query.filter(Job.source == "crawler").order_by(Job.id.desc()).limit(40).all()
    print("id 降序 40 条（最近爬取）:  [OK]=带详情 [--]=无详情")
    for j in rows:
        mark = "OK" if j.description else "--"
        print(f"  id={j.id} {mark} {j.title[:30]}")
