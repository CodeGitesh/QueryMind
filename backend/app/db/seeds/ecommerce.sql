-- ============================================================
-- E-Commerce Schema + Seed Data (~500 rows per table)
-- ============================================================

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ── Schema ────────────────────────────────────────────────────────────────────
CREATE SCHEMA IF NOT EXISTS ecommerce;

SET search_path TO ecommerce, public;

-- ── Tables ────────────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sellers (
    id             SERIAL PRIMARY KEY,
    name           VARCHAR(200) NOT NULL,
    email          VARCHAR(200) NOT NULL UNIQUE,
    rating         NUMERIC(3,2) DEFAULT 0.00,
    total_sales    INTEGER      DEFAULT 0,
    country        VARCHAR(100),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS products (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(300) NOT NULL,
    description  TEXT,
    price        NUMERIC(10,2) NOT NULL,
    stock        INTEGER       NOT NULL DEFAULT 0,
    category_id  INTEGER       NOT NULL REFERENCES categories(id),
    seller_id    INTEGER       NOT NULL REFERENCES sellers(id),
    sku          VARCHAR(100) UNIQUE,
    is_active    BOOLEAN      DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_seller_id   ON products(seller_id);

CREATE TABLE IF NOT EXISTS customers (
    id         SERIAL PRIMARY KEY,
    name       VARCHAR(200) NOT NULL,
    email      VARCHAR(200) NOT NULL UNIQUE,
    phone      VARCHAR(30),
    country    VARCHAR(100),
    city       VARCHAR(100),
    created_at TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id              SERIAL PRIMARY KEY,
    customer_id     INTEGER      NOT NULL REFERENCES customers(id),
    status          VARCHAR(50)  NOT NULL DEFAULT 'pending',
    total_amount    NUMERIC(12,2) NOT NULL DEFAULT 0,
    shipping_cost   NUMERIC(8,2) DEFAULT 0,
    discount_amount NUMERIC(8,2) DEFAULT 0,
    payment_method  VARCHAR(50),
    ordered_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    shipped_at      TIMESTAMPTZ,
    delivered_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_orders_ordered_at  ON orders(ordered_at);
CREATE INDEX IF NOT EXISTS idx_orders_status      ON orders(status);

CREATE TABLE IF NOT EXISTS order_items (
    id          SERIAL PRIMARY KEY,
    order_id    INTEGER       NOT NULL REFERENCES orders(id),
    product_id  INTEGER       NOT NULL REFERENCES products(id),
    quantity    INTEGER       NOT NULL DEFAULT 1,
    unit_price  NUMERIC(10,2) NOT NULL,
    total_price NUMERIC(12,2) NOT NULL,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_order_items_order_id   ON order_items(order_id);
CREATE INDEX IF NOT EXISTS idx_order_items_product_id ON order_items(product_id);

CREATE TABLE IF NOT EXISTS reviews (
    id          SERIAL PRIMARY KEY,
    product_id  INTEGER NOT NULL REFERENCES products(id),
    customer_id INTEGER NOT NULL REFERENCES customers(id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title       VARCHAR(300),
    body        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_reviews_product_id  ON reviews(product_id);
CREATE INDEX IF NOT EXISTS idx_reviews_customer_id ON reviews(customer_id);

-- ── Seed Data ─────────────────────────────────────────────────────────────────

INSERT INTO categories (name, description) VALUES
  ('Electronics',       'Gadgets and electronic devices'),
  ('Clothing',          'Fashion and apparel'),
  ('Books',             'Physical and digital books'),
  ('Home & Garden',     'Furniture, decor, and gardening'),
  ('Sports & Outdoors', 'Athletic gear and outdoor equipment'),
  ('Beauty',            'Cosmetics and personal care'),
  ('Automotive',        'Car parts and accessories'),
  ('Toys',              'Children toys and games'),
  ('Food & Beverage',   'Gourmet food and drinks'),
  ('Health',            'Supplements and wellness products')
ON CONFLICT DO NOTHING;

INSERT INTO sellers (name, email, rating, total_sales, country) VALUES
  ('TechHub Store',    'sales@techhub.com',      4.7, 12350, 'USA'),
  ('FashionForward',   'info@fashionforward.com', 4.5,  8900, 'UK'),
  ('BookWorld',        'contact@bookworld.com',   4.8,  5600, 'Canada'),
  ('HomeEssentials',   'hello@homeessentials.com',4.3,  7800, 'Australia'),
  ('SportsPro',        'team@sportspro.com',      4.6,  9400, 'USA'),
  ('GlowBeauty',       'info@glowbeauty.com',     4.4,  6700, 'France'),
  ('AutoParts Direct', 'orders@autoparts.com',    4.2,  3200, 'Germany'),
  ('ToyLand',          'play@toyland.com',        4.9,  4500, 'Japan'),
  ('GourmetGrocer',    'fresh@gourmet.com',       4.6,  2100, 'Italy'),
  ('WellnessPlus',     'care@wellnessplus.com',   4.5,  3800, 'USA')
ON CONFLICT DO NOTHING;

-- Customers (100 rows)
INSERT INTO customers (name, email, phone, country, city)
SELECT
  'Customer ' || i,
  'customer' || i || '@example.com',
  '+1-555-' || LPAD(i::TEXT, 7, '0'),
  (ARRAY['USA','UK','Canada','Australia','Germany','France','Japan','India','Brazil','Mexico'])[1 + (i % 10)],
  (ARRAY['New York','London','Toronto','Sydney','Berlin','Paris','Tokyo','Mumbai','São Paulo','Mexico City'])[1 + (i % 10)]
FROM generate_series(1, 500) AS i
ON CONFLICT DO NOTHING;

-- Products (100 per category = 1000 total)
INSERT INTO products (name, description, price, stock, category_id, seller_id, sku)
SELECT
  cat.name || ' Product ' || i,
  'High quality ' || lower(cat.name) || ' product, model ' || i,
  ROUND((RANDOM() * 490 + 10)::NUMERIC, 2),
  (RANDOM() * 500 + 1)::INT,
  cat.id,
  1 + ((i - 1) % 10),
  cat.name || '-SKU-' || LPAD(i::TEXT, 5, '0')
FROM generate_series(1, 50) AS i
CROSS JOIN categories cat
ON CONFLICT DO NOTHING;

-- Orders (last 24 months, ~500 orders)
INSERT INTO orders (customer_id, status, total_amount, shipping_cost, discount_amount, payment_method, ordered_at, delivered_at)
SELECT
  1 + ((i - 1) % 500),
  (ARRAY['pending','processing','shipped','delivered','cancelled','refunded'])[1 + (i % 6)],
  ROUND((RANDOM() * 2000 + 20)::NUMERIC, 2),
  ROUND((RANDOM() * 30)::NUMERIC, 2),
  ROUND((RANDOM() * 50)::NUMERIC, 2),
  (ARRAY['credit_card','debit_card','paypal','stripe','bank_transfer'])[1 + (i % 5)],
  NOW() - (RANDOM() * INTERVAL '730 days'),
  CASE WHEN i % 6 = 3 THEN NOW() - (RANDOM() * INTERVAL '700 days') ELSE NULL END
FROM generate_series(1, 500) AS i
ON CONFLICT DO NOTHING;

-- Order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price, total_price)
SELECT
  o.id,
  1 + ((o.id + i - 1) % 500),
  (RANDOM() * 4 + 1)::INT,
  ROUND((RANDOM() * 200 + 10)::NUMERIC, 2),
  ROUND(((RANDOM() * 4 + 1) * (RANDOM() * 200 + 10))::NUMERIC, 2)
FROM orders o
CROSS JOIN generate_series(1, 2) AS i
ON CONFLICT DO NOTHING;

-- Reviews (300 rows)
INSERT INTO reviews (product_id, customer_id, rating, title, body)
SELECT
  1 + ((i - 1) % 500),
  1 + ((i - 1) % 500),
  1 + (i % 5),
  (ARRAY['Great product!','Highly recommend','Good value','Not as expected','Excellent quality'])[1 + (i % 5)],
  'Review body for product ' || i || '. Quality is ' || (ARRAY['excellent','good','average','poor','outstanding'])[1 + (i % 5)] || '.'
FROM generate_series(1, 500) AS i
ON CONFLICT DO NOTHING;

RESET search_path;
