"""后端启动入口
用法：
    python run.py            # 开发模式，默认 5000 端口
    python run.py --port 8000
    python run.py --reload   # 启用代码热重载（默认关闭，避免在部分环境下触发崩溃）
"""
import argparse
import sys

# 禁止写入字节码缓存：部分 Python 环境下 .pyc 写入偶发损坏导致
# "unknown opcode" 类崩溃，禁用写入可从根源规避
sys.dont_write_bytecode = True

from app import create_app

app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智聘通后端服务")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true", default=True)
    # 默认关闭自动重载：部分 Python 环境（如 PyCharm 内置解释器）下
    # watchdog 重载子进程偶发崩溃；需要热更新代码时显式加 --reload
    parser.add_argument("--reload", action="store_true", default=False)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug,
            use_reloader=args.reload, threaded=True)
