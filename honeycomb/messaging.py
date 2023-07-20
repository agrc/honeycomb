#!/usr/bin/env python
# * coding: utf8 *
"""
messaging.py

A module that contains a method for sending emails
"""

from email.mime.text import MIMEText
from os import environ
from smtplib import SMTP

from .config import get_config_value
from .log import logger


def send_email(subject, body):
    """
    subject: string
    body: string | MIMEMultipart
    """
    from_address = "honeycomb@utah.gov"
    smtp_server = environ.get("HONEYCOMB_SMTP_SERVER")
    smtp_port = environ.get("HONEYCOMB_SMTP_PORT")

    if None in [smtp_server, smtp_port]:
        logger.warning(
            "Required environment variables for sending emails do not exist. No emails sent. See README.md for more details."
        )
        return

    to = get_config_value("notify")
    if not isinstance(to, str):
        to_addresses = ",".join(to)
    else:
        to_addresses = to

    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = from_address
    message["To"] = to_addresses

    if get_config_value("sendEmails"):
        smtp = SMTP(smtp_server, smtp_port)
        smtp.sendmail(from_address, to, message.as_string())
        smtp.quit()

        return False

    logger.warning("sendEmails is False. No email sent.")

    return True
