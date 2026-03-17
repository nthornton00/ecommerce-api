from flask import Flask
from dotenv import load_dotenv
from extensions import db
from flask_jwt_extended import JWTManager
import redis
import os

from routes.auth import auth_bp
from routes.products import products_bp
from routes.cart import cart_bp
from routes.orders import orders_bp


load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)
jwt = JWTManager(app)

redis_client = redis.from_url(os.getenv('REDIS_URL'))

with app.app_context():
    from models.user import User
    from models.product import Product
    from models.cart import CartItem
    from models.order import Order, OrderItem
    db.create_all()


app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(cart_bp, url_prefix='/api/cart')
app.register_blueprint(orders_bp, url_prefix='/api/orders')

@app.route('/health')
def health():
    redis_status = redis_client.ping()
    return {
        "status": "ok",
        "database": "connected",
        "redis": "connected" if redis_status else "disconnected"
    }, 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)