import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional

# Email configuration
EMAIL_CONFIG = {
    "smtp_host": "email-service",
    "smtp_port": 587,
    "sender_email": "postfix@wit.edu",
    "sender_name": "SneakerSpot Team"
}

def send_email(to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
    try:
        # Create message
        if html_body:
            msg = MIMEMultipart('alternative')
            msg.attach(MIMEText(body, 'plain'))
            msg.attach(MIMEText(html_body, 'html'))
        else:
            msg = MIMEText(body)
        
        msg["Subject"] = subject
        msg["From"] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg["To"] = to_email
        
        # Send via Postfix service
        server = smtplib.SMTP(EMAIL_CONFIG['smtp_host'], EMAIL_CONFIG['smtp_port'])
        server.sendmail(EMAIL_CONFIG['sender_email'], to_email, msg.as_string())
        server.quit()
        
        return True
        
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def create_order_confirmation_email_content(user_info: Dict, order_info: Dict, items_with_details: List[Dict], total_amount: float) -> tuple[str, str, str]:
    order_id = order_info.get('order_id', 'Unknown')
    subject = f"Order Confirmation - Order #{order_id} from SneakerSpot"
    
    # Calculate subtotal and tax
    subtotal = sum(item['item_total'] for item in items_with_details)
    tax_amount = round(subtotal * 0.0625, 2)
    
    # Plain text body
    body = f"Hi {user_info['first_name']},\n\n"
    body += "Thank you for your purchase! Here are the details of your order:\n\n"
    
    for item in items_with_details:
        body += f"- {item['brand_name']} {item['product_name']}: {item['quantity']} x ${item['unit_price']:.2f} = ${item['item_total']:.2f}\n"
    
    body += f"\nSubtotal: ${subtotal:.2f}\n"
    body += f"Tax (6.25%): ${tax_amount:.2f}\n"
    body += f"Total: ${total_amount:.2f}\n"
    body += "\nYour order is being processed. You'll receive another email when it's shipped.\n\n"
    body += "Thank you for shopping with us!\nSneakerSpot Team"
    
    # HTML body
    html_body = f"""
    <html>
    <body>
        <h2>Order Confirmation</h2>
        <p>Hi {user_info['first_name']},</p>
        <p>Thank you for your purchase! Here are the details of your order:</p>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background-color: #f2f2f2;">
                <th style="padding: 8px;">Product</th>
                <th style="padding: 8px;">Quantity</th>
                <th style="padding: 8px;">Unit Price</th>
                <th style="padding: 8px;">Total</th>
            </tr>
    """
    
    for item in items_with_details:
        html_body += f"""
            <tr>
                <td style="padding: 8px;">{item['brand_name']} {item['product_name']}</td>
                <td style="padding: 8px;">{item['quantity']}</td>
                <td style="padding: 8px;">${item['unit_price']:.2f}</td>
                <td style="padding: 8px;">${item['item_total']:.2f}</td>
            </tr>
        """
    
    html_body += f"""
        </table>
        <p><strong>Subtotal: ${subtotal:.2f}</strong></p>
        <p><strong>Tax (6.25%): ${tax_amount:.2f}</strong></p>
        <p><strong>Total: ${total_amount:.2f}</strong></p>
        <p>Your order is being processed. You'll receive another email when it's shipped.</p>
        <p>Thank you for shopping with us!<br>SneakerSpot Team</p>
    </body>
    </html>
    """
    
    return subject, body, html_body

def create_password_reset_email_content(user_info: Dict, reset_token: str) -> tuple[str, str, str]:
    subject = "Password Reset Request - SneakerSpot"
    
    # Create reset link (this would be your frontend URL)
    reset_link = f"http://localhost:3000/reset-password?token={reset_token}"
    
    # Plain text body
    body = f"Hi {user_info['first_name']},\n\n"
    body += "You requested a password reset for your SneakerSpot account.\n\n"
    body += f"Click the following link to reset your password:\n{reset_link}\n\n"
    body += "This link will expire in 1 hour.\n\n"
    body += "If you didn't request this password reset, please ignore this email.\n\n"
    body += "Best regards,\nSneakerSpot Team"
    
    # HTML body
    html_body = f"""
    <html>
    <body>
        <h2>Password Reset Request</h2>
        <p>Hi {user_info['first_name']},</p>
        <p>You requested a password reset for your SneakerSpot account.</p>
        <p>Click the following link to reset your password:</p>
        <p><a href="{reset_link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px;">Reset Password</a></p>
        <p>This link will expire in 1 hour.</p>
        <p>If you didn't request this password reset, please ignore this email.</p>
        <p>Best regards,<br>SneakerSpot Team</p>
    </body>
    </html>
    """
    
    return subject, body, html_body 