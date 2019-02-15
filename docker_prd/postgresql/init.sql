SELECT pg_terminate_backend(pg_stat_activity.pid)
    FROM pg_stat_activity
    WHERE pg_stat_activity.datname = 'break_content'
      AND pid <> pg_backend_pid();
DROP DATABASE break_content;
CREATE DATABASE break_content;
