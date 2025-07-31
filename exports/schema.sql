
DROP TABLE IF EXISTS feedback CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS agents CASCADE;

DROP TYPE IF EXISTS lead_status;

CREATE TYPE lead_status AS ENUM ('new', 'contacted', 'converted', 'rejected');

CREATE TABLE agents (
id SERIAL PRIMARY KEY,
name TEXT NOT NULL,
email TEXT UNIQUE NOT NULL
);
CREATE TABLE leads (
id SERIAL PRIMARY KEY,
full_name TEXT NOT NULL,
email TEXT UNIQUE NOT NULL,
phone TEXT,
status lead_status NOT NULL DEFAULT 'new',
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
assigned_agent_id INTEGER REFERENCES agents(id)
);
CREATE TABLE feedback (
id SERIAL PRIMARY KEY,
lead_id INTEGER REFERENCES leads(id),
agent_id INTEGER REFERENCES agents(id),
rating INTEGER CHECK (rating BETWEEN 1 AND 5),
comments TEXT,
submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);