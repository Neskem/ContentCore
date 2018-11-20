DROP DATABASE break_article;
CREATE DATABASE break_article;
CREATE USER breaktime WITH ENCRYPTED PASSWORD 'breaktime';
GRANT ALL PRIVILEGES ON DATABASE break_article TO breaktime;
