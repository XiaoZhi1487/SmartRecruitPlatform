"""一次性：统计 crawler 职位详情覆盖率（用后即删）"""
import sys

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.job import Job

app = create_app()
with app.app_context():
    total = Job.query.filter(Job.source == "crawler").count()
    with_desc = Job.query.filter(Job.source == "crawler",
                                 Job.description.isnot(None),
                                 Job.description != "").count()
    print(f"crawler 总数: {total}, 带详情: {with_desc} ({with_desc * 100 // max(total, 1)}%)")
    rows = Job.query.filter(Job.source == "crawler").order_by(Job.id.desc()).limit(8).all()
    for j in rows:
        print(f"  {'OK ' if j.description else '-- '} {j.title} len={len(j.description or '')}")
