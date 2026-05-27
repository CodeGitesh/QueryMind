-- ============================================================
-- Finance Schema + Seed Data
-- ============================================================

CREATE SCHEMA IF NOT EXISTS finance;
SET search_path TO finance, public;

CREATE TABLE IF NOT EXISTS categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    type        VARCHAR(50)  NOT NULL DEFAULT 'expense',  -- expense/income/transfer
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS accounts (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(200) NOT NULL,
    account_type VARCHAR(50)  NOT NULL DEFAULT 'checking',  -- checking/savings/investment/credit
    currency     VARCHAR(10)  NOT NULL DEFAULT 'USD',
    balance      NUMERIC(14,2) NOT NULL DEFAULT 0,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS transactions (
    id           SERIAL PRIMARY KEY,
    account_id   INTEGER       NOT NULL REFERENCES accounts(id),
    category_id  INTEGER       REFERENCES categories(id),
    amount       NUMERIC(12,2) NOT NULL,
    type         VARCHAR(20)   NOT NULL DEFAULT 'debit',  -- debit/credit
    description  VARCHAR(500),
    merchant     VARCHAR(200),
    transaction_date DATE      NOT NULL,
    reference    VARCHAR(100),
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_transactions_account_id       ON transactions(account_id);
CREATE INDEX IF NOT EXISTS idx_transactions_category_id      ON transactions(category_id);
CREATE INDEX IF NOT EXISTS idx_transactions_transaction_date ON transactions(transaction_date);

CREATE TABLE IF NOT EXISTS budgets (
    id          SERIAL PRIMARY KEY,
    category_id INTEGER       NOT NULL REFERENCES categories(id),
    amount      NUMERIC(12,2) NOT NULL,
    period      VARCHAR(20)   NOT NULL DEFAULT 'monthly',  -- monthly/quarterly/annual
    year        INTEGER       NOT NULL,
    month       INTEGER,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_budgets_category_id ON budgets(category_id);

CREATE TABLE IF NOT EXISTS monthly_summaries (
    id             SERIAL PRIMARY KEY,
    account_id     INTEGER       NOT NULL REFERENCES accounts(id),
    year           INTEGER       NOT NULL,
    month          INTEGER       NOT NULL CHECK (month BETWEEN 1 AND 12),
    total_income   NUMERIC(14,2) NOT NULL DEFAULT 0,
    total_expenses NUMERIC(14,2) NOT NULL DEFAULT 0,
    net_savings    NUMERIC(14,2) NOT NULL DEFAULT 0,
    transaction_count INTEGER   NOT NULL DEFAULT 0,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    UNIQUE(account_id, year, month)
);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_account_id ON monthly_summaries(account_id);
CREATE INDEX IF NOT EXISTS idx_monthly_summaries_year_month ON monthly_summaries(year, month);

CREATE TABLE IF NOT EXISTS investments (
    id            SERIAL PRIMARY KEY,
    account_id    INTEGER       NOT NULL REFERENCES accounts(id),
    symbol        VARCHAR(20)   NOT NULL,
    asset_type    VARCHAR(50)   NOT NULL DEFAULT 'stock',  -- stock/bond/etf/crypto/real_estate
    quantity      NUMERIC(16,6) NOT NULL,
    purchase_price NUMERIC(12,2) NOT NULL,
    current_price  NUMERIC(12,2) NOT NULL,
    purchase_date  DATE          NOT NULL,
    created_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at     TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_investments_account_id ON investments(account_id);
CREATE INDEX IF NOT EXISTS idx_investments_symbol     ON investments(symbol);

CREATE TABLE IF NOT EXISTS loans (
    id              SERIAL PRIMARY KEY,
    account_id      INTEGER       NOT NULL REFERENCES accounts(id),
    loan_type       VARCHAR(50)   NOT NULL DEFAULT 'personal',  -- personal/mortgage/auto/student
    principal       NUMERIC(14,2) NOT NULL,
    outstanding     NUMERIC(14,2) NOT NULL,
    interest_rate   NUMERIC(5,2)  NOT NULL,
    monthly_payment NUMERIC(12,2) NOT NULL,
    start_date      DATE          NOT NULL,
    end_date        DATE          NOT NULL,
    status          VARCHAR(50)   NOT NULL DEFAULT 'active',
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_loans_account_id ON loans(account_id);

-- ── Seed Data ─────────────────────────────────────────────────────────────────

INSERT INTO categories (name, type) VALUES
  ('Salary',          'income'),
  ('Freelance',       'income'),
  ('Dividends',       'income'),
  ('Rent',            'expense'),
  ('Groceries',       'expense'),
  ('Transportation',  'expense'),
  ('Healthcare',      'expense'),
  ('Entertainment',   'expense'),
  ('Utilities',       'expense'),
  ('Insurance',       'expense'),
  ('Education',       'expense'),
  ('Travel',          'expense'),
  ('Dining Out',      'expense'),
  ('Subscriptions',   'expense'),
  ('Transfer',        'transfer')
ON CONFLICT DO NOTHING;

INSERT INTO accounts (name, account_type, currency, balance) VALUES
  ('Main Checking',        'checking',   'USD', 25430.50),
  ('Emergency Savings',    'savings',    'USD', 52000.00),
  ('Investment Portfolio', 'investment', 'USD', 189500.00),
  ('Credit Card',          'credit',     'USD', -3200.00),
  ('Euro Account',         'checking',   'EUR', 8900.00),
  ('Retirement Fund',      'investment', 'USD', 340000.00),
  ('Business Checking',    'checking',   'USD', 78200.00),
  ('HSA Account',          'savings',    'USD', 12300.00)
ON CONFLICT DO NOTHING;

-- Transactions: 2 years of daily data across 8 accounts
INSERT INTO transactions (account_id, category_id, amount, type, description, merchant, transaction_date)
SELECT
  1 + ((i-1) % 8),
  1 + ((i-1) % 15),
  ROUND((10 + RANDOM() * 2990)::NUMERIC, 2),
  CASE WHEN (i % 3) = 0 THEN 'credit' ELSE 'debit' END,
  'Transaction ' || i,
  (ARRAY['Amazon','Walmart','Target','Starbucks','Netflix','Spotify','Shell','Whole Foods',
         'Apple','Google','Uber','Airbnb','Delta Airlines','Home Depot','CVS'])[1+(i%15)],
  DATE '2023-01-01' + ((i-1) % 730) * INTERVAL '1 day'
FROM generate_series(1, 1500) AS i
ON CONFLICT DO NOTHING;

-- Budgets
INSERT INTO budgets (category_id, amount, period, year, month)
SELECT
  cat_id,
  ROUND((500 + RANDOM() * 4500)::NUMERIC, 2),
  'monthly',
  yr,
  mo
FROM generate_series(1, 15) AS cat_id
CROSS JOIN generate_series(2023, 2024) AS yr
CROSS JOIN generate_series(1, 12) AS mo
ON CONFLICT DO NOTHING;

-- Monthly summaries (24 months x 8 accounts)
INSERT INTO monthly_summaries (account_id, year, month, total_income, total_expenses, net_savings, transaction_count)
SELECT
  acc_id,
  yr,
  mo,
  ROUND((3000 + RANDOM() * 7000)::NUMERIC, 2),
  ROUND((1500 + RANDOM() * 5000)::NUMERIC, 2),
  ROUND((500 + RANDOM() * 2500)::NUMERIC, 2),
  (10 + (acc_id * mo) % 90)::INT
FROM generate_series(1, 8) AS acc_id
CROSS JOIN generate_series(2023, 2024) AS yr
CROSS JOIN generate_series(1, 12) AS mo
ON CONFLICT DO NOTHING;

-- Investments
INSERT INTO investments (account_id, symbol, asset_type, quantity, purchase_price, current_price, purchase_date)
VALUES
  (3, 'AAPL',   'stock',  150.00,  142.50,  187.30, '2022-03-15'),
  (3, 'GOOGL',  'stock',   25.00, 2750.00, 3050.00, '2022-01-10'),
  (3, 'VTI',    'etf',    200.00,  215.00,  243.50, '2021-06-01'),
  (3, 'BTC',    'crypto',   2.50, 28000.00,43500.00, '2023-01-05'),
  (3, 'TSLA',   'stock',   75.00,  220.00,  250.00, '2022-09-20'),
  (6, 'VTSAX',  'etf',   1000.00,   95.00,  112.00, '2020-01-01'),
  (6, 'BONDS',  'bond',   500.00,  100.00,   98.50, '2021-01-01'),
  (6, 'AMZN',   'stock',   30.00, 3200.00, 3400.00, '2021-11-15'),
  (3, 'MSFT',   'stock',  100.00,  285.00,  380.00, '2022-02-14'),
  (3, 'SPY',    'etf',     80.00,  420.00,  470.00, '2022-07-04')
ON CONFLICT DO NOTHING;

-- Loans
INSERT INTO loans (account_id, loan_type, principal, outstanding, interest_rate, monthly_payment, start_date, end_date, status)
VALUES
  (1, 'mortgage', 450000, 380000, 3.75, 2083.33, '2019-06-01', '2049-06-01', 'active'),
  (1, 'auto',      28000,  12000, 5.25,  529.00, '2021-09-01', '2026-09-01', 'active'),
  (7, 'personal',  15000,   5500, 8.99,  311.00, '2022-03-15', '2027-03-15', 'active'),
  (1, 'student',   45000,  22000, 4.50,  467.00, '2018-09-01', '2028-09-01', 'active')
ON CONFLICT DO NOTHING;

RESET search_path;
