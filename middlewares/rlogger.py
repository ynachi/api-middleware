import logging
import sys
from typing import Any, MutableMapping, Optional
import uuid
import time, datetime
from starlette.types import ASGIApp, Scope, Receive, Send
from shared import token_info, user_info_from_scope
from connexion.lifecycle import ConnexionRequest

class RequestLoggingMiddlewarev4:
    def __init__(self, next_app: ASGIApp):
        self.next_app = next_app

        # Configure logger
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        # Create console handler if none exists
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        print("Middleware initialized")  # Debug print

    def get_user_info_(self, scope: Scope) -> Optional[dict]:
        conn_req = ConnexionRequest(scope)
        print()
        print()
        print("=============start:user:info=====================")
        print(conn_req.query_params)
        print("=============end:user:info=====================")
        print()
        auth_header = conn_req.headers.get('authorization')
        if auth_header and auth_header.startswith('Bearer '):
            try:
                token = auth_header.split('Bearer ')[1]
                user_info = token_info(token, None, conn_req)
                return user_info
            except Exception as e:
                print(f"error in get_user_info: {str(e)}")
                pass
        return None

    def log_request_start(self, scope: Scope) -> None:
        if scope["type"] != "http":
            print("Skipping non-HTTP request")  # Debug print
            return

        # print()
        # print()
        # print("=============start:user:info=====================")
        print(self.get_user_info_(scope))
        # print("=============end:user:info=====================")
        # print()
        method = scope.get("method", "")
        path = scope.get("path", "")
        client = scope.get("client", ("unknown", 0))

        request_id = str(uuid.uuid4())
        scope["state"]["request_id"] = request_id
        scope["state"]["request_start_time"] = time.time()

        message = f"Request started - Method: {method} Path: {path} Client: {client[0]}:{client[1]}"
        #print(message)  # Debug print
        self.logger.info(message)

    def log_request_end(self, scope: Scope) -> None:
        if scope["type"] != "http":
            return

        start_time = scope["state"].get("request_start_time", time.time())
        duration = time.time() - start_time

        method = scope.get("method", "")
        path = scope.get("path", "")
        status_code = scope["state"].get("status_code")
        headers = scope["state"].get("headers", [])

        message = f"Request completed - Method: {method} Path: {path} Duration: {duration:.3f}s, http_status_code: {status_code}"
       # print(message)  # Debug print
        self.logger.info(message)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        print("Middleware __call__ invoked")  # Debug print

        if "state" not in scope:
            scope["state"] = {}

        self.log_request_start(scope)

        original_send = send

        async def wrapped_send(message: MutableMapping[str, Any]) -> None:
            if message["type"] == "http.response.start":
                scope["state"]["status_code"] = message["status"]
                scope["state"]["headers"] = message.get("headers", [])
                print("Response started")  # Debug print
            elif message["type"] == "http.response.body" and message.get("more_body", False) is False:
                self.log_request_end(scope)
            await original_send(message)

        try:
            await self.next_app(scope, receive, wrapped_send)
        except Exception as e:
            # Add error tracking info to the exception
            if hasattr(e, 'request_context'):
                e.request_context = {
                    'request_id': scope["state"].get("request_id"),
                    'duration': time.time() - scope["state"].get("request_start_time", time.time()),
                    'timestamp': datetime.utcnow().isoformat()
                }
            error_message = f"Request failed - Error: {str(e)}"
            #print(error_message)  # Debug print
            self.logger.error(error_message)
            # important, it is fundamental to re-raise the exception
            raise