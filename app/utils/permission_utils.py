def filter_allowed_data(data, schema, method):
    if not schema:
        return data
    print(schema)
    output = {}
    for key, value in schema.items():
        if isinstance(value, dict):
            output[key] = filter_allowed_data(data.get(key, {}), value, method)
        else:
            if method <= value and key in data:
                output[key] = data[key]
    return output


def get_max(obj, val):
    if val == 1:
        return 1
    output = {}
    for key, value in obj.items():
        if isinstance(value, int):
            output[key] = max(value, val)
        elif isinstance(value, dict):
            output[key] = get_max(value, val)
        else:
            output[key] = val
    return output


def merge_permissions(p1, p2):
    output = {}
    keys = set(p1.keys()).union(set(p2.keys()))
    for key in keys:
        if isinstance(p1[key], int) and isinstance(p2[key], int):
            output[key] = max(p1[key], p2[key])
        elif isinstance(p1[key], dict) and isinstance(p2[key], dict):
            output[key] = merge_permissions(p1[key], p2[key])
        elif isinstance(p1[key], dict) and isinstance(p2[key], int):
            output[key] = get_max(p1[key], p2[key])
        elif isinstance(p1[key], int) and isinstance(p2[key], dict):
            output[key] = get_max(p2[key], p1[key])
    return output

