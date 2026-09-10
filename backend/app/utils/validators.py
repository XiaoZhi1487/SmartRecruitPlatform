"""输入校验工具"""
import re

EMAIL_RE = re.compile(r"^[\w.+-]+@[\w-]+(\.[\w-]+)+$")
PHONE_RE = re.compile(r"^1[3-9]\d{9}$")
USERNAME_RE = re.compile(r"^[a-zA-Z0-9_\u4e00-\u9fa5]{2,32}$")

# 密码强度：至少8位，且包含字母+数字+特殊字符
PASSWORD_MIN_LEN = 8
PASSWORD_RE = re.compile(r"^(?=.*[A-Za-z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,64}$")

JOB_KEYWORDS = [
    "Python", "Java", "前端", "后端", "算法", "人工智能", "数据分析", "运维",
    "测试", "产品经理", "运营", "UI设计", "C++", "Go", "机器学习", "深度学习",
]


def is_valid_email(email: str) -> bool:
    return bool(email and EMAIL_RE.match(email.strip()))


def is_valid_phone(phone: str) -> bool:
    return bool(phone and PHONE_RE.match(phone.strip()))


def is_valid_username(name: str) -> bool:
    return bool(name and USERNAME_RE.match(name.strip()))


def check_password_strength(password: str) -> tuple:
    """返回 (是否通过, 错误信息)"""
    if not password:
        return False, "密码不能为空"
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"密码长度至少 {PASSWORD_MIN_LEN} 位"
    if len(password) > 64:
        return False, "密码长度不能超过 64 位"
    if not re.search(r"[A-Za-z]", password):
        return False, "密码必须包含字母"
    if not re.search(r"\d", password):
        return False, "密码必须包含数字"
    if not re.search(r"[^A-Za-z0-9]", password):
        return False, "密码必须包含特殊字符"
    return True, "ok"


def clean_text(text):
    """清洗文本：去除多余空白与控制字符"""
    if not text:
        return ""
    import re as _re
    text = _re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", str(text))
    return _re.sub(r"\s+", " ", text).strip()
