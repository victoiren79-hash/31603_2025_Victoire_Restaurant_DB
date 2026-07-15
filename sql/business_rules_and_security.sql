-- ============================================================
-- PHASE VII: ADVANCED DATABASE PROGRAMMING
-- Business rule: block INSERT/UPDATE/DELETE on orders during
-- weekdays (Mon-Fri) and public holidays (stored in holidays table)
-- + Security: restrict direct DML on orders to force use of the
-- order_management_pkg package (Auditing & security marks)
-- Run this against your EXISTING schema. It does not drop or
-- touch your current tables/data.
-- ============================================================

-- ------------------------------------------------------------
-- 1. Holiday reference table (required by the spec)
-- ------------------------------------------------------------
CREATE TABLE holidays (
    holiday_id   NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    holiday_date DATE NOT NULL UNIQUE,
    holiday_name VARCHAR2(100) NOT NULL
);

INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-01-01', 'New Year''s Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-04-07', 'Genocide Memorial Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-05-01', 'Labour Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-07-01', 'Independence Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-07-04', 'Liberation Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-08-15', 'Assumption Day');
INSERT INTO holidays (holiday_date, holiday_name) VALUES (DATE '2026-12-25', 'Christmas Day');
COMMIT;

-- ------------------------------------------------------------
-- 2. Replace the old no-op trigger with a real enforcing one
-- ------------------------------------------------------------
DROP TRIGGER restrict_weekday_dml;

CREATE OR REPLACE TRIGGER restrict_weekday_dml
BEFORE INSERT OR UPDATE OR DELETE ON orders
FOR EACH ROW
DECLARE
    v_day           VARCHAR2(3);
    v_holiday_count NUMBER;
BEGIN
    v_day := TO_CHAR(SYSDATE, 'DY', 'NLS_DATE_LANGUAGE=AMERICAN');

    SELECT COUNT(*) INTO v_holiday_count
    FROM holidays
    WHERE holiday_date = TRUNC(SYSDATE);

    IF v_day IN ('MON', 'TUE', 'WED', 'THU', 'FRI') THEN
        RAISE_APPLICATION_ERROR(
            -20010,
            'Business rule violation: orders cannot be placed, modified, or cancelled on weekdays (Mon-Fri). Please try again on the weekend.'
        );
    ELSIF v_holiday_count > 0 THEN
        RAISE_APPLICATION_ERROR(
            -20011,
            'Business rule violation: orders cannot be placed, modified, or cancelled on a public holiday.'
        );
    END IF;
END;
/

-- ------------------------------------------------------------
-- 3. Security control: force all order changes through the
--    package instead of direct table DML (Auditing & security marks)
-- ------------------------------------------------------------
CREATE ROLE restaurant_app_role;

-- Application layer should only ever need to read orders directly
-- and call the package for anything that changes data.
GRANT EXECUTE ON order_management_pkg TO restaurant_app_role;
GRANT SELECT ON orders TO restaurant_app_role;

-- Explicitly block direct DML on the orders table from PUBLIC so
-- that INSERT/UPDATE/DELETE can only happen via order_management_pkg
-- (which runs with the owner's privileges via definer's rights).
REVOKE INSERT, UPDATE, DELETE ON orders FROM PUBLIC;

-- Optional (recommended, not required tonight): create a dedicated,
-- least-privilege application user matching the course naming
-- convention, e.g.:
--   CREATE USER 2210_2025_YourName_Restaurant_DB IDENTIFIED BY "SomeStrongPass1";
--   GRANT CONNECT TO 2210_2025_YourName_Restaurant_DB;
--   GRANT restaurant_app_role TO 2210_2025_YourName_Restaurant_DB;
-- Not applied here because app.py currently connects as SYSTEM, and
-- switching that at 1am risks breaking your working demo. Mention
-- this as a "next step" during your presentation if asked about the
-- naming convention requirement.

COMMIT;
