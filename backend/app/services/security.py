"""敏感数据加密：使用 cryptography.Fernet 对称加密
密钥优先取配置，否则自动生成并持久化到 instance/data.key
"""
import os
import base64
from cryptography.fernet import Fernet

_fernet = None
_key_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                         "instance", "data.key")


def _get_fernet(app=None):
    global _fernet
    if _fernet is not None:
        return _fernet

    if app is None:
        from flask import has_app_context, current_app
        app = current_app if has_app_context() else None
    key = (app.config.get("DATA_ENCRYPTION_KEY") if app else None) or os.environ.get("DATA_ENCRYPTION_KEY", "")

    if not key:
        os.makedirs(os.path.dirname(_key_file), exist_ok=True)
        if os.path.exists(_key_file):
            with open(_key_file, "rb") as f:
                key = f.read().decode().strip()
        else:
            key = Fernet.generate_key().decode()
            with open(_key_file, "w") as f:
                f.write(key)
    _fernet = Fernet(key.encode() if isinstance(key, str) else key)
    return _fernet


def encrypt_text(plain: str) -> str:
    """加密字符串，返回带前缀密文"""
    if not plain:
        return ""
    return "enc:" + _get_fernet().encrypt(plain.encode("utf-8")).decode()


def decrypt_text(token: str) -> str:
    """解密字符串；非加密内容原样返回"""
    if not token:
        return ""
    if not token.startswith("enc:"):
        return token
    try:
        return _get_fernet().decrypt(token[4:].encode()).decode("utf-8")
    except Exception:
        return ""
