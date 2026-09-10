"""第三方扩展统一初始化"""
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_migrate import Migrate
from apscheduler.schedulers.background import BackgroundScheduler

db = SQLAlchemy()
jwt = JWTManager()
bcrypt = Bcrypt()
cors = CORS()
migrate = Migrate()
scheduler = BackgroundScheduler(timezone="Asia/Shanghai")
