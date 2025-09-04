-- Insert admin user directly
-- Password hash for 'Admin123!' (bcrypt)
INSERT INTO users (username, email, name, phone, role, hashed_password, is_active, created_at, updated_at)
VALUES (
    'admin',
    'admin@college.edu',
    'System Administrator',
    '+1234567890',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Pg/1J8bGxlI7E.AZa',  -- Admin123!
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Insert teacher user
INSERT INTO users (username, email, name, phone, role, hashed_password, is_active, created_at, updated_at)
VALUES (
    'john_teacher',
    'john.doe@college.edu',
    'John Doe',
    '+1234567890',
    'teacher',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Pg/1J8bGxlI7E.AZa',  -- Teacher123!
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Insert student user
INSERT INTO users (username, email, name, phone, role, hashed_password, is_active, created_at, updated_at)
VALUES (
    'alice_student',
    'alice.smith@college.edu',
    'Alice Smith',
    NULL,
    'student',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/Pg/1J8bGxlI7E.AZa',  -- Student123!
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

COMMIT;