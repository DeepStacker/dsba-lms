-- Create the main database user if it doesn't exist
DO $$
BEGIN
   IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'lmsadmin') THEN
      CREATE ROLE lmsadmin LOGIN PASSWORD 'apollo';
   END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE apollo_lms TO lmsadmin;
GRANT USAGE ON SCHEMA public TO lmsadmin;

-- Make sure lmsadmin can create schemas
ALTER ROLE lmsadmin CREATEDB;
