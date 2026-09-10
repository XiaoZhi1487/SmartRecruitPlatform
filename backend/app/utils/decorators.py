"""权限与通用装饰器"""
from functools import wraps
from flask import request
from flask_jwt_extended import verify_jwt_in_request, get_jwt

from app.utils.response import fail


def role_required(*roles):
    """要求当前 JWT 携带指定角色"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("role") not in roles:
                return fail("无权限访问", code=403, http_status=403)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def admin_required(fn):
    """管理员权限"""
    return role_required("admin")(fn)
