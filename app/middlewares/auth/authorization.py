from functools import wraps

from flask_jwt_extended import get_jwt, verify_jwt_in_request


class AuthorizationError(Exception):
    """Exception raised in case the user is not Authorized.

    Attributes:
        role -- The role that's required
        message -- explanation of the error
    """

    def __init__(self, allowed_roles, message="The user is not authorized for this action"):
        self.allowed_roles = allowed_roles
        self.message = message
        super().__init__(self.message)


def authorized(roles):
    def check_roles(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_roles = [role["name"] for role in claims["role"]]
            allowed_roles = roles
            if any([role in allowed_roles for role in user_roles]):
                return fn(*args, **kwargs)
            raise AuthorizationError(allowed_roles)

        return wrapper

    return check_roles
