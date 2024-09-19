from flask import current_app, g, request
from flask_jwt_extended import (
    get_jwt,
    get_jwt_identity,
    jwt_required,
    verify_jwt_in_request,
)
from flask_jwt_extended.exceptions import NoAuthorizationError


@jwt_required()
def check_valid_token(auth_token):
    user = get_jwt_identity()
    if not user:
        raise NoAuthorizationError("User token expired/invalid")
    verify_jwt_in_request()
    auth_token = auth_token.replace("Bearer ", "")
    payload = get_jwt()
    roles = [role["name"] for role in payload["role"]]
    g.user = {"id": str(user), "is_user": True}
    g.permissions = {}
    g.global_filters = {}
    g.roles = roles


def set_user():
    if request.method in ["PUT", "DELETE", "POST", "GET", "PATCH"]:
        auth_token = request.headers.get(current_app.config["JWT_HEADER_NAME"]) or request.args.get(
            current_app.config["JWT_QUERY_STRING_NAME"]
        )
        if not auth_token:
            raise NoAuthorizationError("User token is missing")
        return check_valid_token(auth_token)
