import logging
import os

logger = logging.getLogger("qudo")

mongo_db_password = None
openai_key = None
mongo_private_key = None
try:
    mongo_db_password = os.environ["mongo_db_password"]
    openai_key = os.environ["openai_api_key"]
    mongo_private_key = os.environ["mongo_private_key"]

except KeyError:
    logger.warning("Either Mongodb password /openai key/mongo private key is not set in the os environment")

jwt_secret_key = os.environ.get("JWT_SECRET_KEY", default=None)


class Config(object):
    """Parent configuration class."""

    DEBUG = False
    CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
    NAME = "development"  # change it to APP_ENV

    S3_DS_ENVIRONMENT = "prod"  # TODO: change it to staging
    MONGO_DB_URL = "mongodb://localhost:27017/pythia-api-service"
    REDIS_URL = "localhost"
    REDIS_PORT = "6379"
    REDIS_DB = 0

    JWT_TOKEN_LOCATION = ["headers", "query_string"]
    JWT_HEADER_NAME = "Authorization"
    JWT_QUERY_STRING_NAME = "token"
    JWT_HEADER_TYPE = "Bearer"
    JWT_SECRET_KEY = jwt_secret_key

    PER_PAGE = 20
    MAX_PER_PAGE = 100
    OPENAI_API_KEY = openai_key
    ATLAS_API = (
        '"https://cloud.mongodb.com/api/atlas/v1.0/groups/6387f132c29b70062dc8fbe8/clusters/staging-cluster/fts/indexes"'
    )
    MONGODB_ATLAS_CLUSTER_URI = "https://cloud.mongodb.com/api/atlas/v1.0/groups/6387f132c29b70062dc8fbe8"
    DB_NAME = "pythia-api-service"
    ATLAS_VECTOR_SEARCH_INDEX_NAME = "default_search_index"
    MONGO_PUBLIC_KEY = "hhjjqgao"
    MONGO_PRIVATE_KEY = mongo_private_key
    MONGO_CLUSTER = "staging-cluster"
    MONGO_GROUP_ID = "6387f132c29b70062dc8fbe8"

    AUTH_ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY5Njg1MjY5MSwianRpIjoiMTM1YzVmMGEtNjdmMi00NzE0LTg0ZjMtNGEzMzU1Y2M4ZWY5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjk2ODUyNjkxLCJleHAiOjE4NTQ1MzI2OTEsInJvbGUiOlt7ImlkIjoxLCJuYW1lIjoiU1VQRVJfQURNSU4ifSx7ImlkIjozLCJuYW1lIjoiU1RBTkRBUkQifSx7ImlkIjo3LCJuYW1lIjoiTEFCX1VTRVIifV0sIm5hbWUiOiJQcmF2ZWVuIFRpd2FyaSIsInN0YXR1cyI6IkFjdGl2ZSIsImFjY291bnQiOnsiaWQiOiJhMzBlZWQ1YWI3NWY0NDVlYTUyOWMzYWQ2MDMzYzRiMiIsIm5hbWUiOiJRdWRvIiwidXNlcnMiOjI0fX0.xCbpGi6l5sGy9haahElF2Z3IpXRFGdpVeJwDgAK750c"
    AUTH_SERVICE_API = "https://staging-auth-service.qudo.ai"

    TRIAL_THRESHOLD = 20


class DevelopmentConfig(Config):
    """Configurations for Development."""

    DEBUG = True


class DockerConfig(DevelopmentConfig):
    CELERY_BROKER_URL = "redis://redis:6379/0"
    MONGO_DB_URL = f"mongodb+srv://staging_service:{mongo_db_password}@staging-cluster.v9ht4.mongodb.net/pythia-api-service?retryWrites=true&w=majority&ssl=true"


class TestingConfig(Config):
    """Configurations for Testing, with a separate test database."""

    TESTING = True
    DEBUG = True
    NAME = "testing"
    MONGO_DB_URL = "mongodb://localhost/pythia-api-service"


class StagingConfig(Config):
    """Configurations for Staging."""

    DEBUG = True
    NAME = "staging"
    MONGO_DB_URL = f"mongodb+srv://staging_service:{mongo_db_password}@staging-cluster.v9ht4.mongodb.net/pythia-api-service?retryWrites=true&w=majority&ssl=true"

    S3_DS_ENVIRONMENT = "prod"  # TODO: change it to staging
    REDIS_URL = "staging-redis.odgsx0.ng.0001.use1.cache.amazonaws.com"
    REDIS_DB = 1
    REDIS_PORT = "6379"
    AUTH_ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY5Njg1MjY5MSwianRpIjoiMTM1YzVmMGEtNjdmMi00NzE0LTg0ZjMtNGEzMzU1Y2M4ZWY5IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjk2ODUyNjkxLCJleHAiOjE4NTQ1MzI2OTEsInJvbGUiOlt7ImlkIjoxLCJuYW1lIjoiU1VQRVJfQURNSU4ifSx7ImlkIjozLCJuYW1lIjoiU1RBTkRBUkQifSx7ImlkIjo3LCJuYW1lIjoiTEFCX1VTRVIifV0sIm5hbWUiOiJQcmF2ZWVuIFRpd2FyaSIsInN0YXR1cyI6IkFjdGl2ZSIsImFjY291bnQiOnsiaWQiOiJhMzBlZWQ1YWI3NWY0NDVlYTUyOWMzYWQ2MDMzYzRiMiIsIm5hbWUiOiJRdWRvIiwidXNlcnMiOjI0fX0.xCbpGi6l5sGy9haahElF2Z3IpXRFGdpVeJwDgAK750c"
    AUTH_SERVICE_API = "https://staging-auth-service.qudo.ai"


class ProductionConfig(Config):
    """Configurations for Production."""

    DEBUG = False
    TESTING = False
    CELERY_BROKER_URL = "redis://production-redis.a9qdyp.ng.0001.aps1.cache.amazonaws.com:6379/0"
    NAME = "production"
    MONGO_DB_URL = f"mongodb+srv://qudo-user:{mongo_db_password}@prod-mongo-db.v9ht4.mongodb.net/pythia-api-service?retryWrites=true&w=majority&ssl=true"
    REDIS_URL = "production-redis.uaq43i.ng.0001.euw2.cache.amazonaws.com"
    REDIS_DB = 1
    AUTH_ADMIN_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTY5Njg1MjYyMCwianRpIjoiMTI0NjdjODktN2E5Ni00NmU1LThlZjMtOWNhZGRmOGEzOTM2IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6MSwibmJmIjoxNjk2ODUyNjIwLCJleHAiOjE4NTQ1MzI2MjAsInJvbGUiOlt7ImlkIjoxLCJuYW1lIjoiU1VQRVJfQURNSU4ifSx7ImlkIjozLCJuYW1lIjoiU1RBTkRBUkQifSx7ImlkIjo3LCJuYW1lIjoiTEFCX1VTRVIifV0sIm5hbWUiOiJQcmF2ZWVuIFRpd2FyaSIsInN0YXR1cyI6IkFjdGl2ZSIsImFjY291bnQiOnsiaWQiOiJhMzBlZWQ1YWI3NWY0NDVlYTUyOWMzYWQ2MDMzYzRiMiIsIm5hbWUiOiJRdWRvIiwidXNlcnMiOjI0fX0.EkbFCFZ2dhRdUQbv97QHTTJvUJLzgUoHJrQQGJYDkZc"
    AUTH_SERVICE_API = "https://auth-api.qudo.ai"
    S3_DS_ENVIRONMENT = "prod"
    MONGO_CLUSTER = "prod-mongo-db"
    ATLAS_API = (
        '"https://cloud.mongodb.com/api/atlas/v1.0/groups/6387f132c29b70062dc8fbe8/clusters/prod-mongo-db/fts/indexes"'
    )


app_config = {
    "development": DevelopmentConfig,
    "docker": DockerConfig,
    "testing": TestingConfig,
    "staging": StagingConfig,
    "production": ProductionConfig,
}
