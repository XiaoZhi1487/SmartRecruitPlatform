# -*- coding: utf-8 -*-
"""生成毕业设计答辩 PPT：智聘通智能招聘平台.pptx"""
import os
import math
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
from pptx.oxml.ns import qn

OUT = r"e:\Allcode\毕业设计\答辩PPT\智聘通_答辩PPT.pptx"
os.makedirs(os.path.dirname(OUT), exist_ok=True)

# ---------- 主题色 ----------
DARK = RGBColor(0x1E, 0x29, 0x3B)   # 深蓝标题
BLUE = RGBColor(0x25, 0x63, 0xEB)      # 主蓝
LBLUE = RGBColor(0xDB, 0xEA, 0xFE)  # 浅蓝
GRAY = RGBColor(0x47, 0x55, 0x69)   # 正文灰
LIGHT = RGBColor(0xF1, 0xF5, 0xF9)  # 浅底
GREEN = RGBColor(0x10, 0xB9, 0x81)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)
PURPLE = RGBColor(0x8B, 0x5C, 0xF6)

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
W, H = prs.slide_width, prs.slide_height
BLANK = prs.slide_layouts[6]


def set_cn(run, size, bold=False, color=DARK, name="微软雅黑"):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    run.font.name = name
    r = run._r
    rPr = r.get_or_add_rPr()
    ea = rPr.find(qn('a:ea'))
    if ea is None:
        ea = rPr.makeelement(qn('a:ea'), {})
        rPr.append(ea)
    ea.set('typeface', name)


def add_text(slide, left, top, w, h, lines, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    """lines: list of (text, size, bold, color) or str"""
    tb = slide.shapes.add_textbox(left, top, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.05)
    tf.margin_top = tf.margin_bottom = Inches(0.02)
    first = True
    for ln in lines:
        if isinstance(ln, str):
            ln = (ln, 16, False, GRAY)
        text, size, bold, color = ln
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.alignment = align
        p.space_after = Pt(4)
        r = p.add_run()
        r.text = text
        set_cn(r, size, bold, color)
    return tb


def add_rect(slide, l, t, w, h, fill, line=None, shape=MSO_SHAPE.RECTANGLE):
    sp = slide.shapes.add_shape(shape, l, t, w, h)
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(1)
    sp.shadow.inherit = False
    return sp


def header(slide, title, subtitle=None):
    add_rect(slide, 0, 0, W, Inches(1.0), BLUE)
    add_rect(slide, 0, Inches(1.0), W, Pt(3), ORANGE)
    add_text(slide, Inches(0.6), Inches(0.16), Inches(11), Inches(0.6),
             [(title, 26, True, WHITE)])
    if subtitle:
        add_text(slide, Inches(0.6), Inches(0.72), Inches(12), Inches(0.3),
                 [(subtitle, 13, False, WHITE)])
    add_rect(slide, 0, H - Inches(0.4), W, Inches(0.4), DARK)
    add_text(slide, Inches(0.4), H - Inches(0.42), Inches(12), Inches(0.4),
             [("智聘通 · 智能招聘平台 | 毕业设计答辩", 11, False, WHITE)])


def section_slide(title, en, bullets):
    s = prs.slides.add_slide(BLANK)
    add_rect(s, 0, 0, W, H, LIGHT)
    add_rect(s, 0, 0, Inches(4.6), H, DARK)
    add_text(s, Inches(0.5), Inches(2.4), Inches(3.6), Inches(2),
             [(en, 18, True, ORANGE)], align=PP_ALIGN.LEFT)
    add_text(s, Inches(0.5), Inches(2.85), Inches(3.6), Inches(2),
             [("智聘通", 15, False, LIGHT)])
    # big number
    add_text(s, Inches(0.5), Inches(4.7), Inches(3.6), Inches(1.6),
             [("0" + title[0] if False else title, 60, True, RGBColor(0x2E, 0x3A, 0x4C))])
    for i, b in enumerate(bullets):
        add_text(s, Inches(5.3), Inches(1.5 + i * 1.3), Inches(7.3), Inches(1.1),
                 [(b, 20, True, DARK)], anchor=MSO_ANCHOR.MIDDLE)
    return s


# ---------------- 封面 ----------------
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, W, H, DARK)
add_rect(s, Inches(0.9), Inches(1.3), Inches(11.5), Pt(3), ORANGE)
add_text(s, Inches(1.0), Inches(1.6), Inches(11), Inches(1.2),
         [("智聘通 智能招聘平台", 48, True, WHITE)], align=PP_ALIGN.CENTER)
add_text(s, Inches(1.0), Inches(3.0), Inches(11), Inches(0.7),
         [("基于数据爬取 + DeepSeek 大模型的一站式求职招聘平台", 20, False, LBLUE)],
         align=PP_ALIGN.CENTER)
add_text(s, Inches(1.0), Inches(5.2), Inches(11), Inches(1.2),
         [("毕业设计答辩 | 汇报人：XXX | 指导教师：XXX", 16, False, GRAY),
          ("技术栈：Python · Flask · Vue3 · ECharts · Selenium · DeepSeek", 13, False, RGBColor(0x94, 0xA3, 0xB8))],
         align=PP_ALIGN.CENTER)

# ---------------- 目录 ----------------
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, W, H, LIGHT)
header(s, "目录", "CONTENTS")
items = ["1  项目概述", "2  技术栈介绍", "3  项目总体架构", "4  核心功能实现",
         "5  数据分析与可视化成果", "6  项目难点与解决方案", "7  项目总结与展望"]
cols, rows = 1, len(items)
for i, it in enumerate(items):
    c, r_ = i % 1, i // 1
    add_text(s, Inches(1.2 + c * 6), Inches(1.6 + r_ * 0.95), Inches(5), Inches(0.7),
             [(it, 18, True, DARK)], anchor=MSO_ANCHOR.MIDDLE)
    add_rect(s, Inches(0.8 + c * 6), Inches(1.6 + r_ * 0.95), Inches(0.22), Inches(0.22), BLUE, shape=MSO_SHAPE.OVAL)

# ================= 1 项目概述 =================
section_slide("项目概述", "PROJECT OVERVIEW",
              ["数据洪流下的求职痛点", "一站式采集 + AI 匹配闭环", "让求职决策有据可依"])

s = prs.slides.add_slide(BLANK)
header(s, "1.1 项目背景与应用场景", "背景 · 场景")
add_text(s, Inches(0.6), Inches(1.3), Inches(12), Inches(0.5),
         [("项目背景", 18, True, BLUE)])
add_li = ["招聘信息分散在多个平台，求职者需频繁切换、人工比对，效率低；",
          "薪资/技能/经验等字段口径不一（万/年、千/月、元/天），难以量化比较；",
          "海量岗位造成信息过载，普通求职者缺少个性化筛选与专业指导；",
          "近年 AI 大模型（DeepSeek）能力成熟，为智能化求职提供了可行性。"]
for i, t in enumerate(add_li):
    add_rect(s, Inches(0.8), Inches(1.9 + i * 0.62), Inches(0.16), Inches(0.16), BLUE, shape=MSO_SHAPE.OVAL)
    add_text(s, Inches(1.1), Inches(1.85 + i * 0.62), Inches(11.5), Inches(0.6),
             [(t, 15, False, GRAY)], anchor=MSO_ANCHOR.MIDDLE)
add_text(s, Inches(0.6), Inches(4.4), Inches(12), Inches(0.5), [("应用场景", 18, True, BLUE)])
add_text(s, Inches(1.1), Inches(4.9), Inches(11.5), Inches(1.8),
         [("求职者：浏览/收藏职位、画像建模、智能推荐、AI 职业助手多轮提问、简历优化；",
           15, False, GRAY),
          ("企业：按岗位发布并获取候选人匹配（嵌套 reverse 评分）；",
           15, False, GRAY),
          ("管理员：用户管理、爬虫任务监控与数据维护。",
           15, False, GRAY)])

s = prs.slides.add_slide(BLANK)
header(s, "1.2 研究意义", "价值")
add_text(s, Inches(0.6), Inches(1.35), Inches(12), Inches(4.8),
         [("▍ 求职者：", 18, True, BLUE),
          ("高效获取与自身画像匹配的职位，减少盲目投递；", 16, False, GRAY),
          ("获得岗位深度解读与简历 AI 优化，提升命中率。", 16, False, GRAY),
          ("▍ 数据价值：", 18, True, GREEN),
          ("将海量异构招聘数据归一化（统一 K/月），量化薪资/学历/地区影响，还原就业趋势。", 16, False, GRAY),
          ("▍ 技术意义：", 18, True, ORANGE),
          ("完整落地“数据采集→清洗→建模→匹配→AI 增强→可视化”工程链路，具备可扩展架构。", 16, False, GRAY),
          ("▍ 研究方法参考：", 18, True, PURPLE),
          ("本课题所建立的招聘信息采集、岗位画像建模与 AI 辅助求职方法，可为同类就业分析研究提供借鉴。", 16, False, GRAY)])

s = prs.slides.add_slide(BLANK)
header(s, "1.3 项目目标", "GOALS")
goals = [
    ("多源可靠的数据底座", "Selenium 多线程爬取 51job，抗反爬 + 自动降级，构建干净可用数据库"),
    ("个性化智能匹配", "技能/薪资/地点/经验/学历五维加权评分，求职端推荐 + 企业端候选匹配"),
    ("AI 深度辅助", "DeepSeek 集成岗位解读、简历优化、职业助手，并自动归档形成可追问闭环"),
    ("数据驱动可视化", "ECharts 多维图表 + AI 结论，直观呈现就业市场趋势"),
]
for i, (t, d) in enumerate(goals):
    c, r_ = i % 2, i // 2
    l, tp = Inches(0.7 + c * 6.2), Inches(1.5 + r_ * 2.5)
    add_rect(s, l, tp, Inches(5.9), Inches(2.1), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, l + Inches(0.3), tp + Inches(0.25), Inches(5.3), Inches(0.5),
             [(t, 18, True, BLUE)])
    add_text(s, l + Inches(0.3), tp + Inches(0.9), Inches(5.3), Inches(1.0),
             [(d, 14, False, GRAY)])

# ================= 2 技术栈 =================
section_slide("技术栈介绍", "TECH STACK",
              ["语言 · 框架 · 工具 · 数据库", "AI 大模型能力接入", "前后端分离架构"])

s = prs.slides.add_slide(BLANK)
header(s, "2.1 技术栈一览", "LANGUAGE · FRAMEWORK · TOOL · DB")
rows = [
    ("后端语言", "Python 3.9+", "Web 框架", "Flask 3 / Flask-SQLAlchemy / JWT / Bcrypt", BLUE),
    ("爬虫工具", "Selenium + Edge WebDriver", "调度", "APScheduler（每 6h 定时爬取）", GREEN),
    ("前端框架", "Vue 3 + Vite", "UI / 图表", "Element Plus / ECharts", ORANGE),
    ("状态 / 路由", "Pinia / Vue Router", "HTTP", "Axios", PURPLE),
    ("数据库", "SQLite", "AI 模型", "DeepSeek Chat Completions", RGBColor(0x0E, 0x7A, 0x0D)),
]
top = 1.4
for name, a, name2, b, col in rows:
    add_rect(s, Inches(0.6), Inches(top), Inches(1.9), Inches(0.82), col, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, Inches(0.6), Inches(top + 0.15), Inches(1.9), Inches(0.5),
             [(name, 14, True, WHITE)], align=PP_ALIGN.CENTER)
    add_text(s, Inches(2.7), Inches(top + 0.1), Inches(4.7), Inches(0.62),
             [(a, 14, True, DARK)], anchor=MSO_ANCHOR.MIDDLE)
    add_rect(s, Inches(7.5), Inches(top), Inches(1.9), Inches(0.82), LBLUE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, Inches(7.5), Inches(top + 0.15), Inches(1.9), Inches(0.5),
             [(name2, 14, True, BLUE)], align=PP_ALIGN.CENTER)
    add_text(s, Inches(9.6), Inches(top + 0.1), Inches(3.3), Inches(0.62),
             [(b, 14, False, GRAY)], anchor=MSO_ANCHOR.MIDDLE)
    top += 1.05
add_rect(s, Inches(0.6), Inches(6.6), Inches(12.1), Inches(0.5), LIGHT)
add_text(s, Inches(0.8), Inches(6.66), Inches(12), Inches(0.4),
         [("选型理由：Flask 轻量易定制 · Vue3+Element 生态成熟 · SQLite 单机演示友好 · DeepSeek 成本低且支持 JSON 结构化输出", 13, True, GRAY)])

# ================= 3 总体架构 =================
section_slide("项目总体架构", "SYSTEM ARCHITECTURE",
              ["分层式整体设计", "数据→采集→处理→分析→可视化→展示", "功能模块与业务闭环"])

s = prs.slides.add_slide(BLANK)
header(s, "3.1 数据流转总体架构", "数据采集 → 处理 → 分析 → 可视化")
flow = [
    ("数据来源", "前程无忧 51job", LBLUE, BLUE),
    ("数据采集", "Selenium 多线程 · 抗反爬 · 定时任务", BLUE, WHITE),
    ("数据处理", "清洗归一化（薪资→K/月）· 画像入库", PURPLE, WHITE),
    ("数据分析", "五维匹配 · 多维聚合 · DeepSeek 推理", GREEN, WHITE),
    ("数据可视化", "ECharts 图表 · AI 结论", ORANGE, WHITE),
    ("系统展示", "职位大厅 · 智能推荐 · 市场分析", RGBColor(0xE0, 0x7F, 0x1E), WHITE),
]
for i, (t, d, fill, tcol) in enumerate(flow):
    l, w_ = Inches(0.75), Inches(2.0)
    tp = Inches(1.6 + i * 0.92)
    add_rect(s, l, tp, w_, Inches(0.72), fill, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, l, tp + 0.08, w_, Inches(0.4), [(t, 14, True, tcol)], align=PP_ALIGN.CENTER)
    add_rect(s, Inches(0.55), tp + Inches(0.16), Inches(0.18), Inches(0.4), ORANGE)
    add_text(s, Inches(3.0), tp + 0.03, Inches(9.2), Inches(0.66),
             [(d, 14, False, GRAY)], anchor=MSO_ANCHOR.MIDDLE)
    if i < len(flow) - 1:
        add_text(s, Inches(1.15), tp + 0.6, Inches(1), Inches(0.3), [("▼", 14, False, ORANGE)])

s = prs.slides.add_slide(BLANK)
header(s, "3.2 模块化整体设计", "整体 · 功能模块 · 业务流程")
add_rect(s, Inches(0.6), Inches(1.35), Inches(1.8), Inches(0.6), DARK, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
add_text(s, Inches(0.6), Inches(1.44), Inches(1.8), Inches(0.4), [("前端层 Vue3", 13, True, WHITE)], align=PP_ALIGN.CENTER)
mods = {"求职端": ["职位大厅", "智能推荐", "简历管理", "AI职业助手", "市场分析", "我的收藏"],
        "企业端": ["职位管理", "候选人匹配"], "管理端": ["用户管理", "爬虫控制台"]}
x = 2.7
for label, items in mods.items():
    add_rect(s, Inches(x), Inches(1.25), Inches(3.05), Inches(0.6), BLUE if label != "管理端" else ORANGE, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, Inches(x), Inches(1.33), Inches(3.05), Inches(0.4), [(label, 14, True, WHITE)], align=PP_ALIGN.CENTER)
    for j, m in enumerate(items):
        add_rect(s, Inches(x), Inches(1.9 + j * 0.6), Inches(3.05), Inches(0.5), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
        add_text(s, Inches(x), Inches(1.96 + j * 0.6), Inches(3.05), Inches(0.4), [(m, 13, False, DARK)], align=PP_ALIGN.CENTER)
    x += 3.3
add_text(s, Inches(0.6), Inches(5.65), Inches(12), Inches(1.4),
         [("业务闭环：登录 → 简历/画像建模 → 智能推荐 → AI 解读（自动归档职业助手）→ 投递决策 → 市场分析复盘就业趋势",
           14, True, GRAY)])

# ================= 4 核心功能 =================
section_slide("核心功能实现", "CORE FEATURES",
              ["采集 → 清洗 → 分析 → 展示", "五维推荐算法", "AI 自动归档闭环"])

s = prs.slides.add_slide(BLANK)
header(s, "4.1 数据处理流程", "采集 → 清洗 → 模型 → 可视化")
steps = [
    ("数据采集模块", "Selenium 加载 SPA 列表页提取 .joblist-item 卡片；SPA+手机版双源；CDP 附加复用登录态；UA/代理/间隔/验证码"),
    ("清洗模块", "解析薪资文本 → 归一化 K/月（万÷10、万/年÷12、元/天×22）；技能标签 JSON；城市代码映射 28 城"),
    ("分析模型", "五维加权匹配评分（权重见右图）；市场数据多维聚合；DeepSeek 生成解读/结论"),
    ("可视化展示", "ECharts 柱/饼/横向条形；岗位需求、平均薪资、学历影响、学历分布、地区排行 + AI 结论"),
]
for i, (t, d) in enumerate(steps):
    c, r_ = i % 2, i // 2
    l, tp = Inches(0.6 + c * 6.15), Inches(1.4 + r_ * 2.6)
    add_rect(s, l, tp, Inches(5.9), Inches(2.3), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_rect(s, l, tp, Inches(0.14), Inches(2.3), BLUE if i % 2 == 0 else ORANGE)
    add_text(s, l + Inches(0.4), tp + Inches(0.2), Inches(5.2), Inches(0.5),
             [(t, 17, True, BLUE)])
    add_text(s, l + Inches(0.4), tp + Inches(0.8), Inches(5.2), Inches(1.4),
             [(d, 13, False, GRAY)])
    if i < 3:
        add_text(s, l + Inches(5.7), tp + Inches(0.9), Inches(0.6), Inches(0.4), [("→", 22, True, ORANGE)])

s = prs.slides.add_slide(BLANK)
header(s, "4.2 核心算法：五维加权匹配", "技能 0.40 · 薪资 0.20 · 地点 0.15 · 经验 0.15 · 学历 0.10")
weights = [("技能匹配", 0.40, "与职位标签/标题关键词求交集", BLUE),
           ("薪资匹配", 0.20, "期望区间 × 职位区间 重叠率", GREEN),
           ("地点匹配", 0.15, "城市一致判定", ORANGE),
           ("经验匹配", 0.15, "年限档位差缩放", PURPLE),
           ("学历匹配", 0.10, "学历等级差缩放", RGBColor(0x0E, 0x7A, 0x0D))]
top = 1.5
for name, w, desc, col in weights:
    add_rect(s, Inches(0.7), Inches(top), Inches(1.6), Inches(0.62), col, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, Inches(0.7), Inches(top + 0.1), Inches(1.6), Inches(0.4), [(name, 14, True, WHITE)], align=PP_ALIGN.CENTER)
    # bar
    add_rect(s, Inches(2.6), Inches(top + 0.14), Inches(6.2), Inches(0.34), LIGHT)
    add_rect(s, Inches(2.6), Inches(top + 0.14), Inches(int(6.2 * w)), Inches(0.34), col)
    add_text(s, Inches(2.7), Inches(top + 0.14), Inches(6), Inches(0.34),
             [(f"{int(w*100)}%", 12, True, WHITE)])
    add_text(s, Inches(9.1), Inches(top + 0.08), Inches(3.7), Inches(0.5),
             [(desc, 12, False, GRAY)], anchor=MSO_ANCHOR.MIDDLE)
    top += 0.8
add_text(s, Inches(0.7), Inches(5.7), Inches(12), Inches(1.2),
         [("综合分 = Σ(维度分 × 权重)，≥20 进入候选，按分降序返回 Top10 并生成匹配原因；",
           14, True, DARK),
          ("企业端复用同一框架，通过反转维度方向实现“候选人对岗位”匹配。",
           14, True, DARK)])

s = prs.slides.add_slide(BLANK)
header(s, "4.3 AI 能力与功能运行截图", "解读 → 优化 → 助手 → 自动归档")
add_rect(s, Inches(0.6), Inches(1.4), Inches(5.9), Inches(2.0), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
add_text(s, Inches(0.8), Inches(1.5), Inches(5.5), Inches(0.5), [("岗位深度解读", 16, True, BLUE)])
add_text(s, Inches(0.8), Inches(2.0), Inches(5.5), Inches(1.3),
         [("DeepSeek 输出：核心技能 / 适配建议 / 成长路径 / 面试提示；成功即自动新建职业助手对话（user+assistant 两条消息）。",
           13, False, GRAY)])
add_rect(s, Inches(6.8), Inches(1.4), Inches(5.9), Inches(2.0), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
add_text(s, Inches(7.0), Inches(1.5), Inches(5.5), Inches(0.5), [("简历 AI 优化", 16, True, GREEN)])
add_text(s, Inches(7.0), Inches(2.0), Inches(5.5), Inches(1.3),
         [("上传解析 → 输出评分 / 总体评价 / 分维度建议；结果自动归档，可在职业助手继续追问修改。",
           13, False, GRAY)])
add_rect(s, Inches(0.6), Inches(3.7), Inches(5.9), Inches(2.0), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
add_text(s, Inches(0.8), Inches(3.8), Inches(5.5), Inches(0.5), [("AI 职业助手多轮对话", 16, True, ORANGE)])
add_text(s, Inches(0.8), Inches(4.3), Inches(5.5), Inches(1.3),
         [("会话 + 消息双表结构，承载多轮上下文；自动归档的解读/优化记录可直接续聊。",
           13, False, GRAY)])
add_rect(s, Inches(6.8), Inches(3.7), Inches(5.9), Inches(2.0), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
add_text(s, Inches(7.0), Inches(3.8), Inches(5.5), Inches(0.5), [("认证与权限", 16, True, PURPLE)])
add_text(s, Inches(7.0), Inches(4.3), Inches(5.5), Inches(1.3),
         [("JWT 携带角色，BCrypt 加密密码，登录失败锁定，敏感字段加密存储，三端权限隔离。",
           13, False, GRAY)])
add_text(s, Inches(0.6), Inches(6.0), Inches(12), Inches(0.6),
         [("（提示：答辩时在此页或后续插入对应页面运行截图）", 13, False, RGBColor(0xB0, 0x1B, 0x1B))])

# ================= 5 数据分析 =================
section_slide("数据分析与可视化成果", "ANALYSIS & DASHBOARD",
              ["多维度 ECharts 图表", "AI 生成分析结论", "市场趋势 Dashboard"])

s = prs.slides.add_slide(BLANK)
header(s, "5.1 市场分析 Dashboard（ECharts）", "需求 · 薪资 · 学历 · 地区")
charts = [
    ("岗位需求排行（柱状图）", "各类别职位数量 Top，直观反映人才需求结构"),
    ("岗位平均薪资（横向条形）", "各类别月均薪资 Top5，突出重点高薪岗位"),
    ("学历对薪资影响（柱状图）", "学历→平均月薪正相关趋势（本科 16.6K / 硕士 28K）"),
    ("学历分布（饼图）", "各学历段岗位占比，刻画用人门槛"),
    ("地区平均薪资排行（柱状图）", "城市→月均薪资，识别高薪城市"),
    ("AI 分析结论", "DeepSeek 对以上聚合生成自然语言洞察"),
]
for i, (t, d) in enumerate(charts):
    c, r_ = i % 2, i // 2
    l, tp = Inches(0.6 + c * 6.15), Inches(1.35 + r_ * 1.9)
    add_rect(s, l, tp, Inches(5.9), Inches(1.6), LIGHT, shape=MSO_SHAPE.ROUNDED_RECTANGLE)
    add_text(s, l + Inches(0.3), tp + Inches(0.15), Inches(5.3), Inches(0.45),
             [(t, 15, True, BLUE)])
    add_text(s, l + Inches(0.3), tp + Inches(0.7), Inches(5.3), Inches(0.8),
             [(d, 12.5, False, GRAY)])

s = prs.slides.add_slide(BLANK)
header(s, "5.2 分析结论与示例数据", "数据背后的洞察")
add_text(s, Inches(0.6), Inches(1.35), Inches(12), Inches(0.5), [("AI 分析结论示例", 16, True, BLUE)])
concl = [
    "薪资与学历整体呈正相关：高中 9.5K → 大专 13.7K → 本科 16.6K → 硕士 28.0K，学历仍是薪酬重要分水岭；",
    "高薪岗位相对集中：产品 / Python / 人工智能等类别平均月薪领先，技术岗位具备薪资优势；",
    "地区差异显著：杭州 / 长沙 / 苏州 / 深圳等城市平均月薪居前列，就业决策需结合城市因素；",
    "岗位需求结构反映市场上开发、运营、销售等类别需求体量差异。",
]
for i, c in enumerate(concl):
    add_text(s, Inches(1.0), Inches(1.95 + i * 0.62), Inches(11.6), Inches(0.6),
             [("• " + c, 14, False, GRAY)])
add_text(s, Inches(0.6), Inches(4.6), Inches(12), Inches(0.5), [("薪资归一化口径（统一 K/月）", 16, True, GREEN)])
add_text(s, Inches(1.0), Inches(5.15), Inches(11.6), Inches(1.6),
         [("万/月 ×10 ｜ 千/月 原值 ｜ 万/年 ÷12 ｜ 元/天 ×22",
           15, True, DARK),
          ("（例：30-50万/年 → 25.0-41.7K；300-500元/天 → 5.5-9.2K）——保证跨岗位/城市/学历公平比较。",
           13, False, GRAY)])

# ================= 6 难点与方案 =================
section_slide("项目难点与解决方案", "CHALLENGES & SOLUTIONS",
              ["开发过程中遇到的问题", "针对性解决与优化", "量化前后对比"])

s = prs.slides.add_slide(BLANK)
header(s, "6.1 难点与解决方案", "问题 → 方案 → 结果")
data = [
    ("网站结构变化导致解析失败", "结构变更监测 + 多选择器兜底", "采集成功率稳定，快速感知异常"),
    ("真实模式无产出/被验证码拦截", "SPA+手机版双源、验证码人工处理、auto 自动降级模拟数据", "演示流程不中断，兼顾真实与稳定"),
    ("企业端与求职端匹配逻辑重复", "统一五维评分框架，反转维度复用", "代码复用、单一逻辑、易扩展新维度"),
    ("薪资口径不统一难统计", "统一归一化为 K/月（万/年÷12、元/天×22）", "可实现跨维度公平比较与统计"),
    ("登录态复用困难", "CDP 附加模式（--remote-debugging-port=9222）", "复用本地浏览器登录态，不重复开窗"),
    ("数据量大、聚合慢", "索引/精确查询 + 后端聚合 + 前端图表", "分析页响应快、可视化流畅"),
    ("页面展示不足、交互弱", "ECharts 多图表 + Element Plus 组件 + AI 结论", "Dashboard 直观、图文并茂"),
    ("DeepSeek 输出不稳定", "统一封装：系统提示注入 + 重试 + JSON 解析 + 模板兜底", "AI 返回稳定，符合业务结构"),
]
# table-like
head = ["遇到问题", "解决方案", "优化结果"]
colw = [4.6, 4.3, 3.2]
add_rect(s, Inches(0.5), Inches(1.35), Inches(12.3), Inches(0.5), BLUE)
x = 0.5
for cname, cw in zip(head, colw):
    add_text(s, Inches(x), Inches(1.42), Inches(cw), Inches(0.4),
             [(cname, 14, True, WHITE)], align=PP_ALIGN.CENTER)
    x += cw
top = 1.9
for i, (p, so, r) in enumerate(data):
    fill = WHITE if i % 2 == 0 else LIGHT
    add_rect(s, Inches(0.5), Inches(top), Inches(12.3), Inches(0.62), fill)
    x = 0.5
    for txt, cw in zip((p, so, r), colw):
        add_text(s, Inches(x + 0.1), Inches(top + 0.02), Inches(cw - 0.2), Inches(0.58),
                 [(txt, 12, False, DARK)], anchor=MSO_ANCHOR.MIDDLE)
        x += cw
    top += 0.62

# ================= 7 总结展望 =================
section_slide("项目总结与展望", "SUMMARY & OUTLOOK",
              ["完成情况与个人收获", "当前不足与思考", "后续优化方向"])

s = prs.slides.add_slide(BLANK)
header(s, "7.1 完成情况与个人收获", "SUMMARY")
add_text(s, Inches(0.6), Inches(1.3), Inches(12), Inches(0.5), [("完成情况", 17, True, BLUE)])
add_li = ["数据采集：多线程爬虫 + 定时任务 + 三种采集模式 + 抗反爬与自动降级，构建可用职位数据库；",
          "智能匹配：五维加权推荐 + 企业端候选人匹配；",
          "AI 能力：岗位解读、简历优化、职业助手多轮对话，自动归档形成闭环；",
          "数据可视化：市场分析 Dashboard + AI 结论；",
          "测试验证：pytest 28 例 + 前端构建通过，完成端到端联调。"]
for i, t in enumerate(add_li):
    add_text(s, Inches(0.9), Inches(1.8 + i * 0.55), Inches(11.8), Inches(0.5),
             [("• " + t, 13.5, False, GRAY)])
add_text(s, Inches(0.6), Inches(4.4), Inches(12), Inches(0.5), [("个人收获", 17, True, GREEN)])
add_li2 = ["工程能力：前后端分离、REST API、数据库建模、并发爬虫与反爬；",
           "AI 集成：大模型 API 封装、结构化输出解析与容错；",
           "算法思维：将业务抽象为多维加权模型并做双端复用；",
           "分析意识：用数据归一化与图表量化招聘市场规律。" ]
for i, t in enumerate(add_li2):
    add_text(s, Inches(0.9), Inches(4.9 + i * 0.5), Inches(11.8), Inches(0.5),
             [("• " + t, 13.5, False, GRAY)])

s = prs.slides.add_slide(BLANK)
header(s, "7.2 当前不足与后续优化方向", "OUTLOOK")
add_text(s, Inches(0.6), Inches(1.35), Inches(12), Inches(0.5), [("当前不足", 17, True, ORANGE)])
add_li = ["数据源单一（仅 51job），样本规模有限；",
          "SQLite 单机部署，未支撑多源高并发；",
          "推荐以规则加权为主，未引入语义/协同召回；",
          "爬虫依赖本地浏览器，规模化受限。"]
for i, t in enumerate(add_li):
    add_text(s, Inches(0.9), Inches(1.85 + i * 0.5), Inches(11.8), Inches(0.5),
             [("• " + t, 13.5, False, GRAY)])
add_text(s, Inches(0.6), Inches(3.9), Inches(12), Inches(0.5), [("后续优化方向", 17, True, PURPLE)])
add_li2 = ["多平台聚合 + 定时增量入库，扩大数据规模；",
           "PostgreSQL + Gunicorn/Nginx 生产化部署；",
           "引入 Embedding 语义召回 + 协同过滤，提升推荐质量；",
           "简历自动投递、薪资预测、更细粒度趋势模型。"]
for i, t in enumerate(add_li2):
    add_text(s, Inches(0.9), Inches(4.4 + i * 0.5), Inches(11.8), Inches(0.5),
             [("• " + t, 13.5, False, GRAY)])

# ---------------- 致谢 ----------------
s = prs.slides.add_slide(BLANK)
add_rect(s, 0, 0, W, H, DARK)
add_text(s, Inches(1), Inches(2.6), Inches(11), Inches(1),
         [("感谢聆听 · 恳请指正", 44, True, WHITE)], align=PP_ALIGN.CENTER)
add_text(s, Inches(1), Inches(4.2), Inches(11), Inches(1),
         [("智聘通 智能招聘平台 | 毕业设计答辩", 16, False, GRAY)], align=PP_ALIGN.CENTER)

prs.save(OUT)
print("saved", OUT, os.path.getsize(OUT) // 1024, "KB")