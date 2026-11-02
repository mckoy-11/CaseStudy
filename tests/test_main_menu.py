from ui.main_menu import MainMenu


class FakeClient:
    def __init__(self) -> None:
        self.closed = False

    def close(self) -> None:
        self.closed = True


class FakeScreen:
    def __init__(self) -> None:
        self.runs = 0

    def run(self) -> None:
        self.runs += 1


def test_main_menu_prioritizes_inventory_sales_and_reports(monkeypatch) -> None:
    client = FakeClient()
    menu = MainMenu(client)
    screens = {choice: FakeScreen() for choice in (2, 3, 4)}
    menu.screens = screens
    choices = iter((2, 3, 4, 0))
    menu_options = []

    monkeypatch.setattr("ui.main_menu.header", lambda _title: None)
    monkeypatch.setattr(
        "ui.main_menu.show_menu",
        lambda options: (menu_options.append(list(options)), next(choices))[1],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")

    menu.run()

    assert menu_options[0] == [
        "[1] Dashboard",
        "[2] Inventory management",
        "[3] Sales and reservations",
        "[4] Reports",
        "[5] Products and production",
        "[0] Exit",
    ]
    assert [screen.runs for screen in screens.values()] == [1, 1, 1]
    assert client.closed


def test_operations_menu_routes_and_returns_to_main_menu(monkeypatch) -> None:
    client = FakeClient()
    menu = MainMenu(client)
    assert set(menu.operations_screens) == {1, 2}
    screen = FakeScreen()
    menu.operations_screens = {1: screen}
    choices = iter((5, 1, 0, 0))
    menu_options = []

    monkeypatch.setattr("ui.main_menu.header", lambda _title: None)
    monkeypatch.setattr(
        "ui.main_menu.show_menu",
        lambda options: (menu_options.append(list(options)), next(choices))[1],
    )
    monkeypatch.setattr("builtins.input", lambda _prompt="": "")

    menu.run()

    assert screen.runs == 1
    assert menu_options[1] == [
        "[1] Product catalog",
        "[2] Production",
        "[0] Back",
    ]
    assert client.closed
