from functools import wraps

from flask import jsonify, request

from runtime_config import api_key


# Decorator that verifies the API key
def verify_api_key(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        request_api_key = request.headers.get("API-Key")
        if request_api_key is None or request_api_key != api_key:
            return jsonify({"error": "Invalid API key"}), 401
        return func(*args, **kwargs)
    return wrapper
