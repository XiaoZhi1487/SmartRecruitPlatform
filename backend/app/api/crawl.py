"""爬虫控制接口：启动/停止/状态/日志/结构监测/任务历史/数据清空"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required

from app.extensions import db
from app.models.interaction import CrawlTask, CrawlLog, FavoriteJob
from app.models.job import Job
from app.services.crawler import crawl_manager
from app.utils.response import ok, fail, page_result

bp = Blueprint("crawl", __name__)


@bp.post("/start")
@jwt_required()
def start_crawl():
    data = request.get_json(silent=True) or {}
    keywords = data.get("keywords") or []
    if isinstance(keywords, str):
        keywords = [k for k in keywords.replace("，", ",").split(",")]
    if not keywords:
        return fail("请至少填写一个爬取关键字")
    city = data.get("city") or ""
    if not city:
        return fail("请选择要爬取的城市")
    pages = int(data.get("pages") or 3)
    threads = int(data.get("threads") or crawl_manager.app.config["CRAWL_THREADS"])
    mode = data.get("mode") or crawl_manager.app.config["CRAWL_MODE"]
    if mode not in ("real", "mock", "auto"):
        mode = "auto"
    # 是否显示浏览器窗口（None 表示跟随配置 CRAWL_HEADLESS）
    headless = data.get("headless")
    if headless is not None:
        headless = str(headless).lower() in ("1", "true", "yes", "on")
    try:
        task_id = crawl_manager.start(keywords, city, pages, threads, mode, headless)
        return ok({"task_id": task_id}, "爬取任务已启动")
    except RuntimeError as e:
        return fail(str(e), http_status=409)
    except ValueError as e:
        return fail(str(e))


@bp.post("/stop")
@jwt_required()
def stop_crawl():
    if not crawl_manager.running:
        return fail("当前没有运行中的爬取任务")
    crawl_manager.stop()
    return ok(None, "已发送停止指令，正在收尾...")


@bp.get("/status")
@jwt_required(optional=True)
def crawl_status():
    return ok(crawl_manager.status())


@bp.get("/logs")
@jwt_required(optional=True)
def crawl_logs():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(int(request.args.get("page_size", 20)), 100)
    task_id = request.args.get("task_id", type=int)
    query = CrawlLog.query
    if task_id:
        query = query.filter_by(task_id=task_id)
    query = query.order_by(CrawlLog.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(page_result([i.to_dict() for i in items], total, page, page_size))


@bp.get("/tasks")
@jwt_required()
def crawl_tasks():
    page = max(1, int(request.args.get("page", 1)))
    page_size = min(int(request.args.get("page_size", 10)), 50)
    query = CrawlTask.query.order_by(CrawlTask.created_at.desc())
    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()
    return ok(page_result([t.to_dict() for t in items], total, page, page_size))


@bp.post("/structure-check")
@jwt_required()
def structure_check():
    """手动触发网站结构变更监测"""
    from app.services.crawler.structure_monitor import check_structure
    app = crawl_manager.app
    # 在后台线程执行，避免阻塞
    from threading import Thread
    result_box = {}
    def _run():
        result_box["summary"] = check_structure(app)
    Thread(target=_run, daemon=True).start()
    return ok(None, "结构监测已触发，请稍后查看结果")


@bp.get("/structure-checks")
@jwt_required()
def structure_checks():
    from app.models.interaction import SiteStructureCheck
    items = SiteStructureCheck.query.order_by(
        SiteStructureCheck.created_at.desc()).limit(50).all()
    return ok([i.to_dict() for i in items])


@bp.post("/clear")
@jwt_required()
def clear_crawl_data():
    """清空爬取数据（模拟/真实爬取产生的职位），所有登录用户可用。
    仅删除 source 为 crawler/mock 的数据，保留种子演示数据；同时清理相关收藏。"""
    if crawl_manager.running:
        return fail("爬取任务运行中，请先停止再清空数据", http_status=409)
    ids = [r[0] for r in db.session.query(Job.id).filter(
        Job.source.in_(["crawler", "mock"])).all()]
    if not ids:
        return ok({"deleted": 0}, "没有可清空的爬取数据")
    FavoriteJob.query.filter(FavoriteJob.job_id.in_(ids)).delete(
        synchronize_session=False)
    deleted = Job.query.filter(Job.id.in_(ids)).delete(synchronize_session=False)
    db.session.commit()
    return ok({"deleted": deleted}, f"已清空 {deleted} 条爬取数据")
