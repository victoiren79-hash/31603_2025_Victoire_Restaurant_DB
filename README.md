# Restaurant Order & Table Reservation System
### DPR400210 Capstone Project

## Setup Order

1. `01_create_user.sql` — run as SYSDBA/SYSTEM. Replace `<STUDENTID>` and `<FIRSTNAME>` first.
2. Connect as your new user, then run in order:
   - `02_schema.sql`
   - `03_sample_data.sql`
   - `04_packages.sql`
   - `05_triggers.sql`
3. Use `06_verification_queries.sql` during your live demo.

## Important: the weekday/holiday blocking rule

Per the spec, `05_triggers.sql` blocks INSERT/UPDATE/DELETE on `RESERVATIONS`,
`ORDERS`, and `PAYMENTS` on weekdays (Mon–Fri) and on any date listed in
`PUBLIC_HOLIDAYS`. This is why sample data is loaded (step 3) **before** the
triggers are created (step 4) — otherwise the inserts would fail depending on
the day you run the script.

For your live demo: if the actual day you present on is a weekday, either
demo the failure case (show the `ORA-20050` error, which proves the rule
works), or temporarily disable the trigger to show a successful booking, then
re-enable it:
```sql
ALTER TRIGGER trg_block_reservations_dml DISABLE;
-- demo
ALTER TRIGGER trg_block_reservations_dml ENABLE;
```

## Frontend (Innovation component)

`frontend/` is plain HTML/CSS/JS (`public/`) served by a single small Node
server (`server.js`). The server is the only piece that talks to Oracle —
a browser can't connect to a database directly. Every HTML page fetches
JSON from the server with `fetch()` and renders it with vanilla JS.

- `public/style.css` — one shared stylesheet for all pages
- `public/*.html` — one page per feature, with page-specific JS inline
- `server.js` — Express routes that run SQL and call your PL/SQL packages

Setup:
```
cd frontend
npm install
```
Edit `server.js` and set `DB_USER`, `DB_PASSWORD`, `DB_DSN` to match your
Oracle instance, then:
```
npm start
```
Visit `http://localhost:3000`.

Pages: table status, menu, reservation form (calls `pkg_reservations.book_table`),
orders dashboard (calls `pkg_orders.calculate_order_total`), and a live audit
log view.

## Marking scheme coverage

| Component | Where |
|---|---|
| ERD & 3NF | `02_schema.sql` — 11 normalized tables |
| Table creation & constraints | `02_schema.sql` — PK/FK/CHECK/UNIQUE/NOT NULL |
| SQL operations (DML/DDL) | `03_sample_data.sql`, `06_verification_queries.sql` |
| PL/SQL (procedures, functions, packages, cursors) | `04_packages.sql` |
| Triggers & exception handling | `05_triggers.sql`, exceptions throughout `04_packages.sql` |
| Auditing & security | `trg_audit_orders`, `trg_audit_reservations` (compound triggers), `audit_log` table |
| Innovation | `frontend/` Flask web app |

## Still needed from you

- Phase I slides (problem statement, 3 slides max, Helvetica)
- Phase II BPMN/UML swimlane diagram + 1-page explanation
- Phase III ERD diagram (draw.io / Lucidchart from the schema above)
- Final ≤10-slide presentation deck
- GitHub repo named per convention, with all these files pushed
- OEM screenshots if available
