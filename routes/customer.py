from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from models.database import MenuDAO, OrderDAO, TableDAO
from functools import wraps
import logging

logger = logging.getLogger(__name__)

customer_bp = Blueprint('customer', __name__)


def customer_required(f):
    """装饰器：要求顾客角色"""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if current_user.role != 'customer':
            flash('此功能仅限顾客使用', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


@customer_bp.route('/menu')
@customer_required
def menu():
    """菜单浏览页面"""
    try:
        # 获取分类和搜索参数
        category_id = request.args.get('category', type=int)
        keyword = request.args.get('keyword', '').strip()

        # 获取所有分类
        categories = MenuDAO.get_all_categories()

        # 获取菜品
        if keyword:
            menu_items = MenuDAO.search_menu(keyword)
        elif category_id:
            menu_items = MenuDAO.get_menu_by_category(category_id)
        else:
            menu_items = MenuDAO.get_menu_by_category()

        # 获取购物车数量
        cart = session.get('cart', {})
        cart_count = sum(item['quantity'] for item in cart.values())

        return render_template(
            'customer/menu.html',
            categories=categories,
            menu_items=menu_items,
            selected_category=category_id,
            keyword=keyword,
            cart_count=cart_count
        )
    except Exception as e:
        logger.error(f"Menu page error: {e}")
        flash('加载菜单失败', 'danger')
        return redirect(url_for('index'))


@customer_bp.route('/cart')
@customer_required
def cart():
    """购物车页面"""
    try:
        cart = session.get('cart', {})
        cart_items = []
        total = 0

        for item_id, item_data in cart.items():
            menu_item = MenuDAO.get_menu_item(int(item_id))
            if menu_item:
                cart_items.append({
                    'item_id': menu_item['item_id'],
                    'name': menu_item['name'],
                    'price': float(menu_item['price']),
                    'image_url': menu_item['image_url'],
                    'quantity': item_data['quantity'],
                    'subtotal': float(menu_item['price']) * item_data['quantity']
                })
                total += float(menu_item['price']) * item_data['quantity']

        # 获取可用桌台
        tables = TableDAO.get_available_tables()

        return render_template(
            'customer/cart.html',
            cart_items=cart_items,
            total=total,
            tables=tables
        )
    except Exception as e:
        logger.error(f"Cart page error: {e}")
        flash('加载购物车失败', 'danger')
        return redirect(url_for('customer.menu'))


@customer_bp.route('/cart/add', methods=['POST'])
@customer_required
def add_to_cart():
    """添加到购物车"""
    try:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', 1, type=int)

        if not item_id or quantity < 1:
            return jsonify({'success': False, 'message': '参数错误'})

        # 验证菜品是否存在
        menu_item = MenuDAO.get_menu_item(item_id)
        if not menu_item or menu_item['is_available'] != 1:
            return jsonify({'success': False, 'message': '菜品不存在或已下架'})

        # 获取或创建购物车
        cart = session.get('cart', {})
        item_key = str(item_id)

        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'quantity': quantity,
                'name': menu_item['name'],
                'price': float(menu_item['price'])
            }

        session['cart'] = cart
        cart_count = sum(item['quantity'] for item in cart.values())

        return jsonify({
            'success': True,
            'message': '已添加到购物车',
            'cart_count': cart_count
        })

    except Exception as e:
        logger.error(f"Add to cart error: {e}")
        return jsonify({'success': False, 'message': '添加失败'})


@customer_bp.route('/cart/update', methods=['POST'])
@customer_required
def update_cart():
    """更新购物车数量"""
    try:
        item_id = request.form.get('item_id', type=int)
        quantity = request.form.get('quantity', type=int)

        if not item_id or quantity < 0:
            return jsonify({'success': False, 'message': '参数错误'})

        cart = session.get('cart', {})
        item_key = str(item_id)

        if quantity == 0:
            # 移除商品
            if item_key in cart:
                del cart[item_key]
        else:
            # 更新数量
            if item_key in cart:
                cart[item_key]['quantity'] = quantity

        session['cart'] = cart

        # 重新计算总价
        total = 0
        for item_data in cart.values():
            total += item_data['price'] * item_data['quantity']

        cart_count = sum(item['quantity'] for item in cart.values())

        return jsonify({
            'success': True,
            'total': total,
            'cart_count': cart_count
        })

    except Exception as e:
        logger.error(f"Update cart error: {e}")
        return jsonify({'success': False, 'message': '更新失败'})


@customer_bp.route('/cart/clear', methods=['POST'])
@customer_required
def clear_cart():
    """清空购物车"""
    session.pop('cart', None)
    return jsonify({'success': True, 'message': '购物车已清空'})


@customer_bp.route('/orders')
@customer_required
def orders():
    """我的订单页面"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 10

        orders = OrderDAO.get_user_orders(current_user.user_id, page, per_page)

        return render_template(
            'customer/orders.html',
            orders=orders,
            page=page
        )
    except Exception as e:
        logger.error(f"Orders page error: {e}")
        flash('加载订单失败', 'danger')
        return redirect(url_for('customer.menu'))


@customer_bp.route('/order/<int:order_id>')
@customer_required
def order_detail(order_id):
    """订单详情页面"""
    try:
        order = OrderDAO.get_order_by_id(order_id)

        if not order:
            flash('订单不存在', 'danger')
            return redirect(url_for('customer.orders'))

        # 验证订单是否属于当前用户
        if order['user_id'] != current_user.user_id:
            flash('无权查看此订单', 'danger')
            return redirect(url_for('customer.orders'))

        order_items = OrderDAO.get_order_items(order_id)

        return render_template(
            'customer/order_detail.html',
            order=order,
            order_items=order_items
        )
    except Exception as e:
        logger.error(f"Order detail error: {e}")
        flash('加载订单详情失败', 'danger')
        return redirect(url_for('customer.orders'))
