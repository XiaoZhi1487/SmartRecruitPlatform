"""爬虫调度管理器：多线程并发、任务队列、状态跟踪、auto降级"""
import queue
import threading
import time
from datetime import datetime

from app.extensions import db
from app.models.interaction import CrawlTask
from app.models.job import Job
from app.services.crawler.anti_detect import create_driver, close_driver, humanize, random_delay
from app.services.crawler.job51_crawler import (
    extract_job_card, extract_job_id, save_jobs, record_log,
)
from app.services.crawler.captcha_handler import detect_captcha, handle_captcha
from app.services.crawler.proxy_pool import ProxyPool
from app.services.crawler.user_agents import get_random_ua
from app.utils.logger import get_logger

logger = get_logger()

# 会话失效关键词：标签页崩溃 / 会话被删除 / 浏览器窗口关闭等
_DEAD_SESSION_MARKERS = (
    "invalid session id",
    "tab crashed",
    "no such window",
    "target window already closed",
    "session deleted because of page crash",
    "browser has been closed",
    "session not created",
)


class DriverSessionError(Exception):
    """驱动会话失效（标签页崩溃/会话丢失），需要重建驱动并重试当前页"""


def _is_dead_session(exc) -> bool:
    msg = str(exc).lower()
    return any(m in msg for m in _DEAD_SESSION_MARKERS)


class CrawlManager:
    """全局爬虫管理器（单例）"""

    def __init__(self, app=None):
        self.app = app
        self.task_queue = queue.Queue()
        self.workers = []
        self.running = False
        self.stop_event = threading.Event()
        self.stats_lock = threading.Lock()
        self.stats = {"found": 0, "saved": 0, "captcha": 0}
        self.current_task_id = None
        self.current_keywords = []
        self.current_item = None  # [关键字, 页码]，前端展示当前处理进度
        self.mode_used = "auto"
        self.headless = True
        self.attach_port = 0
        self._retries = {}  # (kw, city, page) -> 会话失效重建驱动的重试次数

    # ---------------- 对外控制 ----------------
    def start(self, keywords, city, pages, threads, mode="auto", headless=None) -> int:
        """启动爬取任务，返回任务ID；已有任务运行中则抛出异常"""
        if self.running:
            raise RuntimeError("已有爬取任务正在运行，请先停止")
        cfg = self.app.config
        threads = max(1, min(int(threads), 8))
        pages = max(1, min(int(pages), 20))
        keywords = [k.strip() for k in keywords if k.strip()][:10]
        if not keywords:
            raise ValueError("爬取关键字不能为空")

        # 是否显示浏览器窗口（真实模式建议开启，便于人工处理验证码）
        self.headless = bool(headless) if headless is not None else bool(cfg["CRAWL_HEADLESS"])

        # CDP 附加模式：附加到已运行的浏览器复用登录态（共用实例），强制单线程避免多会话冲突
        self.attach_port = int(cfg.get("CRAWL_ATTACH_PORT") or 0)
        if self.attach_port:
            threads = 1
            self.headless = False
            logger.info("已启用 CDP 附加模式，将复用已打开的浏览器（单线程）")

        with self.app.app_context():
            task = CrawlTask(keywords=",".join(keywords), city=city or "",
                             pages=pages, threads=threads, status="running", mode=mode)
            db.session.add(task)
            db.session.commit()
            self.current_task_id = task.id

        self.stop_event.clear()
        self.running = True
        self.stats = {"found": 0, "saved": 0, "captcha": 0}
        self.current_keywords = keywords
        self.current_item = None
        self._retries = {}
        # 每次任务使用全新队列，避免残留哨兵/任务影响下一次运行
        self.task_queue = queue.Queue()

        for kw in keywords:
            for page in range(1, pages + 1):
                self.task_queue.put((kw, city, page))

        self.mode_used = mode
        workers_n = 1 if mode == "mock" else threads
        # 每个 worker 一个哨兵，任务取完后依次退出，避免空队列死等
        for _ in range(workers_n):
            self.task_queue.put(None)
        self.workers = []
        for i in range(workers_n):
            t = threading.Thread(target=self._worker, args=(i, mode), daemon=True)
            t.start()
            self.workers.append(t)
        # 监控线程：等待所有 worker 结束后收尾
        threading.Thread(target=self._monitor, args=(list(self.workers),),
                         daemon=True).start()
        logger.info("爬虫任务#%s 启动 mode=%s threads=%d", task.id, mode, workers_n)
        return task.id

    def stop(self):
        """停止爬取任务"""
        self.stop_event.set()
        self.running = False
        self.current_item = None
        # 立即清空任务队列，worker 不再取出新任务（当前页处理完即退出）
        while True:
            try:
                self.task_queue.get_nowait()
                self.task_queue.task_done()
            except queue.Empty:
                break
        with self.app.app_context():
            task = db.session.get(CrawlTask, self.current_task_id)
            if task and task.status == "running":
                # 停止时把已完成的统计写入任务记录，避免历史显示 found=0/saved=0
                task.total_found = self.stats["found"]
                task.total_saved = self.stats["saved"]
                task.captcha_hits = self.stats["captcha"]
                task.status = "stopped"
                task.message = "已手动停止"
                task.finished_at = datetime.utcnow()
                db.session.commit()
        logger.info("爬虫任务已请求停止")

    def status(self) -> dict:
        return {
            "running": self.running,
            "current_task_id": self.current_task_id,
            "keywords": self.current_keywords,
            "current": self.current_item,
            "stats": dict(self.stats),
            "queue_size": self.task_queue.qsize(),
            "mode_used": self.mode_used,
        }

    # ---------------- 内部实现 ----------------
    def _worker(self, wid, mode):
        cfg = self.app.config
        proxy_pool = ProxyPool(cfg["CRAWL_PROXY_LIST"])
        driver = None

        while not self.stop_event.is_set():
            try:
                item = self.task_queue.get(timeout=2)
            except queue.Empty:
                if self.stop_event.is_set():
                    break
                continue
            if item is None:  # 哨兵：任务全部处理完，退出
                self.task_queue.task_done()
                break
            kw, city, page = item
            # 就地处理并支持会话失效重试（重新入队会落在哨兵之后导致任务丢失）
            while not self.stop_event.is_set():
                try:
                    if mode == "mock":
                        self._process_mock_page(kw, city, page)
                    else:
                        if driver is None:
                            driver = self._create_driver(proxy_pool)
                        driver = self._process_real_page(driver, proxy_pool, kw, city, page, cfg)
                    break
                except DriverSessionError as e:
                    # 浏览器标签页崩溃/会话丢失：销毁旧驱动并重建，就地重试当前页
                    key = (kw, city, page)
                    retries = self._retries.get(key, 0)
                    self._retries[key] = retries + 1
                    close_driver(driver)
                    driver = None
                    if retries >= 2:
                        self._log("error", f"[{kw}第{page}页] 会话多次失效({retries + 1}次)，跳过: {e}", kw, page)
                        break
                    self._log("warn", f"[{kw}第{page}页] 浏览器会话失效，重建驱动后重试: {e}", kw, page)
                except Exception as e:
                    logger.exception("worker#%d 处理失败", wid)
                    self._log("error", f"worker#{wid} 处理[{kw}第{page}页]异常: {e}", kw, page)
                    # 出错后销毁驱动，下一轮重建，避免脏状态累积
                    close_driver(driver)
                    driver = None
                    break
            self.task_queue.task_done()

        close_driver(driver)
        logger.info("worker#%d 退出", wid)

    def _create_driver(self, proxy_pool, headless=None):
        cfg = self.app.config
        proxy = proxy_pool.get() if not proxy_pool.is_empty() else None
        return create_driver(ua=get_random_ua(), proxy=proxy,
                             headless=self.headless if headless is None else headless,
                             engine=cfg["CRAWL_BROWSER"],
                             browser_path=cfg["CRAWL_BROWSER_PATH"],
                             driver_path=cfg["CRAWL_DRIVER_PATH"],
                             attach_port=self.attach_port)

    def _build_url(self, cfg, kw, page, city):
        """构建搜索页 URL。city 支持 6 位代码（140400）或城市名称（柳州）。
        城市必选（前端/API 已强制），一律使用桌面版源并携带 jobArea 参数，
        按所选城市精确爬取，不做全国爬取。仅在城市名称无法解析出代码时，
        兜底使用手机版全国源（正常不会走到）。"""
        query = kw.replace(" ", "+")
        city = (city or "").strip()
        code = city if city.isdigit() else cfg.get("CRAWL_CITY_CODES", {}).get(city, "")
        if code and code != "000000":
            return cfg["CRAWL_URL_TEMPLATE"].format(jobarea=code, query=query, page=page)
        return cfg["CRAWL_URL_NATIONWIDE"].format(query=query, page=page)

    def _process_real_page(self, driver, proxy_pool, kw, city, page, cfg):
        self.current_item = [kw, page]
        try:
            return self._process_real_page_inner(driver, proxy_pool, kw, city, page, cfg)
        finally:
            if self.current_item == [kw, page]:
                self.current_item = None

    def _process_real_page_inner(self, driver, proxy_pool, kw, city, page, cfg):
        url = self._build_url(cfg, kw, page, city)
        page_tab = None
        try:
            # 每页使用全新标签页：避免 SPA 状态残留、隔离标签页崩溃，也不干扰用户当前标签页
            page_tab = self._new_tab(driver)
            cards = self._load_list(driver, page_tab, url, kw, page, cfg)

            if self.stop_event.is_set():
                return driver
            if not cards:
                self._log("error", f"[{kw}第{page}页] 列表连续加载失败，跳过", kw, page)
                return driver

            if detect_captcha(driver):
                driver, ok = self._resolve_captcha(driver, proxy_pool, kw, city, page, cfg)
                if driver is None:
                    return None
                if not ok:
                    return driver

            # 懒加载：滚动到底部触发剩余卡片渲染
            try:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                cards = driver.find_elements("css selector", cfg["CRAWL_SELECTORS"]["job_list"])
            except Exception as e:
                if _is_dead_session(e):
                    raise DriverSessionError(str(e)[:200])

            self._bump("found", len(cards))
            items = []
            for card in cards:
                it = extract_job_card(card, cfg["CRAWL_SELECTORS"])
                if not it["title"]:
                    continue
                if not it.get("source_job_id"):
                    it["source_job_id"] = extract_job_id(it.get("link", ""))
                items.append(it)

            # 先保存列表数据（description 暂空），避免详情阶段耗时/崩溃导致整页数据丢失
            n = save_jobs(self.app, items)
            self._bump("saved", n)
            self._log("info", f"[{kw}第{page}页] 找到{len(items)}条，保存{n}条", kw, page)

            # 再抓职位详情：使用独立短生命周期驱动（不访问列表页，规避 WAF 限流与渲染崩溃）
            # 增量跳过：已存在且有描述的职位不再重复抓取，仅补抓新职位/缺失描述的职位
            detail_limit = int(cfg.get("CRAWL_DETAIL_LIMIT") or 12)
            need = [it for it in items if it.get("link")]
            if need:
                ids = [it.get("source_job_id") for it in need if it.get("source_job_id")]
                has_desc = set()
                if ids:
                    with self.app.app_context():
                        rows = Job.query.filter(
                            Job.source_job_id.in_(ids),
                            Job.description.isnot(None),
                            Job.description != "",
                        ).all()
                        has_desc = {r.source_job_id for r in rows}
                got = 0
                fail_streak = 0
                detail_deadline = time.time() + 240  # 单页详情总时长上限
                for it in need:
                    if (self.stop_event.is_set() or got >= detail_limit
                            or time.time() > detail_deadline):
                        break
                    if it.get("source_job_id") in has_desc:
                        continue
                    # 每条详情使用全新驱动：独立会话/指纹，WAF 通过率最高，
                    # 且单个渲染进程崩溃只影响当前一条，不拖累其他详情与主驱动
                    detail_driver = None
                    try:
                        detail_driver = self._create_driver(proxy_pool)
                    except Exception:
                        close_driver(detail_driver)
                        break
                    try:
                        try:
                            it["description"] = self._fetch_detail(detail_driver, it["link"], cfg)
                        except DriverSessionError:
                            it["description"] = ""
                    finally:
                        close_driver(detail_driver)
                    if it.get("description"):
                        got += 1
                        fail_streak = 0
                    else:
                        fail_streak += 1
                        if fail_streak >= 3:
                            # 连续失败说明已被 WAF 限流，停止本页详情抓取，不阻塞后续页
                            self._log("warn", f"[{kw}第{page}页] 详情连续{fail_streak}条失败，"
                                              f"本页详情抓取提前结束", kw, page)
                            break
                    # 每条详情之间留出间隔，降低访问频率触发限流的概率
                    time.sleep(2)
                self._save_details(need)

            # 随机间隔控制，模拟真人访问频率（已停止则不再等待）
            if not self.stop_event.is_set():
                time.sleep(random_delay(cfg))
            return driver
        finally:
            self._close_tab(driver, page_tab)

    def _save_details(self, items):
        """将抓取到的职位描述增量写回数据库（仅填充空描述）"""
        updates = {it.get("source_job_id"): it.get("description")
                   for it in items if it.get("source_job_id") and it.get("description")}
        if not updates:
            return
        with self.app.app_context():
            try:
                jobs = Job.query.filter(Job.source_job_id.in_(list(updates))).all()
                for job in jobs:
                    desc = updates.get(job.source_job_id)
                    if desc and not job.description:
                        job.description = desc
                db.session.commit()
            except Exception:
                db.session.rollback()
                logger.exception("保存职位描述失败")

    def _new_tab(self, driver):
        """打开全新标签页并切换过去，返回其句柄；会话失效时抛 DriverSessionError"""
        try:
            driver.switch_to.new_window("tab")
            return driver.current_window_handle
        except Exception as e:
            if _is_dead_session(e):
                raise DriverSessionError(str(e)[:200])
            raise

    def _close_tab(self, driver, handle):
        """关闭指定标签页（避免关掉最后一个标签页导致会话消亡）；失败静默"""
        if not handle or driver is None:
            return
        try:
            if driver.current_window_handle != handle:
                driver.switch_to.window(handle)
            driver.close()
            handles = driver.window_handles
            if handles:
                driver.switch_to.window(handles[0])
        except Exception:
            pass

    def _load_list(self, driver, tab, url, kw, page, cfg):
        """加载列表页并等待 .joblist-item 出现；返回卡片列表（加载失败返回空列表）。
        会话失效（标签页崩溃/会话丢失）时抛 DriverSessionError，由 worker 重建驱动重试。
        """
        driver.switch_to.window(tab)
        for attempt in range(3):
            if self.stop_event.is_set():
                return []
            try:
                driver.set_page_load_timeout(25)
                driver.get(url)
            except Exception as e:
                if _is_dead_session(e):
                    raise DriverSessionError(str(e)[:200])
            if self.stop_event.is_set():
                return []
            time.sleep(3)
            try:
                cards = driver.find_elements("css selector", cfg["CRAWL_SELECTORS"]["job_list"])
            except Exception as e:
                if _is_dead_session(e):
                    raise DriverSessionError(str(e)[:200])
                cards = []
            if cards:
                return cards
            self._log("warn", f"[{kw}第{page}页] 列表未加载({attempt + 1}/3)，重试", kw, page)
            if not self.stop_event.is_set():
                time.sleep(2)
        return []

    def _fetch_detail(self, driver, link, cfg):
        """在当前标签页直接导航详情页抓取职位描述。
        不使用新标签页：51job 的 WAF 会检测同一浏览器进程内"列表页→新标签页详情"
        的多标签页访问，导致详情标签页崩溃/空白（tab crashed）；在当前标签页顺序
        导航可稳定获取描述。详情页为 JS 渲染，采用轮询等待描述出现；
        WAF 拦截跳转空页时直接放弃。
        """
        try:
            try:
                driver.set_page_load_timeout(10)
                driver.get(link)
            except Exception as e:
                if _is_dead_session(e):
                    raise DriverSessionError(str(e)[:200])
            # 轮询等待详情内容出现（WAF 挑战完成后跳转/渲染真实内容）
            # 临时关闭隐式等待，避免每次 find_elements 最长等待拖慢轮询
            try:
                driver.implicitly_wait(0)
            except Exception:
                pass
            desc = ""
            deadline = time.time() + 12
            while time.time() < deadline:
                if self.stop_event.is_set():
                    break
                time.sleep(2)
                try:
                    # WAF 拦截时页面会被跳转到空页(data:, / about:blank)，直接放弃
                    cur = driver.current_url or ""
                    if not cur or cur.startswith("data:") or cur == "about:blank":
                        break
                    for css in cfg["CRAWL_DETAIL_SELECTORS"]["job_desc"].split(","):
                        css = css.strip()
                        if not css:
                            continue
                        els = driver.find_elements("css selector", css)
                        if els:
                            text = "\n".join(e.text.strip() for e in els if e.text.strip())
                            if text:
                                desc = text
                                break
                except Exception as e:
                    if _is_dead_session(e):
                        raise DriverSessionError(str(e)[:200])
                    break
                if desc:
                    break
            return desc[:10000]
        except Exception as e:
            if _is_dead_session(e):
                raise
            return ""

    def _resolve_captcha(self, driver, proxy_pool, kw, city, page, cfg):
        """处理验证码。返回 (driver, 是否继续解析本页)；
        driver 为 None 时表示旧驱动已销毁，需由 worker 重建。
        无头模式下会弹出有头窗口，交由用户人工完成验证。
        """
        self._bump("captcha")
        self._log("warn", f"[{kw}第{page}页] 命中验证码，进入处理", kw, page)

        if self.headless:
            # 无头窗口用户看不到、也处理不了验证码 → 弹出有头窗口
            self.headless = False  # 本任务后续保持有头，便于继续人工处理
            self._log("warn",
                      f"[{kw}第{page}页] 当前为无头模式，已弹出 Chrome 窗口，"
                      f"请在弹出的窗口中完成验证码验证（最多等待 {cfg['CRAWL_CAPTCHA_WAIT']} 秒）",
                      kw, page)
            close_driver(driver)
            proxy = proxy_pool.get() if not proxy_pool.is_empty() else None
            driver = create_driver(ua=get_random_ua(), proxy=proxy, headless=False,
                                   engine=cfg["CRAWL_BROWSER"],
                                   browser_path=cfg["CRAWL_BROWSER_PATH"],
                                   driver_path=cfg["CRAWL_DRIVER_PATH"],
                                   attach_port=self.attach_port)
            driver.set_page_load_timeout(30)
            try:
                driver.get(self._build_url(cfg, kw, page, city))
            except Exception:
                pass
            time.sleep(2)

        result = handle_captcha(driver, cfg["CRAWL_CAPTCHA_WAIT"], proxy_pool,
                                callback=lambda _t: self._bump("captcha"))
        if result == "rotate":
            self._log("warn", f"[{kw}第{page}页] 轮换代理后重试", kw, page)
            return None, False
        if result is False:
            self._log("warn", f"[{kw}第{page}页] 验证码持续拦截，跳过本页", kw, page)
            return driver, False
        self._log("info", f"[{kw}第{page}页] 验证码已解除，继续解析", kw, page)
        return driver, True

    def _process_mock_page(self, kw, city, page):
        from app.services.crawler import mock_data
        self.current_item = [kw, page]
        try:
            items = mock_data.generate_jobs(kw, pages=1, city=city)
            for it in items:
                it["source_job_id"] = f"mock-p{page}-{it['source_job_id']}"
            n = save_jobs(self.app, items, source="mock")
            self._bump("found", len(items))
            self._bump("saved", n)
            self._log("info", f"[mock {kw}第{page}页] 生成{len(items)}条，保存{n}条", kw, page)
        finally:
            if self.current_item == [kw, page]:
                self.current_item = None
        time.sleep(0.5)

    def _monitor(self, workers):
        for t in workers:
            t.join()
        self._finish()

    def _finish(self):
        self.running = False
        self.current_item = None
        from app.services.crawler import mock_data
        with self.app.app_context():
            task = db.session.get(CrawlTask, self.current_task_id)
            if not task or task.status != "running":
                return
            task.total_found = self.stats["found"]
            task.total_saved = self.stats["saved"]
            task.captcha_hits = self.stats["captcha"]

            # auto 模式：真实爬取无产出时降级为模拟数据
            # （用户明确选择 real 时不注入模拟数据，避免"假真实"结果误导）
            if (self.mode_used == "auto" and task.total_saved == 0
                    and self.app.config["CRAWL_MODE"] != "real"):
                degraded_saved = 0
                for kw in self.current_keywords:
                    items = mock_data.generate_jobs(kw, pages=min(task.pages, 3),
                                                    city=task.city or None)
                    n = save_jobs(self.app, items, source="mock")
                    degraded_saved += n
                    record_log(self.app, task.id, "warn",
                               f"真实爬取无产出，已降级为模拟数据[{kw} 保存{n}条]", kw)
                task.total_found += degraded_saved
                task.total_saved += degraded_saved
                task.mode = "auto(degraded)"
                task.message = "真实爬取未产出，已自动降级为模拟数据"
            elif task.total_saved == 0:
                task.message = "真实爬取未产出（站点无数据或页面被拦截）"
            else:
                task.message = "爬取完成"
            task.status = "done"
            task.finished_at = datetime.utcnow()
            db.session.commit()
        logger.info("爬虫任务#%s 结束，共保存 %s 条", self.current_task_id, self.stats["saved"])

    # ---------------- 辅助 ----------------
    def _bump(self, key, n=1):
        with self.stats_lock:
            self.stats[key] = self.stats.get(key, 0) + n

    def _log(self, level, message, keyword=None, page=None):
        record_log(self.app, self.current_task_id, level, message, keyword, page)


crawl_manager = CrawlManager()
