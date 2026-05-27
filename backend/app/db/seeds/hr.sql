-- ============================================================
-- HR Schema + Seed Data
-- ============================================================

CREATE SCHEMA IF NOT EXISTS hr;
SET search_path TO hr, public;

CREATE TABLE IF NOT EXISTS departments (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL UNIQUE,
    budget      NUMERIC(14,2) DEFAULT 0,
    location    VARCHAR(200),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS roles (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    level       VARCHAR(50)  NOT NULL DEFAULT 'mid',
    min_salary  NUMERIC(12,2),
    max_salary  NUMERIC(12,2),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS employees (
    id            SERIAL PRIMARY KEY,
    first_name    VARCHAR(100) NOT NULL,
    last_name     VARCHAR(100) NOT NULL,
    email         VARCHAR(200) NOT NULL UNIQUE,
    department_id INTEGER      NOT NULL REFERENCES departments(id),
    role_id       INTEGER      NOT NULL REFERENCES roles(id),
    manager_id    INTEGER      REFERENCES employees(id),
    hire_date     DATE         NOT NULL,
    status        VARCHAR(50)  NOT NULL DEFAULT 'active',
    gender        VARCHAR(20),
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_role_id       ON employees(role_id);
CREATE INDEX IF NOT EXISTS idx_employees_hire_date     ON employees(hire_date);

CREATE TABLE IF NOT EXISTS salaries (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER       NOT NULL REFERENCES employees(id),
    amount      NUMERIC(12,2) NOT NULL,
    currency    VARCHAR(10)   NOT NULL DEFAULT 'USD',
    effective_from DATE       NOT NULL,
    effective_to   DATE,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_salaries_employee_id   ON salaries(employee_id);
CREATE INDEX IF NOT EXISTS idx_salaries_effective_from ON salaries(effective_from);

CREATE TABLE IF NOT EXISTS performance_reviews (
    id            SERIAL PRIMARY KEY,
    employee_id   INTEGER     NOT NULL REFERENCES employees(id),
    reviewer_id   INTEGER     NOT NULL REFERENCES employees(id),
    review_period VARCHAR(20) NOT NULL,
    score         INTEGER     NOT NULL CHECK (score BETWEEN 1 AND 5),
    feedback      TEXT,
    review_date   DATE        NOT NULL,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_perf_reviews_employee_id ON performance_reviews(employee_id);
CREATE INDEX IF NOT EXISTS idx_perf_reviews_review_date ON performance_reviews(review_date);

CREATE TABLE IF NOT EXISTS leave_requests (
    id          SERIAL PRIMARY KEY,
    employee_id INTEGER     NOT NULL REFERENCES employees(id),
    leave_type  VARCHAR(50) NOT NULL DEFAULT 'annual',
    start_date  DATE        NOT NULL,
    end_date    DATE        NOT NULL,
    days        INTEGER     NOT NULL,
    status      VARCHAR(50) NOT NULL DEFAULT 'pending',
    reason      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_start_date  ON leave_requests(start_date);

CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(300) NOT NULL,
    description TEXT,
    status      VARCHAR(50)  NOT NULL DEFAULT 'planning',
    start_date  DATE,
    end_date    DATE,
    budget      NUMERIC(14,2),
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS project_assignments (
    id          SERIAL PRIMARY KEY,
    project_id  INTEGER      NOT NULL REFERENCES projects(id),
    employee_id INTEGER      NOT NULL REFERENCES employees(id),
    role        VARCHAR(100) NOT NULL DEFAULT 'contributor',
    start_date  DATE         NOT NULL,
    end_date    DATE,
    hours_per_week INTEGER   DEFAULT 40,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_proj_assign_project_id  ON project_assignments(project_id);
CREATE INDEX IF NOT EXISTS idx_proj_assign_employee_id ON project_assignments(employee_id);

-- Seed departments
INSERT INTO departments (name, budget, location) VALUES
  ('Engineering', 5000000, 'San Francisco, CA'),
  ('Product',     2000000, 'New York, NY'),
  ('Marketing',   1500000, 'Chicago, IL'),
  ('Sales',       3000000, 'Austin, TX'),
  ('HR',           800000, 'Seattle, WA'),
  ('Finance',     1200000, 'Boston, MA'),
  ('Operations',  1000000, 'Denver, CO'),
  ('Data Science',2500000, 'San Francisco, CA'),
  ('Legal',        600000, 'New York, NY'),
  ('Support',      700000, 'Phoenix, AZ')
ON CONFLICT DO NOTHING;

-- Seed roles
INSERT INTO roles (title, level, min_salary, max_salary) VALUES
  ('Software Engineer I',      'junior',  60000,  90000),
  ('Software Engineer II',     'mid',     90000, 130000),
  ('Senior Software Engineer', 'senior', 130000, 180000),
  ('Engineering Manager',      'manager',180000, 260000),
  ('Product Manager',          'mid',    100000, 150000),
  ('Data Scientist',           'mid',     95000, 140000),
  ('Data Engineer',            'mid',     90000, 135000),
  ('Marketing Analyst',        'junior',  55000,  80000),
  ('Sales Representative',     'mid',     65000, 100000),
  ('HR Specialist',            'mid',     60000,  90000),
  ('Financial Analyst',        'mid',     70000, 110000),
  ('DevOps Engineer',          'mid',     95000, 140000),
  ('QA Engineer',              'mid',     75000, 115000),
  ('Staff Engineer',           'lead',   170000, 230000),
  ('Director',                 'manager',220000, 320000)
ON CONFLICT DO NOTHING;

-- Seed employees (500 rows via generate_series)
INSERT INTO employees (first_name, last_name, email, department_id, role_id, hire_date, status, gender)
SELECT
  (ARRAY['Alice','Bob','Carol','David','Emma','Frank','Grace','Henry','Iris','Jack',
         'Karen','Leo','Mia','Noah','Olivia','Paul','Quinn','Rachel','Sam','Tina'])[1 + (i % 20)],
  (ARRAY['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez',
         'Hernandez','Lopez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin','Lee'])[1 + ((i*7) % 20)],
  'emp' || i || '@hr.querymind.io',
  1 + ((i - 1) % 10),
  1 + ((i - 1) % 15),
  DATE '2018-01-01' + ((i * 13) % 2000) * INTERVAL '1 day',
  (ARRAY['active','active','active','inactive','on_leave'])[1 + (i % 5)],
  (ARRAY['Male','Female','Non-binary'])[1 + (i % 3)]
FROM generate_series(1, 500) AS i
ON CONFLICT DO NOTHING;

-- Salaries
INSERT INTO salaries (employee_id, amount, effective_from)
SELECT id, ROUND((70000 + RANDOM() * 130000)::NUMERIC, 2), hire_date
FROM employees
ON CONFLICT DO NOTHING;

-- Performance reviews
INSERT INTO performance_reviews (employee_id, reviewer_id, review_period, score, review_date)
SELECT
  e.id,
  1 + ((e.id * 3) % 500),
  yr || '-Q' || q,
  1 + (e.id % 5),
  (yr || '-0' || (q*3) || '-15')::DATE
FROM employees e
CROSS JOIN (VALUES (2023,1),(2023,2),(2023,3),(2023,4),(2024,1),(2024,2)) AS t(yr,q)
WHERE e.id <= 200
ON CONFLICT DO NOTHING;

-- Leave requests
INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, days, status)
SELECT
  1 + ((i-1) % 500),
  (ARRAY['annual','sick','maternity','paternity','unpaid'])[1+(i%5)],
  DATE '2024-01-01' + ((i*17) % 365) * INTERVAL '1 day',
  DATE '2024-01-01' + ((i*17) % 365) * INTERVAL '1 day' + (1+(i%14)) * INTERVAL '1 day',
  1 + (i % 14),
  (ARRAY['approved','approved','rejected','pending','approved'])[1+(i%5)]
FROM generate_series(1, 300) AS i
ON CONFLICT DO NOTHING;

-- Projects
INSERT INTO projects (name, status, start_date, end_date, budget)
SELECT
  'Project-' || chr(64+i),
  (ARRAY['planning','active','completed','on_hold'])[1+(i%4)],
  DATE '2023-01-01' + (i*30) * INTERVAL '1 day',
  DATE '2023-01-01' + (i*30+180) * INTERVAL '1 day',
  ROUND((50000 + RANDOM()*450000)::NUMERIC, 2)
FROM generate_series(1, 26) AS i
ON CONFLICT DO NOTHING;

-- Project assignments
INSERT INTO project_assignments (project_id, employee_id, role, start_date)
SELECT
  1 + ((i-1) % 26),
  1 + ((i*7) % 500),
  (ARRAY['lead','contributor','reviewer','tester','architect'])[1+(i%5)],
  DATE '2023-01-01' + ((i*23) % 365) * INTERVAL '1 day'
FROM generate_series(1, 500) AS i
ON CONFLICT DO NOTHING;

RESET search_path;
