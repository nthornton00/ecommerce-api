from extensions import db
from datetime import datetime, timezone

class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=datetime.now(timezone.utc))

    # Relationships — lets us access product details directly from a cart item
    # e.g. cart_item.product.name instead of doing a separate query
    user = db.relationship('User', backref='cart_items')
    product = db.relationship('Product', backref='cart_items')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product.name,
            'product_price': float(self.product.price),
            'quantity': self.quantity,
            'subtotal': float(self.product.price * self.quantity)
        }

    def __repr__(self):
        return f'<CartItem user={self.user_id} product={self.product_id}>'