"""Shared HTTP client used by UI-facing service classes."""

from __future__ import annotations

import os
from typing import Any

import requests


class APIError(RuntimeError):
    """The backend returned a non-success HTTP response."""

    def __init__(self, status_code: int, detail: Any) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(f"API request failed ({status_code}): {detail}")


class APIConnectionError(RuntimeError):
    """The frontend could not connect to the backend."""


class APIClient:
    """Send HTTP requests to the FastAPI backend.

    The API base URL can be set with ``KAKINA_API_URL``. No credentials are
    added because the current API does not expose authentication endpoints.
    """

    def __init__(self, base_url: str | None = None, timeout: float = 10.0) -> None:
        self.base_url = (
            base_url or os.environ.get("KAKINA_API_URL", "http://127.0.0.1:8000")
        ).rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()

    def get(self, path: str, *, params: dict[str, Any] | None = None) -> Any:
        """Perform a GET request and return the decoded JSON response."""
        return self.request("GET", path, params=params)

    def post(
        self,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a POST request and return the decoded JSON response."""
        return self.request("POST", path, json_body=json_body, params=params)

    def put(self, path: str, *, json_body: dict[str, Any]) -> Any:
        """Perform a PUT request and return the decoded JSON response."""
        return self.request("PUT", path, json_body=json_body)

    def patch(self, path: str, *, json_body: dict[str, Any]) -> Any:
        """Perform a PATCH request and return the decoded JSON response."""
        return self.request("PATCH", path, json_body=json_body)

    def delete(self, path: str) -> Any:
        """Perform a DELETE request and return its decoded response if present."""
        return self.request("DELETE", path)

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Issue a request, raising explicit errors for transport or API failures."""
        url = f"{self.base_url}/{path.lstrip('/')}"
        try:
            response = self._session.request(
                method=method,
                url=url,
                json=json_body,
                params=params,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise APIConnectionError(
                f"Cannot connect to Kakina API at {self.base_url}: {exc}"
            ) from exc

        if not response.ok:
            try:
                body = response.json()
                detail = body.get("detail", body) if isinstance(body, dict) else body
            except ValueError:
                detail = response.text or response.reason
            raise APIError(response.status_code, detail)

        if response.status_code == 204 or not response.content:
            return None

        try:
            return response.json()
        except ValueError as exc:
            raise APIError(response.status_code, "Backend returned invalid JSON") from exc

    def close(self) -> None:
        """Release the underlying HTTP connection pool."""
        self._session.close()
