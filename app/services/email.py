import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings

def send_otp_email(to_email: str, otp: str, user_name: str = "there"):
    if not settings.SES_SMTP_USER or settings.SES_SMTP_USER == "placeholder":
        # log OTP to console when email is not configured yet
        print(f"\n{'='*40}")
        print(f"OTP for {to_email}: {otp}")
        print(f"{'='*40}\n")
        return True

    subject = "Your Health Tracker OTP"

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="font-family: 'Helvetica Neue', Arial, sans-serif; background: #f5f4f0; padding: 2rem;">
      <div style="max-width: 480px; margin: 0 auto; background: #fff; border-radius: 14px; padding: 2rem; border: 0.5px solid rgba(0,0,0,0.1);">
        <h2 style="font-size: 20px; font-weight: 700; margin-bottom: 0.5rem; color: #1a1a18;">
          Password reset
        </h2>
        <p style="font-size: 14px; color: #6b6a66; margin-bottom: 1.5rem;">
          Hi {user_name}, here is your OTP to reset your Health Tracker password.
        </p>
        <div style="background: #f0ede8; border-radius: 10px; padding: 1.5rem; text-align: center; margin-bottom: 1.5rem;">
          <div style="font-family: 'Courier New', monospace; font-size: 36px; font-weight: 700;
            letter-spacing: 12px; color: #1a1a18;">
            {otp}
          </div>
        </div>
        <p style="font-size: 12px; color: #9e9d99;">
          This OTP expires in <strong>10 minutes</strong>. Do not share it with anyone.
        </p>
        <p style="font-size: 12px; color: #9e9d99; margin-top: 0.5rem;">
          If you did not request this, you can safely ignore this email.
        </p>
        <div style="border-top: 0.5px solid rgba(0,0,0,0.1); margin-top: 1.5rem; padding-top: 1rem;">
          <p style="font-size: 11px; color: #9e9d99; margin: 0;">
            Health Tracker · healthtracker.co.in
          </p>
        </div>
      </div>
    </body>
    </html>
    """

    text_body = f"Your Health Tracker OTP is: {otp}\nExpires in 10 minutes."

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SES_SENDER_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(settings.SES_SMTP_HOST, settings.SES_SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SES_SMTP_USER, settings.SES_SMTP_PASS)
            server.sendmail(settings.SES_SENDER_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email send error: {e}")
        return False