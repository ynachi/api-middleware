"""
Basic example of a resource server
"""

import connexion
from shared import token_info

from pathlib import Path
from datetime import datetime
import traceback

from middlewares.rlogger import RequestLoggingMiddlewarev4


def _setup_logger():
    logger = logging.getLogger('error_logger')
    if not request_logger.hasHandlers():
        logger.setLevel(logging.ERROR)

        Path("logs").mkdir(exist_ok=True)

        fh = logging.FileHandler('logs/error_log.txt')
        fh.setLevel(logging.ERROR)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


def _format_error_log(error, user_info=None, request=None):
    error_details = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': type(error).__name__,
        'error_message': str(error),
        'traceback': traceback.format_exc(),
        # 'path': request.path if request else 'unknown',
        # 'method': request.method if request else 'unknown',
        'user': 'anonymous'
    }

    if user_info:
        error_details['user'] = {
            'id': user_info.get('sub'),
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'role': user_info.get('role')
        }

    return error_details


from connexion.lifecycle import ConnexionRequest, ConnexionResponse
from connexion.exceptions import OAuthProblem
from connexion.problem import problem


def error_handler(request: ConnexionRequest, exc: Exception) -> ConnexionResponse:
    logger = _setup_logger()

    # Get request context from the exception if available
    request_id = request.scope['state'].get('request_id', datetime.utcnow().isoformat())

    # Try to get user info from the token if available
    user_info = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header.split('Bearer ')[1]
            user_info = token_info(token, None, request)
        except:
            pass

    # Log the error with context
    error_details = _format_error_log(
        exc,
        user_info,
        request
    )
    logger.error(f"Application error for request {request_id}: {error_details}")

    # Format the response
    status_code = exc.status_code if hasattr(exc, 'status_code') else 500
    detail = str(exc) if str(exc) else "An unexpected error occurred."

    return problem(
        title="Error",
        detail=detail,
        status=status_code,
        ext={
            'request_id': request_id,
            'user_context': {
                'email': user_info.get('email', 'anonymous'),
                'name': user_info.get('name', 'unknown'),
                'yao': 'yoa'
            } if user_info else {'yao': 'yoa'}
        }
    )


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
import time
import logging

# Set up a logger for request logging
request_logger = logging.getLogger('request_logger')
request_logger.setLevel(logging.INFO)

# Create a file handler for logging
Path("logs").mkdir(exist_ok=True)
fh = logging.FileHandler('logs/request_log.txt')
fh.setLevel(logging.INFO)

# Create a formatter and add it to the handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
request_logger.addHandler(fh)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        print(f"Received request: {request.scope['type']}")
        # Log the start of the request
        start_time = time.time()

        # Extract user details from the token (if available)
        user_info = None
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split('Bearer ')[1]
                user_info = token_info(token)  # Use your token_info function
            except Exception as e:
                request_logger.error(f"Failed to decode token: {e}")

        # Log request details, including user information, query, and headers
        request_logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"Query: {request.url.query} Headers: {dict(request.headers)} "
            f"User: {user_info.get('sub', 'anonymous') if user_info else 'anonymous'} "
            f"Email: {user_info.get('email', 'unknown') if user_info else 'unknown'} "
            f"Role: {user_info.get('role', 'unknown') if user_info else 'unknown'}"
        )

        # Process the request
        response = await call_next(request)

        # Log the end of the request and compute duration
        duration = time.time() - start_time
        request_logger.info(
            f"Request ended: {request.method} {request.url.path} "
            f"Status: {response.status_code} Duration: {duration:.4f} seconds "
            f"User: {user_info.get('sub', 'anonymous') if user_info else 'anonymous'} "
            f"Email: {user_info.get('email', 'unknown') if user_info else 'unknown'} "
            f"Role: {user_info.get('role', 'unknown') if user_info else 'unknown'}"
        )

        return response


app = connexion.FlaskApp(__name__, specification_dir="spec")
app.add_api("swagger.yaml")
app.add_error_handler(OAuthProblem, error_handler)
app.add_error_handler(Exception, error_handler)
app.add_middleware(RequestLoggingMiddlewarev4, connexion.middleware.MiddlewarePosition.BEFORE_EXCEPTION)

if __name__ == "__main__":
    app.run(f"{Path(__file__).stem}:app", port=8080)
