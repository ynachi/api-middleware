# """
# Basic example of a resource server
# """
# from pathlib import Path
#
# import connexion
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# from starlette.types import ASGIApp, Receive, Send, Scope
#
# # our hardcoded mock "Bearer" access tokens
# TOKENS = {"123": "jdoe", "456": "rms"}
#
# import logging
# import traceback
# from datetime import datetime
# from pathlib import Path
#
#
# class LoggedRequestBodySizeMiddleware:
#     def __init__(self, app):
#         self.app = app
#         # Configure logger
#         self.logger = self._setup_logger()
#
#     def _setup_logger(self):
#         logger = logging.getLogger('error_logger')
#         logger.setLevel(logging.ERROR)
#
#         # Create logs directory if it doesn't exist
#         Path("logs").mkdir(exist_ok=True)
#
#         # File handler for external logging
#         fh = logging.FileHandler('logs/error_log.txt')
#         fh.setLevel(logging.ERROR)
#
#         # Format with timestamp and detailed information
#         formatter = logging.Formatter(
#             '%(asctime)s - %(levelname)s - %(message)s'
#         )
#         fh.setFormatter(formatter)
#         logger.addHandler(fh)
#
#         return logger
#
#     def _format_error_log(self, error, user_info, scope):
#         error_details = {
#             'timestamp': datetime.utcnow().isoformat(),
#             'error_type': type(error).__name__,
#             'error_message': str(error),
#             'traceback': traceback.format_exc(),
#             'path': scope.get('path', 'unknown'),
#             'method': scope.get('method', 'unknown'),
#             'user': 'anonymous'
#         }
#
#         if user_info:
#             error_details['user'] = {
#                 'id': user_info.get('sub'),
#                 'email': user_info.get('email'),
#                 'name': user_info.get('name'),
#                 'role': user_info.get('role')
#             }
#
#         return error_details
#
#     async def _wrapped_send(self, send, user_info):
#         async def wrapped_send(message):
#             if message['type'] == 'http.response.start':
#                 status = message['status']
#                 if status >= 400:  # Log all error responses
#                     self.logger.error(
#                         f"Error response {status} - User: {user_info['email'] if user_info else 'anonymous'}")
#             await send(message)
#
#         return wrapped_send
#
#     async def __call__(self, scope, receive, send):
#         if scope["type"] != "http":
#             await self.app(scope, receive, send)
#             return
#
#         body_size = 0
#         user_info = None
#
#         # Extract bearer token from headers
#         headers = scope.get("headers", [])
#         auth_header = next((h[1] for h in headers if h[0] == b"authorization"), None)
#
#         if auth_header:
#             try:
#                 token = auth_header.decode().split("Bearer ")[1]
#                 from app import token_info
#                 user_info = token_info(token)
#             except (IndexError, AttributeError) as e:
#                 self.logger.error(f"Auth header parsing error: {str(e)}")
#
#         async def receive_logging_request_body_size():
#             nonlocal body_size
#             try:
#                 message = await receive()
#                 assert message["type"] == "http.request"
#                 body_size += len(message.get("body", b""))
#
#                 if not message.get("more_body", False):
#                     log_message = f"Size of request body was: {body_size} bytes"
#                     if user_info:
#                         log_message += f" - User: {user_info['sub']} ({user_info['email']})"
#                     print(log_message)
#
#                 return message
#             except Exception as e:
#                 error_details = self._format_error_log(e, user_info, scope)
#                 self.logger.error(f"Request processing error: {error_details}")
#                 raise
#
#         try:
#             wrapped_send = await self._wrapped_send(send, user_info)
#             await self.app(scope, receive_logging_request_body_size, wrapped_send)
#         except Exception as e:
#             error_details = self._format_error_log(e, user_info, scope)
#             self.logger.error(f"Application error: {error_details}")
#
#             # Prepare error response with user context
#             error_response = {
#                 'type': 'http.response.start',
#                 'status': 500,
#                 'headers': [
#                     [b'content-type', b'application/json'],
#                 ]
#             }
#
#             error_message = {
#                 'error': str(e),
#                 'request_id': datetime.utcnow().isoformat(),
#                 'user_context': {
#                     'email': user_info.get('email', 'anonymous') if user_info else 'anonymous',
#                     'name': user_info.get('name', 'unknown') if user_info else 'unknown'
#                 } if user_info else None
#             }
#
#             await send(error_response)
#             await send({
#                 'type': 'http.response.body',
#                 'body': str(error_message).encode(),
#             })
#
# def get_secret(user) -> str:
#     # Access the token info from the context
#     tocken_ = connexion.context.context.get("token_info")
#
#     # Extract additional information
#     name = tocken_.get("name", "Unknown")
#     email = tocken_.get("email", "No email")
#     role = tocken_.get("role", "No role")
#
#     # Use the additional information in the response
#     return f"You are: {user}. Name: {name}, Email: {email}, Role: {role}"
#
#
# def token_info(token) -> dict:
#     sub = TOKENS.get(token)
#     if not sub:
#         return None
#
#     # Add more information to the response
#     return {
#         "sub": sub,  # Required: the user identifier
#         "scope": ["uid"],  # Required: the scopes associated with the token
#         "name": "John Doe",  # Additional info: user's name
#         "email": "johndoe@example.com",  # Additional info: user's email
#         "role": "admin",  # Additional info: user's role
#     }
#
# app = connexion.FlaskApp(__name__, specification_dir="spec")
# # Wrap the Connexion app with the ASGI middleware
# #app.app = LoggedRequestBodySizeMiddleware(app.app)
# app.add_middleware(LoggedRequestBodySizeMiddleware, connexion.middleware.MiddlewarePosition.BEFORE_EXCEPTION)
# app.add_api("openapi.yaml")
# app.add_api("swagger.yaml")
#
#
#
# if __name__ == "__main__":
#     app.run(f"{Path(__file__).stem}:app", port=8080)
