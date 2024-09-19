import logging
from http import HTTPStatus

from flask import Blueprint, jsonify, make_response

from app.middlewares.auth.authorization import AuthorizationError

errors = Blueprint("errors", __name__)

logger = logging.getLogger("qudo")


def return_error(error, message):
    response = {
        "success": False,
        "error": {"code": error.value, "type": error.name, "message": message, "description": error.description},
    }
    return make_response(jsonify(response), error.value)


@errors.app_errorhandler(400)
def handle_400(e):
    logger.debug(e)
    return return_error(HTTPStatus.BAD_REQUEST, message=e.description)


@errors.app_errorhandler(401)
def handle_401(e):
    logger.debug(e)
    e.description = "Your authentication information is incorrect. Please try again."
    return return_error(HTTPStatus.UNAUTHORIZED, message=e.description)


@errors.app_errorhandler(403)
def handle_403(e):
    logger.debug(e)
    e.description = "You don't have permission to perform this action"
    return return_error(HTTPStatus.FORBIDDEN, message=e.description)


@errors.app_errorhandler(404)
def handle_does_not_exist(e):
    logger.debug(e)
    return return_error(HTTPStatus.NOT_FOUND, message=e.description)


@errors.app_errorhandler(409)
def handle_conflict(e):
    logger.debug(e)
    return return_error(HTTPStatus.CONFLICT, message=e.description)


@errors.app_errorhandler(Exception)
def handle_unexpected_error(e):
    logger.exception(e)

    return return_error(HTTPStatus.INTERNAL_SERVER_ERROR, message="An unexpected error has occurred.")


@errors.app_errorhandler(AuthorizationError)
def handle_unexpected_error(e):
    logger.exception(e)

    return return_error(HTTPStatus.FORBIDDEN, message=e.message)
