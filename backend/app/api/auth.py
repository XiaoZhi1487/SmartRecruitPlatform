"""认证接口：注册 / 登录 / 刷新 / 邮箱验证 / 密码重置"""
import time
from datetime import datetime

from flask import Blueprint, request, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity,
)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

from app.extensions import db
from app.models.user import User
from app.models.profile import UserProfile
from app.utils.response import ok, fail
from app.utils.validators import (
    is_valid_email, is_valid_username, check_password_strength,
)
from app.services.mail_service import send_email, build_verification_email, build_reset_email
from app.utils.logger import get_logger

bp = Blueprint("auth", __name__)
logger = get_logger()

# 登录接口内存限流：ip -> [timestamps]
_login_throttle = {}


def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="auth-token")


def _make_token(email, purpose, expires=1800):
    return _serializer().dumps({"email": email, "purpose": purpose})


def _load_token(token, purpose, max_age=1800):
    data = _serializer().loads(token, max_age=max_age)
    if data.get("purpose") != purpose:
        raise BadSignature("purpose mismatch")
    return data["email"]


def _tokens(user):
    return {
        "access_token": create_access_token(
            identity=str(user.id),
            additional_claims={"role": user.role, "username": user.username}),
        "refresh_token": create_refresh_token(identity=str(user.id)),
        "expires_in": 7200,
    }


def _throttled(key, limit=10, window=60):
    now = time.time()
    bucket = _login_throttle.setdefault(key, [])
    bucket[:] = [t for t in bucket if now - t < window]
    if len(bucket) >= limit:
        return True
    bucket.append(now)
    return False


@bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    email = (data.get("email") or "").strip()
    password = data.get("password") or ""

    if not is_valid_username(username):
        return fail("用户名需为2-32位中文/字母/数字/下划线")
    if not is_valid_email(email):
        return fail("邮箱格式不正确")
    ok_flag, msg = check_password_strength(password)
    if not ok_flag:
        return fail(msg)

    if User.query.filter_by(username=username).first():
        return fail("用户名已被占用", http_status=409)
    if User.query.filter_by(email=email).first():
        return fail("邮箱已被注册", http_status=409)

    user = User(username=username, email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    db.session.add(UserProfile(user_id=user.id))
    db.session.commit()

    # 发送邮箱验证邮件
    token = _make_token(email, "verify")
    verify_url = f"{request.host_url}api/auth/verify-email?token={token}"
    send_email(email, "【智聘通】邮箱验证", build_verification_email(verify_url))

    logger.info("新用户注册: %s (%s)", username, email)
    return ok({"user": user.to_dict(), "tokens": _tokens(user)}, "注册成功，请查收验证邮件")


@bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    account = (data.get("account") or "").strip()
    password = data.get("password") or ""
    ip = request.remote_addr or "unknown"

    if not account or not password:
        return fail("请输入账号和密码")

    # IP 级限流（防止暴力破解）
    if _throttled(f"{ip}:{account}", limit=10, window=60):
        return fail("请求过于频繁，请稍后再试", http_status=429)

    user = User.query.filter(
        (User.username == account) | (User.email == account)
    ).first()
    if not user:
        return fail("账号或密码错误", http_status=401)
    if not user.is_active:
        return fail("账号已被禁用，请联系管理员", http_status=403)
    if user.is_locked:
        return fail("登录失败次数过多，账号已锁定，请稍后再试", http_status=423)
    if not user.check_password(password):
        locked = user.register_failure(current_app.config["LOGIN_LOCK_MINUTES"])
        db.session.commit()
        if locked:
            logger.warning("账号 %s 连续失败被锁定", account)
            return fail("密码错误次数过多，账号已锁定15分钟", http_status=423)
        return fail("账号或密码错误", http_status=401)

    user.reset_failures()
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    logger.info("用户登录: %s", user.username)
    return ok({"user": user.to_dict(), "tokens": _tokens(user)}, "登录成功")


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    user = db.session.get(User, int(identity))
    if not user or not user.is_active:
        return fail("用户不存在或已禁用", http_status=401)
    return ok({"access_token": create_access_token(
        identity=identity, additional_claims={"role": user.role, "username": user.username})})


@bp.get("/verify-email")
def verify_email():
    token = request.args.get("token", "")
    try:
        email = _load_token(token, "verify", max_age=3600)
    except SignatureExpired:
        return fail("验证链接已过期，请重新注册或联系管理员", http_status=400)
    except BadSignature:
        return fail("验证链接无效", http_status=400)
    user = User.query.filter_by(email=email).first()
    if not user:
        return fail("用户不存在", http_status=404)
    user.email_verified = True
    db.session.commit()
    return ok({"email": email}, "邮箱验证成功")


@bp.post("/forgot-password")
def forgot_password():
    email = (request.get_json(silent=True) or {}).get("email", "").strip()
    user = User.query.filter_by(email=email).first()
    if not user:
        # 不暴露账号是否存在
        return ok(None, "如果邮箱存在，重置链接已发送")
    token = _make_token(email, "reset", expires=1800)
    reset_url = f"{request.host_url.rstrip('/')}/reset-password?token={token}"
    send_email(email, "【智聘通】重置密码", build_reset_email(reset_url))
    return ok(None, "重置密码邮件已发送，请查收")


@bp.post("/reset-password")
def reset_password():
    data = request.get_json(silent=True) or {}
    token = data.get("token", "")
    password = data.get("password", "")
    ok_flag, msg = check_password_strength(password)
    if not ok_flag:
        return fail(msg)
    try:
        email = _load_token(token, "reset", max_age=1800)
    except SignatureExpired:
        return fail("重置链接已过期", http_status=400)
    except BadSignature:
        return fail("重置链接无效", http_status=400)
    user = User.query.filter_by(email=email).first()
    if not user:
        return fail("用户不存在", http_status=404)
    user.set_password(password)
    user.reset_failures()
    db.session.commit()
    return ok(None, "密码重置成功，请使用新密码登录")


@bp.get("/me")
@jwt_required()
def me():
    user = db.session.get(User, int(get_jwt_identity()))
    if not user:
        return fail("用户不存在", http_status=404)
    profile = UserProfile.query.filter_by(user_id=user.id).first()
    return ok({"user": user.to_dict(),
               "profile": profile.to_dict() if profile else None})
