"""用户交互与系统运行记录模型"""
from datetime import datetime

from app.extensions import db


class FavoriteJob(db.Model):
    __tablename__ = "favorite_jobs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")
    job = db.relationship("Job", back_populates="favorites")

    __table_args__ = (db.UniqueConstraint("user_id", "job_id", name="uq_user_job"),)


class UserFeedback(db.Model):
    """用户行为反馈（用于个性化推荐权重调节）"""
    __tablename__ = "user_feedbacks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False, index=True)
    action = db.Column(db.String(16), nullable=False, index=True)   # browse / view / favorite / apply
    weight = db.Column(db.Float, nullable=False, default=1.0)       # 行为权重
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user = db.relationship("User")
    job = db.relationship("Job", back_populates="feedbacks")


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(64), nullable=False, default="新对话")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    user = db.relationship("User")
    messages = db.relationship("ChatMessage", back_populates="session",
                               cascade="all, delete-orphan",
                               order_by="ChatMessage.created_at")

    def to_dict(self):
        return {
            "id": self.id, "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class ChatMessage(db.Model):
    __tablename__ = "chat_messages"

    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = db.Column(db.String(8), nullable=False)             # user / assistant
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    session = db.relationship("ChatSession", back_populates="messages")

    def to_dict(self):
        return {
            "id": self.id, "role": self.role, "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class CrawlTask(db.Model):
    """爬取任务"""
    __tablename__ = "crawl_tasks"

    id = db.Column(db.Integer, primary_key=True)
    keywords = db.Column(db.String(512), nullable=False)       # 逗号分隔
    city = db.Column(db.String(32), nullable=True)
    pages = db.Column(db.Integer, nullable=False, default=3)
    threads = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(16), nullable=False, default="pending")
    # pending / running / done / stopped / failed
    mode = db.Column(db.String(16), nullable=False, default="real")  # real / mock / auto
    total_found = db.Column(db.Integer, nullable=False, default=0)
    total_saved = db.Column(db.Integer, nullable=False, default=0)
    captcha_hits = db.Column(db.Integer, nullable=False, default=0)
    message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id, "keywords": self.keywords, "city": self.city,
            "pages": self.pages, "threads": self.threads, "status": self.status,
            "mode": self.mode, "total_found": self.total_found,
            "total_saved": self.total_saved, "captcha_hits": self.captcha_hits,
            "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
        }


class CrawlLog(db.Model):
    """爬取运行日志"""
    __tablename__ = "crawl_logs"

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey("crawl_tasks.id"), nullable=True, index=True)
    level = db.Column(db.String(8), nullable=False, default="info")  # info / warn / error
    keyword = db.Column(db.String(64), nullable=True)
    page = db.Column(db.Integer, nullable=True)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "task_id": self.task_id, "level": self.level,
            "keyword": self.keyword, "page": self.page, "message": self.message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class SiteStructureCheck(db.Model):
    """网站结构变更监测记录"""
    __tablename__ = "site_structure_checks"

    id = db.Column(db.Integer, primary_key=True)
    check_type = db.Column(db.String(16), nullable=False, default="list")  # list / detail
    selector_key = db.Column(db.String(32), nullable=False)
    selector = db.Column(db.String(128), nullable=False)
    status = db.Column(db.String(16), nullable=False, default="ok")        # ok / missing / changed
    evidence = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id, "check_type": self.check_type,
            "selector_key": self.selector_key, "selector": self.selector,
            "status": self.status, "evidence": self.evidence,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
