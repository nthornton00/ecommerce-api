from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.cart import CartItem
from models.order import Order, OrderItem
from models.product import Product
import stripe
import os
from services.ses_service import send_order_confirmation

orders_bp = Blueprint('orders', __name__)

# Configure Stripe with our secret key from .env
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')


# ── CHECKOUT ──────────────────────────────────────────────────────────────
# This is the most important endpoint in the whole app!
# Here's what happens step by step:
# 1. Get the user's cart
# 2. Create a Stripe Payment Intent (a pending payment)
# 3. Create an Order in our database
# 4. Return the client_secret to the frontend to complete payment
@orders_bp.route('/checkout', methods=['POST'])
@jwt_required()
def checkout():
    user_id = get_jwt_identity()

    # Get all items in the user's cart
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    if not cart_items:
        return jsonify({'error': 'Your cart is empty'}), 400

    # Calculate total amount
    total = sum(item.product.price * item.quantity for item in cart_items)

    # Check stock availability for all items before charging
    for item in cart_items:
        if item.quantity > item.product.stock:
            return jsonify({
                'error': f'Not enough stock for {item.product.name}'
            }), 400

    try:
        # Create a Stripe Payment Intent
        # Amount must be in cents (multiply by 100)
        # So $79.99 becomes 7999 cents
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total * 100),
            currency='usd',
            metadata={'user_id': user_id},
            automatic_payment_methods={
                'enabled': True,
                'allow_redirects': 'never'
            }
        )

        # Create the order in our database with status 'pending'
        order = Order(
            user_id=user_id,
            total_amount=total,
            status='pending',
            stripe_payment_intent_id=payment_intent.id
        )
        db.session.add(order)
        db.session.flush()  # Gets the order id without committing yet

        # Create an OrderItem for each cart item
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price_at_purchase=item.product.price
            )
            db.session.add(order_item)

            # Reduce stock
            item.product.stock -= item.quantity

        # Clear the cart after checkout
        CartItem.query.filter_by(user_id=user_id).delete()

        db.session.commit()

        return jsonify({
            'message': 'Order created successfully',
            'order_id': order.id,
            'total_amount': float(total),
            'client_secret': payment_intent.client_secret,
            'status': 'pending'
        }), 201

    except stripe.error.StripeError as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


# ── GET ALL ORDERS (for logged in user) ───────────────────────────────────
@orders_bp.route('/', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).order_by(
        Order.created_at.desc()
    ).all()

    return jsonify([order.to_dict() for order in orders]), 200


# ── GET SINGLE ORDER ──────────────────────────────────────────────────────
@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id
    ).first()

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    return jsonify(order.to_dict()), 200


# ── CONFIRM PAYMENT ───────────────────────────────────────────────────────
# After Stripe processes the payment on the frontend,
# we confirm it here and update the order status to 'paid'
@orders_bp.route('/confirm/<int:order_id>', methods=['POST'])
@jwt_required()
def confirm_payment(order_id):
    user_id = get_jwt_identity()

    order = Order.query.filter_by(
        id=order_id,
        user_id=user_id
    ).first()

    if not order:
        return jsonify({'error': 'Order not found'}), 404

    try:
        payment_intent = stripe.PaymentIntent.retrieve(
            order.stripe_payment_intent_id
        )

        if payment_intent.status == 'succeeded':
            order.status = 'paid'
            db.session.commit()

            # Send order confirmation email
            send_order_confirmation(order.user.email, order)

            return jsonify({
                'message': 'Payment confirmed!',
                'order': order.to_dict()
            }), 200
        else:
            order.status = 'failed'
            db.session.commit()
            return jsonify({'error': 'Payment not completed'}), 400

    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400