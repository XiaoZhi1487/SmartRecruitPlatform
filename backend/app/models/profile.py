"""用户画像：个人信息、教育背景、工作经历、技能特长"""
from datetime import datetime

from app.extensions import db
from app.services.security import encrypt_text, decrypt_text


class UserProfile(db.Model):
    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=False)

    real_name = db.Column(db.String(64), nullable=True)
    # 手机号敏感字段加密存储
    phone_enc = db.Column(db.String(256), nullable=True)
    gender = db.Column(db.String(8), nullable=True)            # male / female / other
    birthday = db.Column(db.Date, nullable=True)
    city = db.Column(db.String(32), nullable=True)             # 期望工作城市
    avatar = db.Column(db.String(256), nullable=True)
    self_intro = db.Column(db.Text, nullable=True)             # 个人简介

    # 求职期望
    expected_position = db.Column(db.String(64), nullable=True)
    expected_city = db.Column(db.String(32), nullable=True)
    salary_min = db.Column(db.Integer, nullable=True)          # K/月
    salary_max = db.Column(db.Integer, nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)    # 工作年限
    education_level = db.Column(db.String(16), nullable=True)  # 高中/大专/本科/硕士/博士

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="profile")
    educations = db.relationship("Education", back_populates="profile",
                                 cascade="all, delete-orphan", order_by="Education.start_date.desc()")
    works = db.relationship("WorkExperience", back_populates="profile",
                            cascade="all, delete-orphan", order_by="WorkExperience.start_date.desc()")
    skills = db.relationship("Skill", back_populates="profile",
                             cascade="all, delete-orphan")

    @property
    def phone(self):
        return decrypt_text(self.phone_enc) if self.phone_enc else None

    @phone.setter
    def phone(self, value):
        self.phone_enc = encrypt_text(value) if value else None

    def to_dict(self):
        return {
            "id": self.id,
            "real_name": self.real_name,
            "phone": self.phone,
            "gender": self.gender,
            "birthday": self.birthday.isoformat() if self.birthday else None,
            "city": self.city,
            "avatar": self.avatar,
            "self_intro": self.self_intro,
            "expected_position": self.expected_position,
            "expected_city": self.expected_city,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "experience_years": self.experience_years,
            "education_level": self.education_level,
            "educations": [e.to_dict() for e in self.educations],
            "works": [w.to_dict() for w in self.works],
            "skills": [s.to_dict() for s in self.skills],
        }


class Education(db.Model):
    __tablename__ = "educations"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profiles.id"), nullable=False)
    school = db.Column(db.String(128), nullable=False)
    major = db.Column(db.String(128), nullable=True)
    degree = db.Column(db.String(16), nullable=True)  # 大专/本科/硕士/博士
    start_date = db.Column(db.String(16), nullable=True)
    end_date = db.Column(db.String(16), nullable=True)
    description = db.Column(db.Text, nullable=True)

    profile = db.relationship("UserProfile", back_populates="educations")

    def to_dict(self):
        return {
            "id": self.id, "school": self.school, "major": self.major,
            "degree": self.degree, "start_date": self.start_date,
            "end_date": self.end_date, "description": self.description,
        }


class WorkExperience(db.Model):
    __tablename__ = "work_experiences"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profiles.id"), nullable=False)
    company = db.Column(db.String(128), nullable=False)
    position = db.Column(db.String(64), nullable=False)
    start_date = db.Column(db.String(16), nullable=True)
    end_date = db.Column(db.String(16), nullable=True)
    description = db.Column(db.Text, nullable=True)

    profile = db.relationship("UserProfile", back_populates="works")

    def to_dict(self):
        return {
            "id": self.id, "company": self.company, "position": self.position,
            "start_date": self.start_date, "end_date": self.end_date,
            "description": self.description,
        }


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    profile_id = db.Column(db.Integer, db.ForeignKey("user_profiles.id"), nullable=False)
    name = db.Column(db.String(64), nullable=False, index=True)
    level = db.Column(db.Integer, nullable=False, default=3)  # 1-5 熟练度
    category = db.Column(db.String(32), nullable=True)        # 语言/框架/工具

    profile = db.relationship("UserProfile", back_populates="skills")

    def to_dict(self):
        return {"id": self.id, "name": self.name, "level": self.level, "category": self.category}
