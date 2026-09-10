"""邮件服务：邮箱验证、密码重置邮件
未配置 SMTP 时输出到控制台/日志，保证演示环境可用
"""
import smtplib
from email.mime.text import MIMEText
from email.header import Header

from app.utils.logger import get_logger

logger = get_logger()


def _config():
    from flask import current_app
    return current_app.config


def send_email(to_email: str, subject: str, html_body: str) -> bool:
    """发送邮件；未配置 SMTP 时降级为控制台输出"""
    cfg = _config()
    server = cfg.get("MAIL_SERVER")
    if not server:
        logger.info("[邮件降级-未配置SMTP] 收件人=%s 主题=%s\n%s", to_email, subject, html_body)
        return True
    try:
        msg = MIMEText(html_body, "html", "utf-8")
        msg["Subject"] = Header(subject, "utf-8")
        msg["From"] = cfg.get("MAIL_DEFAULT_SENDER")
        msg["To"] = to_email
        if cfg.get("MAIL_USE_SSL"):
            smtp = smtplib.SMTP_SSL(server, cfg.get("MAIL_PORT"))
        else:
            smtp = smtplib.SMTP(server, cfg.get("MAIL_PORT"))
        if cfg.get("MAIL_USERNAME"):
            smtp.login(cfg.get("MAIL_USERNAME"), cfg.get("MAIL_PASSWORD"))
        smtp.send_message(msg)
        smtp.quit()
        return True
    except Exception as e:
        logger.error("发送邮件失败: %s", e)
        return False


def build_verification_email(verify_url: str) -> str:
    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;border:1px solid #e5e7eb;border-radius:12px">
      <h2 style="color:#2563eb">智聘通 · 邮箱验证</h2>
      <p>您好，欢迎注册智聘通智能招聘平台。请点击下方按钮完成邮箱验证：</p>
      <a href="{verify_url}" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none">立即验证</a>
      <p style="color:#6b7280;font-size:12px">如非本人操作，请忽略此邮件。</p>
    </div>"""


def build_reset_email(reset_url: str) -> str:
    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;padding:24px;border:1px solid #e5e7eb;border-radius:12px">
      <h2 style="color:#2563eb">智聘通 · 重置密码</h2>
      <p>请点击下方链接重置您的登录密码（30分钟内有效）：</p>
      <a href="{reset_url}" style="display:inline-block;background:#2563eb;color:#fff;padding:10px 24px;border-radius:6px;text-decoration:none">重置密码</a>
      <p style="color:#6b7280;font-size:12px">如非本人操作，请忽略此邮件。</p>
    </div>"""
