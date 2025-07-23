/********************************************************
* This script creates the database named SneakerSppot 
*********************************************************/

DROP DATABASE IF EXISTS inventory_database;
CREATE DATABASE inventory_database;
USE inventory_database;


/********************************************************
 *                      TABLES                          *
 ********************************************************/

CREATE TABLE brands (
  brand_id           INT            PRIMARY KEY   AUTO_INCREMENT,
  brand_name         VARCHAR(255)   NOT NULL      UNIQUE
);

CREATE TABLE products (
  product_id         INT            PRIMARY KEY   AUTO_INCREMENT,
  brand_id           INT            NOT NULL,
  product_code       VARCHAR(10)    NOT NULL      UNIQUE,
  product_name       VARCHAR(255)   NOT NULL,
  description        TEXT           DEFAULT NULL,
  market_price         DECIMAL(10,2)  NOT NULL,
  discount_percent   DECIMAL(10,2)  NOT NULL      DEFAULT 0.00,
  date_added         DATETIME       DEFAULT NULL,
  CONSTRAINT products_fk_brands
    FOREIGN KEY (brand_id)
    REFERENCES brands (brand_id)
);


/********************************************************
 *                      INSERTS                         *
 ********************************************************/

-- Brands
INSERT INTO brands (brand_id, brand_name) VALUES
(1, 'Nike'),
(2, 'Adidas'),
(3, 'Jordan'),
(4, 'New Balance'),
(5, 'Yeezy');

-- Sneakers
-- Nike
INSERT INTO products (product_id, brand_id, product_code, product_name, description, market_price, discount_percent, date_added) VALUES
(1, 1, 'AF1', 'Air Force 1', 'Classic white low-top sneaker', 109.99, 30.00, '2025-07-18 09:32:40'),
(2, 1, 'AM90', 'Air Max 90', 'Retro running-inspired design', 129.99, 20.00, '2025-07-17 14:12:10'),
(3, 1, 'DUNK', 'Nike Dunk Low', 'Iconic court silhouette', 114.99, 15.00, '2025-07-16 11:45:22'),
(4, 1, 'TN97', 'Nike Tuned 97', 'Hybrid Air Max design', 169.99, 25.00, '2025-07-15 10:01:00'),
-- Adidas
(5, 2, 'ULTR', 'Ultraboost 22', 'Responsive running shoe', 179.99, 10.00, '2025-07-18 12:00:00'),
(6, 2, 'SAMB', 'Samba OG', 'Vintage indoor soccer style', 99.99, 5.00, '2025-07-16 09:32:40'),
(7, 2, 'FORU', 'Forum Low', 'Classic 80s b-ball shoe', 109.99, 12.00, '2025-07-15 08:20:40'),
(8, 2, 'GAZX', 'Gazelle', 'Timeless suede sneaker', 89.99, 8.00, '2025-07-14 07:45:00'),
-- Jordan
(9, 3, 'AJ1B', 'Air Jordan 1 Bred', 'High-top original colorway', 179.99, 0.00, '2025-07-18 13:00:00'),
(10, 3, 'AJ3W', 'Air Jordan 3 White Cement', 'Tinker Hatfield classic', 199.99, 5.00, '2025-07-17 10:30:00'),
(11, 3, 'AJ4P', 'Air Jordan 4 Panda', 'Black/white clean colorway', 209.99, 10.00, '2025-07-15 14:14:14'),
(12, 3, 'AJ11', 'Air Jordan 11 Concord', 'Patent leather shine', 219.99, 7.00, '2025-07-14 09:50:00'),
-- New Balance
(13, 4, 'NB99', '990v5', 'Made in USA lifestyle runner', 184.99, 12.00, '2025-07-18 11:11:11'),
(14, 4, 'NB55', '550 White/Green', 'Retro basketball silhouette', 109.99, 15.00, '2025-07-17 08:32:20'),
(15, 4, 'NB32', '327 Navy', 'Modern twist on vintage running', 99.99, 10.00, '2025-07-16 10:00:00'),
(16, 4, 'NB90', '9060 Grey', 'Chunky futuristic sneaker', 149.99, 18.00, '2025-07-15 13:30:00'),
-- Yeezy
(17, 5, 'YZ350', 'Yeezy Boost 350 V2', 'Primeknit + Boost comfort', 229.99, 5.00, '2025-07-18 14:00:00'),
(18, 5, 'YZ700', 'Yeezy 700 Wave Runner', 'Dad-shoe style with Boost', 299.99, 10.00, '2025-07-17 09:45:00'),
(19, 5, 'YZSLD', 'Yeezy Slide', 'Minimalist foam sandal', 69.99, 0.00, '2025-07-16 07:20:00'),
(20, 5, 'YZFMR', 'Yeezy Foam Runner', 'Futuristic one-piece design', 89.99, 7.00, '2025-07-15 06:00:00');