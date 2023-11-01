from django.conf import settings
from twilio.rest import Client

account_sid = settings.TWILIO_ACCOUNT_SID
service_sid = settings.TWILIO_SERVICE_SID
auth_token = settings.TWILIO_AUTH_TOKEN


def get_twilio_client():
    return Client(account_sid, auth_token)


def send_whatsapp_code(phone):
    client = get_twilio_client()
    verification = client.verify.v2.services(service_sid).verifications.create(to=f'+966{phone[1:]}', channel='whatsapp')

    if verification.status == 'pending':
        return True
    return False


def check_code(phone, code):
    client = get_twilio_client()
    verification_check = client.verify.v2.services(service_sid).verification_checks.create(to=f'+966{phone[1:]}', code=code)
    if verification_check.status == 'approved':
        return True
    return False

