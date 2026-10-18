from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from models.database import MenuDAO, OrderDAO, StatisticsDAO, UserDAO
from functools import wraps
import logging

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__)


def admin_required(f):
    """装饰器：要求管理员角色"""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'admin':
            flash('此功能仅限管理员使用', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """管理员仪表盘"""
    try:
        # 获取统计数据
        stats = StatisticsDAO.get_dashboard_stats()
        top_items = StatisticsDAO.get_top_selling_items(10)
        recent_orders = StatisticsDAO.get_recent_orders(10)

        return render_template(
            'admin/dashboard.html',
            stats=stats,
            top_items=top_items,
            recent_orders=recent_orders
        )
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        flash('加载仪表盘失败', 'danger')
        return redirect(url_for('index'))


@admin_bp.route('/menu')
@admin_required
def menu_manage():
    """菜品管理页面"""
    try:
        category_id = request.args.get('category', type=int)
        keyword = request.args.get('keyword', '').strip()

        categories = MenuDAO.get_all_categories()

        if keyword:
            menu_items = MenuDAO.search_menu(keyword)
        elif category_id:
            menu_items = MenuDAO.get_menu_by_category(category_id)
        else:
            # 获取所有菜品（包括已下架的）
            query = """
                SELECT m.*, c.name as category_name
                FROM menu_item m
                JOIN category c ON m.category_id = c.category_id
                ORDER BY c.sort_order, m.is_recommend DESC, m.item_id
            """
            from models.database import Database
            menu_items = Database.execute_query(query)

        return render_template(
            'admin/menu_manage.html',
            categories=categories,
            menu_items=menu_items,
            selected_category=category_id,
            keyword=keyword
        )
    except Exception as e:
        logger.error(f"Menu manage error: {e}")
        flash('加载菜品列表失败', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/menu/add', methods=['GET', 'POST'])
@admin_required
def menu_add():
    """添加菜品"""
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price', type=float)
            category_id = request.form.get('category_id', type=int)
            image_url = request.form.get('image_url', '').strip() or '/static/images/default.jpg'
            is_recommend = 1 if request.form.get('is_recommend') else 0
            is_available = 1 if request.form.get('is_available') else 0

            # 验证
            if not all([name, price, category_id]):
                flash('请填写所有必填项', 'danger')
                return redirect(url_for('admin.menu_add'))

            if price <= 0:
                flash('价格必须大于0', 'danger')
                return redirect(url_for('admin.menu_add'))

            MenuDAO.create_menu_item(
                name, description, image_url, price, category_id,
                is_recommend, is_available
            )

            flash('菜品添加成功', 'success')
            return redirect(url_for('admin.menu_manage'))

        except Exception as e:
            logger.error(f"Add menu error: {e}")
            flash('添加菜品失败', 'danger')

    categories = MenuDAO.get_all_categories()
    return render_template('admin/menu_add.html', categories=categories)


@admin_bp.route('/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@admin_required
def menu_edit(item_id):
    """编辑菜品"""
    try:
        menu_item = MenuDAO.get_menu_item(item_id)
        if not menu_item:
            flash('菜品不存在', 'danger')
            return redirect(url_for('admin.menu_manage'))

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            price = request.form.get('price', type=float)
            category_id = request.form.get('category_id', type=int)
            is_recommend = 1 if request.form.get('is_recommend') else 0
            is_available = 1 if request.form.get('is_available') else 0

            if not all([name, price, category_id]):
                flash('请填写所有必填项', 'danger')
                return render_template('admin/menu_edit.html', item=menu_item)

            if price <= 0:
                flash('价格必须大于0', 'danger')
                return render_template('admin/menu_edit.html', item=menu_item)

            MenuDAO.update_menu_item(
                item_id, name, description, price, category_id,
                is_recommend, is_available
            )

            flash('菜品更新成功', 'success')
            return redirect(url_for('admin.menu_manage'))

        categories = MenuDAO.get_all_categories()
        return render_template(
            'admin/menu_edit.html',
            item=menu_item,
            categories=categories
        )

    except Exception as e:
        logger.error(f"Edit menu error: {e}")
        flash('编辑菜品失败', 'danger')
        return redirect(url_for('admin.menu_manage'))


@admin_bp.route('/menu/delete/<int:item_id>', methods=['POST'])
@admin_required
def menu_delete(item_id):
    """删除菜品（软删除）"""
    try:
        MenuDAO.delete_menu_item(item_id)
        return jsonify({'success': True, 'message': '菜品已下架'})
    except Exception as e:
        logger.error(f"Delete menu error: {e}")
        return jsonify({'success': False, 'message': '删除失败'})


@admin_bp.route('/orders')
@admin_required
def order_manage():
    """订单管理页面"""
    try:
        status = request.args.get('status')
        page = request.args.get('page', 1, type=int)
        per_page = 20

        orders = OrderDAO.get_all_orders(status, page, per_page)

        return render_template(
            'admin/order_manage.html',
            orders=orders,
            selected_status=status,
            page=page
        )
    except Exception as e:
        logger.error(f"Order manage error: {e}")
        flash('加载订单列表失败', 'danger')
        return redirect(url_for('admin.dashboard'))


@admin_bp.route('/order/<int:order_id>')
@admin_required
def order_detail(order_id):
    """订单详情（管理员）"""
    try:
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            flash('订单不存在', 'danger')
            return redirect(url_for('admin.order_manage'))

        order_items = OrderDAO.get_order_items(order_id)

        return render_template(
            'admin/order_detail.html',
            order=order,
            order_items=order_items
        )
    except Exception as e:
        logger.error(f"Admin order detail error: {e}")
        flash('加载订单详情失败', 'danger')
        return redirect(url_for('admin.order_manage'))


@admin_bp.route('/order/update-status', methods=['POST'])
@admin_required
def update_order_status():
    """更新订单状态"""
    try:
        order_id = request.form.get('order_id', type=int)
        new_status = request.form.get('status')

        if not order_id or not new_status:
            return jsonify({'success': False, 'message': '参数错误'})

        valid_statuses = ['pending', 'preparing', 'completed', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'message': '无效的状态'})

        OrderDAO.update_order_status(order_id, new_status)

        return jsonify({'success': True, 'message': '状态更新成功'})

    except Exception as e:
        logger.error(f"Update order status error: {e}")
        return jsonify({'success': False, 'message': '更新失败'})


@admin_bp.route('/users')
@admin_required
def user_manage():
    """用户管理页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20

        users = UserDAO.get_all_customers(page, per_page)
        total = UserDAO.count_customers()

        return render_template(
            'admin/user_manage.html',
            users=users,
            page=page,
            per_page=per_page,
            total=total
        )
    except Exception as e:
        logger.error(f"User manage error: {e}")
        flash('加载用户列表失败', 'danger')
        return redirect(url_for('admin.dashboard'))
