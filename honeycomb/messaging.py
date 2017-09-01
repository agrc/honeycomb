#!/usr/bin/env python
# * coding: utf8 *
'''
messaging.py

A module that contains a method for sending emails
'''

from .config import get_config_value
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from os import environ
from smtplib import SMTP


def send_email(subject, body):
    '''
    subject: string
    body: string | MIMEMultipart
    '''
    from_address = 'busybee@utah.gov'
    smtp_server = environ.get('HONEYCOMB_SMTP_SERVER')
    smtp_port = environ.get('HONEYCOMB_SMTP_PORT')

    if None in [smtp_server, smtp_port]:
        print('Required environment variables for sending emails do not exist. No emails sent. See README.md for more details.')
        return

    to = get_config_value('notify')
    if not isinstance(to, str):
        to_addresses = ','.join(to)
    else:
        to_addresses = to

    if isinstance(body, str):
        message = MIMEMultipart()
        message.attach(MIMEText(body, 'html'))
    else:
        message = body

    message['Subject'] = subject
    message['From'] = from_address
    message['To'] = to_addresses

    if get_config_value('sendEmails'):
        smtp = SMTP(smtp_server, smtp_port)
        smtp.sendmail(from_address, to, message.as_string())
        smtp.quit()

        return smtp

    print('sendEmails is False. No email sent.')
