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
    billing_address_id      INT             DEFAULT NULL
);

CREATE TABLE user_roles (
    user_id                 INT             NOT NULL,
    role                    ENUM('customer', 'admin')       NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
);

CREATE TABLE addresses (
    address_id              INT             PRIMARY KEY     AUTO_INCREMENT,
    user_id                 INT             NOT NULL,
    line1                   VARCHAR(60)     NOT NULL,
    line2                   VARCHAR(60)     DEFAULT NULL,
    city                    VARCHAR(40)     NOT NULL,
    state                   VARCHAR(2)      NOT NULL,
    zip_code                VARCHAR(10)     NOT NULL,
    phone                   VARCHAR(12)     NOT NULL,
    disabled                TINYINT(1)      NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
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