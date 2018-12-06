SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'break_article'
      AND pid <> pg_backend_pid();
DROP DATABASE break_article;
CREATE DATABASE break_article;
CREATE USER breaktime WITH ENCRYPTED PASSWORD 'breaktime';
GRANT ALL PRIVILEGES ON DATABASE break_article TO breaktime;
