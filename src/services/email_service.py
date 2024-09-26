import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os
load_dotenv()

def send_verification_email(email: str, token: str):
    """
    Sends a verification email to the specified user.

    This function constructs and sends an email containing a verification 
    link to the user's email address. The link contains a token that the 
    user can click to verify their email.

    Args:
        email (str): The recipient's email address.
        token (str): A unique token used for email verification.

    Raises:
        Exception: If there is an issue with the email sending process.
    """
    sender_email = os.environ.get('EMAIL')
    receiver_email = email
    password = os.environ.get('EMAIL_PASSWORD')

    subject = "Verify your email address"
    body = f"Please verify your email by clicking the following link: http://localhost:8000/auth/verify/{token}"

    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = receiver_email
    message["Subject"] = subject

    message.attach(MIMEText(body, "plain"))

    with smtplib.SMTP("smtp.meta.ua", 465) as server:
        server.starttls()
        server.login(sender_email, password)
        server.send_message(message)
