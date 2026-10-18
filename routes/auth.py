from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models.database import UserDAO
from models.user import User
import logging

logger = logging.getLogger(__name__)

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            remember = request.form.get('remember', False)

            logger.info(f"Login attempt for username: {username}")

            if not username or not password:
                flash('请输入用户名和密码', 'danger')
                return render_template('auth/login.html')

            # 查询用户
            user_data = UserDAO.find_by_username(username)

            if not user_data:
                logger.warning(f"User not found: {username}")
                flash('用户名或密码错误', 'danger')
                return render_template('auth/login.html')

            # 创建用户对象
            user = User(user_data)

            # 检查账户状态
            if not user.is_active():
                logger.warning(f"Inactive account: {username}")
                flash('账户已被禁用，请联系管理员', 'danger')
                return render_template('auth/login.html')

            # 验证密码
            if not check_password_hash(user.password_hash, password):
                logger.warning(f"Invalid password for user: {username}")
                flash('用户名或密码错误', 'danger')
                return render_template('auth/login.html')

            # 登录成功
            login_user(user, remember=remember)
            logger.info(f"Login successful for user: {username}")
            flash(f'欢迎回来，{user.username}！', 'success')

            # 根据角色跳转
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            elif user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('customer.menu'))

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            flash('登录失败，请稍后重试', 'danger')
            return render_template('auth/login.html')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """用户注册"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')
            confirm_password = request.form.get('confirm_password', '')
            phone = request.form.get('phone', '').strip()

            logger.info(f"Registration attempt for username: {username}")

            # 验证输入
            if not all([username, password, confirm_password, phone]):
                flash('请填写所有必填项', 'danger')
                return render_template('auth/register.html')

            if len(username) < 3 or len(username) > 20:
                flash('用户名长度应在3-20个字符之间', 'danger')
                return render_template('auth/register.html')

            if len(password) < 6:
                flash('密码长度至少为6个字符', 'danger')
                return render_template('auth/register.html')

            if password != confirm_password:
                flash('两次输入的密码不一致', 'danger')
                return render_template('auth/register.html')

            if len(phone) != 11 or not phone.isdigit():
                flash('请输入有效的11位手机号', 'danger')
                return render_template('auth/register.html')

            # 检查用户名是否已存在
            existing_user = UserDAO.find_by_username(username)
            if existing_user:
                logger.warning(f"Username already exists: {username}")
                flash('用户名已存在，请选择其他用户名', 'danger')
                return render_template('auth/register.html')

            # 创建新用户
            password_hash = generate_password_hash(password)
            UserDAO.create_user(username, password_hash, phone)

            logger.info(f"Registration successful for user: {username}")
            flash('注册成功！请登录', 'success')
            return redirect(url_for('auth.login'))

        except Exception as e:
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            flash('注册失败，请稍后重试', 'danger')
            return render_template('auth/register.html')

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """用户登出"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    flash('您已成功退出登录', 'info')
    return redirect(url_for('index'))
