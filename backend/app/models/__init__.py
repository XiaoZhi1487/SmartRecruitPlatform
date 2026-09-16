"""模型统一导入入口"""
from app.models.user import User
from app.models.profile import UserProfile, Education, WorkExperience, Skill
from app.models.job import Company, Job
from app.models.resume import Resume
from app.models.interaction import (
    FavoriteJob, ChatSession, ChatMessage, CrawlTask, CrawlLog, SiteStructureCheck,
    UserFeedback,
)

__all__ = [
    "User", "UserProfile", "Education", "WorkExperience", "Skill",
    "Company", "Job", "Resume",
    "FavoriteJob", "ChatSession", "ChatMessage",
    "CrawlTask", "CrawlLog", "SiteStructureCheck", "UserFeedback",
]
