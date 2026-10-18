import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from flask import current_app
import logging

logger = logging.getLogger(__name__)


class Database:
    """数据库操作类"""

    @staticmethod
    @contextmanager
    def get_connection():
        """获取数据库连接（上下文管理器）"""
        conn = None
        try:
            conn = pymysql.connect(
                host=current_app.config['MYSQL_HOST'],
                port=current_app.config['MYSQL_PORT'],
                user=current_app.config['MYSQL_USER'],
                password=current_app.config['MYSQL_PASSWORD'],
                database=current_app.config['MYSQL_DB'],
                charset='utf8mb4',
                cursorclass=DictCursor,
                autocommit=False
            )
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if conn:
                conn.close()

    @staticmethod
    def execute_query(query, params=None, fetch_one=False):
        """执行查询SQL"""
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch_one:
                    return cursor.fetchone()
                return cursor.fetchall()

    @staticmethod
    def execute_update(query, params=None):
        """执行更新SQL（INSERT/UPDATE/DELETE）"""
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount

    @staticmethod
    def execute_many(query, params_list):
        """批量执行SQL"""
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.executemany(query, params_list)
                conn.commit()
                return cursor.rowcount

    @staticmethod
    def call_procedure(proc_name, params=None):
        """调用存储过程"""
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.callproc(proc_name, params or ())
                results = []
                for result in cursor.stored_results():
                    results.extend(result.fetchall())
                conn.commit()
                return results


class UserDAO:
    """用户数据访问对象"""

    @staticmethod
    def find_by_username(username):
        """根据用户名查找用户"""
        query = "SELECT * FROM user WHERE username = %s"
        return Database.execute_query(query, (username,), fetch_one=True)

    @staticmethod
    def find_by_id(user_id):
        """根据ID查找用户"""
        query = "SELECT * FROM user WHERE user_id = %s"
        return Database.execute_query(query, (user_id,), fetch_one=True)

    @staticmethod
    def create_user(username, password_hash, phone, role='customer'):
        """创建新用户"""
        query = """
            INSERT INTO user (username, password_hash, phone, role, status)
            VALUES (%s, %s, %s, %s, 1)
        """
        Database.execute_update(query, (username, password_hash, phone, role))

    @staticmethod
    def get_all_customers(page=1, per_page=10):
        """获取所有顾客（分页）"""
        offset = (page - 1) * per_page
        query = """
            SELECT user_id, username, phone, created_at, status
            FROM user
            WHERE role = 'customer'
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """
        return Database.execute_query(query, (per_page, offset))

    @staticmethod
    def count_customers():
        """统计顾客数量"""
        query = "SELECT COUNT(*) as count FROM user WHERE role = 'customer'"
        result = Database.execute_query(query, fetch_one=True)
        return result['count'] if result else 0


class MenuDAO:
    """菜品数据访问对象"""

    @staticmethod
    def get_all_categories():
        """获取所有分类"""
        query = "SELECT * FROM category ORDER BY sort_order"
        return Database.execute_query(query)

    @staticmethod
    def get_menu_by_category(category_id=None):
        """根据分类获取菜品"""
        if category_id:
            query = """
                SELECT m.*, c.name as category_name
                FROM menu_item m
                JOIN category c ON m.category_id = c.category_id
                WHERE m.category_id = %s AND m.is_available = 1
                ORDER BY m.is_recommend DESC, m.item_id
            """
            return Database.execute_query(query, (category_id,))
        else:
            query = """
                SELECT m.*, c.name as category_name
                FROM menu_item m
                JOIN category c ON m.category_id = c.category_id
                WHERE m.is_available = 1
                ORDER BY c.sort_order, m.is_recommend DESC
            """
            return Database.execute_query(query)

    @staticmethod
    def get_menu_item(item_id):
        """获取单个菜品详情"""
        query = """
            SELECT m.*, c.name as category_name
            FROM menu_item m
            JOIN category c ON m.category_id = c.category_id
            WHERE m.item_id = %s
        """
        return Database.execute_query(query, (item_id,), fetch_one=True)

    @staticmethod
    def create_menu_item(name, description, image_url, price, category_id,
                         is_recommend=0, is_available=1):
        """创建菜品"""
        query = """
            INSERT INTO menu_item 
            (name, description, image_url, price, category_id, is_recommend, is_available)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        Database.execute_update(
            query,
            (name, description, image_url, price, category_id, is_recommend, is_available)
        )

    @staticmethod
    def update_menu_item(item_id, name, description, price, category_id,
                         is_recommend, is_available):
        """更新菜品"""
        query = """
            UPDATE menu_item 
            SET name = %s, description = %s, price = %s, category_id = %s,
                is_recommend = %s, is_available = %s
            WHERE item_id = %s
        """
        Database.execute_update(
            query,
            (name, description, price, category_id, is_recommend, is_available, item_id)
        )

    @staticmethod
    def delete_menu_item(item_id):
        """删除菜品（软删除）"""
        query = "UPDATE menu_item SET is_available = 0 WHERE item_id = %s"
        Database.execute_update(query, (item_id,))

    @staticmethod
    def search_menu(keyword):
        """搜索菜品"""
        query = """
            SELECT m.*, c.name as category_name
            FROM menu_item m
            JOIN category c ON m.category_id = c.category_id
            WHERE m.is_available = 1 
              AND (m.name LIKE %s OR m.description LIKE %s)
            ORDER BY m.is_recommend DESC
        """
        search_term = f"%{keyword}%"
        return Database.execute_query(query, (search_term, search_term))


class OrderDAO:
    """订单数据访问对象"""

    @staticmethod
    def create_order(user_id, table_id, remark=None):
        """创建订单（使用存储过程）"""
        with Database.get_connection() as conn:
            with conn.cursor() as cursor:
                # 调用存储过程
                cursor.callproc('create_order', (user_id, table_id, remark, 0, ''))
                # 获取OUT参数
                cursor.execute("SELECT @_create_order_3 AS order_id, @_create_order_4 AS order_number")
                result = cursor.fetchone()
                conn.commit()
                return result

    @staticmethod
    def add_order_item(order_id, menu_item_id, quantity):
        """添加订单明细（使用存储过程）"""
        try:
            Database.call_procedure('add_order_item', (order_id, menu_item_id, quantity))
            return True
        except Exception as e:
            logger.error(f"Error adding order item: {e}")
            return False

    @staticmethod
    def get_order_by_id(order_id):
        """获取订单详情"""
        query = """
            SELECT o.*, u.username, dt.table_number
            FROM `order` o
            LEFT JOIN user u ON o.user_id = u.user_id
            LEFT JOIN dining_table dt ON o.table_id = dt.table_id
            WHERE o.order_id = %s
        """
        return Database.execute_query(query, (order_id,), fetch_one=True)

    @staticmethod
    def get_order_items(order_id):
        """获取订单明细"""
        query = """
            SELECT oi.*, mi.name as menu_name, mi.image_url,
                   (oi.quantity * oi.unit_price) as subtotal
            FROM order_item oi
            JOIN menu_item mi ON oi.menu_item_id = mi.item_id
            WHERE oi.order_id = %s
        """
        return Database.execute_query(query, (order_id,))

    @staticmethod
    def get_user_orders(user_id, page=1, per_page=10):
        """获取用户订单列表"""
        offset = (page - 1) * per_page
        query = """
            SELECT o.*, dt.table_number,
                   (SELECT COUNT(*) FROM order_item WHERE order_id = o.order_id) as item_count
            FROM `order` o
            LEFT JOIN dining_table dt ON o.table_id = dt.table_id
            WHERE o.user_id = %s
            ORDER BY o.created_at DESC
            LIMIT %s OFFSET %s
        """
        return Database.execute_query(query, (user_id, per_page, offset))

    @staticmethod
    def get_all_orders(status=None, page=1, per_page=10):
        """获取所有订单（管理员）"""
        offset = (page - 1) * per_page
        if status:
            query = """
                SELECT o.*, u.username, dt.table_number
                FROM `order` o
                LEFT JOIN user u ON o.user_id = u.user_id
                LEFT JOIN dining_table dt ON o.table_id = dt.table_id
                WHERE o.order_status = %s
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
            """
            return Database.execute_query(query, (status, per_page, offset))
        else:
            query = """
                SELECT o.*, u.username, dt.table_number
                FROM `order` o
                LEFT JOIN user u ON o.user_id = u.user_id
                LEFT JOIN dining_table dt ON o.table_id = dt.table_id
                ORDER BY o.created_at DESC
                LIMIT %s OFFSET %s
            """
            return Database.execute_query(query, (per_page, offset))

    @staticmethod
    def update_order_status(order_id, new_status):
        """更新订单状态"""
        query = "UPDATE `order` SET order_status = %s WHERE order_id = %s"
        Database.execute_update(query, (new_status, order_id))

    @staticmethod
    def complete_order(order_id, pay_method):
        """完成订单（使用存储过程）"""
        try:
            Database.call_procedure('complete_order', (order_id, pay_method))
            return True
        except Exception as e:
            logger.error(f"Error completing order: {e}")
            return False

    @staticmethod
    def cancel_order(order_id):
        """取消订单（使用存储过程）"""
        try:
            Database.call_procedure('cancel_order', (order_id,))
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False


class TableDAO:
    """桌台数据访问对象"""

    @staticmethod
    def get_all_tables():
        """获取所有桌台"""
        query = "SELECT * FROM dining_table ORDER BY table_number"
        return Database.execute_query(query)

    @staticmethod
    def get_available_tables():
        """获取空闲桌台"""
        query = "SELECT * FROM dining_table WHERE status = 'free' ORDER BY table_number"
        return Database.execute_query(query)

    @staticmethod
    def update_table_status(table_id, status):
        """更新桌台状态"""
        query = "UPDATE dining_table SET status = %s WHERE table_id = %s"
        Database.execute_update(query, (status, table_id))


class StatisticsDAO:
    """统计数据访问对象"""

    @staticmethod
    def get_dashboard_stats():
        """获取仪表盘统计数据"""
        stats = {}

        # 今日订单数
        query = "SELECT COUNT(*) as count FROM `order` WHERE DATE(created_at) = CURDATE()"
        result = Database.execute_query(query, fetch_one=True)
        stats['today_orders'] = result['count'] if result else 0

        # 今日营业额
        query = """
            SELECT IFNULL(SUM(total_amount), 0) as revenue 
            FROM `order` 
            WHERE DATE(created_at) = CURDATE() AND pay_status = 'paid'
        """
        result = Database.execute_query(query, fetch_one=True)
        stats['today_revenue'] = float(result['revenue']) if result else 0

        # 待处理订单
        query = "SELECT COUNT(*) as count FROM `order` WHERE order_status IN ('pending', 'preparing')"
        result = Database.execute_query(query, fetch_one=True)
        stats['pending_orders'] = result['count'] if result else 0

        # 菜品总数
        query = "SELECT COUNT(*) as count FROM menu_item WHERE is_available = 1"
        result = Database.execute_query(query, fetch_one=True)
        stats['menu_count'] = result['count'] if result else 0

        return stats

    @staticmethod
    def get_top_selling_items(limit=10):
        """获取热销菜品"""
        query = """
            SELECT mi.name, mi.price, c.name as category_name,
                   COUNT(DISTINCT oi.order_id) as order_count,
                   SUM(oi.quantity) as total_quantity,
                   SUM(oi.quantity * oi.unit_price) as total_revenue
            FROM order_item oi
            JOIN menu_item mi ON oi.menu_item_id = mi.item_id
            JOIN category c ON mi.category_id = c.category_id
            JOIN `order` o ON oi.order_id = o.order_id
            WHERE o.order_status = 'completed'
            GROUP BY mi.item_id, mi.name, mi.price, c.name
            ORDER BY total_revenue DESC
            LIMIT %s
        """
        return Database.execute_query(query, (limit,))

    @staticmethod
    def get_recent_orders(limit=10):
        """获取最近订单"""
        query = """
            SELECT o.order_id, o.order_number, o.total_amount, o.order_status,
                   o.created_at, u.username, dt.table_number
            FROM `order` o
            LEFT JOIN user u ON o.user_id = u.user_id
            LEFT JOIN dining_table dt ON o.table_id = dt.table_id
            ORDER BY o.created_at DESC
            LIMIT %s
        """
        return Database.execute_query(query, (limit,))
