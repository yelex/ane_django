import logging

from django.urls import reverse
from parser_app.logic.total import Total
# from django.core.mail import send_mail
from anehome.celery import celery_app


@celery_app.task
def send_verification_email(user_id):
    pass


@celery_app.task
def snap_get():
    try:
        Total().printer_test()
    except Exception as e:
        logging.warning("Exception has been occured: '%s'" % e)
