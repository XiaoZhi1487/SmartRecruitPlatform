"""模拟数据源：真实爬取不可用/演示时的兜底数据生成器
保证系统功能（职位列表/推荐/统计）在无外网或强风控环境下仍可演示
"""
import json
import random
import re

CITIES = ["北京", "上海", "深圳", "杭州", "广州", "成都", "武汉", "南京", "西安", "苏州"]
DISTRICTS = {"北京": ["海淀区", "朝阳区", "西城区"], "上海": ["浦东新区", "徐汇区", "静安区"],
             "深圳": ["南山区", "福田区"], "杭州": ["西湖区", "滨江区"], "广州": ["天河区", "海珠区"],
             "成都": ["高新区", "锦江区"], "武汉": ["洪山区", "光谷"], "南京": ["建邺区", "江宁区"],
             "西安": ["高新区", "雁塔区"], "苏州": ["工业园区", "高新区"]}
EXPERIENCES = ["在校生/应届生", "1年以下", "1-3年", "3-5年", "5-10年"]
EDUCATIONS = ["大专", "本科", "硕士"]
COMPANY_SUFFIX = ["科技有限公司", "信息技术有限公司", "网络科技公司", "软件有限公司", "数据服务有限公司", "互联网科技有限公司"]
INDUSTRIES = ["互联网", "人工智能", "大数据", "电子商务", "金融科技", "企业服务", "游戏", "教育科技"]

SKILL_MAP = {
    "Python": ["Python", "Django", "Flask", "爬虫", "数据分析", "MySQL", "Redis", "Linux", "Docker"],
    "Java": ["Java", "Spring Boot", "MySQL", "Redis", "微服务", "Kafka", "MyBatis"],
    "前端": ["JavaScript", "Vue", "React", "TypeScript", "HTML5", "CSS3", "Webpack", "小程序"],
    "数据分析": ["Python", "SQL", "Tableau", "Pandas", "NumPy", "数据可视化", "统计学", "Excel"],
    "人工智能": ["Python", "PyTorch", "TensorFlow", "机器学习", "深度学习", "NLP", "OpenCV"],
    "算法": ["算法", "数据结构", "机器学习", "C++", "Python", "图神经网络"],
    "Go": ["Go", "Golang", "微服务", "Docker", "Kubernetes", "etcd"],
    "C++": ["C++", "STL", "多线程", "网络编程", "Qt"],
    "运维": ["Linux", "Shell", "Docker", "Kubernetes", "监控", "CI/CD", "Ansible"],
    "测试": ["测试", "自动化测试", "Selenium", "JMeter", "接口测试", "Python"],
    "产品经理": ["需求分析", "产品设计", "Axure", "数据分析", "用户研究", "项目管理"],
    "运营": ["用户运营", "内容运营", "活动策划", "数据分析", "社群运营"],
}


def _seeded(seed_str):
    random.seed(seed_str)
    return random


def _salary():
    base = random.choice([10, 12, 15, 18, 20, 25, 30, 35, 40])
    return base, base + random.choice([5, 8, 10, 15, 20])


def _make_link(kw, idx):
    return f"https://jobs.51job.com/beijing/mock-{kw}-{idx}.html"


def generate_jobs(keyword, pages=3, city=None) -> list:
    """为指定关键字生成 pages 页模拟职位数据（每页 10 条）"""
    r = _seeded(keyword)
    items = []
    base_skills = SKILL_MAP.get(keyword, ["Python", "MySQL", "Git"])
    for p in range(1, pages + 1):
        for i in range(10):
            idx = (p - 1) * 10 + i + 1
            c = city or r.choice(CITIES)
            s_min, s_max = _salary()
            title = r.choice([
                f"{keyword}开发工程师", f"高级{keyword}工程师", f"{keyword}工程师",
                f"{keyword}研发工程师", f"资深{keyword}专家", f"{keyword}实习生",
            ])
            skills = r.sample(base_skills, k=min(4, len(base_skills)))
            tags = [s for s in skills] + r.sample(["五险一金", "弹性工作", "年终奖", "带薪年假"], k=2)
            company = f"{r.choice(['星云', '云启', '智汇', '灵犀', '知行', '启明', '蓝图', '极光'])}{r.choice(COMPANY_SUFFIX)}"
            items.append({
                "source_job_id": f"mock-{keyword}-{idx}",
                "title": title,
                "salary_text": f"{s_min}-{s_max}K",
                "salary_min": s_min,
                "salary_max": s_max,
                "city": c,
                "district": r.choice(DISTRICTS.get(c, ["城区"])),
                "job_tags": tags,
                "company_name": company,
                "company_tags": [r.choice(INDUSTRIES), r.choice(["20-99人", "100-499人", "500-999人", "1000-9999人"])],
                "link": _make_link(keyword, idx),
                "experience_required": r.choice(EXPERIENCES),
                "education_required": r.choice(EDUCATIONS),
                "welfare": json.dumps(["五险一金", "节日福利", "定期体检", "带薪年假"], ensure_ascii=False),
                "description": (
                    f"岗位职责：1. 负责{keyword}相关业务系统的设计、开发与维护；"
                    f"2. 参与技术方案评审，保障代码质量与系统稳定性；3. 持续优化系统性能。\n"
                    f"任职要求：1. 本科及以上学历，计算机相关专业；"
                    f"2. 熟悉{', '.join(skills[:3])}等主流技术栈；"
                    f"3. 具备良好的沟通协作能力与学习能力。"
                ),
                "requirement": f"熟练使用{', '.join(base_skills[:4])}",
            })
    return items
