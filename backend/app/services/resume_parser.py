"""简历文件解析：PDF / Word / TXT 文本抽取 + 结构化信息提取"""
import re
import os

from app.utils.logger import get_logger
from app.utils.validators import clean_text

logger = get_logger()


def extract_text(file_path: str, ext: str) -> str:
    """按扩展名抽取文本"""
    ext = ext.lower().lstrip(".")
    if ext == "pdf":
        return _extract_pdf(file_path)
    if ext == "docx":
        return _extract_docx(file_path)
    if ext == "doc":
        return _extract_doc(file_path)
    if ext == "txt":
        return _extract_txt(file_path)
    raise ValueError(f"不支持的文件类型: {ext}")


def _extract_pdf(path: str) -> str:
    from PyPDF2 import PdfReader
    reader = PdfReader(path)
    parts = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            parts.append(text)
    return clean_text("\n".join(parts))


def _extract_docx(path: str) -> str:
    from docx import Document
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs if p.text.strip()]
    for table in doc.tables:
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return clean_text("\n".join(parts))


def _extract_doc(path: str) -> str:
    # .doc 老格式：优先尝试 win32com（Windows 环境）
    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        try:
            doc = word.Documents.Open(os.path.abspath(path))
            text = doc.Content.Text
            doc.Close(False)
            return clean_text(text)
        finally:
            word.Quit()
    except Exception as e:
        logger.warning("解析 .doc 失败（%s），尝试读取原始文本", e)
        with open(path, "rb") as f:
            raw = f.read()
        try:
            return raw.decode("gbk", errors="ignore")
        except Exception:
            return ""


def _extract_txt(path: str) -> str:
    with open(path, "rb") as f:
        raw = f.read()
    for enc in ("utf-8", "gbk"):
        try:
            return clean_text(raw.decode(enc))
        except UnicodeDecodeError:
            continue
    return clean_text(raw.decode("utf-8", errors="ignore"))


# ---------- 正则启发式结构化提取（AI 不可用时的兜底） ----------
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
_PHONE_RE = re.compile(r"1[3-9]\d{9}")
_EDU_KEYWORDS = {"博士", "硕士", "本科", "大专", "高中"}
_SCHOOL_RE = re.compile(r"(?:毕业院校|学校|教育经历)[:：\s]*([\u4e00-\u9fa5A-Za-z·]{4,30})")


def heuristic_extract(text: str) -> dict:
    """基于正则从文本提取基础信息，供 AI 结构化结果补充"""
    result = {}
    m = _EMAIL_RE.search(text)
    if m:
        result["email"] = m.group(0)
    m = _PHONE_RE.search(text)
    if m:
        result["phone"] = m.group(0)
    for edu in _EDU_KEYWORDS:
        if edu in text:
            result["education_level"] = edu
            break
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    # 技能行：包含多个常见技术名词的行
    skill_kw = ["Python", "Java", "C++", "Go", "JavaScript", "Vue", "React", "MySQL",
                "Redis", "Linux", "Docker", "K8s", "TensorFlow", "PyTorch", "Spring",
                "Django", "Flask", "机器学习", "数据分析", "爬虫", "git"]
    found = []
    for kw in skill_kw:
        if kw in text and kw not in found:
            found.append(kw)
    result["skills"] = [{"name": s, "level": 3} for s in found[:20]]
    return result
