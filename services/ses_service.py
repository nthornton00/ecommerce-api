import boto3
import os

def get_ses_client():
    """
    Create and return an SES client.
    Called on demand so environment variables
    are guaranteed to be loaded first.
    """
    return boto3.client(
        'ses',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION')
    )


def send_order_confirmation(to_email, order):
    """
    Send an order confirmation email via AWS SES.

    Args:
        to_email: The customer's email address
        order: The Order object containing order details
    """
    ses_client = get_ses_client()
    # Build the order items list for the email
    items_html = ""
    for item in order.items:
        items_html += f"""
            <tr>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.product.name}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">{item.quantity}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">${item.price_at_purchase}</td>
                <td style="padding: 8px; border-bottom: 1px solid #eee;">${float(item.price_at_purchase * item.quantity)}</td>
            </tr>
            """

    # Build the full HTML email
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h1 style="color: #333;">Order Confirmation</h1>
        <p>Thank you for your order! Here are your order details:</p>

        <div style="background: #f9f9f9; padding: 15px; border-radius: 5px;">
            <p><strong>Order ID:</strong> #{order.id}</p>
            <p><strong>Status:</strong> {order.status}</p>
            <p><strong>Date:</strong> {order.created_at.strftime('%B %d, %Y')}</p>
        </div>

        <h2 style="color: #333; margin-top: 20px;">Items Ordered</h2>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f2f2f2;">
                    <th style="padding: 8px; text-align: left;">Product</th>
                    <th style="padding: 8px; text-align: left;">Quantity</th>
                    <th style="padding: 8px; text-align: left;">Price</th>
                    <th style="padding: 8px; text-align: left;">Subtotal</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>

        <div style="margin-top: 20px; text-align: right;">
            <h2>Total: ${order.total_amount}</h2>
        </div>

        <p style="color: #666; margin-top: 30px;">
            Thank you for shopping with us!
        </p>
    </body>
    </html>
    """

    try:
        ses_client.send_email(
            Source=os.getenv('AWS_SES_SENDER_EMAIL'),
            Destination={
                'ToAddresses': [to_email]
            },
            Message={
                'Subject': {
                    'Data': f'Order Confirmation - Order #{order.id}',
                    'Charset': 'UTF-8'
                },
                'Body': {
                    'Html': {
                        'Data': html_body,
                        'Charset': 'UTF-8'
                    }
                }
            }
        )
        print(f'Order confirmation email sent to {to_email}')
        return True

    except Exception as e:
        # Log the error but don't crash the app
        # A failed email should never block an order from being placed
        print(f'Failed to send email: {str(e)}')
        return False