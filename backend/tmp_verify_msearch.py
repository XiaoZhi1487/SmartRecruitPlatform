"""临时验证：msearch 详情页 requests 直抓（用后即删）"""
import re
import urllib.request

job_id = "173487969"
url = f"https://msearch.51job.com/jobs/all/{job_id}.html"
print("URL:", url)
try:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept-Language": "zh-CN,zh;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode("utf-8", "ignore")
    print("LEN:", len(html))
    text = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>|<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    print("TEXT_PREVIEW:", text[:400])
except Exception as e:
    print("ERR:", type(e).__name__, str(e)[:200])
