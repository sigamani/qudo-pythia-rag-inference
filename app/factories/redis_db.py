import redis


def setup_redis_db(app):
    # TODO: write some code to disconnect and close the connection on program exit
    redis_db = redis.Redis(host=app.config['REDIS_URL'], port=app.config['REDIS_PORT'], db=app.config["REDIS_DB"])
    return redis_db

