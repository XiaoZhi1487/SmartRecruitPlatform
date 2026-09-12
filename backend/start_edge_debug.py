"""以远程调试端口启动 Edge/Chrome，供爬虫 CDP 附加复用登录态（用后即删）。

原理：WebDriver 默认会新起一个浏览器进程（独立临时 Profile），既不新增标签页、
也不带登录数据。要让爬虫直接附加到"你正在用的那个浏览器"，浏览器必须带
--remote-debugging-port 启动一次。本脚本负责完成这一步。

用法：
    1. 完全退出 Edge（重要！Edge 在运行时新开的实例无法开启调试端口）
    2. 运行：python start_edge_debug.py
    3. 浏览器会以调试模式重新打开（默认恢复上次的标签页，登录态保持）
    4. 之后再启动爬虫，就会自动附加到该浏览器，不再新开浏览器窗口

停止调试模式：完全退出该 Edge 窗口后正常打开 Edge 即可。
"""
import os
import socket
import subprocess
import sys

PORT = int(os.environ.get("CRAWL_ATTACH_PORT", "9222"))

_EDGE_PATHS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
]
_CHROME_PATHS = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]


def port_open(port) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def main():
    engine = os.environ.get("CRAWL_BROWSER", "edge").lower()
    candidates = _CHROME_PATHS if engine == "chrome" else _EDGE_PATHS
    exe = next((p for p in candidates if os.path.exists(p)), None)
    if not exe:
        print("未找到浏览器可执行文件，请设置环境变量 CRAWL_BROWSER_PATH 后重试。")
        sys.exit(1)

    if port_open(PORT):
        print(f"[OK] 端口 {PORT} 已有调试实例在运行，爬虫可直接附加，无需重复启动。")
        return

    proc = subprocess.run(["tasklist", "/FI", "IMAGENAME eq "
                           + ("msedge.exe" if engine == "edge" else "chrome.exe")],
                          capture_output=True, text=True)
    if "msedge.exe" in proc.stdout or "chrome.exe" in proc.stdout:
        print("检测到浏览器正在运行。")
        print("请先【完全退出】该浏览器（所有窗口），再重新运行本脚本。")
        print("否则新实例会并入旧进程，调试端口无法开启。")
        print("提示：浏览器设置里勾选『启动时恢复上次的页面』可自动恢复标签页与登录态。")
        sys.exit(1)

    subprocess.Popen([exe, f"--remote-debugging-port={PORT}", "--restore-last-session"])
    print(f"已启动调试模式浏览器（端口 {PORT}），会自动恢复上次会话。")
    print("现在启动爬虫即可复用该浏览器的登录状态，且不会新开浏览器窗口。")


if __name__ == "__main__":
    main()
