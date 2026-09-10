"""简历模型"""
from datetime import datetime

from app.extensions import db


class Resume(db.Model):
    __tablename__ = "resumes"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(8), nullable=False)        # pdf / docx / doc / txt
    file_size = db.Column(db.Integer, nullable=False, default=0)
    parse_status = db.Column(db.String(16), nullable=False, default="pending")
    # pending / success / failed
    raw_text = db.Column(db.Text, nullable=True)               # 解析出的全文
    structured = db.Column(db.Text, nullable=True)             # JSON 结构化数据
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                           onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="resumes")

    def to_dict(self, include_detail=False):
        import json
        data = {
            "id": self.id,
            "file_name": self.file_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "parse_status": self.parse_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_detail:
            data.update({
                "raw_text": (self.raw_text or "")[:20000],
                "structured": json.loads(self.structured) if self.structured else None,
            })
        return data
