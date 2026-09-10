"""后端启动入口
用法：
    python run.py            # 开发模式，默认 5000 端口
    python run.py --port 8000
"""
import argparse

from app import create_app

app = create_app()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智聘通后端服务")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--debug", action="store_true", default=True)
    args = parser.parse_args()
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
