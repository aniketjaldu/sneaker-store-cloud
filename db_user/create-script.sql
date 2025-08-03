/********************************************************
 * This script creates the database named user_database
 *********************************************************/
DROP DATABASE IF EXISTS user_database;

CREATE DATABASE user_database;

USE user_database;

/********************************************************
 *                      TABLES                          *
 ********************************************************/
CREATE TABLE addresses (
    address_id              INT             PRIMARY KEY     AUTO_INCREMENT,
    line1                   VARCHAR(60)     NOT NULL,
    line2                   VARCHAR(60)     DEFAULT NULL,
    city                    VARCHAR(40)     NOT NULL,
    state                   VARCHAR(2)      NOT NULL,
    zip_code                VARCHAR(10)     NOT NULL,
    phone                   VARCHAR(12)     NOT NULL,
    disabled                TINYINT(1)      NOT NULL DEFAULT 0
);

CREATE TABLE users (
    user_id                 INT             PRIMARY KEY     AUTO_INCREMENT,
    first_name              VARCHAR(60)     NOT NULL,
    last_name               VARCHAR(60)     NOT NULL,
    email                   VARCHAR(255)    NOT NULL UNIQUE,
    password                VARCHAR(60)     NOT NULL,
    shipping_address_id     INT             DEFAULT NULL,
    billing_address_id      INT             DEFAULT NULL,
    FOREIGN KEY (shipping_address_id) REFERENCES addresses (address_id),
    FOREIGN KEY (billing_address_id) REFERENCES addresses (address_id)
);

CREATE TABLE user_roles (
    user_id                 INT             NOT NULL,
    role                    ENUM('customer', 'admin')       NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE refresh_tokens (
    token_id                INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    token_hash              VARCHAR(255)    NOT NULL,
    expires_at              DATETIME        NOT NULL,
    created_at              DATETIME        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE password_reset_tokens (
    token_id                INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    token_hash              VARCHAR(255)    NOT NULL        UNIQUE,
    expires_at              DATETIME        NOT NULL,
    created_at              DATETIME        NOT NULL        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE TABLE orders (
    order_id                INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    order_date              DATETIME        NOT NULL        DEFAULT CURRENT_TIMESTAMP,
    shipping_address_id     INT             DEFAULT NULL,
    billing_address_id      INT             DEFAULT NULL,
    email                   VARCHAR(255)    NOT NULL,
    subtotal_amount         DECIMAL(10,2)   NOT NULL,
    tax_amount              DECIMAL(10,2)   NOT NULL,
    total_amount            DECIMAL(10,2)   NOT NULL,
    order_status            ENUM('pending', 'processing', 'shipped', 'delivered', 'cancelled') NOT NULL DEFAULT 'pending',
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY (shipping_address_id) REFERENCES addresses (address_id),
    FOREIGN KEY (billing_address_id) REFERENCES addresses (address_id)
);

CREATE TABLE order_items (
    order_item_id           INT             PRIMARY KEY     AUTO_INCREMENT,
    order_id                INT             NOT NULL,
    product_id              INT             NOT NULL,
    quantity                INT             NOT NULL        DEFAULT 1,
    unit_price              DECIMAL(10,2)   NOT NULL,
    total_price             DECIMAL(10,2)   NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (order_id) ON DELETE CASCADE
);

CREATE TABLE shopping_cart (
    cart_id                 INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    product_id              INT             NOT NULL,
    quantity                INT             NOT NULL        DEFAULT 1,
    added_date              DATETIME        NOT NULL        DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    UNIQUE KEY unique_user_product (user_id, product_id)
    -- Note: product_id references inventory_database.products, but cross-database foreign keys
    -- are not supported in MySQL, so this will be enforced at application level
);

/********************************************************
 *                      INSERTS                         *
 ********************************************************/
INSERT INTO addresses (address_id, line1, line2, city, state, zip_code, phone, disabled) VALUES
    (1, '123 Main St', 'Apt 4B', 'Springfield', 'IL', '62704', '217-555-1234', 0),
    (2, '456 Oak Ave', NULL, 'Madison', 'WI', '53703', '608-555-5678', 0),
    (3, '789 Maple Dr', 'Suite 200', 'Denver', 'CO', '80203', '303-555-9012', 0),
    (4, '321 Pine Ln', NULL, 'Austin', 'TX', '78701', '512-555-3456', 0),
    (5, '654 Birch Blvd', 'Unit 5', 'Portland', 'OR', '97205', '503-555-7890', 1);

INSERT INTO users (user_id, first_name, last_name, email, password, shipping_address_id, billing_address_id) VALUES
    (1, 'Aniket', 'Jaldu', 'jaldua@wit.edu', 'f865b53623b121fd34ee5426c792e5c33af8c227', 1, 1),
    (2, 'Denis', 'Le', 'led11@wit.edu', 'f865b53623b121fd34ee5426c792e5c33af8c227', 2, 2),
    (3, 'Jovaughn', 'Oliver', 'oliverj@wit.edu', 'f865b53623b121fd34ee5426c792e5c33af8c227', 3, 3),
    (4, 'Timmy', 'Tran', 'ttran@wit.edu', 'f865b53623b121fd34ee5426c792e5c33af8c227', 4, 4),
    (5, 'Alice', 'Johnson', 'alice.johnson@example.com', 'cbfdac6008f9cab4083784cbd1874f76618d2a97', 1, 1),
    (6, 'Bob', 'Smith', 'bob.smith@example.com', 'cbfdac6008f9cab4083784cbd1874f76618d2a97', 2, 2),
    (7, 'Carol', 'Davis', 'carol.davis@example.com', 'cbfdac6008f9cab4083784cbd1874f76618d2a97', 3, 3),
    (8, 'David', 'Lee', 'david.lee@example.com', 'cbfdac6008f9cab4083784cbd1874f76618d2a97', 4, 4),
    (9, 'Emma', 'Martinez', 'emma.martinez@example.com', 'cbfdac6008f9cab4083784cbd1874f76618d2a97', 5, 5);

INSERT INTO user_roles (user_id, role) VALUES
    (1, 'admin'),
    (2, 'admin'),
    (3, 'admin'),
    (4, 'admin'),
    (5, 'customer'),
    (6, 'customer'),
    (7, 'customer'),
    (8, 'customer'),
    (9, 'customer');

-- Sample orders
INSERT INTO orders (order_id, user_id, order_date, shipping_address_id, billing_address_id, email, subtotal_amount, tax_amount, total_amount, order_status) VALUES
    (1, 5, '2024-01-15 10:30:00', 1, 1, 'alice.johnson@example.com', 122.34, 7.65, 129.99, 'delivered'),
    (2, 6, '2024-01-20 14:15:00', 2, 2, 'bob.smith@example.com', 169.40, 10.59, 179.99, 'shipped'),
    (3, 7, '2024-01-25 09:45:00', 3, 3, 'carol.davis@example.com', 94.11, 5.88, 99.99, 'processing');

-- Sample order items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price) VALUES
    (1, 1, 2, 1, 129.99, 129.99),  -- Air Max 90
    (2, 2, 5, 1, 179.99, 179.99),  -- Ultraboost 22
    (3, 3, 6, 1, 99.99, 99.99);    -- Samba OG

-- Sample shopping cart items
INSERT INTO shopping_cart (cart_id, user_id, product_id, quantity, added_date) VALUES
    (1, 8, 1, 2, '2024-01-26 11:00:00'),  -- David has 2 Air Force 1s in cart
    (2, 9, 3, 1, '2024-01-26 15:30:00');  -- Emma has 1 Nike Dunk Low in cart