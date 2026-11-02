"""Console screens for booth/event setup and close-out."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from service.event_service import EventService
from service.inventory_service import InventoryService
from utils.component import ask_text, display_records, show_menu, show_table


class EventScreen:
    """Manage selling events as inventory locations."""

    def __init__(self, events: EventService, inventory: InventoryService) -> None:
        self.events = events
        self.inventory = inventory

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] View events",
                "[2] Create event/location",
                "[3] Close event and return unsold stock",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.list_events()
            elif choice == 2:
                self.create_event()
            elif choice == 3:
                self.close_event()
            else:
                print("Select a valid event option.")

    def list_events(self) -> list[dict]:
        events = self.events.list_events()
        display_records(
            "Booth Events",
            events,
            (
                ("Event ID / Location", "location_id"),
                ("Event", "name"),
                ("Place", "location_name"),
                ("Province", "province"),
                ("Date", "event_date"),
                ("Status", "status"),
            ),
        )
        return events

    def create_event(self) -> dict:
        event_id = f"EVT-{uuid4().hex[:8].upper()}"
        payload = {
            "event_id": event_id,
            "name": ask_text("Event or booth name: "),
            "location_name": ask_text("Town, venue, or place: "),
            "province": ask_text("Province (blank for Nueva Ecija): ", required=False) or "Nueva Ecija",
            "event_date": f"{ask_text('Event date (YYYY-MM-DD, blank for today): ', required=False) or date.today().isoformat()}T00:00:00",
        }
        event = self.events.create_event(payload)
        print(
            f"Event created. Use location ID {event['location_id']} "
            "when transferring stock or recording booth sales."
        )
        return event

    def close_event(self) -> dict:
        events = self.events.list_events(status="open")
        display_records(
            "Open Events",
            events,
            (("ID", "event_id"), ("Event", "name"), ("Location", "location_name")),
        )
        event_id = ask_text("Event ID to close: ")
        if not any(item["event_id"] == event_id for item in events):
            raise ValueError(f"Unknown open event: {event_id}")
        stock = self.inventory.get_stock_levels(event_id)
        if stock:
            show_table(
                ["Product", "Unsold stock to return"],
                [[item["product_name"], item["quantity_on_hand"]] for item in stock],
            )
        else:
            print("No unsold stock remains at this event.")
        result = self.events.close_event(event_id)
        print(f"Event closed. Returned quantities: {result['unsold_returned']}")
        return result
