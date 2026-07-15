# ============================================================
# RESTAURANT ORDERING SYSTEM - FIXED WORKING VERSION
# Oracle 19c SQL*Plus | system/1968@localhost:1521/orcl
# Run: python app.py
# Open: http://localhost:5000
# ============================================================

import http.server
import socketserver
import json
import subprocess
import re
import tempfile
import os
from urllib.parse import urlparse

# ============================================================
# ORACLE CONNECTION
# ============================================================
DB_USER = "system"
DB_PASSWORD = "1968"
DB_SERVICE = "localhost:1521/orcl"

PORT = 5000

def run_sql(sql_lines, description=""):
    """
    Run SQL via sqlplus using a temp file.

    IMPORTANT: every plain SQL statement (SELECT/INSERT/UPDATE/DELETE) passed
    in sql_lines MUST end with a semicolon ';'. PL/SQL blocks must end with
    'END;' followed by a line containing only '/'. If a statement is left
    unterminated, SQL*Plus treats the next line (including EXIT) as a
    CONTINUATION of that statement instead of a new command - the statement
    never runs and you silently get no results / wrong results.
    """
    lines = [
        "SET PAGESIZE 100",
        "SET FEEDBACK OFF",
        "SET VERIFY OFF",
        "SET HEADING ON",
        "SET MARKUP HTML ON",
        "SET ECHO OFF",
        "SET TERMOUT ON",   
        "SET WRAP OFF",
        "SET LINESIZE 1000",
        "SET TRIMSPOOL ON",
    ]
    lines.extend(sql_lines)
    lines.append("EXIT")

    sql_content = "\n".join(lines) + "\n"

    fd, temp_path = tempfile.mkstemp(suffix=".sql")
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(sql_content)

        cmd = f"sqlplus -S {DB_USER}/{DB_PASSWORD}@{DB_SERVICE} @{temp_path}"
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True, timeout=30)
        combined = result.stdout
        if result.stderr:
            combined += "\n--STDERR--\n" + result.stderr
        return combined
    finally:
        try:
            os.unlink(temp_path)
        except:
            pass

def parse_html_table(html):
    rows = []
    trs = re.findall(r'<tr>(.*?)</tr>', html, re.DOTALL | re.IGNORECASE)
    if len(trs) < 2:
        return rows
    
    headers = re.findall(r'<th[^>]*>(.*?)</th>', trs[0], re.DOTALL | re.IGNORECASE)
    for tr in trs[1:]:
        tds = re.findall(r'<td[^>]*>(.*?)</td>', tr, re.DOTALL | re.IGNORECASE)
        if tds and len(tds) == len(headers):
            row = {}
            for i, h in enumerate(headers):
                val = tds[i].strip().replace('&nbsp;', ' ')
                row[h.strip().upper()] = val
            rows.append(row)
    return rows

# ============================================================
# HTML PAGE WITH LOADING SPINNER
# ============================================================
HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Bite & Grill</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:Segoe UI,sans-serif;background:#f0f0f0}
header{background:#d32f2f;color:white;text-align:center;padding:25px}
header h1{font-size:2.2em}
nav{background:#333;text-align:center;padding:12px}
nav button{background:transparent;border:2px solid white;color:white;padding:10px 25px;margin:0 5px;cursor:pointer;border-radius:20px;font-size:1em}
nav button:hover,nav button.active{background:#d32f2f;border-color:#d32f2f}
.container{max-width:1100px;margin:0 auto;padding:20px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:20px;margin-top:20px}
.item{background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)}
.item .img{height:150px;background:linear-gradient(135deg,#ff6b6b,#ee5a5a);display:flex;align-items:center;justify-content:center;font-size:3em}
.item .info{padding:18px}
.item h3{margin-bottom:6px}
.item p{color:#666;font-size:0.9em;margin-bottom:12px}
.item .row{display:flex;justify-content:space-between;align-items:center}
.item .price{font-size:1.3em;font-weight:bold;color:#d32f2f}
.btn{background:#d32f2f;color:white;border:none;padding:10px 22px;border-radius:20px;cursor:pointer;font-weight:bold}
.btn:hover{background:#b71c1c}
.modal{display:none;position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.5);justify-content:center;align-items:center;z-index:1000}
.modal.show{display:flex}
.box{background:white;border-radius:15px;padding:25px;width:90%;max-width:450px;max-height:90vh;overflow-y:auto}
.box h2{color:#d32f2f;margin-bottom:15px;text-align:center}
.field{margin-bottom:12px}
.field label{display:block;margin-bottom:4px;font-weight:600;color:#555}
.field input,.field select,.field textarea{width:100%;padding:10px;border:2px solid #ddd;border-radius:8px;font-size:1em}
.field input:focus,.field select:focus,.field textarea:focus{border-color:#d32f2f;outline:none}
.field textarea{min-height:60px;resize:vertical}
.qty{display:flex;align-items:center;gap:12px}
.qty button{width:35px;height:35px;border-radius:50%;border:2px solid #d32f2f;background:white;color:#d32f2f;font-size:1.1em;cursor:pointer}
.qty span{font-size:1.2em;font-weight:bold;min-width:25px;text-align:center}
.total{background:#f5f5f5;padding:12px;border-radius:8px;text-align:center;margin:15px 0}
.total .amt{font-size:1.8em;color:#d32f2f;font-weight:bold}
.btns{display:flex;gap:10px}
.btns button{flex:1;padding:12px;border:none;border-radius:8px;font-size:1em;font-weight:bold;cursor:pointer}
.cancel{background:#e0e0e0;color:#333}
.submit{background:#4caf50;color:white}
.submit:disabled{background:#ccc}
.spinner{display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top:2px solid transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin-right:6px;vertical-align:middle}
@keyframes spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.notify{position:fixed;top:20px;right:20px;padding:15px 25px;border-radius:8px;color:white;font-weight:bold;z-index:2000}
.notify.ok{background:#4caf50}
.notify.bad{background:#f44336}
.orders{display:none}
.orders.show{display:block}
table{width:100%;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1);border-collapse:collapse}
th,td{padding:12px;text-align:left;border-bottom:1px solid #eee}
th{background:#d32f2f;color:white}
tr:hover{background:#f5f5f5}
.badge{padding:4px 12px;border-radius:15px;font-size:0.8em;font-weight:bold}
.PENDING{background:#fff3e0;color:#e65100}
.CONFIRMED{background:#e3f2fd;color:#1565c0}
.PREPARING{background:#f3e5f5;color:#6a1b9a}
.READY{background:#e8f5e9;color:#2e7d32}
.DELIVERED{background:#e0f2f1;color:#00695c}
.CANCELLED{background:#ffebee;color:#c62828}
.empty{text-align:center;padding:50px;color:#999}
footer{text-align:center;padding:25px;color:#888;margin-top:30px}
</style>
</head>
<body>
<header><h1>🍔 Bite & Grill</h1><p>Order delicious food online</p></header>
<nav>
<button class="active" onclick="show('menu')">Menu</button>
<button onclick="show('orders')">My Orders</button>
</nav>
<div class="container">
<div id="menu-page">
<h2 style="margin-bottom:10px">Our Menu</h2>
<div class="grid" id="grid"></div>
</div>
<div id="orders-page" class="orders">
<h2 style="margin-bottom:10px">My Orders</h2>
<table><thead><tr><th>#</th><th>Item</th><th>Qty</th><th>Total</th><th>Status</th><th>Date</th></tr></thead>
<tbody id="orders-body"><tr><td colspan="6" class="empty">Loading...</td></tr></tbody></table>
</div>
</div>
<div class="modal" id="modal">
<div class="box">
<h2>Place Order</h2>
<div class="field"><label>Item</label><input id="m-item" readonly></div>
<div class="field"><label>Price</label><input id="m-price" readonly></div>
<div class="field"><label>Quantity</label><div class="qty"><button onclick="chg(-1)">-</button><span id="qty">1</span><button onclick="chg(1)">+</button></div></div>
<div class="total"><p>Total</p><p class="amt" id="total">$0.00</p></div>
<div class="field"><label>Your Name *</label><input id="name" placeholder="Full name"></div>
<div class="field"><label>Phone</label><input id="phone" placeholder="Phone number"></div>
<div class="field"><label>Address</label><input id="address" placeholder="Delivery address"></div>
<div class="field"><label>Payment</label><select id="pay"><option value="CASH">Cash</option><option value="CARD">Card</option><option value="MOBILE_MONEY">Mobile Money</option></select></div>
<div class="field"><label>Notes</label><textarea id="notes" placeholder="Special requests"></textarea></div>
<div class="btns"><button class="cancel" onclick="closeM()">Cancel</button><button class="submit" id="send" onclick="send()">Place Order</button></div>
</div>
</div>
<footer>Bite & Grill | DPR400210 Project</footer>
<script>
const menu=[{id:1,name:"Classic Beef Burger",desc:"Juicy beef with cheese and sauce",price:8.99,emoji:"🍔"},{id:2,name:"Chicken Burger",desc:"Grilled chicken with fresh veggies",price:7.99,emoji:"🍗"},{id:3,name:"Veggie Burger",desc:"Plant-based with avocado",price:9.49,emoji:"🥬"},{id:4,name:"Pepperoni Pizza",desc:"Classic pepperoni and mozzarella",price:12.99,emoji:"🍕"},{id:5,name:"Margherita Pizza",desc:"Mozzarella, tomatoes, basil",price:10.99,emoji:"🍕"},{id:6,name:"BBQ Chicken Pizza",desc:"Chicken with BBQ sauce",price:13.99,emoji:"🍕"},{id:7,name:"Coca Cola",desc:"500ml bottle",price:2.49,emoji:"🥤"},{id:8,name:"Orange Juice",desc:"Freshly squeezed",price:3.99,emoji:"🧃"},{id:9,name:"Chocolate Cake",desc:"Rich chocolate layers",price:5.99,emoji:"🍰"},{id:10,name:"French Fries",desc:"Crispy golden fries",price:3.49,emoji:"🍟"},{id:11,name:"Onion Rings",desc:"Beer-battered rings",price:4.49,emoji:"🧅"}];
let cur=null,qty=1;
document.getElementById("grid").innerHTML=menu.map(i=>`<div class="item"><div class="img">${i.emoji}</div><div class="info"><h3>${i.name}</h3><p>${i.desc}</p><div class="row"><span class="price">$${i.price.toFixed(2)}</span><button class="btn" onclick="openM(${i.id})">Order Now</button></div></div></div>`).join("");
function openM(id){cur=menu.find(i=>i.id===id);qty=1;document.getElementById("m-item").value=cur.name;document.getElementById("m-price").value="$"+cur.price.toFixed(2);document.getElementById("qty").textContent=qty;upd();document.getElementById("name").value="";document.getElementById("phone").value="";document.getElementById("address").value="";document.getElementById("notes").value="";document.getElementById("pay").value="CASH";document.getElementById("modal").classList.add("show")}
function closeM(){document.getElementById("modal").classList.remove("show");cur=null}
function chg(d){qty=Math.max(1,qty+d);document.getElementById("qty").textContent=qty;upd()}
function upd(){if(cur)document.getElementById("total").textContent="$"+(cur.price*qty).toFixed(2)}
document.getElementById("modal").addEventListener("click",e=>{if(e.target.id==="modal")closeM()});
async function send(){const n=document.getElementById("name").value.trim();if(!n){toast("Enter your name","bad");return}const b=document.getElementById("send");b.disabled=true;b.innerHTML='<span class="spinner"></span>Sending...';try{const r=await fetch("/api/order",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({customer_name:n,customer_phone:document.getElementById("phone").value.trim(),customer_address:document.getElementById("address").value.trim(),item_name:cur.name,quantity:qty,unit_price:cur.price,payment_method:document.getElementById("pay").value,special_instructions:document.getElementById("notes").value.trim()})});const d=await r.json();if(d.success){toast("Order placed! #"+d.order_id,"ok");closeM()}else{toast("Failed: "+(d.error||"Unknown"),"bad")}}catch(e){toast("Error: "+e.message,"bad")}b.disabled=false;b.innerHTML="Place Order"}
function toast(m,t){const o=document.querySelector(".notify");if(o)o.remove();const n=document.createElement("div");n.className="notify "+t;n.textContent=m;document.body.appendChild(n);setTimeout(()=>n.remove(),4000)}
function show(p){document.querySelectorAll("nav button").forEach(b=>b.classList.remove("active"));event.target.classList.add("active");if(p==="menu"){document.getElementById("menu-page").style.display="block";document.getElementById("orders-page").classList.remove("show")}else{document.getElementById("menu-page").style.display="none";document.getElementById("orders-page").classList.add("show");load()}}
async function load(){const b=document.getElementById("orders-body");b.innerHTML='<tr><td colspan="6" class="empty"><div style="text-align:center;padding:20px;">Loading orders...</div></td></tr>';try{const r=await fetch("/api/orders");const d=await r.json();if(d.success&&d.orders.length>0){b.innerHTML=d.orders.map(o=>`<tr><td>#${o.ORDER_ID}</td><td>${o.ITEM_NAME}</td><td>${o.QUANTITY}</td><td>$${parseFloat(o.TOTAL_AMOUNT).toFixed(2)}</td><td><span class="badge ${o.ORDER_STATUS}">${o.ORDER_STATUS}</span></td><td>${o.ORDER_DATE}</td></tr>`).join("")}else{b.innerHTML='<tr><td colspan="6" class="empty">No orders found</td></tr>'}}catch(e){b.innerHTML='<tr><td colspan="6" class="empty">Error loading orders: '+e.message+'</td></tr>'}}
</script>
</body>
</html>"""

# ============================================================
# HTTP HANDLER
# ============================================================
class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())

        elif path == "/api/orders":
            
            result = run_sql(
                ["SELECT order_id, customer_name, item_name, quantity, total_amount, order_status, order_date "
                 "FROM orders ORDER BY order_date DESC;"],
                "GET ORDERS"
            )
            rows = parse_html_table(result)
            response = {"success": True, "orders": rows}
            if not rows:
               
                response["debug_raw_output"] = result[:2000]
            self.send_json(response)

        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/api/order":
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body)

            name = data.get("customer_name", "").replace("'", "''")
            phone = data.get("customer_phone", "").replace("'", "''")
            address = data.get("customer_address", "").replace("'", "''")
            item = data.get("item_name", "").replace("'", "''")
            qty = int(data.get("quantity", 1))
            price = float(data.get("unit_price"))
            pay = data.get("payment_method", "CASH")
            notes = data.get("special_instructions", "").replace("'", "''")

            # FIX: capture the order_id directly from the function call using a
            # bind variable instead of re-querying MAX(order_id) by name/item
            # (which could grab the wrong row if the same customer orders the
            # same item more than once, and previously never ran anyway
            # because the SELECT wasn't terminated with ';').
            result = run_sql(
                [
                    "VARIABLE v_id NUMBER",
                    "BEGIN",
                    f"  :v_id := order_management_pkg.place_order('{name}', '{phone}', '{address}', "
                    f"'{item}', {qty}, {price}, '{pay}', '{notes}');",
                    "END;",
                    "/",
                    "SELECT :v_id AS order_id FROM dual;"
                ],
                "PLACE ORDER"
            )

            rows = parse_html_table(result)
            order_id = "unknown"
            if rows and len(rows) > 0:
                order_id = rows[0].get("ORDER_ID", "unknown")

            self.send_json({"success": True, "order_id": order_id})
        else:
            self.send_response(404)
            self.end_headers()

    def send_json(self, data):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

# ============================================================
# START
# ============================================================
if __name__ == "__main__":
    print("=" * 60)
    print("  RESTAURANT ORDERING SYSTEM")
    print("  Oracle: system/1968@localhost:1521/orcl")
    print("  Open: http://localhost:5000")
    print("=" * 60)

    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print("\n[SERVER] Running on http://localhost:5000")
        print("[SERVER] Press Ctrl+C to stop")
        httpd.serve_forever()
