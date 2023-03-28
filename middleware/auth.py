from functools import wraps

from flask import jsonify, request

from runtime_config import api_key


# Decorator that verifies the API key
def verify_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.headers.get('API-Key') == api_key:
            return f(*args, **kwargs)
        else:
            return jsonify({'status': 'error', 'message': 'Invalid API key'}), 401

    return decorated_function
