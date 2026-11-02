"""Console screens for ingredient stock and cost management."""

from __future__ import annotations

from uuid import uuid4

from service.ingredient_service import IngredientService
from utils.component import ask_number, ask_text, display_records, show_menu


class IngredientScreen:
    """Create ingredients, monitor quantities, and record stock movements."""

    def __init__(self, ingredients: IngredientService) -> None:
        self.ingredients = ingredients

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] View ingredient inventory",
                "[2] Add ingredient/opening stock",
                "[3] Adjust ingredient quantity",
                "[4] Update ingredient details",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.list_ingredients()
            elif choice == 2:
                self.create_ingredient()
            elif choice == 3:
                self.adjust_stock()
            elif choice == 4:
                self.update_ingredient()
            else:
                print("Select a valid ingredient option.")

    def list_ingredients(self) -> list[dict]:
        records = self.ingredients.list_ingredients()
        display_records(
            "Ingredient Inventory",
            records,
            (
                ("ID", "ingredient_id"),
                ("Ingredient", "name"),
                ("Unit", "unit"),
                ("On Hand", "current_stock_qty"),
                ("Reorder At", "reorder_level"),
                ("Unit Cost", "unit_cost"),
            ),
        )
        return records

    def create_ingredient(self) -> dict:
        payload = {
            "ingredient_id": f"ING-{uuid4().hex[:8].upper()}",
            "name": ask_text("Ingredient name: "),
            "unit": ask_text("Unit (kg, g, pcs, packs, etc.): "),
            "unit_cost": ask_number("Unit cost (PHP): ", minimum=0),
            "current_stock_qty": ask_number("Opening stock quantity: ", minimum=0),
            "reorder_level": ask_number("Low-stock warning level: ", minimum=0),
        }
        record = self.ingredients.create_ingredient(payload)
        print(f"Ingredient {record['ingredient_id']} saved.")
        return record

    def adjust_stock(self) -> dict:
        ingredients = self.list_ingredients()
        ingredient_id = ask_text("Ingredient ID: ")
        if not any(item["ingredient_id"] == ingredient_id for item in ingredients):
            raise ValueError(f"Unknown ingredient ID: {ingredient_id}")
        quantity_change = ask_number(
            "Quantity change (use a negative value for stock loss): ",
        )
        if not quantity_change:
            raise ValueError("Quantity change cannot be zero.")
        result = self.ingredients.adjust_stock(ingredient_id, {
            "quantity_change": quantity_change,
            "reason": ask_text("Reason: "),
        })
        print(f"New ingredient stock: {result['current_stock_qty']}")
        return result

    def update_ingredient(self) -> dict:
        ingredient_id = ask_text("Ingredient ID: ")
        changes = {}
        name = ask_text("New name (blank to keep): ", required=False)
        unit = ask_text("New unit (blank to keep): ", required=False)
        unit_cost = ask_number("New unit cost (blank to keep): ", minimum=0, allow_blank=True)
        reorder_level = ask_number(
            "New low-stock level (blank to keep): ", minimum=0, allow_blank=True
        )
        if name:
            changes["name"] = name
        if unit:
            changes["unit"] = unit
        if unit_cost is not None:
            changes["unit_cost"] = unit_cost
        if reorder_level is not None:
            changes["reorder_level"] = reorder_level
        if not changes:
            print("No changes entered.")
            return {}
        return self.ingredients.update_ingredient(ingredient_id, changes)
