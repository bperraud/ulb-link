from django.core.mail import send_mail
import smtplib

smtplib.SMTP.debuglevel = 1

send_mail(
    subject="Test email",
    message="Hello from Django",
    from_email=None,
    recipient_list=["benjamin.perraudin@ulb.be"],
)
