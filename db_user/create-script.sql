/********************************************************
 * This script creates the database named user_database
 *********************************************************/
DROP DATABASE IF EXISTS user_database;

CREATE DATABASE user_database;

USE user_database;

/********************************************************
 *                      TABLES                          *
 ********************************************************/
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

CREATE TABLE addresses (
    address_id              INT             PRIMARY KEY     AUTO_INCREMENT,
    line1                   VARCHAR(60)     NOT NULL,
    line2                   VARCHAR(60)     DEFAULT NULL,
    city                    VARCHAR(40)     NOT NULL,
    state                   VARCHAR(2)      NOT NULL,
    zip_code                VARCHAR(10)     NOT NULL,
    phone                   VARCHAR(12)     NOT NULL,
    disabled                TINYINT(1)      NOT NULL DEFAULT 0,
);

CREATE TABLE payment_methods (
    payment_method_id       INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    billing_address_id      INT             NOT NULL,
    card_last_four          VARCHAR(4)      NOT NULL,
    card_type               VARCHAR(60)     NOT NULL,
    expiration_month        INT             NOT NULL,
    expiration_year         INT             NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id),
    FOREIGN KEY(billing_address_id) REFERENCES addresses (address_id)
);

/********************************************************
 *                      INSERTS                         *
 ********************************************************/
INSERT INTO users (user_id, first_name, last_name, email, password, shipping_address_id, billing_address_id) VALUES
    (1, 'Aniket', 'Jaldu', 'jaldua@wit.edu', '6a718fbd768c2378b511f8249b54897f940e9022', 1, 1),
    (2, 'Denis', 'Le', 'led11@wit.edu', '971e95957d3b74d70d79c20c94e9cd91b85f7aae', 2, 2),
    (3, 'Jovaughn', 'Oliver', 'oliverj@wit.edu', '974e95957d3b74d70d79c20c94e9cd91b85f7aae', 3, 3),
    (4, 'Timmy', 'Tran', 'ttran@wit.edu', '3f2975c819cefc686282456aeae3a137bf896ee8', 4, 4);

INSERT INTO user_roles (user_id, role) VALUES
    (1, 'admin'),
    (2, 'admin'),
    (3, 'admin'),
    (4, 'admin');

INSERT INTO addresses (address_id, line1, line2, city, state, zip_code, phone, disabled) VALUES
    (1, '123 Main St', 'Apt 4B', 'Springfield', 'IL', '62704', '217-555-1234', 0),
    (2, '456 Oak Ave', NULL, 'Madison', 'WI', '53703', '608-555-5678', 0),
    (3, '789 Maple Dr', 'Suite 200', 'Denver', 'CO', '80203', '303-555-9012', 0),
    (4, '321 Pine Ln', NULL, 'Austin', 'TX', '78701', '512-555-3456', 0),
    (5, '654 Birch Blvd', 'Unit 5', 'Portland', 'OR', '97205', '503-555-7890', 1);

INSERT INTO payment_methods (payment_method_id, user_id, billing_address_id, card_last_four, card_type, expiration_month, expiration_year) VALUES
    (1, 10, 1, '4242', 'Visa', 12, 2027),
    (2, 11, 2, '1111', 'MasterCard', 6, 2026),
    (3, 12, 3, '5678', 'Amex', 3, 2028),
    (4, 13, 4, '9999', 'Discover', 9, 2025),
    (5, 14, 5, '3456', 'Visa', 1, 2029);