from flask_cors import CORS
from flask_jwt_extended import JWTManager

from app.factories.application import setup_app
from app.factories.logging import setup_logging
from app.factories.mongo_db import setup_mongo_db
from app.factories.redis_db import setup_redis_db
from app.factories.sentry import setup_sentry

flask_app = setup_app()
setup_logging()
setup_sentry(flask_app)

mongo_client = setup_mongo_db(flask_app)
jwt = JWTManager(flask_app)
redis_db = setup_redis_db(flask_app)

CORS(flask_app, expose_headers="*")


if __name__ == "__main__":
    flask_app.run()
