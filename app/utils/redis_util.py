from app.flask_app import redis_db


class RedisUtil:

    @staticmethod
    def get_cached_data(key):
        return redis_db.get(key)

    @staticmethod
    def set_cache_data( key, data, timeout):
        redis_db.set(key, data, timeout)

    @staticmethod
    def invalidate_cache_data(key):
        redis_db.delete(key)
