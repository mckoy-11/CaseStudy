"""Console screens for operating expenses."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from service.expense_service import ExpenseService
from service.production_service import ProductionService
from utils.component import ask_choice, ask_number, ask_text, display_records, show_menu


EXPENSE_CATEGORIES = (
    "Raw Materials",
    "Packaging",
    "Labor",
    "Transportation",
    "Utilities",
    "Booth Rental",
    "Maintenance",
    "Other Expenses",
)


class ExpenseScreen:
    """Record/filter expenses and optionally link production costs to a batch."""

    def __init__(self, expenses: ExpenseService, production: ProductionService) -> None:
        self.expenses = expenses
        self.production = production

    def run(self) -> None:
        while True:
            choice = show_menu([
                "[1] View expenses",
                "[2] Record expense",
                "[3] Update expense",
                "[4] Delete expense",
                "[0] Back",
            ])
            if choice == 0:
                return
            if choice == 1:
                self.list_expenses()
            elif choice == 2:
                self.create_expense()
            elif choice == 3:
                self.update_expense()
            elif choice == 4:
                self.delete_expense()
            else:
                print("Select a valid expense option.")

    def list_expenses(self) -> list[dict]:
        records = self.expenses.list_expenses()
        display_records(
            "Expenses",
            records,
            (
                ("ID", "expense_id"),
                ("Date", "expense_date"),
                ("Category", "category"),
                ("Description", "description"),
                ("Amount", "amount"),
                ("Batch", "related_batch_id"),
                ("Location", "location_id"),
            ),
        )
        return records

    def create_expense(self) -> dict:
        batches = self.production.list_batches()
        if batches:
            display_records(
                "Production batches (optional cost link)",
                batches,
                (("Batch ID", "batch_id"), ("Product ID", "product_id"), ("Date", "production_date")),
            )
        related_batch_id = ask_text(
            "Related production batch ID (blank if not production-related): ",
            required=False,
        ) or None
        payload = {
            "expense_id": f"EXP-{uuid4().hex[:8].upper()}",
            "category": ask_choice("Expense category: ", EXPENSE_CATEGORIES),
            "description": ask_text("Description: "),
            "amount": ask_number("Amount (PHP): ", minimum=0.01),
            "expense_date": (
                f"{ask_text('Expense date (YYYY-MM-DD, blank for today): ', required=False) or date.today().isoformat()}T00:00:00"
            ),
            "related_batch_id": related_batch_id,
            "location_id": ask_text("Location ID (optional): ", required=False) or None,
        }
        result = self.expenses.create_expense(payload)
        print(f"Expense {result['expense_id']} recorded.")
        return result

    def update_expense(self) -> dict:
        expense_id = ask_text("Expense ID: ")
        changes = {}
        description = ask_text("New description (blank to keep): ", required=False)
        amount = ask_number("New amount (blank to keep): ", minimum=0.01, allow_blank=True)
        if description:
            changes["description"] = description
        if amount is not None:
            changes["amount"] = amount
        if not changes:
            print("No changes entered.")
            return {}
        return self.expenses.update_expense(expense_id, changes)

    def delete_expense(self) -> None:
        expense_id = ask_text("Expense ID: ")
        confirm = ask_text(f"Type DELETE to remove {expense_id}: ")
        if confirm != "DELETE":
            print("Expense deletion cancelled.")
            return
        self.expenses.delete_expense(expense_id)
        print("Expense deleted.")
