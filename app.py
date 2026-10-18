from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, current_user
import os
import logging

# 配置日志
logging.basicConfig(
    level=logging.DEBUG,  # 开发环境使用DEBUG
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)

# 加载配置
from config import config

env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

logger.info(f"Starting application in {env} mode")
logger.info(f"Database: {app.config['MYSQL_DB']}")

# 初始化Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = '请先登录'


# 用户加载函数
@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    from models.database import UserDAO
    try:
        user_data = UserDAO.find_by_id(user_id)
        if user_data:
            return User(user_data)
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
    return None


# 注册蓝图
from routes.auth import auth_bp
from routes.customer import customer_bp
from routes.admin import admin_bp
from routes.order import order_bp

app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(customer_bp, url_prefix='/customer')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(order_bp, url_prefix='/order')

logger.info("Blueprints registered successfully")


# 首页路由
@app.route('/')
def index():
    """首页"""
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('customer.menu'))
    return render_template('index.html')


# 错误处理
@app.errorhandler(404)
def not_found(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal error: {error}", exc_info=True)
    return render_template('errors/500.html'), 500


@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}", exc_info=True)
    return render_template('errors/500.html'), 500


# 模板上下文处理器
@app.context_processor
def inject_user():
    """注入用户信息到所有模板"""
    return dict(current_user=current_user)


if __name__ == '__main__':
    # 确保上传目录存在
    upload_folder = app.config.get('UPLOAD_FOLDER', 'static/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
        logger.info(f"Created upload folder: {upload_folder}")

    logger.info("Starting Flask development server...")
    app.run(host='0.0.0.0', port=5000, debug=app.config['DEBUG'])
