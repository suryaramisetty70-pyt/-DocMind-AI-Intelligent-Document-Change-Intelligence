"""Email service for sending OTP and notifications."""
import smtplib
import os
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(env_path)

logger = logging.getLogger(__name__)


class EmailService:
    """Email service using SMTP."""
    
    def __init__(self):
        import base64
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "suryaramisetty70@gmail.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", base64.b64decode("Y2ppbm1jcHV0YW13Z3BsbA==").decode('utf-8'))
        self.from_email = os.getenv("SMTP_FROM", self.smtp_user)
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.enabled = bool(self.smtp_user and self.smtp_password)
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """
        Send an email.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Plain text body
            html_body: Optional HTML body
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.enabled:
            logger.warning(f"Email service not configured. Would send to {to_email}: {subject}")
            print(f"\n{'='*50}")
            print(f"📧 EMAIL (not sent - configure SMTP)")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body: {body}")
            print(f"{'='*50}\n")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add plain text
            msg.attach(MIMEText(body, 'plain'))
            
            # Add HTML if provided
            if html_body:
                msg.attach(MIMEText(html_body, 'html'))
            
            # Connect and send
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.from_email, to_email, msg.as_string())
            
            logger.info(f"Email sent successfully to {to_email}")
            print(f"\n{'='*50}")
            print(f"✅ EMAIL SENT")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"{'='*50}\n")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            print(f"\n{'='*50}")
            print(f"❌ EMAIL FAILED")
            print(f"To: {to_email}")
            print(f"Error: {str(e)}")
            print(f"{'='*50}\n")
            return False
    
    def send_otp(self, to_email: str, otp: str) -> bool:
        """Send OTP email."""
        subject = "Your DocFinder Verification Code"
        body = f"""
Your verification code is: {otp}

This code will expire in 10 minutes.

If you didn't request this code, please ignore this email.

- DocFinder Team
        """
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ background-color: white; border-radius: 10px; padding: 30px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        .code {{ font-size: 32px; font-weight: bold; color: #4F46E5; text-align: center; letter-spacing: 5px; padding: 20px; background: #f0f0f0; border-radius: 5px; margin: 20px 0; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h2 style="color: #333;">DocFinder Verification</h2>
        <p>Your verification code is:</p>
        <div class="code">{otp}</div>
        <p>This code will expire in <strong>10 minutes</strong>.</p>
        <p>If you didn't request this code, please ignore this email.</p>
        <div class="footer">
            <p>📄 DocFinder - Intelligent Document Comparison</p>
        </div>
    </div>
</body>
</html>
        """
        return self.send_email(to_email, subject, body, html_body)
    
    def send_welcome_email(self, to_email: str, username: str) -> bool:
        """Send welcome email after successful registration."""
        subject = "Welcome to DocFinder!"
        body = f"""
Welcome to DocFinder, {username}!

Your account has been successfully created. You can now:
- Compare documents (Text, PDF, Excel, CSV)
- Save your comparison history
- Access AI-powered document analysis

Get started by logging in and uploading your first document!

- DocFinder Team
        """
        html_body = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
        .container {{ background-color: white; border-radius: 10px; padding: 30px; max-width: 500px; margin: 0 auto; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h2 {{ color: #4F46E5; }}
        .features {{ background: #f9f9f9; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .features li {{ margin: 5px 0; }}
        .footer {{ color: #666; font-size: 12px; margin-top: 20px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h2>Welcome to DocFinder, {username}! 🎉</h2>
        <p>Your account has been successfully created.</p>
        <div class="features">
            <p><strong>You can now:</strong></p>
            <ul>
                <li>📄 Compare documents (Text, PDF, Excel, CSV)</li>
                <li>💾 Save your comparison history</li>
                <li>🤖 Access AI-powered document analysis</li>
            </ul>
        </div>
        <p>Get started by logging in and uploading your first document!</p>
        <div class="footer">
            <p>📄 DocFinder - Intelligent Document Comparison</p>
        </div>
    </div>
</body>
</html>
        """
        return self.send_email(to_email, subject, body, html_body)


# Global email service instance
email_service = EmailService()
