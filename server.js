// server.js
// The ONLY file that talks to Oracle. Everything in /public is plain
// HTML/CSS/JS served as static files. Pages call these endpoints with fetch().

const express = require("express");
const oracledb = require("oracledb");
const path = require("path");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "public")));

// ---------------------------------------------------------------------
// DB CONNECTION - replace with your actual values
// ---------------------------------------------------------------------
const DB_USER = "<STUDENTID>_<FIRSTNAME>_RESTAURANT_DB";
const DB_PASSWORD = "ChangeThisPassword123";
const DB_DSN = "localhost:1521/XEPDB1"; // host:port/service_name

async function getConnection() {
  return oracledb.getConnection({ user: DB_USER, password: DB_PASSWORD, connectString: DB_DSN });
}

// GET /api/tables - table status
app.get("/api/tables", async (req, res) => {
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(
      `SELECT table_id, table_number, capacity, location, status FROM restaurant_tables ORDER BY table_number`
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

// GET /api/menu - menu items with category
app.get("/api/menu", async (req, res) => {
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(`
      SELECT mc.category_name, mi.item_name, mi.price, mi.is_available
      FROM menu_items mi
      JOIN menu_categories mc ON mc.category_id = mi.category_id
      ORDER BY mc.category_name, mi.item_name
    `);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

// GET /api/customers - for the reservation form dropdown
app.get("/api/customers", async (req, res) => {
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(
      `SELECT customer_id, first_name || ' ' || last_name AS full_name FROM customers ORDER BY first_name`
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

// POST /api/reserve - calls PKG_RESERVATIONS.book_table
app.post("/api/reserve", async (req, res) => {
  const { customer_id, table_id, reservation_date, reservation_time, party_size } = req.body;
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(
      `BEGIN
         pkg_reservations.book_table(
           p_customer_id => :customer_id,
           p_table_id => :table_id,
           p_date => TO_DATE(:reservation_date, 'YYYY-MM-DD'),
           p_time => :reservation_time,
           p_party_size => :party_size,
           p_reservation_id => :out_id
         );
       END;`,
      {
        customer_id,
        table_id,
        reservation_date,
        reservation_time,
        party_size,
        out_id: { dir: oracledb.BIND_OUT, type: oracledb.NUMBER },
      }
    );
    await conn.commit();
    res.json({ success: true, reservation_id: result.outBinds.out_id });
  } catch (err) {
    if (conn) await conn.rollback();
    res.status(400).json({ success: false, error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

// GET /api/orders - orders with computed totals
app.get("/api/orders", async (req, res) => {
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(`
      SELECT o.order_id, t.table_number, o.status,
             pkg_orders.calculate_order_total(o.order_id) AS total_amount
      FROM orders o
      JOIN restaurant_tables t ON t.table_id = o.table_id
      ORDER BY o.order_id DESC
    `);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

// GET /api/audit - recent audit log entries
app.get("/api/audit", async (req, res) => {
  let conn;
  try {
    conn = await getConnection();
    const result = await conn.execute(`
      SELECT audit_id, table_name, operation, record_id, action_by, action_date
      FROM audit_log
      ORDER BY action_date DESC
      FETCH FIRST 50 ROWS ONLY
    `);
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: err.message });
  } finally {
    if (conn) await conn.close();
  }
});

const PORT = 3000;
app.listen(PORT, () => console.log(`Server running at http://localhost:${PORT}`));
