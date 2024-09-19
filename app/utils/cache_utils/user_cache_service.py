import json
import logging

from flask import current_app

from .auth_service_utils import AuthService

logger = logging.getLogger("qudo")


class UserCacheService:
    def __init__(self, user_id):
        self.timeout = 3600
        self.user_id = user_id
        self.auth_token = current_app.config["AUTH_ADMIN_TOKEN"]

    def get_data(self):
        from app.utils.redis_util import RedisUtil

        data = RedisUtil.get_cached_data("user__%s" % self.user_id)
        if not data:
            auth_service = AuthService(self.auth_token)
            data = auth_service.get_user_data_by_id(self.user_id)
            if not data:
                raise Exception("Could not find user for id: %s" % self.user_id)
            self.set_data(data)
        else:
            data = str(data, "utf-8")
            data = json.loads(data)
        return data

    def set_data(self, data):
        from app.utils.redis_util import RedisUtil

        data = json.dumps(data)
        RedisUtil.set_cache_data("user__%s" % self.user_id, data, self.timeout)

    def invalidate_cache(self):
        from app.utils.redis_util import RedisUtil

        RedisUtil.invalidate_cache_data("user__%s" % self.user_id)


def get_users_name(user_id):
    try:
        cache_service = UserCacheService(user_id)
        user_info = cache_service.get_data()["user"]
        return "%s %s" % (user_info["first_name"], user_info["last_name"])
    except Exception as error:
        logger.info("Error occured while fetchin user details: %s", error)


def get_user(user_id):
    cache_service = UserCacheService(user_id)
    user_info = cache_service.get_data()
    user_info["name"] = f'{user_info["first_name"]} {user_info["last_name"]}'
    return user_info


def get_auth_user(user_id):
    cache_service = UserCacheService(user_id)
    user_info = cache_service.get_data()
    return user_info
