from flask import Blueprint, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from models.database import OrderDAO, MenuDAO
import logging

logger = logging.getLogger(__name__)

order_bp = Blueprint('order', __name__)


@order_bp.route('/create', methods=['POST'])
@login_required
def create():
    """创建订单"""
    try:
        table_id = request.form.get('table_id', type=int)
        remark = request.form.get('remark', '').strip()

        # 获取购物车
        cart = session.get('cart', {})
        if not cart:
            flash('购物车为空', 'warning')
            return redirect(url_for('customer.cart'))

        if not table_id:
            flash('请选择桌台', 'warning')
            return redirect(url_for('customer.cart'))

        # 创建订单
        result = OrderDAO.create_order(current_user.user_id, table_id, remark)
        if not result:
            flash('创建订单失败', 'danger')
            return redirect(url_for('customer.cart'))

        order_id = result['order_id']

        # 添加订单明细
        for item_id, item_data in cart.items():
            success = OrderDAO.add_order_item(
                order_id,
                int(item_id),
                item_data['quantity']
            )
            if not success:
                logger.warning(f"Failed to add item {item_id} to order {order_id}")

        # 清空购物车
        session.pop('cart', None)

        flash('订单创建成功！', 'success')
        return redirect(url_for('customer.order_detail', order_id=order_id))

    except Exception as e:
        logger.error(f"Create order error: {e}")
        flash('创建订单失败，请稍后重试', 'danger')
        return redirect(url_for('customer.cart'))


@order_bp.route('/pay/<int:order_id>', methods=['POST'])
@login_required
def pay(order_id):
    """支付订单"""
    try:
        pay_method = request.form.get('pay_method')

        if not pay_method:
            return jsonify({'success': False, 'message': '请选择支付方式'})

        # 验证订单
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'})

        if order['user_id'] != current_user.user_id and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '无权操作此订单'})

        if order['pay_status'] == 'paid':
            return jsonify({'success': False, 'message': '订单已支付'})

        # 完成订单（使用存储过程）
        success = OrderDAO.complete_order(order_id, pay_method)

        if success:
                return jsonify({'success': True, 'message': '支付成功'})
        else:
                return jsonify({'success': False, 'message': '支付失败'})

    except Exception as e:
        logger.error(f"Pay order error: {e}")
        return jsonify({'success': False, 'message': '支付失败，请稍后重试'})


@order_bp.route('/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel(order_id):
    """取消订单"""
    try:
        # 验证订单
        order = OrderDAO.get_order_by_id(order_id)
        if not order:
            return jsonify({'success': False, 'message': '订单不存在'})

        if order['user_id'] != current_user.user_id and current_user.role != 'admin':
            return jsonify({'success': False, 'message': '无权操作此订单'})

        if order['order_status'] in ['completed', 'cancelled']:
            return jsonify({'success': False, 'message': '订单无法取消'})

        # 取消订单（使用存储过程）
        success = OrderDAO.cancel_order(order_id)

        if success:
            return jsonify({'success': True, 'message': '订单已取消'})
        else:
            return jsonify({'success': False, 'message': '取消失败'})

    except Exception as e:
        logger.error(f"Cancel order error: {e}")
        return jsonify({'success': False, 'message': '取消失败，请稍后重试'})

