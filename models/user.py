from flask_login import UserMixin
from werkzeug.security import check_password_hash


class User(UserMixin):
    """用户模型类"""

    def __init__(self, user_data):
        self.id = user_data['user_id']
        self.user_id = user_data['user_id']
        self.username = user_data['username']
        self.password_hash = user_data['password_hash']
        self.phone = user_data.get('phone')
        self.role = user_data['role']
        self.status = user_data['status']
        self.created_at = user_data.get('created_at')

    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        """判断是否为管理员"""
        return self.role == 'admin'

    def is_active(self):
        """判断账户是否激活"""
        return self.status == 1

    def get_id(self):
        """返回用户ID（Flask-Login要求）"""
        return str(self.user_id)
