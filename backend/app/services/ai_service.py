"""DeepSeek API 封装：统一调用、重试、错误处理、降级兜底"""
import json
import time

import requests

from app.utils.logger import get_logger

logger = get_logger()

SYSTEM_PROMPTS = {
    "chat": (
        "你是「智聘通」智能求职助手，一名资深的职业规划与招聘领域专家。"
        "你可以根据用户提供的简历、技能、期望等信息，给出职业发展建议、求职策略、"
        "面试技巧、行业分析与岗位推荐理由。回答使用简体中文，结构清晰、专业务实。"
    ),
    "resume_optimize": (
        "你是一名资深HR与简历优化专家。请分析用户提供的简历文本，从以下维度给出改进建议："
        "1. 关键词优化（针对目标岗位匹配高频关键词）；2. 内容结构（逻辑层次、亮点前置）；"
        "3. 量化成果（将职责描述转化为可量化的业绩）；4. 排版建议；5. 缺失内容完善建议。"
        "请输出JSON格式：{\"score\": 0-100, \"overall\": \"总评\", "
        "\"suggestions\": [{\"dimension\": \"关键词优化\", \"advice\": \"...\"}]}"
    ),
    "resume_parse": (
        "你是简历信息抽取助手。请从用户提供的简历文本中抽取结构化信息，"
        "严格输出JSON：{\"real_name\": \"\", \"phone\": \"\", \"email\": \"\", "
        "\"city\": \"\", \"education_level\": \"\", \"experience_years\": 0, "
        "\"skills\": [{\"name\": \"\", \"level\": 3}], "
        "\"educations\": [{\"school\": \"\", \"major\": \"\", \"degree\": \"\", "
        "\"start_date\": \"\", \"end_date\": \"\"}], "
        "\"works\": [{\"company\": \"\", \"position\": \"\", \"start_date\": \"\", "
        "\"end_date\": \"\", \"description\": \"\"}], "
        "\"expected_position\": \"\", \"salary_min\": 0, \"salary_max\": 0}. "
        "无法提取的字段返回空字符串或0，不要编造信息。"
    ),
    "job_analysis": (
        "你是招聘数据分析专家。请分析给定的职位信息，输出JSON："
        "{\"core_skills\": [\"\"], \"suitability_advice\": \"\", \"career_growth\": \"\", "
        "\"interview_tips\": \"\"}。回答使用简体中文。"
    ),
}


class DeepSeekService:
    """DeepSeek Chat Completions API 封装"""

    def __init__(self, api_key, base_url="https://api.deepseek.com",
                 model="deepseek-chat", timeout=60, max_retries=3):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def _request(self, messages, temperature=0.7, max_tokens=2000):
        """发起请求并实现指数退避重试"""
        if not self.available:
            raise RuntimeError("DeepSeek API Key 未配置")

        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        last_err = None
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, headers=headers,
                                     timeout=self.timeout)
                if resp.status_code == 429:
                    # 限流：等待后重试
                    time.sleep(min(2 ** attempt, 30))
                    last_err = f"rate limited: {resp.text[:200]}"
                    continue
                if resp.status_code >= 400:
                    last_err = f"HTTP {resp.status_code}: {resp.text[:300]}"
                    # 鉴权失败不重试
                    if resp.status_code in (401, 403):
                        break
                    time.sleep(2 ** attempt)
                    continue
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except requests.RequestException as e:
                last_err = str(e)
                if attempt < self.max_retries:
                    time.sleep(min(2 ** attempt, 30))
        logger.error("DeepSeek API 调用失败: %s", last_err)
        raise RuntimeError(f"AI服务暂时不可用: {last_err}")

    # ---------- 业务能力 ----------
    def chat(self, history, system_key="chat"):
        """多轮对话。history: [{"role","content"}, ...]"""
        messages = [{"role": "system", "content": SYSTEM_PROMPTS.get(system_key, SYSTEM_PROMPTS["chat"])}]
        messages += history[-20:]  # 限制上下文长度
        return self._request(messages)

    def _json_request(self, messages, temperature=0.3, max_tokens=1500):
        """请求并尽力解析 JSON，失败时返回空 dict"""
        content = self._request(messages, temperature=temperature, max_tokens=max_tokens)
        return _extract_json(content)

    def optimize_resume(self, resume_text, job_title=None):
        """简历优化建议"""
        user_msg = f"目标岗位: {job_title or '未指定'}\n简历全文:\n{resume_text[:8000]}"
        return self._json_request([
            {"role": "user", "content": user_msg},
        ], system_key="resume_optimize")

    def parse_resume(self, resume_text):
        """简历结构化抽取"""
        result = self._json_request([
            {"role": "user", "content": resume_text[:8000]},
        ], system_key="resume_parse", max_tokens=1500)
        return result if isinstance(result, dict) else {}

    def analyze_job(self, job_info: dict):
        """岗位AI解读（核心技能/适配建议/成长路径/面试提示）"""
        content = json.dumps(job_info, ensure_ascii=False)[:4000]
        return self._json_request([
            {"role": "user", "content": f"职位信息:\n{content}"},
        ], system_key="job_analysis", max_tokens=1200)

    def generate_recommend_reason(self, job: dict, user_summary: dict):
        """生成推荐理由（模板兜底 + AI润色）"""
        reason = _template_reason(job, user_summary)
        try:
            prompt = (
                f"职位: {job.get('title')} @ {job.get('company_name')}，薪资{job.get('salary_text')}。\n"
                f"候选人画像: {json.dumps(user_summary, ensure_ascii=False)[:800]}。\n"
                f"请用一句不超过60字的中文给出推荐理由，突出技能与岗位匹配点。"
            )
            ai = self._request([{"role": "user", "content": prompt}],
                               temperature=0.5, max_tokens=200)
            if ai and len(ai) > 5:
                return ai.strip()
        except Exception as e:
            logger.warning("AI推荐理由生成失败，使用模板: %s", e)
        return reason


def _extract_json(text: str):
    """从 AI 输出中提取 JSON 对象"""
    if not text:
        return {}
    text = text.strip()
    # 去掉代码块围栏
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    # 截取第一个 { ... } 段落
    start, end = text.find("{"), text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except json.JSONDecodeError:
            pass
    return {"_raw": text}


def _template_reason(job: dict, user_summary: dict) -> str:
    """模板兜底推荐理由"""
    parts = []
    tags = job.get("job_tags") or []
    user_skills = set(user_summary.get("skills") or [])
    hit = [t for t in tags if t in user_skills]
    if hit:
        parts.append(f"你的技能『{', '.join(hit[:3])}』与该岗位高度匹配")
    else:
        parts.append(f"岗位『{job.get('title')}』与你的求职方向契合")
    city = job.get("city")
    if city and user_summary.get("city") == city:
        parts.append(f"工作地点{city}与你的期望一致")
    return "；".join(parts) + "。"


# 全局单例（由 create_app 初始化）
ai_service = None
