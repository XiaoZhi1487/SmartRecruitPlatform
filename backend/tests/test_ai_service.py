"""AI 服务封装测试：system_key 注入、JSON 解析、模板兜底"""
import json
from unittest.mock import patch

from app.services.ai_service import DeepSeekService, _extract_json, _template_reason


def _make_service():
    return DeepSeekService("sk-test", max_retries=1, timeout=2)


def test_analyze_job_injects_system_key():
    svc = _make_service()
    with patch.object(svc, "_request", return_value='{"core_skills":["Python"]}') as m:
        result = svc.analyze_job({"title": "Python开发", "company_name": "某公司",
                                  "salary_text": "20-30K"})
    assert result.get("core_skills") == ["Python"]
    assert m.call_args.kwargs["system_key"] == "job_analysis"
    # 请求消息中应包含用户职位信息
    assert "Python开发" in m.call_args.args[0][0]["content"]


def test_optimize_resume_injects_system_key():
    svc = _make_service()
    with patch.object(svc, "_request",
                      return_value='{"score":80,"overall":"不错","suggestions":[]}') as m:
        result = svc.optimize_resume("我的简历内容", "Python工程师")
    assert result.get("score") == 80
    assert m.call_args.kwargs["system_key"] == "resume_optimize"


def test_parse_resume_injects_system_key():
    svc = _make_service()
    with patch.object(svc, "_request",
                      return_value='{"real_name":"张三","phone":""}') as m:
        result = svc.parse_resume("张三的简历文本")
    assert result.get("real_name") == "张三"
    assert m.call_args.kwargs["system_key"] == "resume_parse"


def test_request_prepends_system_prompt():
    svc = _make_service()
    captured = {}

    def fake_post(url, json=None, headers=None, timeout=None):
        captured["messages"] = json["messages"]
        class R:
            status_code = 200
            def json(self):
                return {"choices": [{"message": {"content": "ok"}}]}
        return R()

    with patch("app.services.ai_service.requests.post", side_effect=fake_post):
        svc.chat([{"role": "user", "content": "你好"}], system_key="chat")
    assert captured["messages"][0]["role"] == "system"
    assert "职业规划" in captured["messages"][0]["content"]
    assert captured["messages"][-1] == {"role": "user", "content": "你好"}


def test_extract_json_variants():
    assert _extract_json('{"a":1}') == {"a": 1}
    assert _extract_json('```json\n{"a":1}\n```') == {"a": 1}
    # 混合文本中提取 JSON
    assert _extract_json('结果是：{"a": 1} 完毕') == {"a": 1}
    # 无法解析时返回 _raw
    raw = _extract_json("完全不是JSON")
    assert "_raw" in raw


def test_template_reason_fallback():
    job = {"title": "Python工程师", "company_name": "某公司", "salary_text": "20-30K",
           "city": "北京", "job_tags": ["Python", "Django"]}
    user = {"skills": ["Python", "Flask"], "city": "北京"}
    reason = _template_reason(job, user)
    assert "Python" in reason
    assert "北京" in reason
