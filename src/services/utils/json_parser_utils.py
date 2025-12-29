import json
def maybe_parse_json(raw, expects_json):
    if expects_json and isinstance(raw, str):
        try:
            return json.loads(raw)
        except:
            pass
    return raw