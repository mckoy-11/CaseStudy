"""Event and booth lifecycle operations for the frontend."""

from __future__ import annotations

from typing import Any

from service.api_client import APIClient


class EventService:
    """Create, list, and close selling events."""

    def __init__(self, client: APIClient | None = None) -> None:
        self.client = client or APIClient()

    def list_events(self, status: str | None = None) -> list[dict[str, Any]]:
        params = {"status_filter": status} if status else None
        return self.client.get("/events", params=params)

    def create_event(self, event: dict[str, Any]) -> dict[str, Any]:
        return self.client.post("/events", json_body=event)

    def close_event(self, event_id: str) -> dict[str, Any]:
        return self.client.post(f"/events/{event_id}/close")
