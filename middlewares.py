import logging
from typing import Callable


class LoggedRequestBodySizeMiddleware2:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger("body_size")
        self.logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)

    async def __call__(self, scope, receive, send):
        print("middleware called")
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        print("middleware called - got http request")
        body_size = 0

        # Explicitly read the entire body
        body = b""
        more_body = True

        while more_body:
            message = await receive()
            print(f"Received message: {message['type']}")

            if message["type"] == "http.request":
                chunk = message.get("body", b"")
                body += chunk
                body_size += len(chunk)
                more_body = message.get("more_body", False)
                print(f"Got chunk: {len(chunk)} bytes, more_body: {more_body}")
                self.logger.info(f"Received chunk size: {len(chunk)} bytes, total: {body_size} bytes")

        # Create a new receive function that returns the stored body
        async def wrapped_receive():
            nonlocal body
            message = {
                "type": "http.request",
                "body": body,
                "more_body": False,
            }
            body = b""  # Clear the body after first read
            return message

        async def wrapped_send(message):
            if message["type"] == "http.response.start":
                self.logger.info(f"Final request body size: {body_size} bytes")
            return await send(message)

        return await self.app(scope, wrapped_receive, wrapped_send)
