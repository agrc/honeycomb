#!/usr/bin/env python
# * coding: utf8 *
"""
messaging.py

A module that contains a method for sending emails
"""

from os import environ

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from .config import get_config_value
from .log import logger


def send_email(subject, body):
    """
    subject: string
    body: string | MIMEMultipart

    Send an email.
    """
    from_address = "honeycomb@utah.gov"
    to = get_config_value("notify")
    if not isinstance(to, str):
        to_addresses = ",".join(to)
    else:
        to_addresses = to
    api_key = environ.get("HONEYCOMB_SENDGRID_API_KEY")

    if None in [api_key]:
        logger.warning(
            "Required environment variables for sending emails do not exist. No emails sent. See README.md for more details."
        )

        return False

    if get_config_value("sendEmails"):
        message = Mail(from_email=from_address, to_emails=to_addresses, subject=subject, plain_text_content=body)

        try:
            client = SendGridAPIClient(api_key)

            client.send(message)

            return False
        except Exception as e:
            logger.error(f"Error sending email with SendGrid: {e}")

            return False

    logger.warning("sendEmails is False. No email sent.")

    return True
