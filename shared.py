# our hardcoded mock "Bearer" access tokens
import time

import connexion
from starlette.types import Scope
from  connexion.lifecycle import ConnexionRequest
from starlette.requests import Request

TOKENS = {"123": "jdoe", "456": "rms"}

def get_secret(user) -> str:
    # Access the token info from the context
    time.sleep(15)
    tocken_ = connexion.context.context.get("token_info")
    connexion.context.request.scope["yao"] = "saved"

    # Extract additional information
    name = tocken_.get("name", "Unknown")
    email = tocken_.get("email", "No email")
    role = tocken_.get("role", "No role")

    # Use the additional information in the response
    return f"You are: {user}. Name: {name}, Email: {email}, Role: {role}"


def token_info(token, required_scopes, request) -> dict:
    # check if we can stre stuff at this stage
    # Access the ASGI scope from the connexion request
    # token_info will call an introspect token, depending on the iam type
    request.scope["state"]["yao"] = "saved"
    sub = TOKENS.get(token)
    if not sub:
        return None

    # Add more information to the response
    ans = {
        "sub": sub,  # Required: the user identifier
        "scope": ["uid"],  # Required: the scopes associated with the token
        "name": "John Doe",  # Additional info: user's name
        "email": "johndoe@example.com",  # Additional info: user's email
        "role": "admin",  # Additional info: user's role
    }
    return ans

def user_info_from_scope(scope: Scope) -> dict:
    user_info = None
    request = ConnexionRequest(scope)
    request2 = Request(scope)
    print(f"connexion request: {request.url}********")
    print(f"starlet request: {request2.headers}********")
    for header_name, header_value in scope['headers']:
        if header_name == b'authorization':
            auth_header = header_value.decode('utf-8')
            if auth_header.startswith('Bearer '):
                try:
                    token = auth_header.split('Bearer ')[1]
                    sub = TOKENS.get(token)
                    if not sub:
                        break
                    user_info = {
                        "sub": sub,  # Required: the user identifier
                        "scope": ["uid"],  # Required: the scopes associated with the token
                        "name": "John Doe",  # Additional info: user's name
                        "email": "johndoe@example.com",  # Additional info: user's email
                        "role": "admin",  # Additional info: user's role
                    }
                except Exception as e:
                    print("Exception occurred:", str(e))
            break

    return user_info