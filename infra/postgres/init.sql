-- FUB Follow-up Assistant Database Initialization
-- This script creates the necessary tables and indexes for the application

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create accounts table
CREATE TABLE IF NOT EXISTS accounts (
    account_id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    fub_access_token TEXT,
    fub_account_id VARCHAR(255) UNIQUE NOT NULL,
    fub_refresh_token TEXT,
    stripe_customer_id VARCHAR(255),
    subscription_status VARCHAR(50) DEFAULT 'trialing',
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create chat_messages table
CREATE TABLE IF NOT EXISTS chat_messages (
    answer TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    person_id VARCHAR(255) NOT NULL,
    question TEXT NOT NULL,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant'))
);

-- Create rate_limit_entries table
CREATE TABLE IF NOT EXISTS rate_limit_entries (
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(255) NOT NULL,
    request_count INTEGER DEFAULT 1,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_accounts_fub_account_id ON accounts(fub_account_id);
CREATE INDEX IF NOT EXISTS idx_accounts_stripe_customer_id ON accounts(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_person_id ON chat_messages(person_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_identifier ON rate_limit_entries(identifier);
CREATE INDEX IF NOT EXISTS idx_rate_limit_entries_window_start ON rate_limit_entries(window_start);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
CREATE TRIGGER update_accounts_updated_at 
    BEFORE UPDATE ON accounts 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data for development (only if not exists)
INSERT INTO accounts (fub_account_id, subscription_status) 
VALUES ('dev-account-123', 'active') 
ON CONFLICT (fub_account_id) DO NOTHING;

-- Clean up old rate limit entries (older than 24 hours)
CREATE OR REPLACE FUNCTION cleanup_old_rate_limits()
RETURNS void AS $$
BEGIN
    DELETE FROM rate_limit_entries 
    WHERE window_start < CURRENT_TIMESTAMP - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

-- Create a job to clean up old entries (this would be handled by a cron job in production)
-- For development, we'll rely on application-level cleanup

COMMENT ON TABLE accounts IS 'Stores Follow Up Boss account information and subscription details';
COMMENT ON TABLE chat_messages IS 'Stores all chat conversations between users and AI assistant';
COMMENT ON TABLE rate_limit_entries IS 'Tracks rate limiting data for API requests';

-- Grant permissions to application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO fubuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO fubuser; 