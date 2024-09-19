import os

from flask import Flask

from app.blueprints.admin.api import admin_bp
from app.blueprints.conversations.api import conversation_bp
from app.blueprints.error_handler.errors import errors
from app.blueprints.messages.api import message_bp
from app.blueprints.messages.v2.api import message_v2_bp
from app.blueprints.ping.api import ping_blueprint
from app.blueprints.trials.api import trial_bp
from app.middlewares.before_request.set_user import set_user
from app.settings import config


def setup_app():
    app = Flask(__name__)
    app.register_blueprint(ping_blueprint, url_prefix="/v1/ping")
    app.register_blueprint(conversation_bp, url_prefix="/v1/conversation")
    app.register_blueprint(message_bp, url_prefix="/v1/message")
    app.register_blueprint(message_v2_bp, url_prefix="/v2/message")
    app.register_blueprint(admin_bp, url_prefix="/v1/admin")
    app.register_blueprint(trial_bp, url_prefix="/v1/trial")
    app.register_blueprint(errors)

    config_name = os.getenv("QUDO_ENV")
    if not config_name:
        config_name = "development"
    app.config.from_object(config.app_config[config_name])

    app.before_request_funcs = {"conversation_api": [set_user], "message_api": [set_user], "message_v2_api": [set_user]}

    @app.after_request
    def set_default_content_type(response):
        if response.headers.get("content-type") not in ["application/pdf", "application/json", "text/html"]:
            response.headers["content-type"] = "application/json"
        return response

    return app
