import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
import logging

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
            return self._get_default_otp_template()
    
    def _get_default_otp_template(self) -> str:
        """Fallback OTP template if file is not found"""
        return """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Your Utakula OTP Code</title>
        </head>
        <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F3E3ED;">
            <table role="presentation" style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td align="center" style="padding: 40px 20px;">
                        <table role="presentation" style="max-width: 500px; width: 100%; margin: 0 auto; background-color: #FFFFFF; border-radius: 20px; overflow: hidden; box-shadow: 0 4px 20px rgba(16, 81, 0, 0.15);">
                            <tr>
                                <td style="background: linear-gradient(135deg, #105100 0%, #1a6600 100%); padding: 30px; text-align: center;">
                                    <h1 style="color: #FFFFFF; font-size: 32px; margin: 0 0 5px 0; font-weight: bold;">Utakula</h1>
                                    <p style="color: #FFE9F4; font-size: 14px; margin: 0;">Meals in your pocket.</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 40px 30px 20px 30px; text-align: center;">
                                    <div style="width: 80px; height: 80px; background: linear-gradient(135deg, #FFE9F4 0%, #F3E3ED 100%); border-radius: 50%; margin: 0 auto 20px auto; display: inline-flex; align-items: center; justify-content: center;">
                                        <span style="font-size: 40px;">🔐</span>
                                    </div>
                                    <h2 style="color: #105100; font-size: 24px; margin: 0 0 10px 0;">Verification Code</h2>
                                    <p style="color: #666666; font-size: 14px; margin: 0;">Enter this code to verify your account</p>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 0 30px 30px 30px; text-align: center;">
                                    <div style="background: linear-gradient(135deg, #FFE9F4 0%, #F3E3ED 100%); border: 3px dashed #105100; border-radius: 15px; padding: 25px 40px; display: inline-block;">
                                        <div style="font-size: 42px; font-weight: bold; color: #105100; letter-spacing: 8px; font-family: 'Courier New', monospace;">
                                            {OTP_CODE}
                                        </div>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 0 30px 30px 30px;">
                                    <div style="background-color: #F3E3ED; border-radius: 12px; padding: 20px;">
                                        <p style="color: #105100; font-size: 14px; margin: 0 0 12px 0; font-weight: 600;">⏰ This code will expire in 10 minutes</p>
                                        <p style="color: #666666; font-size: 13px; margin: 0;">If you didn't request this code, please ignore this email.</p>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 0 30px 30px 30px;">
                                    <div style="background-color: #FFF3CD; border-left: 4px solid #FF9800; border-radius: 8px; padding: 15px;">
                                        <p style="color: #856404; font-size: 12px; margin: 0;">
                                            <strong>🛡️ Security Tip:</strong> Never share this code with anyone.
                                        </p>
                                    </div>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 30px; background-color: #105100; text-align: center;">
                                    <p style="color: #FFE9F4; font-size: 13px; margin: 0 0 10px 0;">Need help? Contact us</p>
                                    <p style="color: #FFFFFF; font-size: 14px; margin: 0 0 15px 0;">
                                        <a href="mailto:support@utakula.co.ke" style="color: #FFFFFF; text-decoration: none;">📧 support@utakula.co.ke</a>
                                    </p>
                                    <p style="color: #FFE9F4; font-size: 11px; margin: 0;">
                                        © 2026 Utakula. All rights reserved.<br>
                                        <a href="https://utakula.arifulib.co.ke/privacy" style="color: #FFE9F4;">Privacy Policy</a>
                                    </p>
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

    def send_OTP_via_SMTP(self, recipient_email: str, otp: str):
        """
        Send OTP to user's email via SMTP with custom HTML template
        Args:
            recipient_email: Recipient's email address
            otp: One-time password code
        Returns:
            dict: Status and message of email sending operation
        """
        try:
            # Simple, spam-filter-friendly HTML template
            html_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Your Utakula Verification Code</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: Arial, sans-serif; background-color: #f5f5f5;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td align="center" style="padding: 40px 20px;">
                            <table role="presentation" style="max-width: 500px; width: 100%; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; border: 1px solid #e0e0e0;">
                                
                                <tr>
                                    <td style="background-color: #105100; padding: 30px; text-align: center;">
                                        <h1 style="color: #ffffff; font-size: 28px; margin: 0;">Utakula</h1>
                                        <p style="color: #ffffff; font-size: 14px; margin: 5px 0 0 0;">Meals in your pocket</p>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding: 40px 30px; text-align: center;">
                                        <h2 style="color: #105100; font-size: 22px; margin: 0 0 15px 0;">Verification Code</h2>
                                        <p style="color: #666666; font-size: 14px; margin: 0 0 25px 0; line-height: 1.5;">
                                            Please use the following code to verify your account:
                                        </p>
                                        
                                        <div style="background-color: #f0f0f0; border: 2px solid #105100; border-radius: 8px; padding: 20px; margin: 0 auto; display: inline-block;">
                                            <div style="font-size: 32px; font-weight: bold; color: #105100; letter-spacing: 5px; font-family: 'Courier New', monospace;">
                                                {otp}
                                            </div>
                                        </div>
                                        
                                        <p style="color: #999999; font-size: 13px; margin: 25px 0 0 0;">
                                            This code expires in 10 minutes
                                        </p>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <div style="background-color: #f9f9f9; border-radius: 6px; padding: 15px; border-left: 4px solid #105100;">
                                            <p style="color: #666666; font-size: 13px; margin: 0; line-height: 1.5;">
                                                <strong>Security Note:</strong> If you did not request this code, please ignore this email. 
                                                Never share this code with anyone.
                                            </p>
                                        </div>
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding: 20px 30px; background-color: #f5f5f5; text-align: center; border-top: 1px solid #e0e0e0;">
                                        <p style="color: #999999; font-size: 12px; margin: 0 0 5px 0;">
                                            Need help? Contact us at support@utakula.co.ke
                                        </p>
                                        <p style="color: #999999; font-size: 11px; margin: 0;">
                                            &copy; 2026 Utakula. All rights reserved.
                                        </p>
                                    </td>
                                </tr>

                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            # Create the email message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = "Your Utakula OTP Code"
            
            # Add headers to improve deliverability
            import time
            import uuid
            domain = self.sender_email.split('@')[1] if '@' in self.sender_email else 'utakula.co.ke'
            message["Message-ID"] = f"<{uuid.uuid4()}@{domain}>"
            message["Date"] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
            
            # Plain text fallback (cleaned up formatting)
            text_body = f"""Utakula - Meals in your pocket

                OTP Code

                Please use the following code to reset your password:

                {otp}

                This code expires in 10 minutes.

                Security Note: If you did not request this code, please ignore this email. 
                Never share this code with anyone.

                Need help? Contact us at support@utakula.co.ke

                © 2026 Utakula. All rights reserved.
            """
            
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
            
            logger.info(f"OTP sent successfully to {recipient_email}")
            return {
                "status": "success",
                "message": f"OTP sent successfully to {recipient_email}"
            }
            
        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP authentication failed for {self.sender_email}")
            return {
                "status": "error",
                "message": "SMTP authentication failed. Please check email credentials."
            }
        
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused for {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": f"Invalid recipient email address: {recipient_email}"
            }
        
        except smtplib.SMTPSenderRefused as e:
            logger.error(f"Sender refused: {str(e)}")
            return {
                "status": "error",
                "message": "Email sender address was refused by the server."
            }
        
        except smtplib.SMTPDataError as e:
            logger.error(f"SMTP data error sending OTP to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": "Email was rejected. Please try again or contact support."
            }
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending OTP to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send email. Please try again later."
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending OTP to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": "An unexpected error occurred. Please contact support."
            }
    
    def send_welcome_email(self, recipient_email: str, username: str) -> dict:
        """
        Send welcome email to new users
        
        Args:
            recipient_email: Recipient's email address
            username: User's name
            
        Returns:
            dict: Status and message of email sending operation
        """
        try:
            # Custom HTML template for welcome email
            html_body = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Welcome to Utakula!</title>
            </head>
            <body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #F3E3ED;">
                <table role="presentation" style="width: 100%; border-collapse: collapse;">
                    <tr>
                        <td align="center" style="padding: 40px 20px;">
                            <table role="presentation" style="max-width: 600px; width: 100%; margin: 0 auto; background-color: #FFFFFF; border-radius: 20px; overflow: hidden; box-shadow: 0 4px 20px rgba(16, 81, 0, 0.15);">
                                
                                <!-- Header -->
                                <tr>
                                    <td style="background: linear-gradient(135deg, #105100 0%, #1a6600 100%); padding: 40px 30px; text-align: center;">
                                        <h1 style="color: #FFFFFF; font-size: 42px; margin: 0 0 10px 0; font-weight: bold; letter-spacing: -1px;">Utakula</h1>
                                        <p style="color: #FFE9F4; font-size: 18px; margin: 0; font-weight: 300;">Meals in your pocket</p>
                                    </td>
                                </tr>

                                <!-- Welcome Icon -->
                                <tr>
                                    <td style="padding: 40px 30px 20px 30px; text-align: center;">
                                        <div style="width: 100px; height: 100px; background: linear-gradient(135deg, #FFE9F4 0%, #F3E3ED 100%); border-radius: 50%; margin: 0 auto 20px auto; display: inline-flex; align-items: center; justify-content: center; border: 4px solid #105100;">
                                            <span style="font-size: 50px;">🎉</span>
                                        </div>
                                        <h2 style="color: #105100; font-size: 32px; margin: 0 0 15px 0; font-weight: bold;">Welcome, {username}!</h2>
                                        <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0;">
                                            We're thrilled to have you join the Utakula family! Your journey to better meal planning starts now.
                                        </p>
                                    </td>
                                </tr>

                                <!-- Features Section -->
                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <div style="background-color: #FFE9F4; border-radius: 15px; padding: 30px;">
                                            <h3 style="color: #105100; font-size: 24px; margin: 0 0 25px 0; font-weight: bold; text-align: center;">What You Can Do Now:</h3>
                                            
                                            <!-- Feature 1 -->
                                            <table role="presentation" style="width: 100%; margin-bottom: 20px;">
                                                <tr>
                                                    <td style="width: 60px; vertical-align: top;">
                                                        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #105100 0%, #1a6600 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                                            <span style="font-size: 28px;">📅</span>
                                                        </div>
                                                    </td>
                                                    <td style="vertical-align: top; padding-left: 15px;">
                                                        <h4 style="color: #105100; font-size: 18px; margin: 0 0 8px 0; font-weight: bold;">Plan Your Week</h4>
                                                        <p style="color: #333333; font-size: 15px; line-height: 1.5; margin: 0;">Create meal plans for the entire week and say goodbye to daily meal stress!</p>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Feature 2 -->
                                            <table role="presentation" style="width: 100%; margin-bottom: 20px;">
                                                <tr>
                                                    <td style="width: 60px; vertical-align: top;">
                                                        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #105100 0%, #1a6600 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                                            <span style="font-size: 28px;">🔥</span>
                                                        </div>
                                                    </td>
                                                    <td style="vertical-align: top; padding-left: 15px;">
                                                        <h4 style="color: #105100; font-size: 18px; margin: 0 0 8px 0; font-weight: bold;">Track Your Calories</h4>
                                                        <p style="color: #333333; font-size: 15px; line-height: 1.5; margin: 0;">Use our TDEE calculator to understand your daily needs and monitor your intake.</p>
                                                    </td>
                                                </tr>
                                            </table>

                                            <!-- Feature 3 -->
                                            <table role="presentation" style="width: 100%; margin-bottom: 0;">
                                                <tr>
                                                    <td style="width: 60px; vertical-align: top;">
                                                        <div style="width: 50px; height: 50px; background: linear-gradient(135deg, #105100 0%, #1a6600 100%); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                                                            <span style="font-size: 28px;">⏰</span>
                                                        </div>
                                                    </td>
                                                    <td style="vertical-align: top; padding-left: 15px;">
                                                        <h4 style="color: #105100; font-size: 18px; margin: 0 0 8px 0; font-weight: bold;">Set Custom Reminders</h4>
                                                        <p style="color: #333333; font-size: 15px; line-height: 1.5; margin: 0;">Never miss a meal with personalized reminders tailored to your schedule.</p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Getting Started -->
                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <div style="background: linear-gradient(135deg, #F3E3ED 0%, #FFE9F4 100%); border-radius: 12px; padding: 25px; border-left: 5px solid #105100;">
                                            <h4 style="color: #105100; font-size: 20px; margin: 0 0 12px 0; font-weight: bold;">🚀 Ready to Get Started?</h4>
                                            <p style="color: #333333; font-size: 15px; line-height: 1.6; margin: 0 0 15px 0;">
                                                Here are some quick tips to make the most of Utakula:
                                            </p>
                                            <ul style="color: #333333; font-size: 14px; line-height: 1.8; margin: 0; padding-left: 20px;">
                                                <li>Complete your profile for personalized recommendations</li>
                                                <li>Set your daily calorie goals using the TDEE calculator</li>
                                                <li>Create your first meal plan for the week ahead</li>
                                                <li>Enable notifications so you never miss a meal</li>
                                            </ul>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Support Section -->
                                <tr>
                                    <td style="padding: 0 30px 30px 30px;">
                                        <div style="background-color: #FFF3CD; border-left: 4px solid #FF9800; border-radius: 8px; padding: 20px;">
                                            <p style="color: #856404; font-size: 14px; margin: 0 0 8px 0; font-weight: bold;">
                                                💡 Need Help?
                                            </p>
                                            <p style="color: #856404; font-size: 14px; line-height: 1.5; margin: 0;">
                                                We're here to support you! If you have any questions or feedback, don't hesitate to reach out to our support team at <a href="mailto:support@utakula.co.ke" style="color: #105100; text-decoration: none; font-weight: bold;">support@utakula.co.ke</a>
                                            </p>
                                        </div>
                                    </td>
                                </tr>

                                <!-- Social Media -->
                                <tr>
                                    <td style="padding: 30px; background-color: #F9F9F9; text-align: center; border-top: 1px solid #E0E0E0;">
                                        <h4 style="color: #105100; font-size: 18px; margin: 0 0 15px 0; font-weight: bold;">Stay Connected</h4>
                                        <p style="color: #666666; font-size: 14px; margin: 0 0 15px 0;">Follow us on social media for tips, recipes, and updates!</p>
                                        <table role="presentation" style="margin: 0 auto;">
                                            <tr>
                                                <td style="padding: 0 10px;">
                                                    <a href="https://www.instagram.com/utakulake/" style="color: #105100; text-decoration: none; font-size: 14px; font-weight: 600;">
                                                        📷 Instagram
                                                    </a>
                                                </td>
                                                <td style="padding: 0 10px;">
                                                    <a href="https://x.com/utakulaKE" style="color: #105100; text-decoration: none; font-size: 14px; font-weight: 600;">
                                                        🐦 Twitter
                                                    </a>
                                                </td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>

                                <!-- Footer -->
                                <tr>
                                    <td style="padding: 30px; background-color: #105100; text-align: center;">
                                        <p style="color: #FFE9F4; font-size: 15px; margin: 0 0 15px 0; font-weight: 500;">
                                            Thank you for choosing Utakula!
                                        </p>
                                        <p style="color: #FFFFFF; font-size: 14px; margin: 0 0 20px 0;">
                                            We're excited to be part of your meal planning journey. 🍽️
                                        </p>
                                        <p style="color: #FFE9F4; font-size: 12px; margin: 0;">
                                            © 2026 Utakula. All rights reserved.<br>
                                            <a href="https://utakula.arifulib.co.ke/privacy" style="color: #FFE9F4; text-decoration: none;">Privacy Policy</a>
                                        </p>
                                    </td>
                                </tr>

                            </table>
                        </td>
                    </tr>
                </table>
            </body>
            </html>
            """
            
            # Create the email message
            message = MIMEMultipart("alternative")
            message["From"] = self.sender_email
            message["To"] = recipient_email
            message["Subject"] = f"Welcome to Utakula, {username}! 🎉"
            
            # Add headers to improve deliverability
            import time
            import uuid
            domain = self.sender_email.split('@')[1] if '@' in self.sender_email else 'utakula.co.ke'
            message["Message-ID"] = f"<{uuid.uuid4()}@{domain}>"
            message["Date"] = time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
            
            # Plain text fallback
            text_body = f"""
            Welcome to Utakula, {username}!

            We're thrilled to have you join the Utakula family! Your journey to better meal planning starts now.

            What You Can Do Now:

            📅 Plan Your Week
            Create meal plans for the entire week and say goodbye to daily meal stress!

            🔥 Track Your Calories
            Use our TDEE calculator to understand your daily needs and monitor your intake.

            ⏰ Set Custom Reminders
            Never miss a meal with personalized reminders tailored to your schedule.

            Ready to Get Started?
            Here are some quick tips to make the most of Utakula:
            - Complete your profile for personalized recommendations
            - Set your daily calorie goals using the TDEE calculator
            - Create your first meal plan for the week ahead
            - Enable notifications so you never miss a meal

            Need Help?
            We're here to support you! If you have any questions or feedback, reach out at support@utakula.co.ke

            Stay Connected:
            Follow us on social media for tips, recipes, and updates!
            Instagram: https://www.instagram.com/utakulake/
            Twitter: https://x.com/utakulaKE

            Thank you for choosing Utakula!
            We're excited to be part of your meal planning journey.

            © 2026 Utakula. All rights reserved.
            Privacy Policy: https://utakula.arifulib.co.ke/privacy
            """
            
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
            
            logger.info(f"Welcome email sent successfully to {recipient_email}")
            return {
                "status": "success",
                "message": f"Welcome email sent successfully to {recipient_email}"
            }
            
        except smtplib.SMTPAuthenticationError:
            logger.error(f"SMTP authentication failed for {self.sender_email}")
            return {
                "status": "error",
                "message": "SMTP authentication failed. Please check email credentials."
            }
        
        except smtplib.SMTPRecipientsRefused as e:
            logger.error(f"Recipient refused for {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": f"Invalid recipient email address: {recipient_email}"
            }
        
        except smtplib.SMTPSenderRefused as e:
            logger.error(f"Sender refused: {str(e)}")
            return {
                "status": "error",
                "message": "Email sender address was refused by the server."
            }
        
        except smtplib.SMTPDataError as e:
            logger.error(f"SMTP data error sending welcome email to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": "Email was rejected. Please try again or contact support."
            }
        
        except smtplib.SMTPException as e:
            logger.error(f"SMTP error sending welcome email to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": f"Failed to send email. Please try again later."
            }
        
        except Exception as e:
            logger.error(f"Unexpected error sending welcome email to {recipient_email}: {str(e)}")
            return {
                "status": "error",
                "message": "An unexpected error occurred. Please contact support."
            }