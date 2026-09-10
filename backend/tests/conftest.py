"""pytest 公共夹具"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app  # noqa: E402
from app.config import Config  # noqa: E402


@pytest.fixture
def app(tmp_path):
    db_path = tmp_path / "test.db"

    class TestConfig(Config):
        TESTING = True
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
        CRAWL_MODE = "mock"
        DEEPSEEK_API_KEY = ""          # 测试禁用真实 AI 调用
        CRAWL_THREADS = 1

    app = create_app(TestConfig)
    yield app


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers(client):
    """注册并登录一个测试用户，返回请求头"""
    resp = client.post("/api/auth/register", json={
        "username": "tester001",
        "email": "tester001@test.com",
        "password": "Passw0rd!x",
    })
    assert resp.get_json()["code"] == 0
    token = resp.get_json()["data"]["tokens"]["access_token"]
    return {"Authorization": f"Bearer {token}"}
