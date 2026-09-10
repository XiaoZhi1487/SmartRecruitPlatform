"""简历上传解析接口测试"""
import io


def _make_txt_stream(content):
    return io.BytesIO(content.encode("utf-8")), "resume.txt"


def test_upload_and_parse(client, auth_headers):
    content = ("王五 硕士 13712345678 wang@test.com\n"
               "技能：Python Flask MySQL Linux\n"
               "2020-2024 某科技有限公司 后端开发工程师")
    f, name = _make_txt_stream(content)
    resp = client.post("/api/resume/upload",
                       headers=auth_headers,
                       data={"file": (f, name)},
                       content_type="multipart/form-data")
    data = resp.get_json()
    assert data["code"] == 0
    resume_id = data["data"]["id"]
    assert data["data"]["file_type"] == "txt"

    # 等待后台解析完成
    import time
    parsed = None
    for _ in range(10):
        r = client.get(f"/api/resume/{resume_id}", headers=auth_headers).get_json()
        if r["data"]["parse_status"] != "pending":
            parsed = r["data"]
            break
        time.sleep(0.3)
    assert parsed is not None
    assert parsed["parse_status"] == "success"
    assert "Python" in (parsed["raw_text"] or "")
    structured = parsed["structured"] or {}
    assert structured.get("phone") == "13712345678" or "13712345678" in (parsed["raw_text"] or "")


def test_upload_invalid_type(client, auth_headers):
    f = io.BytesIO(b"xxxx"), "evil.exe"
    resp = client.post("/api/resume/upload", headers=auth_headers,
                       data={"file": (f, "evil.exe")},
                       content_type="multipart/form-data")
    assert resp.get_json()["code"] != 0


def test_resume_requires_auth(client):
    resp = client.get("/api/resume")
    assert resp.status_code == 401
