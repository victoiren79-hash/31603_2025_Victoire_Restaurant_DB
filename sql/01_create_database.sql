CREATE TABLE categories (
    category_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR2(50) NOT NULL UNIQUE
);

CREATE TABLE menu_items (
    item_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    item_name VARCHAR2(100) NOT NULL,
    description VARCHAR2(500),
    price NUMBER(10,2) NOT NULL CHECK (price > 0),
    category_id NUMBER,
    image_url VARCHAR2(200),
    is_available NUMBER(1) DEFAULT 1 CHECK (is_available IN (0,1)),
    CONSTRAINT fk_menu_category FOREIGN KEY (category_id) REFERENCES categories(category_id)
);

CREATE TABLE customers (
    customer_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    full_name VARCHAR2(100) NOT NULL,
    phone VARCHAR2(20),
    email VARCHAR2(100),
    address VARCHAR2(300),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    order_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    customer_id NUMBER,
    customer_name VARCHAR2(100) NOT NULL,
    customer_phone VARCHAR2(20),
    customer_address VARCHAR2(300),
    item_name VARCHAR2(100) NOT NULL,
    quantity NUMBER NOT NULL CHECK (quantity > 0),
    unit_price NUMBER(10,2) NOT NULL,
    total_amount NUMBER(10,2) NOT NULL,
    order_status VARCHAR2(20) DEFAULT 'PENDING' CHECK (order_status IN ('PENDING', 'CONFIRMED', 'PREPARING', 'READY', 'DELIVERED', 'CANCELLED')),
    payment_method VARCHAR2(20) DEFAULT 'CASH' CHECK (payment_method IN ('CASH', 'CARD', 'MOBILE_MONEY')),
    special_instructions VARCHAR2(500),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_order_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL
);

CREATE TABLE order_audit (
    audit_id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id NUMBER,
    action_type VARCHAR2(20) NOT NULL,
    old_status VARCHAR2(20),
    new_status VARCHAR2(20),
    changed_by VARCHAR2(100),
    change_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR2(50)
);

CREATE SEQUENCE seq_order_id START WITH 1 INCREMENT BY 1;
CREATE SEQUENCE seq_customer_id START WITH 1 INCREMENT BY 1;

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_date ON orders(order_date);
CREATE INDEX idx_order_audit_order ON order_audit(order_id);

INSERT INTO categories (category_name) VALUES ('Burgers');
INSERT INTO categories (category_name) VALUES ('Pizza');
INSERT INTO categories (category_name) VALUES ('Drinks');
INSERT INTO categories (category_name) VALUES ('Desserts');
INSERT INTO categories (category_name) VALUES ('Sides');

INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Classic Beef Burger', 'Juicy beef patty with lettuce, tomato, cheese and special sauce', 8.99, 1, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Chicken Burger', 'Grilled chicken breast with mayo and fresh veggies', 7.99, 1, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Veggie Burger', 'Plant-based patty with avocado and caramelized onions', 9.49, 1, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Pepperoni Pizza', 'Classic pepperoni with mozzarella on tomato sauce', 12.99, 2, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Margherita Pizza', 'Fresh mozzarella, tomatoes, and basil', 10.99, 2, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('BBQ Chicken Pizza', 'Grilled chicken with BBQ sauce and red onions', 13.99, 2, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Coca Cola', 'Refreshing 500ml bottle', 2.49, 3, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Orange Juice', 'Freshly squeezed orange juice', 3.99, 3, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Chocolate Cake', 'Rich chocolate layer cake with ganache', 5.99, 4, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('French Fries', 'Crispy golden fries with sea salt', 3.49, 5, 1);
INSERT INTO menu_items (item_name, description, price, category_id, is_available) VALUES ('Onion Rings', 'Beer-battered onion rings', 4.49, 5, 1);

COMMIT;
