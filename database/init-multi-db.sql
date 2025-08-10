-- Multi-Environment Database Setup
-- Creates separate databases for development, testing, and production

-- Create additional databases
CREATE DATABASE french_news_test;
CREATE DATABASE french_news_prod;

-- Connect to each database and set up schemas
\c french_news_dev;
\i /docker-entrypoint-initdb.d/init.sql

\c french_news_test;  
\i /docker-entrypoint-initdb.d/init.sql

\c french_news_prod;
\i /docker-entrypoint-initdb.d/init.sql

-- Grant permissions on all databases
GRANT ALL PRIVILEGES ON DATABASE french_news_dev TO news_user;
GRANT ALL PRIVILEGES ON DATABASE french_news_test TO news_user;  
GRANT ALL PRIVILEGES ON DATABASE french_news_prod TO news_user;