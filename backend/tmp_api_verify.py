"""一次性：API 触发真实爬取并统计详情覆盖率（用后即删）"""
import json
import sys
import time
import urllib.request

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")
from app import create_app
from app.models.user import User
from flask_jwt_extended import create_access_token

app = create_app()
with app.app_context():
    user = User.query.filter_by(username="tester").first()
    if not user:
        from app.extensions import db
        from app.models.profile import UserProfile
        user = User(username="tester", email="tester@test.com", role="user")
        user.set_password("Test@123456")
        db.session.add(user)
        db.session.flush()
        db.session.add(UserProfile(user_id=user.id))
        db.session.commit()
    tok = create_access_token(identity=str(user.id),
                              additional_claims={"role": user.role, "username": user.username})

BASE = "http://127.0.0.1:5000/api/crawl"
H = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


def post(path, body):
    req = urllib.request.Request(BASE + path, data=json.dumps(body).encode("utf-8"),
                                 headers=H, method="POST")
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


def get(path):
    req = urllib.request.Request(BASE + path, headers=H)
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode("utf-8"))


print("启动:", json.dumps(post("/start", {"keywords": ["销售"], "city": "柳州",
                                         "pages": 1, "threads": 1,
                                         "mode": "real", "headless": False}),
                          ensure_ascii=False), flush=True)
for i in range(40):
    time.sleep(5)
    try:
        s = get("/status")["data"]
        st = s["stats"]
        print(f"[{i*5+5:>3}s] running={s['running']} found={st['found']} "
              f"saved={st['saved']} captcha={st['captcha']}", flush=True)
        if not s["running"]:
            break
    except Exception as e:
        print(f"查询异常: {e}", flush=True)
        break
logs = get("/logs?page_size=15")["data"]["items"]
for l in logs:
    print(f"LOG[{l['level']}] {l['message']}", flush=True)
