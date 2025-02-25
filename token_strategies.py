from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional, Dict, List
import requests
from pathlib import Path
import logging


@dataclass
class TokenInfo:
    sub: str
    scope: List[str]
    name: str
    email: str
    role: str


class TokenInfoStrategy(ABC):
    @abstractmethod
    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        pass


class IamAasStrategy(TokenInfoStrategy):
    def __init__(self, introspect_url: str):
        self.introspect_url = introspect_url
        self.logger = logging.getLogger('iam_logger')

    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        try:
            response = requests.post(
                self.introspect_url,
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 200:
                self.logger.warning(f"IAMaaS token validation failed with status {response.status_code}")
                return None

            data = response.json()
            return TokenInfo(
                sub=data["sub"],
                scope=data["scope"],
                name=data.get("name", "Unknown"),
                email=data.get("email", "No email"),
                role=data.get("role", "No role")
            )
        except Exception as e:
            self.logger.error(f"IAMaaS token validation error: {str(e)}")
            return None


class AConnectStrategy(TokenInfoStrategy):
    def __init__(self, auth_url: str):
        self.auth_url = auth_url
        self.logger = logging.getLogger('iam_logger')

    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        try:
            response = requests.get(
                f"{self.auth_url}/userinfo",
                headers={"Authorization": f"Bearer {token}"}
            )

            if response.status_code != 200:
                self.logger.warning(f"AConnect token validation failed with status {response.status_code}")
                return None

            data = response.json()
            return TokenInfo(
                sub=data["sub"],
                scope=data["scope"].split(),
                name=data.get("name", "Unknown"),
                email=data.get("email", "No email"),
                role=data.get("role", "No role")
            )
        except Exception as e:
            self.logger.error(f"AConnect token validation error: {str(e)}")
            return None


class TestingStrategy(TokenInfoStrategy):
    def __init__(self):
        self.test_tokens: Dict[str, TokenInfo] = {
            "123": TokenInfo(
                sub="jdoe",
                scope=["uid"],
                name="John Doe",
                email="johndoe@example.com",
                role="admin"
            ),
            "456": TokenInfo(
                sub="rms",
                scope=["uid"],
                name="Richard Stallman",
                email="rms@example.com",
                role="user"
            )
        }

    def get_token_info(self, token: str) -> Optional[TokenInfo]:
        return self.test_tokens.get(token)


class TokenInfoService:
    def __init__(self, strategy: TokenInfoStrategy):
        self.strategy = strategy

    def token_info(self, token: str) -> Optional[Dict]:
        result = self.strategy.get_token_info(token)
        if not result:
            return None

        return {
            "sub": result.sub,
            "scope": result.scope,
            "name": result.name,
            "email": result.email,
            "role": result.role
        }


def create_token_service(config: dict) -> TokenInfoService:
    provider_type = config["iam"]["provider_type"]

    if provider_type == "iamaas":
        strategy = IamAasStrategy(config["iam"]["iamaas"]["introspect_url"])
    elif provider_type == "aconnect":
        strategy = AConnectStrategy(config["iam"]["aconnect"]["auth_url"])
    elif provider_type == "testing":
        strategy = TestingStrategy()
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")

    return TokenInfoService(strategy)