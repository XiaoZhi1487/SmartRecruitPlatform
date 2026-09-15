"""生成答辩文档：痛点·创新点·技术路线.docx"""
import os
import docx
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH

OUT_DIR = r"e:\Allcode\毕业设计\答辩文档"


def set_font(run, size=12, bold=False, name="宋体", color=None):
    run.font.name = "Calibri"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), name)
    run.font.size = Pt(size)
    run.font.bold = bold
    if color:
        run.font.color.rgb = RGBColor(*color)


def add_heading(doc, text, level=1):
    p = doc.add_heading("", level=level)
    r = p.add_run(text)
    for run in p.runs:
        run.font.name = "Calibri"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        run.font.bold = True
    return p


def add_para(doc, text, bold=False, indent=True, size=12):
    p = doc.add_paragraph()
    if indent:
        p.paragraph_format.first_line_indent = Pt(24)
    r = p.add_run(text)
    set_font(r, size=size, bold=bold)
    return p


def add_li(doc, text, level=0):
    p = doc.add_paragraph()
    p.style = doc.styles["List Bullet"] if level == 0 else doc.styles["List Bullet 2"]
    r = p.add_run(text)
    set_font(r, size=12)
    return p


def make_heading_block(doc, level, title, color):
    p = doc.add_heading("", level=level)
    r = p.add_run(title)
    for run in p.runs:
        run.font.name = "Calibri"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "黑体")
        run.font.bold = True
        run.font.size = Pt({1: 18, 2: 15}.get(level, 14))
    # top border accent
    return p


doc = Document()
u = doc.sections[0]
u.top_margin, u.bottom_margin = Cm(2.5), Cm(2.5)
u.left_margin, u.right_margin = Cm(3), Cm(3)

t = doc.add_paragraph()
t.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = t.add_run("智聘通智能招聘平台\n痛点 · 创新点 · 技术路线")
set_font(r, size=28, bold=True, name="黑体")
s = doc.add_paragraph()
s.alignment = WD_ALIGN_PARAGRAPH.CENTER
r = s.add_run("毕业设计答辩专项文档")
set_font(r, size=14)
doc.add_page_break()

# ============ 说明 ============
add_heading(doc, "0 使用说明", 1)
add_para(doc, "本页围绕答辩中常被老师追问的三个核心问题展开：痛点（为什么做）、创新点（比别人强在哪）、技术路线（怎么做出来）。每部分均采用“结论一句话 + 支撑论据若干条”的结构，方便临场口头展开。建议先看每部分首行的结论句，被抓问后再展开说明要点。")

# ============ 一、痛点 ============
make_heading_block(doc, 1, "一、痛点问题（Why：为什么做这个项目）", None)
add_para(doc, "一句话结论：传统求职流程中“信息分散、筛选低效、缺乏个性化与专业指导”三重痛点，本系统用采集 + AI 一站式解决。", bold=True)

add_heading(doc, "1.1 行业痛点", 2)
add_li(doc, "信息分散：职位分布在前程无忧、BOSS 直聘等多家平台，求职者需多平台切换、人工比对，成本高昂。")
add_li(doc, "字段异构：各平台薪资（万/年、千/月、元/天）、技能、经验口径不统一，难以量化横向比较。")
add_li(doc, "供给过剩：海量职位导致“信息过载”，普通求职者缺乏有效筛选手段。")

add_heading(doc, "1.2 求职者个体痛点", 2)
add_li(doc, "缺少个性化：没有依据自身技能、期望薪资、城市、经验、学历画像的精准推荐，投递多是盲目。")
add_li(doc, "缺乏专业指导：简历如何优化、目标岗位的核心技能是什么、成长路径如何，普通求职者无人可问。")
add_li(doc, "决策不透明：看不到岗位薪资分布、学历/地区/经验的影响，择业决策缺少数据支撑。")

add_heading(doc, "1.3 痛点如何在系统中落地", 2)
add_li(doc, "信息分散 → 多线程爬虫自动聚合 51job 职位数据，统一入库。")
add_li(doc, "字段异构 → 数据处理阶段对薪资/经验/学历做归一化（统一 K/月）。")
add_li(doc, "个性化缺失 → 五维度加权匹配推荐算法，按用户画像打分排序。")
add_li(doc, "专业指导缺失 → DeepSeek 集成：岗位深度解读、简历 AI 优化、AI 职业助手。")
add_li(doc, "决策不透明 → 市场数据分析页面用图表 + AI 结论还原就业趋势。")

# ============ 二、创新点 ============
make_heading_block(doc, 1, "二、创新点（Diff：比别人强在哪）", None)
add_para(doc, "一句话结论：本系统的创新集中在“AI 与业务深度融合 + 统一智能匹配框架 + 工程化爬虫体系 + 数据驱动可视化”四个方面。", bold=True)

add_heading(doc, "2.1 创新点一：AI 大模型与业务闭环的深度融合", 2)
add_li(doc, "不满足于“通用聊天”，而是把 DeepSeek 嵌入具体业务：岗位深度解读、简历 AI 优化、市场数据分析结论。")
add_li(doc, "自动归档：解读与优化结果自动写入“AI 职业助手”新对话（user+assistant 两条消息），形成“可追溯、可追问”的知识闭环——界面零改动即可复用多轮对话能力追问。")
add_li(doc, "工程化容错：AI 服务统一封装系统提示注入、重试、JSON 解析与模板兜底，保证不稳定网络下体验不中断。")

add_heading(doc, "2.2 创新点二：一套评分框架，双端智能匹配", 2)
add_li(doc, "将用户画像与职位属性映射到技能/薪资/地点/经验/学历五维空间。")
add_li(doc, "求职端：按画像给职位打分，返回 Top 量与匹配原因。")
add_li(doc, "企业端：反转评分方向复用同一框架，实现“候选人对岗位”的匹配。")
add_li(doc, "价值：逻辑统一、单一数据源、易于扩展新维度，是“模型复用”的典型设计。")

add_heading(doc, "2.3 创新点三：兼顾真实与稳定的工程化爬虫体系", 2)
add_li(doc, "双数据源策略：桌面 SPA 列表页按城市精确爬取 + 手机版详情页免验证码读取。")
add_li(doc, "CDP 附加模式：复用本地浏览器登录态，避免重复登录、提高采集成功率。")
add_li(doc, "完整抗反爬：UA 随机、IP 代理池、请求间隔、验证码人工处理与超时。")
add_li(doc, "健壮性：结构变更监测 + 无产出自动降级模拟数据，演示流程永不中断。")

add_heading(doc, "2.4 创新点四：数据驱动招聘决策的可视化", 2)
add_li(doc, "薪资异类口径归一化为 K/月，支持跨城市/学历/岗位的公平比较。")
add_li(doc, "多维度图表（需求排行、平均薪资、学历影响、区域排行等）+ AI 生成自然语言结论，兼顾直观与专业。")

# ============ 三、技术路线 ============
make_heading_block(doc, 1, "三、技术路线（How：怎么做 / 链路图）", None)
add_para(doc, "一句话结论：以前后端分离为骨架，形成“数据采集 → 数据清洗归一化 → 画像建模 → 智能匹配 → AI 增强 + 可视化”的完整技术链路。", bold=True)

add_heading(doc, "3.1 总体技术选型", 2)
add_li(doc, "后端：Python 3.9+ / Flask 3 / Flask-SQLAlchemy / Flask-JWT-Extended / Flask-Bcrypt / APScheduler。")
add_li(doc, "爬虫：Selenium（Edge，内置 msedgedriver），支持 CDP 附加、代理池、验证码处理。")
add_li(doc, "AI：DeepSeek Chat Completions API（统一 ai_service 封装）。")
add_li(doc, "前端：Vue 3 / Vite / Element Plus / Pinia / Vue Router / ECharts。")
add_li(doc, "数据库：SQLite（单机演示友好，实体关系清晰）。")

add_heading(doc, "3.2 端到端技术链路（建议口述）", 2)
add_li(doc, "① 数据采集：APScheduler 每 6 小时触发，Selenium 多线程爬取 51job → 抗反爬（UA/代理/间隔/验证码）→ 入库 Job。")
add_li(doc, "② 数据处理：抽取清洗薪资/经验/学历 → 归一化（万/年÷12、元/天×22…统一 K/月）→ 技能标签 JSON。")
add_li(doc, "③ 画像建模：用户注册后维护技能、期望薪资、城市、经验、学历（UserProfile + Skill）。")
add_li(doc, "④ 智能匹配：recommend_service 对职位五维加权打分 → Top 排序 + 原因文本；企业端反转复用。")
add_li(doc, "⑤ AI 增强：ai_service 调 DeepSeek 生成解读/优化/结论 → chat_service 自动归档为职业助手新对话。")
add_li(doc, "⑥ 数据可视化：analysis_service 多维度聚合 → ECharts 图表 + AI 结论 → 前端展示。")
add_li(doc, "⑦ 安全与权限：JWT + 角色守卫（user/enterprise/admin）+ BCrypt 密码 + 敏感字段加密。")
add_li(doc, "⑧ 测试与部署：pytest 28 例 + 前端 build + 联调验证。")

add_heading(doc, "3.3 技术路线为何这样选", 2)
add_li(doc, "选 Flask 而非 Django：轻量、上手快、适合毕业设计规模与快速定制。")
add_li(doc, "选 Vue3 + Element Plus：组件化 + 生态成熟，契合前后端分离与现代 UI 需求。")
add_li(doc, "选 SQLite：单机演示无需额外数据库服务，降低部署与答辩环境依赖。")
add_li(doc, "选 DeepSeek：国产大模型、API 成本低、支持 JSON 结构化输出，契合教学场景。")

add_heading(doc, "3.4 面对“如果时间更多 / 生产环境会怎么改”的追问", 2)
add_li(doc, "数据库：SQLite → PostgreSQL，支持并发与高可用。")
add_li(doc, "部署：开发服务器 → Gunicorn/Waitress + Nginx；敏感密钥移入安全配置（KMS/环境变量）。")
add_li(doc, "爬虫：单机 Selenium → 分布式采集 + 更完善的异常重试与队列削峰。")
add_li(doc, "推荐：可用协同过滤 / 基于向量化 Embedding 的语义召回，进一步提升推荐质量。")

os.makedirs(OUT_DIR, exist_ok=True)
doc.save(os.path.join(OUT_DIR, "痛点-创新点-技术路线.docx"))
print("saved 痛点-创新点-技术路线.docx")