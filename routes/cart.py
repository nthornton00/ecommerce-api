from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.cart import CartItem
from models.product import Product

cart_bp = Blueprint('cart', __name__)

# ── GET CART ──────────────────────────────────────────────────────────────
# Returns all items in the logged in user's cart
@cart_bp.route('/', methods=['GET'])
@jwt_required()
def get_cart():
    user_id = get_jwt_identity()
    cart_items = CartItem.query.filter_by(user_id=user_id).all()

    # Calculate the total price of everything in the cart
    total = sum(item.product.price * item.quantity for item in cart_items)

    return jsonify({
        'items': [item.to_dict() for item in cart_items],
        'total': float(total),
        'item_count': len(cart_items)
    }), 200


# ── ADD TO CART ───────────────────────────────────────────────────────────
@cart_bp.route('/add', methods=['POST'])
@jwt_required()
def add_to_cart():
    user_id = get_jwt_identity()
    data = request.get_json()

    if 'product_id' not in data:
        return jsonify({'error': 'product_id is required'}), 400

    # Check the product exists and is active
    product = Product.query.get(data['product_id'])
    if not product or not product.is_active:
        return jsonify({'error': 'Product not found'}), 404

    # Check if there is enough stock
    quantity = data.get('quantity', 1)
    if quantity > product.stock:
        return jsonify({'error': f'Only {product.stock} items in stock'}), 400

    # Check if this product is already in the cart
    # If so, just update the quantity instead of adding a duplicate
    existing_item = CartItem.query.filter_by(
        user_id=user_id,
        product_id=data['product_id']
    ).first()

    if existing_item:
        existing_item.quantity += quantity
        db.session.commit()
        return jsonify({
            'message': 'Cart updated',
            'item': existing_item.to_dict()
        }), 200

    # Add new item to cart
    cart_item = CartItem(
        user_id=user_id,
        product_id=data['product_id'],
        quantity=quantity
    )

    db.session.add(cart_item)
    db.session.commit()

    return jsonify({
        'message': 'Item added to cart',
        'item': cart_item.to_dict()
    }), 201


# ── UPDATE CART ITEM ──────────────────────────────────────────────────────
@cart_bp.route('/update/<int:item_id>', methods=['PUT'])
@jwt_required()
def update_cart_item(item_id):
    user_id = get_jwt_identity()

    cart_item = CartItem.query.filter_by(
        id=item_id,
        user_id=user_id
    ).first()

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    data = request.get_json()
    quantity = data.get('quantity')

    if not quantity or quantity < 1:
        return jsonify({'error': 'Quantity must be at least 1'}), 400

    if quantity > cart_item.product.stock:
        return jsonify({'error': f'Only {cart_item.product.stock} items in stock'}), 400

    cart_item.quantity = quantity
    db.session.commit()

    return jsonify({
        'message': 'Cart updated',
        'item': cart_item.to_dict()
    }), 200


# ── REMOVE FROM CART ──────────────────────────────────────────────────────
@cart_bp.route('/remove/<int:item_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(item_id):
    user_id = get_jwt_identity()

    cart_item = CartItem.query.filter_by(
        id=item_id,
        user_id=user_id
    ).first()

    if not cart_item:
        return jsonify({'error': 'Cart item not found'}), 404

    db.session.delete(cart_item)
    db.session.commit()

    return jsonify({'message': 'Item removed from cart'}), 200


# ── CLEAR CART ────────────────────────────────────────────────────────────
@cart_bp.route('/clear', methods=['DELETE'])
@jwt_required()
def clear_cart():
    user_id = get_jwt_identity()

    CartItem.query.filter_by(user_id=user_id).delete()
    db.session.commit()

    return jsonify({'message': 'Cart cleared'}), 200