"""统一响应格式工具"""
from flask import jsonify


def ok(data=None, message="success"):
    """成功响应"""
    return jsonify({"code": 0, "message": message, "data": data})


def fail(message="error", code=1, http_status=400):
    """失败响应"""
    return jsonify({"code": code, "message": message, "data": None}), http_status


def page_result(items, total, page, page_size):
    """分页数据结构"""
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if page_size else 0,
    }
