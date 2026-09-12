"""临时诊断脚本2：提取51job卡片链接/经验学历/标签/sensorsdata（用后即删）"""
import sys
import time

sys.path.insert(0, r"e:\Allcode\毕业设计\backend")

from app.services.crawler.anti_detect import create_driver

DRIVER = r"e:\Allcode\毕业设计\backend\drivers\msedgedriver.exe"
driver = create_driver(headless=False, engine="edge", driver_path=DRIVER)


def safe(fn, *a, **k):
    try:
        return fn(*a, **k)
    except Exception as e:
        return f"<ERR {type(e).__name__}: {str(e)[:80]}>"


try:
    driver.get("https://we.51job.com/pc/search?keyword=Python&searchType=2&pageNum=1")
    time.sleep(8)
    cards = safe(driver.find_elements, "css selector", ".joblist-item")
    print("CARDS:", len(cards))
    if cards:
        # 保存完整 HTML
        with open(r"e:\Allcode\毕业设计\backend\card_sample.html", "w", encoding="utf-8") as f:
            f.write(cards[0].get_attribute("outerHTML"))
        print("card_sample.html saved, len=", len(cards[0].get_attribute("outerHTML")))

    for i, c in enumerate(cards[:4]):
        print("=" * 30, "card", i)
        # 卡片内的链接元素
        js_links = safe(driver.execute_script,
                        "var c=arguments[0]; var out=[]; "
                        "c.querySelectorAll('a').forEach(function(a){out.push(a.className+' => '+a.href)}); return out;",
                        c)
        print("LINKS:", js_links)
        # sensorsdata
        sd = safe(driver.execute_script,
                  "var c=arguments[0]; var el=c.querySelector('[sensorsdata]'); "
                  "return el? el.getAttribute('sensorsdata'):null;", c)
        print("SENSORSDATA:", (sd or "")[:400])
        # 所有 .tip / .tag 文本
        print("TIPS:", [e.text for e in c.find_elements("css selector", ".tip")])
        print("TAGs:", [e.text for e in c.find_elements("css selector", ".joblist-item-tags .tag, .tags .tag, .tags span")])
finally:
    safe(driver.quit)
