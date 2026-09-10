"""简历解析与安全模块测试"""
import os


def test_extract_txt(tmp_path):
    from app.services.resume_parser import extract_text
    p = tmp_path / "resume.txt"
    p.write_text("张三\n13800138000\nzhangsan@test.com\n熟悉Python与爬虫", encoding="utf-8")
    text = extract_text(str(p), "txt")
    assert "Python" in text


def test_heuristic_extract():
    from app.services.resume_parser import heuristic_extract
    text = ("李四 本科 13912345678 li@test.com "
            "熟练使用Python Java MySQL Linux Docker，三年开发经验")
    r = heuristic_extract(text)
    assert r["phone"] == "13912345678"
    assert r["email"] == "li@test.com"
    assert r["education_level"] == "本科"
    assert "Python" in [s["name"] for s in r["skills"]]


def test_parse_salary():
    from app.services.crawler.boss_crawler import parse_salary
    assert parse_salary("20-30K") == (20, 30)
    assert parse_salary("15K以上") in ((15, 15), (15, None))
    assert parse_salary("面议") == (None, None)


def test_extract_job_id():
    from app.services.crawler.boss_crawler import extract_job_id
    url = "https://www.zhipin.com/job_detail/abc123def.html?ka=search"
    assert extract_job_id(url) == "abc123def"


def test_proxy_pool():
    from app.services.crawler.proxy_pool import ProxyPool
    pool = ProxyPool(["http://1.2.3.4:8080", "http://5.6.7.8:8080"])
    assert pool.size == 2
    proxy = pool.get()
    assert proxy in ("http://1.2.3.4:8080", "http://5.6.7.8:8080")
    pool.mark_fail(proxy)
    pool.mark_fail(proxy)
    pool.mark_fail(proxy)  # 连续3次失败剔除
    assert pool.size == 1


def test_encrypt_decrypt(app):
    from app.services.security import encrypt_text, decrypt_text
    plain = "13800138000"
    token = encrypt_text(plain)
    assert token.startswith("enc:")
    assert decrypt_text(token) == plain
    assert decrypt_text("普通文本") == "普通文本"
