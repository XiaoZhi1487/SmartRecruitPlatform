"""认证模块测试：注册 / 密码强度 / 登录 / 锁定 / 令牌"""
import time


def test_register_success(client):
    resp = client.post("/api/auth/register", json={
        "username": "alice2026", "email": "alice@test.com", "password": "Abc12345!",
    })
    data = resp.get_json()
    assert resp.status_code == 200
    assert data["code"] == 0
    assert "access_token" in data["data"]["tokens"]
    assert "refresh_token" in data["data"]["tokens"]


def test_register_weak_password(client):
    resp = client.post("/api/auth/register", json={
        "username": "bob2026", "email": "bob@test.com", "password": "12345678",
    })
    assert resp.get_json()["code"] != 0


def test_register_dup_username(client):
    payload = {"username": "carol2026", "email": "carol@test.com", "password": "Abc12345!"}
    assert client.post("/api/auth/register", json=payload).get_json()["code"] == 0
    resp = client.post("/api/auth/register", json=payload)
    assert resp.get_json()["code"] != 0


def test_login_success(client):
    client.post("/api/auth/register", json={
        "username": "dave2026", "email": "dave@test.com", "password": "Abc12345!",
    })
    resp = client.post("/api/auth/login", json={
        "account": "dave2026", "password": "Abc12345!",
    })
    assert resp.get_json()["code"] == 0
    assert resp.get_json()["data"]["user"]["username"] == "dave2026"


def test_login_wrong_password(client):
    client.post("/api/auth/register", json={
        "username": "eve2026", "email": "eve@test.com", "password": "Abc12345!",
    })
    resp = client.post("/api/auth/login", json={
        "account": "eve2026", "password": "WrongPass1!",
    })
    assert resp.status_code == 401


def test_login_lock_after_failures(client):
    client.post("/api/auth/register", json={
        "username": "frank2026", "email": "frank@test.com", "password": "Abc12345!",
    })
    for _ in range(5):
        client.post("/api/auth/login", json={
            "account": "frank2026", "password": "WrongPass1!",
        })
    resp = client.post("/api/auth/login", json={
        "account": "frank2026", "password": "Abc12345!",
    })
    assert resp.status_code == 423


def test_me_requires_token(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, auth_headers):
    resp = client.get("/api/auth/me", headers=auth_headers)
    assert resp.get_json()["code"] == 0
    assert resp.get_json()["data"]["user"]["username"] == "tester001"


def test_refresh_token(client, auth_headers):
    login = client.post("/api/auth/login", json={
        "account": "tester001", "password": "Passw0rd!x",
    }).get_json()
    refresh_token = login["data"]["tokens"]["refresh_token"]
    resp = client.post("/api/auth/refresh",
                       headers={"Authorization": f"Bearer {refresh_token}"})
    assert resp.get_json()["code"] == 0
    assert "access_token" in resp.get_json()["data"]


def test_admin_guard(client, auth_headers):
    """普通用户不能访问管理员接口"""
    resp = client.get("/api/admin/stats", headers=auth_headers)
    assert resp.status_code == 403
