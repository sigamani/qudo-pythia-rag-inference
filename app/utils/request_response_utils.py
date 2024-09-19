import json

from flask import make_response


def get_filters(request, allowed_filters):
    return {
        value: request.args.get(key, "").split(",") if value.endswith("__in") else request.args.get(key)
        for key, value in allowed_filters.items() if request.args.get(key)
    }


def make_json_response(data, status_code, headers=None):
    if not headers:
        headers = {'content-type': "application/json"}

    return make_response(json.dumps(data, default=str), status_code, headers)
