"""临时：解析 PC 卡片 HTML 结构（用后即删）"""
import re

with open(r"e:\Allcode\毕业设计\backend\card_sample.html", encoding="utf-8") as f:
    html = f.read()

# 所有 class 值
classes = sorted(set(re.findall(r'class="([^"]+)"', html)))
print("CLASSES:")
for c in classes:
    print("  ", c)

# 所有链接
print("\nLINKS:")
for href in re.findall(r'href="([^"]+)"', html):
    print("  ", href[:120])

# 文本片段
print("\nTEXT_SPANS:")
for m in re.findall(r'<span[^>]*>([^<]{2,40})</span>', html)[:20]:
    print("  ", m.strip())
