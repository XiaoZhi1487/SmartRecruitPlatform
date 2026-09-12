"""临时：解析 PC 卡片 sensorsdata 完整 JSON（用后即删）"""
import json
import re

with open(r"e:\Allcode\毕业设计\backend\card_sample.html", encoding="utf-8") as f:
    html = f.read()

m = re.search(r'sensorsdata="([^"]+)"', html)
if not m:
    print("not found")
else:
    raw = m.group(1)
    # 还原 HTML 实体
    import html as _h
    data = _h.unescape(raw)
    try:
        obj = json.loads(data)
        for k, v in obj.items():
            print(f"  {k}: {str(v)[:60]}")
    except Exception as e:
        print("PARSE_ERR:", e)
        print(data[:800])
