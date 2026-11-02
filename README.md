# Kakina Food Products Mfg. Management System

A Python console UI connects to a FastAPI backend for managing Kakina's products,
production, finished-product inventory, booth events, reservations, sales,
and reports. The UI uses HTTP services; it never edits backend storage directly.
For a complete walkthrough of the architecture and business rules, see
[explanation.txt](explanation.txt).

## Business background

Kakina Food Products Mfg. is a family business established in 2019. It produces
chocolate using cacao from the family's farm, including pure cacao tablea and 60%
dark chocolate with pistachio or mango. The interview described notebook-based
tracking of production, stock, booth sales, Messenger orders,
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
address. Interactive API documentation is available at
`http://127.0.0.1:8000/docs`.

The API persists records in `api/data.json`. Keep backups of this file; it contains
the business records.

## How functions work

Each feature follows **Problem → Operations → Function → Output → Requirement**.
The screen gathers input, the service sends it through `APIClient`, and the API
validates, processes, and saves it. API request and response models are defined
centrally in `api/schemas.py`; endpoints and JSON persistence are implemented in
`api/main.py`.

The console's main menu focuses on:

1. Dashboard
2. Inventory management
3. Sales and reservations
4. Reports
5. Products and production

The Products and production option opens a submenu for product catalog CRUD
and production batches. Event management and expense entry are not available
as console screens. Their records and API routes remain available to reports
and backend integrations.

### Dashboard and navigation

- **Problem:** Operators need a quick view of current business activity and
  direct access to their most-used inventory, sales, reservation, and reporting
  workflows.
- **Operations:** The main menu prioritizes the dashboard, inventory management,
  sales and reservations, and reports. The supporting menu contains product
  catalog and production only. The dashboard requests inventory, production,
  reservation, sales, and financial metrics.
- **Function:** `MainMenu.run()` and `MainMenu.dashboard()` in `ui/main_menu.py`;
  `ReportService.dashboard()` in `service/report_service.py`.
- **Input:** No user data; the dashboard fetches current backend records.
- **Output:** Active products, available finished stock, low-stock warnings,
  production batch and pending reservation counts, open events,
  all-time and today's completed-sales summaries, and estimated financial totals.
- **Requirement:** Quickly monitor inventory, reservations, events, and sales.

### Products

- **Problem:** Sales need a consistent product catalog and prices.
- **Operations:** List, create, update, and deactivate catalog products.
- **Function:** `ProductScreen` in `ui/products.py` and `ProductService` in
  `service/product_service.py`; API routes under `/products`.
- **Input:** Product ID, name, positive unit price, optional details, packaging,
  weight, pieces per pack, reorder level, and active state. The console defaults a
  new product's reorder warning to 10 units unless another level is entered.
- **Output:** Validated product records; inactive products are hidden from the
  active catalog. Product IDs and names must be unique.
- **Requirement:** Maintain the five interview products and their selling prices.

### Production

- **Problem:** Finished goods produced need to be added to inventory with batch
  costs recorded, without maintaining ingredient or recipe records.
- **Operations:** Record a product, quantity, and batch-level packaging, labor,
  and other costs; review production history. Each batch adds finished units to
  central inventory.
- **Function:** `ProductionScreen` (`ui/production.py`) and
  `ProductionService` (`service/production_service.py`); API route `/batches`.
- **Input:** Product ID, quantity produced, packaging cost, labor cost, and other
  batch costs. The console sends an empty ingredient-usage list; it does not
  collect ingredient or recipe data.
- **Output:** A production batch with total and per-unit cost, plus updated
  finished-product stock at `LOC-CENTRAL`.

### Finished-product inventory and events

- **Problem:** The business needs to reconcile stock and track quantities taken to
  and returned from booths.
- **Operations:** View on-hand, reserved, and available stock; transfer stock
  between locations; reconcile physical counts; and inspect movements. Event
  setup and closing are not exposed in the console.
- **Function:** `InventoryScreen` (`ui/inventory.py`) and
  `InventoryService` (`service/inventory_service.py`); API routes `/inventory`.
- **Input:** Location, product, transfer or counted quantity, and reason.
- **Output:** Updated stock and movement records.
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
- **Operations:** Query sales, best sellers, locations, production costs,
  expenses, low stock, and financial summaries by supported date/location filters.
  Expense entry and management are not exposed in the console; the expense API
  can still provide data for reports.
- **Function:** `ReportScreen` (`ui/reports.py`) and `ReportService`
  (`service/report_service.py`); API routes `/reports`.
- **Input:** Reports accept date range and/or location.
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
| `GET/POST /products` | List active products and create a product |
| `GET /products/{product_id}` | Get an active product |
| `PATCH/DELETE /products/{product_id}` | Update or deactivate a product |
| `POST /batches`, `GET /batches` | Record production and list batch history |
| `GET /batches/{batch_id}` | Get a production batch |
| `GET /inventory/stock` | Read on-hand, reserved, and available stock |
| `POST /inventory/transfer` | Transfer finished stock between locations |
| `POST /inventory/adjustments` | Apply a physical-count adjustment |
| `GET /inventory/movements` | Read stock movement history |
| `GET/POST /orders` | List orders or create a sale/reservation |
| `GET /orders/{order_id}` | Get an order |
| `POST /orders/{order_id}/complete` | Complete a pending reservation |
| `POST /orders/{order_id}/cancel` | Cancel a pending reservation |
| `/reports/*` | Dashboard, sales, product, location, production-cost, expense, and financial summaries |
| `/ingredients/*`, `/events/*`, `/expenses/*` | Raw-material, event, and expense endpoints; API only, not console screens |

View exact request/response fields and all registered endpoints at
`http://127.0.0.1:8000/docs` while the API is running.

## Estimation and operational limits

- Estimated COGS is derived from recorded production batches and is not a
  lot-specific inventory valuation. Profit is therefore an estimate, not an
  accounting statement.
- Batch-linked expenses are included in production-cost estimates.
- Messenger is recorded as an order channel; the system does not connect to or
  send messages through Messenger.
- The backend uses a local JSON file and has no authentication or role-based
  access. Run it in a trusted environment and back up `api/data.json`.

The system is for one business and is manually operated by authorized staff.
It has no graphical POS cashier interface or online payment gateway. Recorded
payment methods and channels are bookkeeping fields only.

## Error handling and tests

The console's API client reports connection failures and unsuccessful HTTP
responses instead of showing false success. Run the tests from the project
directory:

```powershell
python -m pytest -q
```
