from django.core.mail import send_mail
from django.template.loader import render_to_string


def send_notification(subject, to_list, template, context):
    msg_plain = render_to_string(template, context)
    msg_html = render_to_string(template, context)
    fromemail = "walkman5411@gmail.com"
    send_mail(
        subject,
        msg_plain,
        fromemail,
        to_list,
        html_message=msg_html,
    )