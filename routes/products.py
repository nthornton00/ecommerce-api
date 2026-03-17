from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from extensions import db
from models.product import Product
from models.user import User
from services.s3_service import upload_image, delete_image
import json

products_bp = Blueprint('products', __name__)

# ── GET ALL PRODUCTS ──────────────────────────────────────────────────────
# This is where Redis caching comes in!
# Instead of hitting PostgreSQL every single time someone browses products,
# we cache the result in Redis for 5 minutes.
# 1st request → hits PostgreSQL, stores result in Redis
# 2nd-Nth requests → served directly from Redis (much faster)
@products_bp.route('/', methods=['GET'])
def get_products():
    from app import redis_client

    # Try to get products from Redis cache first
    cached = redis_client.get('products:all')
    if cached:
        # Cache hit! Return the cached data without touching PostgreSQL
        print('Serving products from cache')
        return jsonify(json.loads(cached)), 200

    # Cache miss — fetch from PostgreSQL
    print('Fetching products from database')
    products = Product.query.filter_by(is_active=True).all()
    products_list = [p.to_dict() for p in products]

    # Store in Redis for 5 minutes (300 seconds)
    redis_client.setex('products:all', 300, json.dumps(products_list))

    return jsonify(products_list), 200


# ── GET SINGLE PRODUCT ────────────────────────────────────────────────────
@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)

    if not product or not product.is_active:
        return jsonify({'error': 'Product not found'}), 404

    return jsonify(product.to_dict()), 200


# ── CREATE PRODUCT (admin only) ───────────────────────────────────────────
@products_bp.route('/', methods=['POST'])
@jwt_required()
def create_product():
    from app import redis_client

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    # Handle both JSON and form data
    # We need form data to support file uploads
    name = request.form.get('name')
    description = request.form.get('description', '')
    price = request.form.get('price')
    stock = request.form.get('stock', 0)

    if not name or not price:
        return jsonify({'error': 'name and price are required'}), 400

    image_url = ''

    # Check if an image was uploaded
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            try:
                image_url = upload_image(file)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

    product = Product(
        name=name,
        description=description,
        price=float(price),
        stock=int(stock),
        image_url=image_url
    )

    db.session.add(product)
    db.session.commit()

    redis_client.delete('products:all')

    return jsonify(product.to_dict()), 201


# ── UPDATE PRODUCT (admin only) ───────────────────────────────────────────
@products_bp.route('/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    from app import redis_client

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Handle both form-data and JSON
    if request.content_type and 'multipart/form-data' in request.content_type:
        data = request.form
    else:
        data = request.get_json() or {}

    # Update fields if provided
    if 'name' in data:
        product.name = data['name']
    if 'description' in data:
        product.description = data['description']
    if 'price' in data:
        product.price = float(data['price'])
    if 'stock' in data:
        product.stock = int(data['stock'])
    if 'is_active' in data:
        product.is_active = data['is_active']

    # Handle image upload if provided
    if 'image' in request.files:
        file = request.files['image']
        if file.filename != '':
            try:
                # Delete old image from S3 if it exists
                if product.image_url:
                    delete_image(product.image_url)
                product.image_url = upload_image(file)
            except ValueError as e:
                return jsonify({'error': str(e)}), 400

    db.session.commit()
    redis_client.delete('products:all')

    return jsonify(product.to_dict()), 200


# ── DELETE PRODUCT (admin only) ───────────────────────────────────────────
@products_bp.route('/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    from app import redis_client

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user or not user.is_admin:
        return jsonify({'error': 'Admin access required'}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404

    # Soft delete — just mark as inactive instead of deleting from database
    # This preserves order history that references this product
    product.is_active = False
    db.session.commit()

    # Invalidate cache
    redis_client.delete('products:all')

    return jsonify({'message': 'Product deleted successfully'}), 200