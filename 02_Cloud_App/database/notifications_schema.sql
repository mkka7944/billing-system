-- SQL Schema for Notifications Table
-- This table stores user notifications for the billing system

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES staff(id) ON DELETE CASCADE,
    message TEXT NOT NULL,
    type VARCHAR(20) NOT NULL DEFAULT 'info' CHECK (type IN ('info', 'success', 'warning', 'error')),
    related_entity VARCHAR(50), -- e.g., 'bill', 'consumer', 'ticket'
    entity_id VARCHAR(100), -- ID of the related entity
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(type);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Sample data for testing
INSERT INTO notifications (user_id, message, type, related_entity, entity_id, is_read) VALUES
(1, 'New bill #BILL-001 has been created', 'info', 'bill', 'BILL-001', FALSE),
(1, 'Payment received for bill #BILL-002', 'success', 'bill', 'BILL-002', FALSE),
(2, 'Consumer #CONS-001 data has been updated', 'warning', 'consumer', 'CONS-001', TRUE),
(1, 'System maintenance scheduled for tonight', 'info', NULL, NULL, FALSE);