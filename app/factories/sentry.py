import logging

import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from sentry_sdk.integrations.logging import LoggingIntegration
from sentry_sdk.integrations.redis import RedisIntegration


def setup_sentry(app):
    sentry_logging = LoggingIntegration(
        level=logging.INFO, event_level=logging.ERROR  # Capture info and above as breadcrumbs  # Send errors as events
    )

    sentry_sdk.init(
        environment=app.config["NAME"],
        dsn="https://a9b24eb7516f499bccae9017b3fc4132@o1053323.ingest.sentry.io/4506020047159296",
        traces_sample_rate=1.0,
        integrations=[sentry_logging, FlaskIntegration(), RedisIntegration()],
    )
