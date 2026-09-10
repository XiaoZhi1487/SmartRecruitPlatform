"""用户模型"""
from datetime import datetime

from app.extensions import db, bcrypt


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(128), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    # 角色: user(求职者) / enterprise(企业) / admin(管理员)
    role = db.Column(db.String(16), nullable=False, default="user", index=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    profile = db.relationship("UserProfile", back_populates="user",
                              uselist=False, cascade="all, delete-orphan")
    resumes = db.relationship("Resume", back_populates="user",
                              cascade="all, delete-orphan")

    # ---------- 密码处理 ----------
    def set_password(self, raw: str):
        self.password_hash = bcrypt.generate_password_hash(raw).decode("utf-8")

    def check_password(self, raw: str) -> bool:
        return bcrypt.check_password_hash(self.password_hash, raw)

    # ---------- 登录安全 ----------
    @property
    def is_locked(self) -> bool:
        return self.locked_until is not None and self.locked_until > datetime.utcnow()

    def register_failure(self, lock_minutes: int = 15):
        self.failed_attempts += 1
        from datetime import timedelta
        if self.failed_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=lock_minutes)
            self.failed_attempts = 0
            return True
        return False

    def reset_failures(self):
        self.failed_attempts = 0
        self.locked_until = None

    # ---------- 序列化 ----------
    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "is_active": self.is_active,
            "email_verified": self.email_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }
