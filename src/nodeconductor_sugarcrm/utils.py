import logging

from django.core.mail import send_mail


logger = logging.getLogger(__name__)


def sms_user_password(crm, phone, password):
    options = crm.service_project_link.service.settings.options or {}
    sender = options.get('sms_email_from')
    recipient = options.get('sms_email_rcpt')

    if sender and recipient and '{phone}' in recipient:
        send_mail(
            '', 'Your OTP is: %s' % password, sender,
            [recipient.format(phone=phone)], fail_silently=True)
    else:
        logger.warning('SMS was not sent to SugarCRM user, because `sms_email_from` and `sms_email_rcpt` '
                       'were not configured properly.')