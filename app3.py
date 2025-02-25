# import connexion
# from connexion.exceptions import OAuthProblem
# from pathlib import Path
# import logging
# from datetime import datetime
# import traceback
# from starlette.middleware.base import BaseHTTPMiddleware
# from starlette.requests import Request
# import time
# from config import load_config
# from token_strategies import  create_token_service
# from typing import Optional, Dict
#
# def _setup_logger():
#     logger = logging.getLogger('error_logger')
#     logger.setLevel(logging.ERROR)
#
#     Path("logs").mkdir(exist_ok=True)
#
#     fh = logging.FileHandler('logs/error_log.txt')
#     fh.setLevel(logging.ERROR)
#
#     formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
#     fh.setFormatter(formatter)
#     logger.addHandler(fh)
#
#     return logger
#
#
# # Initialize logging
# def setup_logging():
#     # Create logs directory
#     Path("logs").mkdir(exist_ok=True)
#
#     # Setup error logger
#     error_logger = logging.getLogger('error_logger')
#     error_logger.setLevel(logging.ERROR)
#     error_handler = logging.FileHandler('logs/error_log.txt')
#     error_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#     error_logger.addHandler(error_handler)
#
#     # Setup request logger
#     request_logger = logging.getLogger('request_logger')
#     request_logger.setLevel(logging.INFO)
#     request_handler = logging.FileHandler('logs/request_log.txt')
#     request_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#     request_logger.addHandler(request_handler)
#
#     # Setup IAM logger
#     iam_logger = logging.getLogger('iam_logger')
#     iam_logger.setLevel(logging.INFO)
#     iam_handler = logging.FileHandler('logs/iam_log.txt')
#     iam_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
#     iam_logger.addHandler(iam_handler)
#
#
# from connexion.lifecycle import ConnexionRequest, ConnexionResponse
# from connexion.exceptions import OAuthProblem
# from connexion.problem import problem
#
# def _format_error_log(error, user_info=None, request=None):
#     print("=============================================================")
#     print(request.scope.get("headers"))
#     print("==============================================================")
#     error_details = {
#         'timestamp': datetime.utcnow().isoformat(),
#         'error_type': type(error).__name__,
#         'error_message': str(error),
#         'traceback': traceback.format_exc(),
#         # 'path': request.path if request else 'unknown',
#         # 'method': request.method if request else 'unknown',
#         'user': 'anonymous'
#     }
#
#     if user_info:
#         error_details['user'] = {
#             'id': user_info.get('sub'),
#             'email': user_info.get('email'),
#             'name': user_info.get('name'),
#             'role': user_info.get('role')
#         }
#
#     return error_details
#
# def error_handler(request: ConnexionRequest, exc: Exception) -> ConnexionResponse:
#     logger = _setup_logger()
#
#     # Try to get user info from the token if available
#     user_info = None
#     auth_header = request.headers.get('Authorization')
#     if auth_header and auth_header.startswith('Bearer '):
#         try:
#             token = auth_header.split('Bearer ')[1]
#             user_info = token_info(token)
#         except:
#             pass
#
#     # Log the error with context
#     error_details = _format_error_log(
#         exc,
#         user_info,
#         request
#     )
#     logger.error(f"Application error: {error_details}")
#
#     # Format the response
#     status_code = exc.status_code if hasattr(exc, 'status_code') else 500
#     detail = str(exc) if str(exc) else "An unexpected error occurred."
#
#     return problem(
#         title="Error",
#         detail=detail,
#         status=status_code,
#         ext={
#             'request_id': datetime.utcnow().isoformat(),
#             'user_context': {
#                 'email': user_info.get('email', 'anonymous'),
#                 'name': user_info.get('name', 'unknown')
#             } if user_info else None
#         }
#     )
#
# # Load configuration and create token service
# config = load_config()
# token_service = create_token_service(config)
#
#
# def token_info(token: str) -> Optional[Dict]:
#     return token_service.token_info(token)
#
#
# def get_secret(user) -> str:
#     token_info = connexion.context.context.get("token_info")
#
#     name = token_info.get("name", "Unknown")
#     email = token_info.get("email", "No email")
#     role = token_info.get("role", "No role")
#
#     return f"You are: {user}. Name: {name}, Email: {email}, Role: {role}"
#
#
# class RequestLoggingMiddleware(BaseHTTPMiddleware):
#     async def dispatch(self, request: Request, call_next):
#         start_time = time.time()
#         request_logger = logging.getLogger('request_logger')
#
#         user_info = None
#         auth_header = request.headers.get('Authorization')
#         if auth_header and auth_header.startswith('Bearer '):
#             try:
#                 token = auth_header.split('Bearer ')[1]
#                 user_info = token_info(token)
#             except Exception as e:
#                 request_logger.error(f"Failed to decode token: {e}")
#
#         request_logger.info(
#             f"Request started: {request.method} {request.url.path} "
#             f"Query: {request.url.query} Headers: {dict(request.headers)} "
#             f"User: {user_info.get('sub', 'anonymous') if user_info else 'anonymous'} "
#             f"Email: {user_info.get('email', 'unknown') if user_info else 'unknown'} "
#             f"Role: {user_info.get('role', 'unknown') if user_info else 'unknown'}"
#         )
#
#         response = await call_next(request)
#
#         duration = time.time() - start_time
#         request_logger.info(
#             f"Request ended: {request.method} {request.url.path} "
#             f"Status: {response.status_code} Duration: {duration:.4f} seconds "
#             f"User: {user_info.get('sub', 'anonymous') if user_info else 'anonymous'}"
#         )
#
#         return response
#
#
# app = connexion.FlaskApp(__name__, specification_dir="spec")
# # Wrap the Connexion app with the ASGI middleware
# # app.app = LoggedRequestBodySizeMiddleware(app.app)
# # Add the middleware to the app
# app.add_middleware(RequestLoggingMiddleware)
# app.add_api("openapi.yaml")
# app.add_api("swagger.yaml")
# app.add_error_handler(OAuthProblem, error_handler)
# app.add_error_handler(Exception, error_handler)
#
#
# if __name__ == "__main__":
#     app.run(f"{Path(__file__).stem}:app", port=8080)