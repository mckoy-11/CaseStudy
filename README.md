# Kakina Food Products Mfg. Management System

A Python console UI connects to a FastAPI backend for managing Kakina's products,
raw ingredients, production, inventory, booth events, reservations, sales, expenses,
and reports. The UI uses HTTP services; it never edits backend storage directly.

## Business background

Kakina Food Products Mfg. is a family business established in 2019. It produces
chocolate using cacao from the family's farm, including pure cacao tablea and 60%
dark chocolate with pistachio or mango. The interview described notebook-based
tracking of ingredient costs, production, stock, booth sales, Messenger orders,
reservations, and expenses. Manual counting and calculations make it harder to
reconcile stock and compare sales across events and locations.

The interview's product list and prices are preloaded by the API when it starts.
Existing catalog records are preserved.

| Product | Price |
|---|---:|
| Purong Cacao (Tablea) Pouch 100G (11 Pcs) | ₱120 |
| 60% Dark Chocolate with Pistachio Nuts Pouch 20G | ₱40 |
| 60% Dark Chocolate with Pistachio Nuts Bar 60G | ₱150 |
| 60% Dark Chocolate with Mango Bits Pouch 20G | ₱40 |
| 60% Dark Chocolate with Mango Bits Bar 60G | ₱150 |

## Run the application

From `F:\Python\z`, install requirements and start the API:

```powershell
python -m pip install -r requirements.txt
python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

In another terminal:

```powershell
python main.py
```

The API defaults to `http://127.0.0.1:8000`. Set `KAKINA_API_URL` to use another
address. Interactive API documentation is available at `/docs`.

The API persists records in `api/data.json`. Keep backups of this file; it contains
the business records.

## How functions work

Each feature follows **Problem → Operations → Function → Output → Requirement**.
The screen gathers input, the service sends it through `APIClient`, and the API
validates, processes, and saves it.

### Dashboard and navigation

- **Problem:** Operators need a quick view of current business activity.
- **Operations:** The main menu routes to feature screens. The dashboard requests
  operational metrics and sales/financial summaries.
- **Function:** `MainMenu.run()` and `MainMenu.dashboard()` in `ui/main_menu.py`;
  `ReportService.dashboard()` in `service/report_service.py`.
- **Input:** No user data; the dashboard fetches current backend records.
- **Output:** Active product and ingredient counts, available finished stock,
  low-stock warnings, production batch and pending reservation counts, open events,
  all-time and today's completed-sales summaries, and estimated financial totals.
- **Requirement:** Quickly monitor inventory, reservations, events, and sales.

### Products

- **Problem:** Sales and production need a consistent product catalog and prices.
- **Operations:** List, create, update, and deactivate catalog products.
- **Function:** `ProductScreen` in `ui/products.py` and `ProductService` in
  `service/product_service.py`; API routes under `/products`.
- **Input:** Product ID, name, positive unit price, optional details, packaging,
  weight, pieces per pack, reorder level, and active state. The console defaults a
  new product's reorder warning to 10 units unless another level is entered.
- **Output:** Validated product records; inactive products are hidden from the
  active catalog. Product IDs and names must be unique.
- **Requirement:** Maintain the five interview products and their selling prices.

### Ingredients and production

- **Problem:** Production needs ingredient quantities, costs, and finished-unit
  cost recorded together.
- **Operations:** Track ingredient stock and reorder levels, adjust raw materials,
  create production batches, and list production history. A batch deducts managed
  ingredients and adds finished products to central stock.
- **Function:** `IngredientScreen` (`ui/ingredients.py`),
  `ProductionScreen` (`ui/production.py`), and the corresponding services under
  `service/`; API routes `/ingredients` and `/batches`.
- **Input:** Ingredient ID/name, unit, unit cost, opening quantity and reorder
  level; batch ID, product, production quantity, ingredient usage, packaging,
  labor, and other costs.
- **Output:** Updated ingredient quantity and movement history; a batch with total
  production cost and unit cost; finished-product stock at `LOC-CENTRAL`.
  Ingredient use is rejected if the available managed stock is insufficient.
- **Requirement:** Replace handwritten ingredient/production records and estimate
  product cost.

### Finished-product inventory and events

- **Problem:** The business needs to reconcile stock and track quantities taken to
  and returned from booths.
- **Operations:** View on-hand, reserved, and available stock; transfer stock
  between locations; reconcile physical counts; inspect movements; create events
  and close them to return unsold stock to central inventory.
- **Function:** `InventoryScreen` (`ui/inventory.py`),
  `EventScreen` (`ui/events.py`), and `InventoryService`/`EventService` in
  `service/`; API routes `/inventory` and `/events`.
- **Input:** Location, product, transfer or counted quantity and reason; event ID,
  event name, location, and date. Event IDs are used as inventory location IDs.
- **Output:** Updated stock and movement records. Closing an event returns its
  remaining stock to `LOC-CENTRAL`; it is blocked while pending reservations remain
  at that location.
- **Requirement:** Monitor booth quantities, retain unsold items, and record
  physical count adjustments.

### Orders, sales, and reservations

- **Problem:** Customer purchases and Messenger reservations need consistent
  customer, item, payment, fulfillment, and status records.
- **Operations:** Create pending reservations or completed sales, list/filter
  orders, complete reservations, or cancel them. Pending reservations hold
  availability without reducing physical on-hand stock; completion deducts stock
  and cancellation releases the hold.
- **Function:** `OrderScreen` (`ui/orders.py`) and `OrderService` in
  `service/order_service.py`; API routes `/orders`.
- **Input:** Order ID, channel (including Messenger, booth, and direct offering),
  location, customer/contact details, one or more products and quantities, payment
  method, pickup/delivery selection, delivery fee, and initial status.
- **Output:** Item subtotals and order total using catalog prices, order status,
  inventory movement history, and reservation-aware stock. Completed orders are
  included in sales reports; pending orders are not.
- **Requirement:** Record booth sales, direct sales, customer orders, and
  reservation status while preventing overselling.

### Expenses and reports

- **Problem:** The business needs sales and cost summaries by day, product, and
  selling location.
- **Operations:** Record and manage dated expenses, optionally link an expense to
  a production batch, and query sales, best sellers, locations, production costs,
  expenses, low stock, and financial summaries by supported date/location filters.
- **Function:** `ExpenseScreen` (`ui/expenses.py`), `ReportScreen` (`ui/reports.py`),
  `ExpenseService` and `ReportService` under `service/`; API routes `/expenses`
  and `/reports`.
- **Input:** Expense ID, category, amount, date, and optional batch/location
  references; reports accept date range and/or location.
- **Output:** Daily completed sales, quantities/revenue by product, ranked best
  sellers, totals by named event location/category, low-stock warnings, production
  costs, and estimated profit.
  Estimated profit is sales revenue minus estimated COGS and operating expenses.
  COGS is derived from recorded production batches; profit is marked unavailable
  when a sold product lacks production cost history.
- **Requirement:** Reduce manual calculations and compare sales performance across
  Talavera, CLSU, Nueva Ecija, Bulacan, Manila, and other locations.

## Main API routes

| Route | Purpose |
|---|---|
| `/products` | Product catalog CRUD and deactivation |
| `/ingredients` | Raw ingredient stock and adjustments |
| `/batches` | Production history, ingredient deduction, finished stock |
| `/inventory/stock`, `/inventory/transfer`, `/inventory/adjustments`, `/inventory/movements` | Stock, transfers, counts, and history |
| `/events` | Event setup, lookup, and unsold-stock return |
| `/orders` | Sales and reservations, list and status transitions |
| `/expenses` | Expense create/list/update/delete |
| `/reports/dashboard`, `/reports/low-stock` | Operational dashboard and warnings |
| `/reports/daily-sales`, `/reports/product-sales`, `/reports/best-sellers`, `/reports/location-sales` | Sales analysis |
| `/reports/production-costs`, `/reports/expenses`, `/reports/financial-summary` | Cost and financial analysis |

## Estimation and operational limits

- Estimated COGS is derived from recorded production batches and is not a
  lot-specific inventory valuation. Profit is therefore an estimate, not an
  accounting statement.
- Raw-material purchase expenses are reported as expenses; they are not counted
  again as operating expenses in estimated profit. Batch-linked expenses are
  included in production-cost estimates.
- Messenger is recorded as an order channel; the system does not connect to or
  send messages through Messenger.
- The backend uses a local JSON file and has no authentication or role-based
  access. Run it in a trusted environment and back up `api/data.json`.
