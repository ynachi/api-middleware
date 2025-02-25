"""
Basic example of a resource server
"""

import connexion

# our hardcoded mock "Bearer" access tokens
TOKENS = {"123": "jdoe", "456": "rms"}

from connexion.exceptions import OAuthProblem
from pathlib import Path
import logging
from datetime import datetime
import traceback
import json
from starlette.responses import JSONResponse

from jaeger_client import Config
from opentracing import tracer as global_tracer

def init_tracer(service_name: str):
    config = Config(
        config={
            'sampler': {
                'type': 'const',
                'param': 1,  # Sample all requests
            },
            'logging': True,  # Enable logging for debugging
        },
        service_name=service_name,
    )
    return config.initialize_tracer()

# Initialize the tracer
tracer = init_tracer("my-service")
# global_tracer.override(tracer)

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
    print("=============================================================")
    print(request.scope.get("headers"))
    print("==============================================================")
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

    # Try to get user info from the token if available
    user_info = None
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        try:
            token = auth_header.split('Bearer ')[1]
            user_info = token_info(token)
        except:
            pass

    # Log the error with context
    error_details = _format_error_log(
        exc,
        user_info,
        request
    )
    logger.error(f"Application error: {error_details}")

    # Format the response
    status_code = exc.status_code if hasattr(exc, 'status_code') else 500
    detail = str(exc) if str(exc) else "An unexpected error occurred."

    return problem(
        title="Error",
        detail=detail,
        status=status_code,
        ext={
            'request_id': datetime.utcnow().isoformat(),
            'user_context': {
                'email': user_info.get('email', 'anonymous'),
                'name': user_info.get('name', 'unknown'),
                'yao': 'yoa'
            } if user_info else {'yao': 'yoa'}
        }
    )


def get_secret(user) -> str:
    # Access the token info from the context
    time.sleep(15)
    tocken_ = connexion.context.context.get("token_info")
    print(f"Token info: {connexion.context.context}")
    print("=======================================================")

    # Extract additional information
    name = tocken_.get("name", "Unknown")
    email = tocken_.get("email", "No email")
    role = tocken_.get("role", "No role")

    # Use the additional information in the response
    return f"You are: {user}. Name: {name}, Email: {email}, Role: {role}"


def token_info(token) -> dict:
    # token_info will call an introspect token, depending on the iam type
    sub = TOKENS.get(token)
    if not sub:
        return None

    # Add more information to the response
    return {
        "sub": sub,  # Required: the user identifier
        "scope": ["uid"],  # Required: the scopes associated with the token
        "name": "John Doe",  # Additional info: user's name
        "email": "johndoe@example.com",  # Additional info: user's email
        "role": "admin",  # Additional info: user's role
    }


from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
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


from opentracing import tags
from opentracing.ext import tags as ext_tags
from opentracing.propagation import Format
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
        # Only process HTTP requests
        if request.scope["type"] != "http":
            return await call_next(request)

        # Extract the OpenTracing context from the request headers
        span_ctx = tracer.extract(Format.HTTP_HEADERS, request.headers)
        span = tracer.start_span(request.url.path, child_of=span_ctx)

        # Add request details to the span
        span.set_tag(tags.HTTP_METHOD, request.method)
        span.set_tag(tags.HTTP_URL, str(request.url))
        span.set_tag(tags.SPAN_KIND, tags.SPAN_KIND_RPC_SERVER)

        # Log the start of the request
        start_time = time.time()
        request_logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"Query: {request.url.query} Headers: {dict(request.headers)}"
        )

        try:
            # Process the request
            response = await call_next(request)

            # Log the end of the request and compute duration
            duration = time.time() - start_time
            request_logger.info(
                f"Request ended: {request.method} {request.url.path} "
                f"Status: {response.status_code} Duration: {duration:.4f} seconds"
            )

            # Add response details to the span
            span.set_tag(tags.HTTP_STATUS_CODE, response.status_code)

            return response
        except Exception as e:
            # Log the error and set the error tag on the span
            span.set_tag(tags.ERROR, True)
            span.log_kv({
                'event': 'error',
                'error.object': e,
                'message': str(e),
                'stack': traceback.format_exc(),
            })
            raise
        finally:
            # Finish the span
            span.finish()


app = connexion.FlaskApp(__name__, specification_dir="spec")
# Wrap the Connexion app with the ASGI middleware
#app.app = LoggedRequestBodySizeMiddleware(app.app)
# Add the middleware to the app
app.add_middleware(RequestLoggingMiddleware, connexion.middleware.MiddlewarePosition.BEFORE_EXCEPTION)
# app.add_middleware(LoggedRequestBodySizeMiddleware, connexion.middleware.MiddlewarePosition.BEFORE_EXCEPTION)
# app.add_middleware(RequestLoggingMiddleware)
# app.add_api("openapi.yaml")
app.add_api("swagger.yaml")
app.add_error_handler(OAuthProblem, error_handler)
app.add_error_handler(Exception, error_handler)

if __name__ == "__main__":
    app.run(f"{Path(__file__).stem}:app", port=8080)
