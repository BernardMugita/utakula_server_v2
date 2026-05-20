import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging
import time
import uuid

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via SMTP"""
    
    def __init__(self):
        self.sender_email = os.getenv("SMTP_EMAIL")
        self.sender_password = os.getenv("SMTP_SENDER_PASSWORD")
        self.smtp_server = os.getenv("SMTP_SERVER")
        self.smtp_port = int(os.getenv("SMTP_PORT", 465))
        
        # Path to email templates
        self.templates_dir = Path(__file__).parent / "email_templates"
        
    def _load_template(self, template_name: str) -> str:
        """Load HTML email template from file"""
        template_path = self.templates_dir / template_name
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                return file.read()
        except FileNotFoundError:
            logger.error(f"Email template not found: {template_path}")
            return "<html><body>{CONTENT}</body></html>"
    
    def _send_email(self, recipient_email: str, subject: str, html_body: str, text_body: str) -> dict:
        """Generic helper to send email via SMTP"""
        try:
            # Create the email message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = subject
            
            # Add headers to improve deliverability
            domain = self.sender_email.split('@')[1] if '@' in self.sender_email else 'utakula.co.ke'
            message["Message-ID"] = f"<{uuid.uuid4()}@{domain}>"
            message["Date"] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
            
            # Attach both plain text and HTML versions
            part1 = MIMEText(text_body, "plain", "utf-8")
            part2 = MIMEText(html_body, "html", "utf-8")
            
            message.attach(part1)
            message.attach(part2)
            
            # Send email via SMTP
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    recipient_email,
                    message.as_string()
                )
            
            logger.info(f"Email '{subject}' sent successfully to {recipient_email}")
            return {
                "status": "success",
                "message": f"Email sent successfully to {recipient_email}"
            }
        except Exception as e:
            logger.error(f"Error sending email '{subject}' to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": str(e)
            }

    def send_support_email(self, recipient_email: str, user_name: str, user_email: str, subject: str, message: str) -> dict:
        """Send support request to the support team"""
        template = self._load_template("support_request_template.html")
        html_body = template.format(
            USER_NAME=user_name,
            USER_EMAIL=user_email,
            SUBJECT=subject,
            MESSAGE=message
        )
        text_body = f"New Support Request\n\nName: {user_name}\nEmail: {user_email}\nSubject: {subject}\n\nMessage:\n{message}"
        
        return self._send_email(recipient_email, f"Support Request: {subject}", html_body, text_body)

    def send_acknowledgment_email(self, recipient_email: str, user_name: str, subject: str, message: str) -> dict:
        """Send acknowledgment email to the user"""
        template = self._load_template("support_acknowledgment_template.html")
        html_body = template.format(
            USER_NAME=user_name,
            SUBJECT=subject,
            MESSAGE=message
        )
        text_body = f"Hello {user_name},\n\nThank you for reaching out. We've received your message regarding '{subject}' and will get back to you soon.\n\nYour message:\n{message}"
        
        return self._send_email(recipient_email, f"We've received your request: {subject}", html_body, text_body)

    def send_OTP_via_SMTP(self, recipient_email: str, otp: str):
        """Send OTP to user's email via SMTP"""
        template = self._load_template("otp_email_template.html")
        html_body = template.replace("{OTP_CODE}", otp)
        text_body = f"Your Utakula verification code is: {otp}"
        return self._send_email(recipient_email, "Your Utakula OTP Code", html_body, text_body)

    def send_welcome_email(self, recipient_email: str, username: str) -> dict:
        """Send welcome email to new users"""
        template = self._load_template("welcome_email_template.html")
        html_body = template.format(USER_NAME=username)
        text_body = f"Welcome to Utakula, {username}! We're thrilled to have you join the family."
        return self._send_email(recipient_email, f"Welcome to Utakula, {username}! 🎉", html_body, text_body)
