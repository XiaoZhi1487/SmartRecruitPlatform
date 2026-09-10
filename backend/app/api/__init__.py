"""API 蓝图注册"""
from app.api.auth import bp as auth_bp
from app.api.user import bp as user_bp
from app.api.jobs import bp as jobs_bp
from app.api.resume import bp as resume_bp
from app.api.crawl import bp as crawl_bp
from app.api.chat import bp as chat_bp
from app.api.recommend import bp as recommend_bp
from app.api.admin import bp as admin_bp


def register_blueprints(app):
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(jobs_bp, url_prefix="/api/jobs")
    app.register_blueprint(resume_bp, url_prefix="/api/resume")
    app.register_blueprint(crawl_bp, url_prefix="/api/crawl")
    app.register_blueprint(chat_bp, url_prefix="/api/chat")
    app.register_blueprint(recommend_bp, url_prefix="/api/recommend")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")

    @app.get("/api/health")
    def health():
        from app.utils.response import ok
        return ok({"status": "up"})
