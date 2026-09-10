"""职位与公司模型（爬虫数据落库目标）"""
from datetime import datetime

from app.extensions import db


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False, unique=True, index=True)
    industry = db.Column(db.String(64), nullable=True)         # 行业
    scale = db.Column(db.String(32), nullable=True)            # 规模
    financing = db.Column(db.String(32), nullable=True)        # 融资阶段
    description = db.Column(db.Text, nullable=True)
    address = db.Column(db.String(255), nullable=True)
    logo_url = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    jobs = db.relationship("Job", back_populates="company")

    def to_dict(self):
        return {
            "id": self.id, "name": self.name, "industry": self.industry,
            "scale": self.scale, "financing": self.financing,
            "description": self.description, "address": self.address,
            "logo_url": self.logo_url,
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    # Boss直聘职位唯一标识，用于去重与增量更新
    boss_job_id = db.Column(db.String(64), unique=True, index=True, nullable=True)
    title = db.Column(db.String(128), nullable=False, index=True)
    salary_text = db.Column(db.String(32), nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)          # K/月
    salary_max = db.Column(db.Integer, nullable=True)
    city = db.Column(db.String(32), nullable=True, index=True)
    district = db.Column(db.String(32), nullable=True)         # 区
    experience_required = db.Column(db.String(16), nullable=True)  # 经验要求
    education_required = db.Column(db.String(16), nullable=True)   # 学历要求
    job_tags = db.Column(db.Text, nullable=True)               # JSON数组：技能标签
    welfare = db.Column(db.Text, nullable=True)                # JSON数组：福利
    description = db.Column(db.Text, nullable=True)            # 职位描述
    requirement = db.Column(db.Text, nullable=True)            # 任职要求
    company_name = db.Column(db.String(128), nullable=True, index=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=True)
    link = db.Column(db.String(512), nullable=True)            # 原文链接（一键跳转）
    source = db.Column(db.String(16), nullable=False, default="crawler")  # crawler / mock / seed
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    company = db.relationship("Company", back_populates="jobs")
    favorites = db.relationship("FavoriteJob", back_populates="job",
                                cascade="all, delete-orphan")

    def to_dict(self, brief=False):
        data = {
            "id": self.id,
            "boss_job_id": self.boss_job_id,
            "title": self.title,
            "salary_text": self.salary_text,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "city": self.city,
            "district": self.district,
            "experience_required": self.experience_required,
            "education_required": self.education_required,
            "company_name": self.company_name,
            "link": self.link,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if not brief:
            import json
            data.update({
                "job_tags": json.loads(self.job_tags) if self.job_tags else [],
                "welfare": json.loads(self.welfare) if self.welfare else [],
                "description": self.description,
                "requirement": self.requirement,
                "company": self.company.to_dict() if self.company else None,
            })
        return data
