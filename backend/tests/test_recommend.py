"""智能推荐模块测试"""
import json

from app.extensions import db
from app.models.job import Job, Company
from app.models.profile import UserProfile, Skill


def _create_jobs(app, n=5):
    with app.app_context():
        for i in range(n):
            company = Company.query.filter_by(name=f"测试公司{i}").first()
            if not company:
                company = Company(name=f"测试公司{i}", industry="互联网")
                db.session.add(company)
                db.session.flush()
            job = Job(
                source_job_id=f"test-job-{i}", title=f"Python开发工程师{i}",
                salary_text="20-30K", salary_min=20, salary_max=30,
                city="北京", district="海淀区",
                job_tags=json.dumps(["Python", "Django", "爬虫"], ensure_ascii=False),
                company_name=company.name, company_id=company.id,
                experience_required="1-3年", education_required="本科",
                description="负责Python后端开发", source="test",
            )
            db.session.add(job)
        db.session.commit()


def _create_profile(app, user_id):
    with app.app_context():
        p = UserProfile.query.filter_by(user_id=user_id).first()
        if not p:
            p = UserProfile(user_id=user_id, expected_position="Python开发工程师",
                            expected_city="北京", salary_min=18, salary_max=28,
                            experience_years=3, education_level="本科")
            db.session.add(p)
            db.session.flush()
        else:
            p.expected_city = "北京"
            p.salary_min, p.salary_max = 18, 28
            p.experience_years = 3
            p.education_level = "本科"
        Skill.query.filter_by(profile_id=p.id).delete()
        for name in ["Python", "Django", "爬虫"]:
            db.session.add(Skill(profile_id=p.id, name=name, level=4))
        db.session.commit()


def test_recommend_jobs(app, client, auth_headers):
    _create_jobs(app)
    uid = client.get("/api/auth/me", headers=auth_headers).get_json()["data"]["user"]["id"]
    _create_profile(app, uid)
    resp = client.get("/api/recommend/jobs", headers=auth_headers)
    data = resp.get_json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1
    first = data["data"]["items"][0]
    assert "match_score" in first
    assert first["match_score"] >= 20


def test_jobs_list(app, client):
    _create_jobs(app)
    resp = client.get("/api/jobs?keyword=Python&city=北京")
    data = resp.get_json()
    assert data["code"] == 0
    assert data["data"]["total"] >= 1
    assert data["data"]["items"][0]["title"].startswith("Python")


def test_job_stats(app, client):
    _create_jobs(app)
    resp = client.get("/api/jobs/stats")
    data = resp.get_json()
    assert data["code"] == 0
    assert data["data"]["total_jobs"] >= 5
