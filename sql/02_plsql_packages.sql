CREATE OR REPLACE PACKAGE order_management_pkg IS
    FUNCTION place_order(
        p_customer_name IN VARCHAR2,
        p_customer_phone IN VARCHAR2,
        p_customer_address IN VARCHAR2,
        p_item_name IN VARCHAR2,
        p_quantity IN NUMBER,
        p_unit_price IN NUMBER,
        p_payment_method IN VARCHAR2 DEFAULT 'CASH',
        p_special_instructions IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER;
    
    PROCEDURE update_order_status(
        p_order_id IN NUMBER,
        p_new_status IN VARCHAR2,
        p_changed_by IN VARCHAR2 DEFAULT 'SYSTEM'
    );
    
    FUNCTION get_order_details(p_order_id IN NUMBER) RETURN SYS_REFCURSOR;
    FUNCTION get_total_sales RETURN NUMBER;
    FUNCTION get_orders_by_status(p_status IN VARCHAR2) RETURN SYS_REFCURSOR;
END order_management_pkg;
/

CREATE OR REPLACE PACKAGE BODY order_management_pkg IS
    FUNCTION place_order(
        p_customer_name IN VARCHAR2,
        p_customer_phone IN VARCHAR2,
        p_customer_address IN VARCHAR2,
        p_item_name IN VARCHAR2,
        p_quantity IN NUMBER,
        p_unit_price IN NUMBER,
        p_payment_method IN VARCHAR2 DEFAULT 'CASH',
        p_special_instructions IN VARCHAR2 DEFAULT NULL
    ) RETURN NUMBER IS
        v_order_id NUMBER;
        v_total NUMBER;
    BEGIN
        v_total := p_quantity * p_unit_price;
        INSERT INTO orders (customer_name, customer_phone, customer_address, item_name, quantity, unit_price, total_amount, payment_method, special_instructions)
        VALUES (p_customer_name, p_customer_phone, p_customer_address, p_item_name, p_quantity, p_unit_price, v_total, p_payment_method, p_special_instructions)
        RETURNING order_id INTO v_order_id;
        COMMIT;
        RETURN v_order_id;
    EXCEPTION
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END place_order;
    
    PROCEDURE update_order_status(
        p_order_id IN NUMBER,
        p_new_status IN VARCHAR2,
        p_changed_by IN VARCHAR2 DEFAULT 'SYSTEM'
    ) IS
        v_old_status VARCHAR2(20);
    BEGIN
        SELECT order_status INTO v_old_status FROM orders WHERE order_id = p_order_id;
        UPDATE orders SET order_status = p_new_status WHERE order_id = p_order_id;
        COMMIT;
    EXCEPTION
        WHEN NO_DATA_FOUND THEN
            RAISE_APPLICATION_ERROR(-20001, 'Order not found: ' || p_order_id);
        WHEN OTHERS THEN
            ROLLBACK;
            RAISE;
    END update_order_status;
    
    FUNCTION get_order_details(p_order_id IN NUMBER) RETURN SYS_REFCURSOR IS
        v_cursor SYS_REFCURSOR;
    BEGIN
        OPEN v_cursor FOR
            SELECT order_id, customer_name, customer_phone, customer_address, item_name, quantity, unit_price, total_amount, order_status, payment_method, special_instructions, order_date
            FROM orders WHERE order_id = p_order_id;
        RETURN v_cursor;
    END get_order_details;
    
    FUNCTION get_total_sales RETURN NUMBER IS
        v_total NUMBER;
    BEGIN
        SELECT NVL(SUM(total_amount), 0) INTO v_total FROM orders WHERE order_status != 'CANCELLED';
        RETURN v_total;
    END get_total_sales;
    
    FUNCTION get_orders_by_status(p_status IN VARCHAR2) RETURN SYS_REFCURSOR IS
        v_cursor SYS_REFCURSOR;
    BEGIN
        OPEN v_cursor FOR
            SELECT order_id, customer_name, item_name, quantity, total_amount, order_date
            FROM orders WHERE order_status = p_status ORDER BY order_date DESC;
        RETURN v_cursor;
    END get_orders_by_status;
END order_management_pkg;
/

CREATE OR REPLACE TRIGGER order_audit_trigger
AFTER UPDATE OF order_status ON orders
FOR EACH ROW
BEGIN
    INSERT INTO order_audit (order_id, action_type, old_status, new_status, changed_by, change_date)
    VALUES (:OLD.order_id, 'STATUS_CHANGE', :OLD.order_status, :NEW.order_status, NVL(SYS_CONTEXT('USERENV', 'OS_USER'), 'UNKNOWN'), CURRENT_TIMESTAMP);
END;
/

CREATE OR REPLACE TRIGGER order_insert_audit
AFTER INSERT ON orders
FOR EACH ROW
BEGIN
    INSERT INTO order_audit (order_id, action_type, old_status, new_status, changed_by, change_date)
    VALUES (:NEW.order_id, 'ORDER_CREATED', NULL, :NEW.order_status, NVL(SYS_CONTEXT('USERENV', 'OS_USER'), 'UNKNOWN'), CURRENT_TIMESTAMP);
END;
/

CREATE OR REPLACE TRIGGER restrict_weekday_dml
BEFORE INSERT OR UPDATE OR DELETE ON orders
BEGIN
    IF TO_CHAR(SYSDATE, 'DY', 'NLS_DATE_LANGUAGE=AMERICAN') IN ('MON', 'TUE', 'WED', 'THU', 'FRI') THEN
        NULL;
    END IF;
END;
/

CREATE OR REPLACE PROCEDURE get_daily_orders_report IS
    CURSOR c_orders IS
        SELECT order_id, customer_name, item_name, quantity, total_amount, order_status
        FROM orders WHERE TRUNC(order_date) = TRUNC(SYSDATE) ORDER BY order_date DESC;
    v_count NUMBER := 0;
    v_total NUMBER := 0;
BEGIN
    DBMS_OUTPUT.PUT_LINE('=== DAILY ORDERS REPORT ===');
    DBMS_OUTPUT.PUT_LINE('Date: ' || TO_CHAR(SYSDATE, 'YYYY-MM-DD'));
    FOR rec IN c_orders LOOP
        DBMS_OUTPUT.PUT_LINE('Order #' || rec.order_id || ' | ' || rec.customer_name || ' | ' || rec.item_name || ' x' || rec.quantity || ' | $' || rec.total_amount || ' | ' || rec.order_status);
        v_count := v_count + 1;
        v_total := v_total + rec.total_amount;
    END LOOP;
    DBMS_OUTPUT.PUT_LINE('Total Orders: ' || v_count);
    DBMS_OUTPUT.PUT_LINE('Total Sales: $' || v_total);
END;
/

COMMIT;