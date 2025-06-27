-- SQL commands to create tables for the Kinky game models

CREATE TABLE IF NOT EXISTS missions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    mission_type VARCHAR(50) NOT NULL,
    reward_type VARCHAR(50) NOT NULL,
    reward_amount INTEGER NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    mission_data JSONB,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS pistas (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    item_type VARCHAR(50) NOT NULL,
    content_text TEXT,
    content_url VARCHAR,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS backpack_items (
    user_id BIGINT NOT NULL REFERENCES users(id),
    pista_id INTEGER NOT NULL REFERENCES pistas(id),
    quantity INTEGER NOT NULL DEFAULT 1,
    obtained_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    PRIMARY KEY (user_id, pista_id)
);

