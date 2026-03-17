# E-Commerce REST API

A full-featured e-commerce REST API built with Flask, PostgreSQL, Redis, Stripe, and AWS.

## Live API

Base URL: https://ecommerce-api-production-0181.up.railway.app

Test the API is running: `GET /health` or https://ecommerce-api-production-0181.up.railway.app/health

## Tech Stack

- **Flask** - Web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching layer for product listings
- **AWS S3** - Product image storage
- **AWS SES** - Order confirmation emails
- **Stripe** - Payment processing
- **JWT** - Authentication

## Features

- User registration and authentication with JWT tokens
- Product management with image uploads to AWS S3
- Redis caching on product listings for improved performance
- Shopping cart management
- Order processing with Stripe payment integration
- Order confirmation emails via AWS SES
- Admin role-based access control

## API Endpoints

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/register` | Register a new user | No |
| POST | `/api/auth/login` | Login and get JWT token | No |
| GET | `/api/auth/me` | Get current user details | Yes |

### Products
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/products/` | Get all products (cached) | No |
| GET | `/api/products/<id>` | Get single product | No |
| POST | `/api/products/` | Create product with image | Admin |
| PUT | `/api/products/<id>` | Update product | Admin |
| DELETE | `/api/products/<id>` | Delete product | Admin |

### Cart
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/cart/` | Get cart | Yes |
| POST | `/api/cart/add` | Add item to cart | Yes |
| PUT | `/api/cart/update/<id>` | Update item quantity | Yes |
| DELETE | `/api/cart/remove/<id>` | Remove item from cart | Yes |
| DELETE | `/api/cart/clear` | Clear cart | Yes |

### Orders
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/orders/checkout` | Checkout cart | Yes |
| GET | `/api/orders/` | Get all orders | Yes |
| GET | `/api/orders/<id>` | Get single order | Yes |
| POST | `/api/orders/confirm/<id>` | Confirm payment | Yes |

## Local Setup

### Prerequisites
- Python 3.12+
- PostgreSQL
- Redis
- AWS Account
- Stripe Account

### Installation

1. Clone the repository:
```bash
git clone https://github.com/nthornton00/ecommerce-api.git
cd ecommerce-api
```

2. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file using `.env.example` as a template and fill in your values.

5. Run the application:
```bash
python app.py
```

6. Visit `http://127.0.0.1:5000/health` to verify everything is running.

## Environment Variables
```
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost:5432/ecommerce
REDIS_URL=redis://localhost:6379/0
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_REGION=us-east-2
AWS_S3_BUCKET=your-s3-bucket
AWS_SES_SENDER_EMAIL=your-verified-email
STRIPE_SECRET_KEY=sk_test_your-stripe-key
```

## Testing

API endpoints were tested using [Postman](https://www.postman.com/).

To test the API:
1. Register a user via `POST /api/auth/register`
2. Login via `POST /api/auth/login` and copy the `access_token`
3. Add the token as a Bearer Token in Postman's Authorization tab
4. Manually set `is_admin = true` in your database to test admin endpoints

Use Stripe test card `4242 4242 4242 4242` for payment testing.

## Third Party Services

This project requires your own API keys for:
- **AWS** - S3 bucket and SES verified email
- **Stripe** - Test mode secret key

See `.env` section above for setup instructions.
