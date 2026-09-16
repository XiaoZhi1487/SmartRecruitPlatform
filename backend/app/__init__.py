"""Flask 应用工厂"""
import os

from flask import Flask, jsonify

from app.config import Config
from app.extensions import db, jwt, bcrypt, cors, migrate
from app.utils.logger import setup_logger, get_logger


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # 目录准备
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    setup_logger(app)
    logger = get_logger()

    # 扩展初始化
    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})
    migrate.init_app(app, db)

    # 注册模型
    from app import models  # noqa: F401

    # 初始化全局 AI 服务与爬虫管理器
    from app.services import ai_service as ai_mod
    from app.services.ai_service import DeepSeekService
    ai_mod.ai_service = DeepSeekService(
        api_key=app.config["DEEPSEEK_API_KEY"],
        base_url=app.config["DEEPSEEK_API_BASE"],
        model=app.config["DEEPSEEK_MODEL"],
        timeout=app.config["AI_TIMEOUT"],
        max_retries=app.config["AI_MAX_RETRIES"],
    )
    from app.services.crawler import crawl_manager
    crawl_manager.app = app

    # 注册蓝图
    from app.api import register_blueprints
    register_blueprints(app)

    # JWT 异常处理
    _register_jwt_handlers(app)

    # 全局错误处理
    _register_error_handlers(app)

    # 初始化数据库 + 种子数据
    with app.app_context():
        db.create_all()
        _seed_admin(app)
        _seed_demo_jobs(app)

    logger.info("智聘通后端启动完成")
    return app


# ---------------- JWT 异常处理 ----------------
def _register_jwt_handlers(app):
    @jwt.unauthorized_loader
    def _unauthorized(reason):
        return jsonify({"code": 401, "message": f"未认证: {reason}", "data": None}), 401

    @jwt.invalid_token_loader
    def _invalid(reason):
        return jsonify({"code": 401, "message": f"无效令牌: {reason}", "data": None}), 401

    @jwt.expired_token_loader
    def _expired(header, payload):
        return jsonify({"code": 401, "message": "令牌已过期，请重新登录", "data": None}), 401

    @jwt.revoked_token_loader
    def _revoked(header, payload):
        return jsonify({"code": 401, "message": "令牌已失效", "data": None}), 401


def _register_error_handlers(app):
    @app.errorhandler(404)
    def _not_found(e):
        return jsonify({"code": 404, "message": "资源不存在", "data": None}), 404

    @app.errorhandler(405)
    def _method_not_allowed(e):
        return jsonify({"code": 405, "message": "请求方法不允许", "data": None}), 405

    @app.errorhandler(500)
    def _server_error(e):
        get_logger().error("服务器内部错误: %s", e)
        return jsonify({"code": 500, "message": "服务器内部错误", "data": None}), 500

    @app.errorhandler(413)
    def _too_large(e):
        return jsonify({"code": 413, "message": "上传文件过大（上限16MB）", "data": None}), 413


# ---------------- 种子数据 ----------------
def _seed_admin(app):
    from app.models.user import User
    if User.query.filter_by(username="admin").first():
        return
    admin = User(username="admin", email="admin@jobai.com", role="admin",
                 email_verified=True, is_active=True)
    admin.set_password("Admin@123456")
    db.session.add(admin)
    db.session.commit()
    get_logger().info("已创建默认管理员: admin / Admin@123456")

    if not User.query.filter_by(username="demo").first():
        demo = User(username="demo", email="demo@jobai.com", role="user",
                    email_verified=True, is_active=True)
        demo.set_password("Demo@123456")
        db.session.add(demo)
        db.session.flush()
        from app.models.profile import UserProfile, Skill
        p = UserProfile(user_id=demo.id, real_name="示例用户", expected_position="Python开发工程师",
                        expected_city="北京", salary_min=18, salary_max=25,
                        experience_years=3, education_level="本科",
                        self_intro="3年后端开发经验，擅长Python/爬虫与数据分析。")
        db.session.add(p)
        db.session.flush()
        for name in ["Python", "Django", "爬虫", "MySQL", "Linux", "数据分析"]:
            db.session.add(Skill(profile_id=p.id, name=name, level=4))
        db.session.commit()
        get_logger().info("已创建演示用户: demo / Demo@123456")


def _seed_demo_jobs(app):
    from app.models.job import Job
    if Job.query.count() > 0 or app.config["CRAWL_MODE"] == "real":
        return
    from app.services.crawler import mock_data
    saved = 0
    for kw in ["Python", "Java", "前端", "数据分析"]:
        items = mock_data.generate_jobs(kw, pages=2)
        for it in items:
            it["source_job_id"] = "seed-" + it["source_job_id"]
        saved += _seed_save(items)
    get_logger().info("已生成演示职位数据 %s 条", saved)


def _seed_save(items):
    from app.models.job import Job, Company
    import json
    saved = 0
    for it in items:
        company = Company.query.filter_by(name=it["company_name"]).first()
        if not company:
            company = Company(name=it["company_name"],
                              industry=(it.get("company_tags") or [""])[0],
                              scale=next((t for t in (it.get("company_tags") or [])
                                          if "人" in t), None))
            db.session.add(company)
            db.session.flush()
        job = Job(source_job_id=it["source_job_id"], title=it["title"],
                  salary_text=it["salary_text"],
                  salary_min=it.get("salary_min") or None,
                  salary_max=it.get("salary_max") or None,
                  city=it["city"], district=it["district"],
                  job_tags=json.dumps(it.get("job_tags") or [], ensure_ascii=False),
                  company_name=it["company_name"], company_id=company.id,
                  link=it["link"], description=it.get("description"),
                  experience_required=it.get("experience_required"),
                  education_required=it.get("education_required"),
                  welfare=it.get("welfare"), source="seed")
        db.session.add(job)
        saved += 1
    db.session.commit()
    return saved

