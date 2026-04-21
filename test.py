import smtplib
from email.mime.text import MIMEText

# Email details
sender = "sandheepk27@gmail.com"
receiver = "shanmathi0518@gmail.com"
password = "cuqigbhxcadsyjht"  # NOT your real password!

# Create message
msg = MIMEText("Hello! This is a test email sent from Python.")
msg["Subject"] = "Test Email"
msg["From"] = sender
msg["To"] = receiver

# Send email
with smtplib.SMTP("smtp.gmail.com", 587) as server:
    server.starttls()  # Secure connection
    server.login(sender, password)
    server.send_message(msg)

print("Email sent!")


# SES_SMTP_HOST=email-smtp.ap-south-1.amazonaws.com
# SES_SMTP_PORT=587
# SES_SMTP_USER=AKIAXUDMHHLLRI2QTNE4
# SES_SMTP_PASS=BErXIuBCumcwlEcyOOuJOLyRWu9pgVE/am8HWrnhywo3
# SES_SENDER_EMAIL=noreply@healthtracker.co.in